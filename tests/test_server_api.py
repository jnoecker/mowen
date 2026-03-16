"""Integration tests for the mowen server API."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from mowen_server.config import Settings, get_settings
from mowen_server.db import Base, init_db, engine as _engine, SessionLocal
from mowen_server.main import create_app


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """Create a test client with an in-memory SQLite database."""
    tmp = tmp_path_factory.mktemp("mowen_test")
    db_path = tmp / "test.db"
    upload_dir = tmp / "uploads"
    upload_dir.mkdir()

    settings = Settings(
        database_url=f"sqlite:///{db_path}",
        upload_dir=upload_dir,
    )

    # Override the settings dependency
    get_settings.cache_clear()
    original_get_settings = get_settings.__wrapped__

    def override_settings():
        return settings

    app = create_app()
    app.dependency_overrides[get_settings] = override_settings

    # Initialize the database before running tests
    init_db(settings.database_url)

    # Patch the runner to execute synchronously using the existing DB session
    # (avoids SQLite multi-connection locking issues in tests)
    from mowen_server.runner import experiment_runner, execute_experiment

    original_submit = experiment_runner.submit

    def sync_submit(experiment_id, db_url, upload_dir):
        from mowen_server.db import SessionLocal
        session = SessionLocal()
        try:
            execute_experiment(experiment_id, session)
        except Exception as e:
            session.rollback()
            from mowen_server.models import Experiment
            exp = session.get(Experiment, experiment_id)
            if exp:
                from datetime import datetime
                exp.status = "failed"
                exp.error_message = str(e)
                exp.completed_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    experiment_runner.submit = sync_submit  # type: ignore[assignment]

    with TestClient(app) as c:
        yield c

    experiment_runner.submit = original_submit  # type: ignore[assignment]
    # Cleanup
    get_settings.cache_clear()


@pytest.fixture
def uploaded_doc(client):
    """Upload a sample document and return its response data."""
    content = b"The quick brown fox jumps over the lazy dog."
    resp = client.post(
        "/api/v1/documents/",
        files={"file": ("sample.txt", content, "text/plain")},
        data={"title": "Sample", "author_name": "TestAuthor"},
    )
    assert resp.status_code == 201
    return resp.json()


# -----------------------------------------------------------------------
# Health
# -----------------------------------------------------------------------

class TestHealth:
    def test_health(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# -----------------------------------------------------------------------
# Pipeline (read-only)
# -----------------------------------------------------------------------

class TestPipeline:
    def test_list_canonicizers(self, client):
        resp = client.get("/api/v1/pipeline/canonicizers")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        names = {c["name"] for c in data}
        assert "unify_case" in names

    def test_list_event_drivers(self, client):
        resp = client.get("/api/v1/pipeline/event-drivers")
        assert resp.status_code == 200
        names = {c["name"] for c in resp.json()}
        assert "character_ngram" in names

    def test_list_event_cullers(self, client):
        resp = client.get("/api/v1/pipeline/event-cullers")
        assert resp.status_code == 200
        names = {c["name"] for c in resp.json()}
        assert "most_common" in names

    def test_list_distance_functions(self, client):
        resp = client.get("/api/v1/pipeline/distance-functions")
        assert resp.status_code == 200
        names = {c["name"] for c in resp.json()}
        assert "cosine" in names

    def test_list_analysis_methods(self, client):
        resp = client.get("/api/v1/pipeline/analysis-methods")
        assert resp.status_code == 200
        names = {c["name"] for c in resp.json()}
        assert "knn" in names

    def test_component_has_params(self, client):
        resp = client.get("/api/v1/pipeline/event-drivers")
        data = resp.json()
        ngram = next(c for c in data if c["name"] == "character_ngram")
        assert ngram["params"] is not None
        assert any(p["name"] == "n" for p in ngram["params"])


# -----------------------------------------------------------------------
# Documents
# -----------------------------------------------------------------------

class TestDocuments:
    def test_upload_document(self, client):
        content = b"Hello, world!"
        resp = client.post(
            "/api/v1/documents/",
            files={"file": ("hello.txt", content, "text/plain")},
            data={"title": "Hello Doc"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Hello Doc"
        assert data["original_filename"] == "hello.txt"
        assert data["char_count"] == len("Hello, world!")
        assert data["author_name"] is None

    def test_upload_with_author(self, client):
        resp = client.post(
            "/api/v1/documents/",
            files={"file": ("test.txt", b"content", "text/plain")},
            data={"title": "Test", "author_name": "Author X"},
        )
        assert resp.status_code == 201
        assert resp.json()["author_name"] == "Author X"

    def test_list_documents(self, client, uploaded_doc):
        resp = client.get("/api/v1/documents/")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert any(d["id"] == uploaded_doc["id"] for d in data)

    def test_get_document(self, client, uploaded_doc):
        resp = client.get(f"/api/v1/documents/{uploaded_doc['id']}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Sample"

    def test_get_document_not_found(self, client):
        resp = client.get("/api/v1/documents/99999")
        assert resp.status_code == 404

    def test_update_document(self, client, uploaded_doc):
        resp = client.patch(
            f"/api/v1/documents/{uploaded_doc['id']}",
            json={"title": "Updated Title", "author_name": "NewAuthor"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"
        assert resp.json()["author_name"] == "NewAuthor"

    def test_get_document_text(self, client, uploaded_doc):
        resp = client.get(f"/api/v1/documents/{uploaded_doc['id']}/text")
        assert resp.status_code == 200
        assert "quick brown fox" in resp.text

    def test_delete_document(self, client):
        # Upload, then delete
        resp = client.post(
            "/api/v1/documents/",
            files={"file": ("del.txt", b"delete me", "text/plain")},
            data={"title": "To Delete"},
        )
        doc_id = resp.json()["id"]
        resp = client.delete(f"/api/v1/documents/{doc_id}")
        assert resp.status_code == 204
        resp = client.get(f"/api/v1/documents/{doc_id}")
        assert resp.status_code == 404


# -----------------------------------------------------------------------
# Corpora
# -----------------------------------------------------------------------

class TestCorpora:
    def test_create_corpus(self, client):
        resp = client.post(
            "/api/v1/corpora/",
            json={"name": "Test Corpus", "description": "A test corpus"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Corpus"
        assert data["document_count"] == 0

    def test_list_corpora(self, client):
        resp = client.get("/api/v1/corpora/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_corpus(self, client):
        resp = client.post("/api/v1/corpora/", json={"name": "Fetch Me"})
        corpus_id = resp.json()["id"]
        resp = client.get(f"/api/v1/corpora/{corpus_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Fetch Me"

    def test_get_corpus_not_found(self, client):
        resp = client.get("/api/v1/corpora/99999")
        assert resp.status_code == 404

    def test_update_corpus(self, client):
        resp = client.post("/api/v1/corpora/", json={"name": "Old Name"})
        corpus_id = resp.json()["id"]
        resp = client.patch(
            f"/api/v1/corpora/{corpus_id}",
            json={"name": "New Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New Name"

    def test_delete_corpus(self, client):
        resp = client.post("/api/v1/corpora/", json={"name": "Delete Me"})
        corpus_id = resp.json()["id"]
        resp = client.delete(f"/api/v1/corpora/{corpus_id}")
        assert resp.status_code == 204

    def test_add_documents_to_corpus(self, client, uploaded_doc):
        resp = client.post("/api/v1/corpora/", json={"name": "With Docs"})
        corpus_id = resp.json()["id"]
        resp = client.post(
            f"/api/v1/corpora/{corpus_id}/documents",
            json={"document_ids": [uploaded_doc["id"]]},
        )
        assert resp.status_code == 200
        assert resp.json()["document_count"] == 1

    def test_remove_documents_from_corpus(self, client, uploaded_doc):
        resp = client.post("/api/v1/corpora/", json={"name": "Remove Test"})
        corpus_id = resp.json()["id"]
        client.post(
            f"/api/v1/corpora/{corpus_id}/documents",
            json={"document_ids": [uploaded_doc["id"]]},
        )
        resp = client.request(
            "DELETE",
            f"/api/v1/corpora/{corpus_id}/documents",
            json={"document_ids": [uploaded_doc["id"]]},
        )
        assert resp.status_code == 200
        assert resp.json()["document_count"] == 0


# -----------------------------------------------------------------------
# Experiments (end-to-end)
# -----------------------------------------------------------------------

class TestExperiments:
    def _setup_experiment(self, client):
        """Upload docs, create corpora, return corpus IDs."""
        # Known docs
        known_texts = [
            (b"The government must be strong to protect liberty and ensure order.", "Hamilton"),
            (b"A strong federal union requires the power of taxation and defense.", "Hamilton"),
            (b"The separation of powers prevents tyranny in republican government.", "Madison"),
            (b"Factions are controlled by the diversity of a large republic.", "Madison"),
        ]
        doc_ids_known = []
        for text, author in known_texts:
            resp = client.post(
                "/api/v1/documents/",
                files={"file": (f"{author.lower()}.txt", text, "text/plain")},
                data={"title": f"{author} doc", "author_name": author},
            )
            assert resp.status_code == 201
            doc_ids_known.append(resp.json()["id"])

        # Unknown doc
        resp = client.post(
            "/api/v1/documents/",
            files={"file": ("unknown.txt", b"The government must protect the union through strong federal power.", "text/plain")},
            data={"title": "Mystery doc"},
        )
        assert resp.status_code == 201
        unknown_id = resp.json()["id"]

        # Create corpora
        resp = client.post("/api/v1/corpora/", json={"name": "Known"})
        known_corpus_id = resp.json()["id"]
        client.post(
            f"/api/v1/corpora/{known_corpus_id}/documents",
            json={"document_ids": doc_ids_known},
        )

        resp = client.post("/api/v1/corpora/", json={"name": "Unknown"})
        unknown_corpus_id = resp.json()["id"]
        client.post(
            f"/api/v1/corpora/{unknown_corpus_id}/documents",
            json={"document_ids": [unknown_id]},
        )

        return known_corpus_id, unknown_corpus_id

    def test_create_experiment(self, client):
        known_cid, unknown_cid = self._setup_experiment(client)
        resp = client.post(
            "/api/v1/experiments/",
            json={
                "name": "Test Experiment",
                "config": {
                    "canonicizers": [{"name": "unify_case"}],
                    "event_drivers": [{"name": "character_ngram", "params": {"n": 3}}],
                    "event_cullers": [],
                    "distance_function": {"name": "cosine"},
                    "analysis_method": {"name": "nearest_neighbor"},
                },
                "known_corpus_ids": [known_cid],
                "unknown_corpus_ids": [unknown_cid],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Experiment"
        assert data["status"] in ("pending", "running", "completed")

    def test_list_experiments(self, client):
        resp = client.get("/api/v1/experiments/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_full_experiment_flow(self, client):
        """Submit experiment, check completion and results."""
        known_cid, unknown_cid = self._setup_experiment(client)
        resp = client.post(
            "/api/v1/experiments/",
            json={
                "name": "Full Flow",
                "config": {
                    "canonicizers": [{"name": "unify_case"}],
                    "event_drivers": [{"name": "word_events"}],
                    "event_cullers": [],
                    "distance_function": {"name": "cosine"},
                    "analysis_method": {"name": "nearest_neighbor"},
                },
                "known_corpus_ids": [known_cid],
                "unknown_corpus_ids": [unknown_cid],
            },
        )
        assert resp.status_code == 201
        exp_id = resp.json()["id"]

        # Runner executes synchronously in test mode
        resp = client.get(f"/api/v1/experiments/{exp_id}")
        status = resp.json()["status"]
        assert status == "completed", f"Experiment status: {status}, error: {resp.json().get('error_message')}"

        # Get results
        resp = client.get(f"/api/v1/experiments/{exp_id}/results")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) == 1
        assert len(results[0]["rankings"]) == 2
        authors = {r["author"] for r in results[0]["rankings"]}
        assert authors == {"Hamilton", "Madison"}

    def test_delete_experiment(self, client):
        known_cid, unknown_cid = self._setup_experiment(client)
        resp = client.post(
            "/api/v1/experiments/",
            json={
                "name": "Delete Me",
                "config": {
                    "canonicizers": [],
                    "event_drivers": [{"name": "word_events"}],
                    "event_cullers": [],
                    "distance_function": {"name": "cosine"},
                    "analysis_method": {"name": "nearest_neighbor"},
                },
                "known_corpus_ids": [known_cid],
                "unknown_corpus_ids": [unknown_cid],
            },
        )
        exp_id = resp.json()["id"]
        resp = client.delete(f"/api/v1/experiments/{exp_id}")
        assert resp.status_code == 204

    def test_experiment_not_found(self, client):
        resp = client.get("/api/v1/experiments/99999")
        assert resp.status_code == 404
