"""Tests for sample corpora: core data loading and server import endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from mowen.data import get_sample_corpus, get_sample_corpus_path, list_sample_corpora
from mowen_server.config import Settings, get_settings
from mowen_server.db import init_db
from mowen_server.main import create_app

# -----------------------------------------------------------------------
# Core data tests
# -----------------------------------------------------------------------


class TestCoreData:
    def test_list_sample_corpora(self):
        corpora = list_sample_corpora()
        assert len(corpora) >= 13
        ids = {c["id"] for c in corpora}
        assert "aaac_problem_a" in ids
        assert "aaac_problem_m" in ids

    def test_list_has_expected_fields(self):
        corpora = list_sample_corpora()
        entry = corpora[0]
        assert "id" in entry
        assert "name" in entry
        assert "description" in entry
        assert "num_known" in entry
        assert "num_unknown" in entry
        assert "num_authors" in entry

    def test_get_sample_corpus(self):
        corpus = get_sample_corpus("aaac_problem_a")
        assert corpus["id"] == "aaac_problem_a"
        assert corpus["name"] == "AAAC Problem A"
        assert len(corpus["known"]) == 38
        assert len(corpus["unknown"]) >= 13

    def test_get_sample_corpus_not_found(self):
        with pytest.raises(KeyError, match="not found"):
            get_sample_corpus("nonexistent")

    def test_corpus_files_exist(self):
        """Verify that all files referenced in the manifest actually exist."""
        data_dir = get_sample_corpus_path()
        corpus = get_sample_corpus("aaac_problem_a")
        for entry in corpus["known"]:
            assert (data_dir / entry["file"]).is_file(), f"Missing: {entry['file']}"
        for entry in corpus["unknown"]:
            assert (data_dir / entry["file"]).is_file(), f"Missing: {entry['file']}"

    def test_all_corpora_files_exist(self):
        """Verify that all files in all corpora exist."""
        data_dir = get_sample_corpus_path()
        for meta in list_sample_corpora():
            corpus = get_sample_corpus(meta["id"])
            for entry in corpus["known"] + corpus["unknown"]:
                assert (data_dir / entry["file"]).is_file(), (
                    f"Missing: {entry['file']} in {meta['id']}"
                )


# -----------------------------------------------------------------------
# Server API tests
# -----------------------------------------------------------------------


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    """Create a test client for sample corpora tests."""
    tmp = tmp_path_factory.mktemp("sample_corpora_test")
    db_path = tmp / "test.db"
    upload_dir = tmp / "uploads"
    upload_dir.mkdir()

    settings = Settings(
        database_url=f"sqlite:///{db_path}",
        upload_dir=upload_dir,
    )

    get_settings.cache_clear()

    def override_settings():
        return settings

    app = create_app(settings=settings)
    app.dependency_overrides[get_settings] = override_settings

    init_db(settings.database_url)

    with TestClient(app) as c:
        yield c

    get_settings.cache_clear()


class TestSampleCorporaAPI:
    def test_list_sample_corpora(self, client):
        resp = client.get("/api/v1/sample-corpora/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 13
        assert data[0]["id"] == "federalist_papers"
        assert data[0]["num_authors"] > 0

    def test_import_sample_corpus(self, client):
        resp = client.post("/api/v1/sample-corpora/aaac_problem_h/import")
        assert resp.status_code == 201
        data = resp.json()

        known = data["known_corpus"]
        unknown = data["unknown_corpus"]

        assert "Known" in known["name"]
        assert "Unknown" in unknown["name"]
        assert known["document_count"] == 3
        assert unknown["document_count"] == 3

    def test_import_creates_documents(self, client):
        """Importing creates real document records accessible via the documents API."""
        resp = client.post("/api/v1/sample-corpora/aaac_problem_j/import")
        assert resp.status_code == 201
        data = resp.json()

        # Verify documents exist in the known corpus
        known_id = data["known_corpus"]["id"]
        resp = client.get(f"/api/v1/corpora/{known_id}/documents")
        assert resp.status_code == 200
        docs = resp.json()
        assert len(docs) == 5  # Problem J has 5 known docs

        # Known docs should have author names
        assert all(d["author_name"] is not None for d in docs)

        # Verify unknown corpus documents
        unknown_id = data["unknown_corpus"]["id"]
        resp = client.get(f"/api/v1/corpora/{unknown_id}/documents")
        assert resp.status_code == 200
        unknown_docs = resp.json()
        assert len(unknown_docs) == 2  # Problem J has 2 unknown docs

        # Unknown docs should have true author names (from AAAC ground truth)
        assert all(d["author_name"] is not None for d in unknown_docs)

    def test_import_not_found(self, client):
        resp = client.post("/api/v1/sample-corpora/nonexistent/import")
        assert resp.status_code == 404

    def test_import_corpora_appear_in_list(self, client):
        """Imported corpora should show up in the general corpora listing."""
        resp = client.post("/api/v1/sample-corpora/aaac_problem_g/import")
        assert resp.status_code == 201
        data = resp.json()

        resp = client.get("/api/v1/corpora/")
        assert resp.status_code == 200
        corpus_names = {c["name"] for c in resp.json()}
        assert data["known_corpus"]["name"] in corpus_names
        assert data["unknown_corpus"]["name"] in corpus_names
