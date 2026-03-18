"""End-to-end pipeline test: small attribution experiment."""

import tempfile
from pathlib import Path

from mowen import Pipeline, PipelineConfig, load_document


def test_e2e_attribution_from_files():
    """Write sample texts to disk, load them, run attribution, verify results."""
    author_a_texts = [
        "I believe the proposed constitution deserves ratification. "
        "The union of states requires a strong federal government. "
        "Without adequate power, the government cannot protect liberty.",
        "The judiciary must be independent of political influence. "
        "Lifetime appointments ensure judges decide cases on merit. "
        "An independent judiciary protects the rights of individuals.",
    ]
    author_b_texts = [
        "The powers of the federal government must be strictly limited. "
        "States retain sovereignty over their internal affairs. "
        "A bill of rights is necessary to protect individual freedoms.",
        "Standing armies in peacetime threaten democratic governance. "
        "The militia provides sufficient defense for a free state. "
        "Citizens must remain vigilant against government overreach.",
    ]
    unknown_text = (
        "A strong federal government is essential for national defense. "
        "The constitution provides the framework for effective governance. "
        "Liberty is best protected by a well-structured government."
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir)
        known = []
        for i, text in enumerate(author_a_texts):
            f = p / f"a_{i}.txt"
            f.write_text(text, encoding="utf-8")
            known.append(load_document(str(f), author="Hamilton"))
        for i, text in enumerate(author_b_texts):
            f = p / f"b_{i}.txt"
            f.write_text(text, encoding="utf-8")
            known.append(load_document(str(f), author="AntiFederalist"))

        f_unknown = p / "unknown.txt"
        f_unknown.write_text(unknown_text, encoding="utf-8")
        unknown = [load_document(str(f_unknown))]

        config = PipelineConfig(
            canonicizers=[{"name": "unify_case"}, {"name": "normalize_whitespace"}],
            event_drivers=[{"name": "character_ngram", "params": {"n": 3}}],
            event_cullers=[{"name": "most_common", "params": {"n": 50}}],
            distance_function={"name": "cosine"},
            analysis_method={"name": "knn", "params": {"k": 3}},
        )
        results = Pipeline(config).execute(known, unknown)

        assert len(results) == 1
        result = results[0]
        assert len(result.rankings) == 2
        authors = {r.author for r in result.rankings}
        assert authors == {"Hamilton", "AntiFederalist"}
        # Verify scores are valid proportions summing to 1
        total = sum(r.score for r in result.rankings)
        assert abs(total - 1.0) < 1e-9
        assert result.top_author in ("Hamilton", "AntiFederalist")


def test_e2e_word_events_manhattan():
    """Different pipeline config: word events + manhattan + nearest neighbor."""
    from mowen.types import Document

    known = [
        Document(text="the cat sat on the mat the cat is fluffy", author="CatPerson"),
        Document(text="the dog ran in the park the dog is loyal", author="DogPerson"),
        Document(
            text="the cat played with yarn the fluffy cat purred", author="CatPerson"
        ),
    ]
    unknown = [Document(text="the cat napped on a soft fluffy blanket")]

    config = PipelineConfig(
        canonicizers=[{"name": "unify_case"}],
        event_drivers=[{"name": "word_events"}],
        distance_function={"name": "manhattan"},
        analysis_method={"name": "nearest_neighbor"},
    )
    results = Pipeline(config).execute(known, unknown)
    assert results[0].top_author == "CatPerson"
