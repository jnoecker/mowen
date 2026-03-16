"""Tests for Phase 3 distance functions and event cullers."""

import math

from mowen.distance_functions import distance_function_registry
from mowen.event_cullers import event_culler_registry
from mowen.types import Event, EventSet, Histogram


# ---------------------------------------------------------------------------
# Distance functions
# ---------------------------------------------------------------------------


class TestKeseljWeightedDistance:
    def test_identical(self):
        d = distance_function_registry.create("keselj_weighted")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("keselj_weighted")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("keselj_weighted")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # Each event: (1-0)/(1+0) = 1, squared = 1. Two events -> 2.0
        assert abs(d.distance(h1, h2) - 2.0) < 1e-6

    def test_non_negative(self):
        d = distance_function_registry.create("keselj_weighted")
        h1 = Histogram({Event("a"): 5, Event("b"): 2})
        h2 = Histogram({Event("a"): 1, Event("c"): 3})
        assert d.distance(h1, h2) >= 0.0


class TestCrossEntropyDistance:
    def test_identical(self):
        d = distance_function_registry.create("cross_entropy")
        h = Histogram({Event("a"): 1, Event("b"): 1})
        # H(P, P) = -sum(p * log(p)) = entropy of P
        val = d.distance(h, h)
        expected = -2 * (0.5 * math.log(0.5))  # = log(2)
        assert abs(val - expected) < 1e-6

    def test_non_negative(self):
        d = distance_function_registry.create("cross_entropy")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert d.distance(h1, h2) >= 0.0


class TestSoergelDistance:
    def test_identical(self):
        d = distance_function_registry.create("soergel")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("soergel")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("soergel")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # |1-0|+|0-1| / max(1,0)+max(0,1) = 2/2 = 1.0
        assert abs(d.distance(h1, h2) - 1.0) < 1e-6

    def test_range(self):
        d = distance_function_registry.create("soergel")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert 0.0 <= d.distance(h1, h2) <= 1.0


class TestMatusitaDistance:
    def test_identical(self):
        d = distance_function_registry.create("matusita")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("matusita")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_related_to_hellinger(self):
        """Matusita should be exactly sqrt(2) * Hellinger."""
        m = distance_function_registry.create("matusita")
        h_dist = distance_function_registry.create("hellinger")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(m.distance(h1, h2) - math.sqrt(2) * h_dist.distance(h1, h2)) < 1e-6


class TestWaveHedgesDistance:
    def test_identical(self):
        d = distance_function_registry.create("wave_hedges")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("wave_hedges")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_non_negative(self):
        d = distance_function_registry.create("wave_hedges")
        h1 = Histogram({Event("a"): 5, Event("b"): 2, Event("c"): 3})
        h2 = Histogram({Event("a"): 1, Event("b"): 3, Event("c"): 2})
        assert d.distance(h1, h2) >= 0.0


# ---------------------------------------------------------------------------
# Event cullers
# ---------------------------------------------------------------------------


def _make_event_sets() -> list[EventSet]:
    """Create test event sets: 'a' appears in all, 'b' varies, 'c' is rare."""
    es1 = EventSet([Event("a"), Event("a"), Event("a"), Event("b"), Event("b")])
    es2 = EventSet([Event("a"), Event("a"), Event("b")])
    es3 = EventSet([Event("a"), Event("a"), Event("a"), Event("a"), Event("c")])
    return [es1, es2, es3]


class TestMeanAbsoluteDeviation:
    def test_keeps_top_n(self):
        c = event_culler_registry.create("mean_absolute_deviation", {"n": 1})
        event_sets = _make_event_sets()
        c.init(event_sets)
        # 'a' counts: [3,2,4] mean=3, MAD=2/3
        # 'b' counts: [2,1,0] mean=1, MAD=2/3
        # 'c' counts: [0,0,1] mean=1/3, MAD=2/9
        # 'a' and 'b' are tied for highest MAD; top-1 should pick one
        kept = c._kept_events
        assert len(kept) == 1
        assert kept <= {Event("a"), Event("b")}

    def test_keeps_all_when_n_exceeds(self):
        c = event_culler_registry.create("mean_absolute_deviation", {"n": 100})
        event_sets = _make_event_sets()
        c.init(event_sets)
        assert Event("a") in c._kept_events
        assert Event("b") in c._kept_events
        assert Event("c") in c._kept_events


class TestIndexOfDispersion:
    def test_keeps_top_n(self):
        c = event_culler_registry.create("index_of_dispersion", {"n": 2})
        event_sets = _make_event_sets()
        c.init(event_sets)
        assert len(c._kept_events) == 2

    def test_zero_mean_event(self):
        """Events that never appear should have IOD=0."""
        c = event_culler_registry.create("index_of_dispersion", {"n": 1})
        es = [EventSet([Event("a")])]
        c.init(es)
        assert Event("a") in c._kept_events


class TestExtremeCuller:
    def test_keeps_universal_events(self):
        c = event_culler_registry.create("extreme")
        event_sets = _make_event_sets()
        c.init(event_sets)
        # Only 'a' appears in all 3 event sets
        assert Event("a") in c._kept_events
        assert Event("b") not in c._kept_events  # missing from es3
        assert Event("c") not in c._kept_events  # missing from es1, es2

    def test_empty_input(self):
        c = event_culler_registry.create("extreme")
        c.init([])
        assert c._kept_events == set()

    def test_single_document(self):
        c = event_culler_registry.create("extreme")
        es = [EventSet([Event("a"), Event("b")])]
        c.init(es)
        assert c._kept_events == {Event("a"), Event("b")}
