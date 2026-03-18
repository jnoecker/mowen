"""Tests for Phase 6 long-tail components."""

from __future__ import annotations

import math
import string

import pytest

from mowen.canonicizers import canonicizer_registry
from mowen.analysis_methods import analysis_method_registry
from mowen.distance_functions import distance_function_registry
from mowen.event_cullers import event_culler_registry
from mowen.event_drivers import event_driver_registry
from mowen.types import Document, Event, EventSet, Histogram

# ---------------------------------------------------------------------------
# Event drivers
# ---------------------------------------------------------------------------


class TestSyllablesPerWord:
    def test_basic(self):
        d = event_driver_registry.create("syllables_per_word")
        es = d.create_event_set("hello world")
        # "hello" = 2 syllables (hel-lo), "world" = 1
        assert Event("2") in es
        assert Event("1") in es

    def test_monosyllable(self):
        d = event_driver_registry.create("syllables_per_word")
        es = d.create_event_set("cat dog hat")
        assert all(e.data == "1" for e in es)

    def test_empty(self):
        d = event_driver_registry.create("syllables_per_word")
        assert len(d.create_event_set("")) == 0

    def test_minimum_one(self):
        """Words with no vowels should still count as 1 syllable."""
        d = event_driver_registry.create("syllables_per_word")
        es = d.create_event_set("Dr Mrs")
        assert all(e.data == "1" for e in es)


class TestSyllableTransitions:
    def test_basic(self):
        d = event_driver_registry.create("syllable_transitions", {"n": 2})
        es = d.create_event_set("hello beautiful world")
        # syllables: 2, 4, 1 -> bigrams: "2 4", "4 1"
        assert len(es) == 2

    def test_empty(self):
        d = event_driver_registry.create("syllable_transitions")
        assert len(d.create_event_set("")) == 0


class TestLineLength:
    def test_basic(self):
        d = event_driver_registry.create("line_length")
        es = d.create_event_set("hello world\nfoo bar baz")
        assert Event("2") in es
        assert Event("3") in es

    def test_empty_lines_skipped(self):
        d = event_driver_registry.create("line_length")
        es = d.create_event_set("hello\n\nworld")
        assert len(es) == 2

    def test_single_line(self):
        d = event_driver_registry.create("line_length")
        es = d.create_event_set("one two three")
        assert es[0].data == "3"


class TestNewLines:
    def test_basic(self):
        d = event_driver_registry.create("new_lines")
        es = d.create_event_set("line one\nline two\nline three")
        assert len(es) == 3
        assert Event("line one") in es

    def test_empty_lines_skipped(self):
        d = event_driver_registry.create("new_lines")
        es = d.create_event_set("hello\n\nworld")
        assert len(es) == 2

    def test_empty(self):
        d = event_driver_registry.create("new_lines")
        assert len(d.create_event_set("")) == 0


class TestPunctuationNGram:
    def test_basic(self):
        d = event_driver_registry.create("punctuation_ngram", {"n": 2})
        es = d.create_event_set("Hello, world! How are you?")
        # punctuation: , ! ?  -> bigrams: ",!", "!?"
        assert Event(",!") in es
        assert Event("!?") in es
        assert len(es) == 2

    def test_no_punctuation(self):
        d = event_driver_registry.create("punctuation_ngram")
        assert len(d.create_event_set("hello world")) == 0

    def test_empty(self):
        d = event_driver_registry.create("punctuation_ngram")
        assert len(d.create_event_set("")) == 0


class TestVowelMNLetterWords:
    def test_basic(self):
        d = event_driver_registry.create("vowel_mn_letter_words", {"m": 3, "n": 5})
        es = d.create_event_set("apple banana orange eat it all")
        assert Event("apple") in es
        assert Event("eat") in es
        assert Event("all") in es
        assert Event("banana") not in es  # consonant-initial
        assert Event("it") not in es  # too short (len 2 < m=3)

    def test_empty(self):
        d = event_driver_registry.create("vowel_mn_letter_words")
        assert len(d.create_event_set("")) == 0


# ---------------------------------------------------------------------------
# Canonicizer
# ---------------------------------------------------------------------------


class TestSmashI:
    def test_basic(self):
        c = canonicizer_registry.create("smash_i")
        assert c.process("I went to the store") == "i went to the store"

    def test_preserves_other_caps(self):
        c = canonicizer_registry.create("smash_i")
        result = c.process("I met Ian at IBM")
        assert result.startswith("i met ")
        # "Ian" and "IBM" should be preserved
        assert "Ian" in result
        assert "IBM" in result

    def test_mid_sentence(self):
        c = canonicizer_registry.create("smash_i")
        assert c.process("and I said") == "and i said"

    def test_no_i(self):
        c = canonicizer_registry.create("smash_i")
        assert c.process("hello world") == "hello world"


# ---------------------------------------------------------------------------
# Event cullers
# ---------------------------------------------------------------------------


