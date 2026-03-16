"""Property-based tests for distance function mathematical invariants."""

from __future__ import annotations

import math

import pytest

from mowen.distance_functions import distance_function_registry
from mowen.types import Event, Histogram


def _make_histogram(items: dict[str, int]) -> Histogram:
    return Histogram({Event(k): v for k, v in items.items()})


# Symmetric distance functions (KL divergence and chi-square are asymmetric)
SYMMETRIC_DISTANCES = [
    "cosine", "euclidean", "manhattan",
    "bhattacharyya", "hellinger", "intersection", "histogram_intersection",
    "bray_curtis", "canberra", "chord", "angular_separation",
    "kendall_correlation", "pearson_correlation",
]

ALL_DISTANCES = SYMMETRIC_DISTANCES + ["kl_divergence", "chi_square"]

# Correlation-based distances don't satisfy d(x,x)=0 for uniform distributions
# (all-tied ranks -> tau=0 -> distance=0.5). They are rank-correlation distances,
# not true metrics.
IDENTITY_DISTANCES = [d for d in ALL_DISTANCES if d not in (
    "kendall_correlation", "pearson_correlation",
)]


# Sample histograms for property tests
HISTOGRAMS = [
    _make_histogram({"a": 3, "b": 1}),
    _make_histogram({"a": 1, "b": 3}),
    _make_histogram({"a": 1, "b": 1, "c": 1}),
    _make_histogram({"x": 10}),
    _make_histogram({"a": 1}),
    _make_histogram({"a": 5, "b": 2, "c": 3}),
    _make_histogram({"a": 1, "b": 1, "c": 1, "d": 1, "e": 1}),
]


class TestIdentityOfIndiscernibles:
    """d(x, x) == 0 for all metric distance functions and all histograms."""

    @pytest.mark.parametrize("name", IDENTITY_DISTANCES)
    @pytest.mark.parametrize("h", HISTOGRAMS, ids=lambda h: f"n={len(h)}")
    def test_self_distance_is_zero(self, name, h):
        d = distance_function_registry.create(name)
        assert d.distance(h, h) < 1e-6, f"{name}: d(x,x)={d.distance(h, h)}"


class TestSymmetry:
    """d(x, y) == d(y, x) for symmetric distance functions."""

    @pytest.mark.parametrize("name", SYMMETRIC_DISTANCES)
    def test_symmetric_pairs(self, name):
        d = distance_function_registry.create(name)
        for i, h1 in enumerate(HISTOGRAMS):
            for h2 in HISTOGRAMS[i + 1:]:
                d12 = d.distance(h1, h2)
                d21 = d.distance(h2, h1)
                if math.isinf(d12) and math.isinf(d21):
                    continue  # both inf is symmetric
                assert abs(d12 - d21) < 1e-6, (
                    f"{name}: d(h1,h2)={d12} != d(h2,h1)={d21}"
                )


class TestNonNegativity:
    """d(x, y) >= 0 for all distance functions."""

    @pytest.mark.parametrize("name", ALL_DISTANCES)
    def test_non_negative(self, name):
        d = distance_function_registry.create(name)
        for i, h1 in enumerate(HISTOGRAMS):
            for h2 in HISTOGRAMS[i:]:
                val = d.distance(h1, h2)
                assert val >= -1e-6, f"{name}: d={val} is negative"
