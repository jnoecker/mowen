"""Tests for components from recent authorship attribution literature."""

from __future__ import annotations

import pytest

from mowen.analysis_methods import analysis_method_registry
from mowen.distance_functions import distance_function_registry
from mowen.event_cullers import event_culler_registry
from mowen.types import Document, Event, EventSet, Histogram


def _make_histogram(word_counts: dict[str, int]) -> Histogram:
    events = []
    for word, count in word_counts.items():
        events.extend([Event(data=word)] * count)
    return EventSet(events).to_histogram()


# -- NCD --


class TestNCD:
    def test_registered(self):
        assert "ncd" in distance_function_registry.names()

    def test_identical_histograms(self):
        h = _make_histogram({"the": 10, "quick": 5, "fox": 3})
        d = distance_function_registry.create("ncd")
        result = d.distance(h, h)
        # Identical texts should compress very well together.
        assert result < 0.5

    def test_disjoint_histograms(self):
        h1 = _make_histogram({"aaa": 20, "bbb": 20})
        h2 = _make_histogram({"xxx": 20, "yyy": 20})
        d = distance_function_registry.create("ncd")
        result = d.distance(h1, h2)
        # Completely different texts should have high NCD.
        assert result > 0.3

    def test_empty_histogram(self):
        h1 = _make_histogram({"a": 1})
        h2 = _make_histogram({})
        d = distance_function_registry.create("ncd")
        assert d.distance(h1, h2) == 1.0

    def test_range_zero_to_one(self):
        h1 = _make_histogram({"the": 10, "a": 5, "is": 3})
        h2 = _make_histogram({"the": 8, "a": 6, "was": 4})
        d = distance_function_registry.create("ncd")
        result = d.distance(h1, h2)
        # NCD can slightly exceed 1.0 due to compression overhead,
        # but should be in a reasonable range.
        assert 0.0 <= result <= 1.5


# -- Craig's Zeta --


class TestZeta:
    def test_registered(self):
        assert "zeta" in event_culler_registry.names()

    def test_basic_zeta(self):
        culler = event_culler_registry.create("zeta")
        culler.set_params({"threshold": 0.5, "primary_author": "A"})

        # Author A always uses "the" and "was", never "sehr"
        # Author B always uses "sehr" and "und", never "was"
        es_a1 = EventSet([Event("the"), Event("was"), Event("big")])
        es_a2 = EventSet([Event("the"), Event("was"), Event("small")])
        es_b1 = EventSet([Event("the"), Event("sehr"), Event("und")])
        es_b2 = EventSet([Event("the"), Event("sehr"), Event("und")])

        keep = culler.cull(
            [es_a1, es_a2, es_b1, es_b2],
            ["A", "A", "B", "B"],
        )

        # "was": dp=1.0, do=0.0, zeta=1.0 -> keep
        # "sehr": dp=0.0, do=1.0, zeta=-1.0 -> keep (|zeta| >= 0.5)
        # "the": dp=1.0, do=1.0, zeta=0.0 -> drop
        assert Event("was") in keep
        assert Event("sehr") in keep
        assert Event("the") not in keep

    def test_auto_selects_primary(self):
        culler = event_culler_registry.create("zeta")
        culler.set_params({"threshold": 0.0})

        es1 = EventSet([Event("a")])
        es2 = EventSet([Event("a")])
        es3 = EventSet([Event("b")])
        # Author A has 2 docs, B has 1 — A should be auto-selected.
        keep = culler.cull([es1, es2, es3], ["A", "A", "B"])
        assert len(keep) > 0


# -- Eder's Delta --


class TestEdersDelta:
    def test_registered(self):
        assert "eders_delta" in analysis_method_registry.names()

    def test_basic_attribution(self):
        m = analysis_method_registry.create("eders_delta")
        m.set_params({"top_n": 0})  # use all features

        known = [
            (
                Document(text="", author="A"),
                _make_histogram({"the": 10, "a": 8, "was": 5}),
            ),
            (
                Document(text="", author="A"),
                _make_histogram({"the": 12, "a": 7, "was": 6}),
            ),
            (
                Document(text="", author="B"),
                _make_histogram({"the": 3, "a": 2, "big": 10}),
            ),
            (
                Document(text="", author="B"),
                _make_histogram({"the": 4, "a": 1, "big": 8}),
            ),
        ]
        m.train(known)

        result = m.analyze(_make_histogram({"the": 11, "a": 9, "was": 4}))
        assert result[0].author == "A"
        assert m.lower_is_better is True

    def test_top_n_limits_features(self):
        m = analysis_method_registry.create("eders_delta")
        m.set_params({"top_n": 2})

        known = [
            (Document(text="", author="A"), _make_histogram({"a": 10, "b": 5, "c": 1})),
            (Document(text="", author="B"), _make_histogram({"a": 2, "b": 8, "c": 1})),
        ]
        m.train(known)
        result = m.analyze(_make_histogram({"a": 9, "b": 4, "c": 2}))
        # Should still produce results using only top 2 features.
        assert len(result) == 2
        assert result[0].author == "A"