def _make_event_sets():
    es1 = EventSet([Event("a"), Event("a"), Event("b"), Event("c")])
    es2 = EventSet([Event("a"), Event("b"), Event("b"), Event("c")])
    es3 = EventSet([Event("a"), Event("a"), Event("a"), Event("d")])
    return [es1, es2, es3]


class TestWeightedVariance:
    def test_keeps_top_n(self):
        c = event_culler_registry.create("weighted_variance", {"n": 2})
        c.init(_make_event_sets())
        assert len(c._kept_events) == 2

    def test_empty(self):
        c = event_culler_registry.create("weighted_variance", {"n": 5})
        c.init([])
        assert c._kept_events == set()


class TestSetCuller:
    def test_removes_duplicates(self):
        c = event_culler_registry.create("set_culler")
        es = EventSet([Event("a"), Event("b"), Event("a"), Event("c"), Event("b")])
        result = c.cull(es)
        assert len(result) == 3
        assert result[0] == Event("a")
        assert result[1] == Event("b")
        assert result[2] == Event("c")

    def test_no_duplicates(self):
        c = event_culler_registry.create("set_culler")
        es = EventSet([Event("x"), Event("y"), Event("z")])
        result = c.cull(es)
        assert len(result) == 3

    def test_empty(self):
        c = event_culler_registry.create("set_culler")
        assert len(c.cull(EventSet())) == 0


# ---------------------------------------------------------------------------
# Distance functions
# ---------------------------------------------------------------------------


class TestWEDDistance:
    def test_identical(self):
        d = distance_function_registry.create("wed")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_non_negative(self):
        d = distance_function_registry.create("wed")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert d.distance(h1, h2) >= 0.0

    def test_disjoint(self):
        d = distance_function_registry.create("wed")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        assert d.distance(h1, h2) > 0


class TestNominalKSDistance:
    def test_identical(self):
        d = distance_function_registry.create("nominal_ks")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("nominal_ks")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_half_manhattan(self):
        """Nominal KS should equal Manhattan / 2."""
        ks = distance_function_registry.create("nominal_ks")
        man = distance_function_registry.create("manhattan")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(ks.distance(h1, h2) - man.distance(h1, h2) / 2) < 1e-6

    def test_range(self):
        d = distance_function_registry.create("nominal_ks")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        assert 0.0 <= d.distance(h1, h2) <= 1.0


# ---------------------------------------------------------------------------
# Analysis methods
# ---------------------------------------------------------------------------


def _make_training_data():
    data = []
    for i, (a, b) in enumerate([(5, 1), (4, 2), (6, 1), (5, 2)]):
        data.append(
            (
                Document(text="", author="A", title=f"a{i}"),
                Histogram({Event("a"): a, Event("b"): b}),
            )
        )
    for i, (a, b) in enumerate([(1, 5), (2, 4), (1, 6), (2, 5)]):
        data.append(
            (
                Document(text="", author="B", title=f"b{i}"),
                Histogram({Event("a"): a, Event("b"): b}),
            )
        )
    return data


class TestBaggingNN:
    def test_attributes_correctly(self):
        method = analysis_method_registry.create(
            "bagging_nn", {"n_samples": 5, "sample_size": 100, "random_seed": 42}
        )
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "A"

    def test_all_authors_present(self):
        method = analysis_method_registry.create(
            "bagging_nn", {"n_samples": 3, "sample_size": 50, "random_seed": 42}
        )
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        assert {r.author for r in results} == {"A", "B"}

    def test_scores_sum_to_one_or_less(self):
        method = analysis_method_registry.create(
            "bagging_nn", {"n_samples": 5, "sample_size": 100, "random_seed": 42}
        )
        method.distance_function = distance_function_registry.create("cosine")
        method.train(_make_training_data())
        results = method.analyze(Histogram({Event("a"): 3, Event("b"): 3}))
        assert sum(r.score for r in results) <= 1.0 + 1e-9


class TestThinCrossEntropy:
    def test_attributes_correctly(self):
        method = analysis_method_registry.create("thin_xent", {"window": 5})
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 6, Event("b"): 1})
        results = method.analyze(unknown)
        assert results[0].author == "A"

    def test_all_authors_present(self):
        method = analysis_method_registry.create("thin_xent")
        method.train(_make_training_data())
        unknown = Histogram({Event("a"): 3, Event("b"): 3})
        results = method.analyze(unknown)
        assert {r.author for r in results} == {"A", "B"}

    def test_scores_sorted_ascending(self):
        """Lower cross-entropy = better match, so sorted ascending."""
        method = analysis_method_registry.create("thin_xent")
        method.train(_make_training_data())
        results = method.analyze(Histogram({Event("a"): 6, Event("b"): 1}))
        assert results[0].score <= results[-1].score

    def test_scores_non_negative(self):
        method = analysis_method_registry.create("thin_xent")
        method.train(_make_training_data())
        results = method.analyze(Histogram({Event("a"): 3, Event("b"): 3}))
        assert all(r.score >= 0 for r in results)
