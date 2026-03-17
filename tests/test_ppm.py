"""Tests for the PPM compression distance function."""

from mowen.distance_functions import distance_function_registry
from mowen.types import Event, Histogram


class TestPPMDistance:
    def test_registered(self):
        assert "ppm" in distance_function_registry.names()

    def test_identical_histograms_low_distance(self):
        h = Histogram({Event("hello"): 5, Event("world"): 3})
        df = distance_function_registry.create("ppm")
        dist = df.distance(h, h)
        assert dist >= 0.0
        # Self-distance should be low (text is predictable under own model)
        assert dist < 10.0

    def test_different_histograms_higher_distance(self):
        h1 = Histogram({Event("hello"): 5, Event("world"): 3})
        h2 = Histogram({Event("xyz"): 5, Event("abc"): 3})
        df = distance_function_registry.create("ppm")
        d_same = df.distance(h1, h1)
        d_diff = df.distance(h1, h2)
        # Different texts should have higher cross-entropy
        assert d_diff > d_same

    def test_symmetric(self):
        h1 = Histogram({Event("the"): 5, Event("cat"): 3})
        h2 = Histogram({Event("a"): 4, Event("dog"): 2})
        df = distance_function_registry.create("ppm")
        assert df.distance(h1, h2) == df.distance(h2, h1)

    def test_non_negative(self):
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        df = distance_function_registry.create("ppm")
        assert df.distance(h1, h2) >= 0.0

    def test_empty_histogram(self):
        h1 = Histogram()
        h2 = Histogram({Event("a"): 1})
        df = distance_function_registry.create("ppm")
        assert df.distance(h1, h2) == 1.0

    def test_order_parameter(self):
        h1 = Histogram({Event("hello"): 5, Event("world"): 3})
        h2 = Histogram({Event("hello"): 3, Event("there"): 4})
        d_low = distance_function_registry.create("ppm", {"order": 1})
        d_high = distance_function_registry.create("ppm", {"order": 8})
        dist_low = d_low.distance(h1, h2)
        dist_high = d_high.distance(h1, h2)
        # Both should be valid distances (may or may not differ)
        assert dist_low >= 0.0
        assert dist_high >= 0.0
