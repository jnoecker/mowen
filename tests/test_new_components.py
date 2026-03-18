"""Tests for components added from JGAAP experiment-redesign branch."""

from __future__ import annotations

import pytest

from mowen.distance_functions import distance_function_registry
from mowen.analysis_methods import analysis_method_registry
from mowen.event_drivers import event_driver_registry
from mowen.types import Document, Event, EventSet, Histogram

# -- Helpers --


def _make_histogram(word_counts: dict[str, int]) -> Histogram:
    events = []
    for word, count in word_counts.items():
        events.extend([Event(data=word)] * count)
    return EventSet(events).to_histogram()


SAMPLE_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "The fox was very quick and the dog was very lazy."
)


# -- Distance Functions --


class TestStamatatosDistance:
    def test_registered(self):
        assert "stamatatos" in distance_function_registry.names()

    def test_identical_histograms(self):
        h = _make_histogram({"a": 3, "b": 2})
        d = distance_function_registry.create("stamatatos")
        assert d.distance(h, h) == pytest.approx(0.0)

    def test_disjoint_histograms(self):
        h1 = _make_histogram({"a": 5})
        h2 = _make_histogram({"b": 5})
        d = distance_function_registry.create("stamatatos")
        # Each event has (2*(p-0)/(p+0))^2 = 4.0 for its side
        assert d.distance(h1, h2) == pytest.approx(8.0)

    def test_overlapping(self):
        h1 = _make_histogram({"a": 3, "b": 2, "c": 1})
        h2 = _make_histogram({"a": 1, "b": 2, "c": 3})
        d = distance_function_registry.create("stamatatos")
        result = d.distance(h1, h2)
        assert result > 0.0


class TestKendallTauB:
    def test_registered(self):
        assert "kendall_tau_b" in distance_function_registry.names()

    def test_identical_histograms(self):
        h = _make_histogram({"a": 3, "b": 2, "c": 1})
        d = distance_function_registry.create("kendall_tau_b")
        assert d.distance(h, h) == pytest.approx(0.0)

    def test_reversed_ranking(self):
        h1 = _make_histogram({"a": 3, "b": 2, "c": 1})
        h2 = _make_histogram({"a": 1, "b": 2, "c": 3})
        d = distance_function_registry.create("kendall_tau_b")
        result = d.distance(h1, h2)
        assert result > 0.5  # largely discordant

    def test_with_ties(self):
        h1 = _make_histogram({"a": 3, "b": 3, "c": 1})
        h2 = _make_histogram({"a": 1, "b": 2, "c": 3})
        d = distance_function_registry.create("kendall_tau_b")
        result = d.distance(h1, h2)
        assert 0.0 <= result <= 1.0


# -- Analysis Methods --


class TestMahalanobis:
    def test_registered(self):
        assert "mahalanobis" in analysis_method_registry.names()

    def test_basic_attribution(self):
        pytest.importorskip("numpy")
        m = analysis_method_registry.create("mahalanobis")

        known = [
            (Document(text="a a a b", author="A"), _make_histogram({"a": 3, "b": 1})),
            (Document(text="a a b b", author="A"), _make_histogram({"a": 2, "b": 2})),
            (Document(text="c c c d", author="B"), _make_histogram({"c": 3, "d": 1})),
            (Document(text="c c d d", author="B"), _make_histogram({"c": 2, "d": 2})),
        ]
        m.train(known)
        result = m.analyze(_make_histogram({"a": 4, "b": 1}))
        assert result[0].author == "A"
        assert m.lower_is_better is True


# -- Event Drivers --


class TestLeaveKOutNgrams:
    def test_character_registered(self):
        assert "leave_k_out_character_ngram" in event_driver_registry.names()

    def test_word_registered(self):
        assert "leave_k_out_word_ngram" in event_driver_registry.names()

    def test_character_basic(self):
        d = event_driver_registry.create("leave_k_out_character_ngram")
        d.set_params({"n": 3, "k": 1})
        es = d.create_event_set("abcd")
        # "abc" -> "_ b c", "a _ c", "a b _"
        # "bcd" -> "_ c d", "b _ d", "b c _"
        assert len(es) == 6
        assert Event(data="_ b c") in es

    def test_word_basic(self):
        d = event_driver_registry.create("leave_k_out_word_ngram")
        d.set_params({"n": 3, "k": 1})
        es = d.create_event_set("the quick brown fox")
        assert len(es) > 0
        # First trigram "the quick brown" -> "_ quick brown", "the _ brown", "the quick _"
        assert Event(data="_ quick brown") in es

    def test_k_equals_n_returns_empty(self):
        d = event_driver_registry.create("leave_k_out_character_ngram")
        d.set_params({"n": 3, "k": 3})
        es = d.create_event_set("abcdef")
        assert len(es) == 0


class TestTruncatedFrequency:
    def test_registered(self):
        assert "truncated_frequency" in event_driver_registry.names()

    def test_basic(self):
        d = event_driver_registry.create("truncated_frequency")
        # "the" appears 4x -> bin 2, "fox" 1x -> bin 0, etc.
        es = d.create_event_set("the the the the fox")
        h = es.to_histogram()
        # 4 occurrences of "the" -> log2(4) = 2 -> bin "2"
        assert h.absolute_frequency(Event(data="2")) == 4
        # 1 occurrence of "fox" -> log2(1) = 0 -> bin "0"
        assert h.absolute_frequency(Event(data="0")) == 1


class TestReactionTime:
    def test_registered(self):
        assert "reaction_time" in event_driver_registry.names()

    def test_basic_rt(self):
        d = event_driver_registry.create("reaction_time")
        es = d.create_event_set("the quick brown fox")
        # Should find at least some ELP entries
        assert len(es) > 0

    def test_basic_freq(self):
        d = event_driver_registry.create("reaction_time")
        d.set_params({"measure": "freq"})
        es = d.create_event_set("the quick brown fox")
        assert len(es) > 0

    def test_unknown_words_dropped(self):
        d = event_driver_registry.create("reaction_time")
        es = d.create_event_set("xyzzyplugh qwfwq")
        # Nonsense words should not be in ELP
        assert len(es) == 0
