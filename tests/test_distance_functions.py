"""Tests for distance function implementations."""

import math

from mowen.distance_functions import distance_function_registry
from mowen.types import Event, Histogram


class TestCosineDistance:
    def test_identical(self):
        d = distance_function_registry.create("cosine")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-9

    def test_orthogonal(self):
        d = distance_function_registry.create("cosine")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        assert abs(d.distance(h1, h2) - 1.0) < 1e-9

    def test_symmetric(self):
        d = distance_function_registry.create("cosine")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-9

    def test_empty_histograms(self):
        d = distance_function_registry.create("cosine")
        h1 = Histogram()
        h2 = Histogram({Event("a"): 1})
        assert d.distance(h1, h2) == 1.0

    def test_range(self):
        d = distance_function_registry.create("cosine")
        h1 = Histogram({Event("a"): 5, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("c"): 5})
        dist = d.distance(h1, h2)
        assert 0.0 <= dist <= 1.0


class TestManhattanDistance:
    def test_identical(self):
        d = distance_function_registry.create("manhattan")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-9

    def test_disjoint(self):
        d = distance_function_registry.create("manhattan")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # h1 has a=1.0, b=0.0; h2 has a=0.0, b=1.0
        # |1-0| + |0-1| = 2.0
        assert abs(d.distance(h1, h2) - 2.0) < 1e-9

    def test_symmetric(self):
        d = distance_function_registry.create("manhattan")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-9

    def test_known_value(self):
        d = distance_function_registry.create("manhattan")
        h1 = Histogram({Event("a"): 1, Event("b"): 1})  # a=0.5, b=0.5
        h2 = Histogram({Event("a"): 3, Event("b"): 1})  # a=0.75, b=0.25
        # |0.5-0.75| + |0.5-0.25| = 0.25 + 0.25 = 0.5
        assert abs(d.distance(h1, h2) - 0.5) < 1e-9


class TestEuclideanDistance:
    def test_identical(self):
        d = distance_function_registry.create("euclidean")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("euclidean")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("euclidean")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # h1: a=1.0, b=0.0; h2: a=0.0, b=1.0
        # sqrt((1-0)^2 + (0-1)^2) = sqrt(2)
        assert abs(d.distance(h1, h2) - math.sqrt(2.0)) < 1e-6

    def test_known_value(self):
        d = distance_function_registry.create("euclidean")
        h1 = Histogram({Event("a"): 1, Event("b"): 1})  # a=0.5, b=0.5
        h2 = Histogram({Event("a"): 3, Event("b"): 1})  # a=0.75, b=0.25
        # sqrt((0.5-0.75)^2 + (0.5-0.25)^2) = sqrt(0.0625+0.0625) = sqrt(0.125)
        assert abs(d.distance(h1, h2) - math.sqrt(0.125)) < 1e-6


class TestChiSquareDistance:
    def test_identical(self):
        d = distance_function_registry.create("chi_square")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("chi_square")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("chi_square")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # events: a, b. h1: a=1.0, b=0.0; h2: a=0.0, b=1.0
        # event a: q=0.0, skipped. event b: (0-1)^2/1 = 1.0
        assert abs(d.distance(h1, h2) - 1.0) < 1e-6

    def test_known_value(self):
        d = distance_function_registry.create("chi_square")
        h1 = Histogram({Event("a"): 1, Event("b"): 1})  # a=0.5, b=0.5
        h2 = Histogram({Event("a"): 3, Event("b"): 1})  # a=0.75, b=0.25
        # event a: (0.5-0.75)^2/0.75 = 0.0625/0.75 = 1/12
        # event b: (0.5-0.25)^2/0.25 = 0.0625/0.25 = 0.25
        expected = 1.0 / 12.0 + 0.25
        assert abs(d.distance(h1, h2) - expected) < 1e-6


class TestKLDivergence:
    def test_identical(self):
        d = distance_function_registry.create("kl_divergence")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("kl_divergence")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # h1: a=1.0. h2: a=0.0 -> epsilon. p*log(p/eps) = 1*log(1/1e-10) = log(1e10)
        expected = math.log(1e10)
        assert abs(d.distance(h1, h2) - expected) < 1e-6

    def test_known_value(self):
        d = distance_function_registry.create("kl_divergence")
        h1 = Histogram({Event("a"): 1, Event("b"): 1})  # a=0.5, b=0.5
        h2 = Histogram({Event("a"): 3, Event("b"): 1})  # a=0.75, b=0.25
        # 0.5*log(0.5/0.75) + 0.5*log(0.5/0.25) = 0.5*log(2/3) + 0.5*log(2)
        expected = 0.5 * math.log(2.0 / 3.0) + 0.5 * math.log(2.0)
        assert abs(d.distance(h1, h2) - expected) < 1e-6

    def test_non_negative(self):
        d = distance_function_registry.create("kl_divergence")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert d.distance(h1, h2) >= -1e-6


class TestBhattacharyyaDistance:
    def test_identical(self):
        d = distance_function_registry.create("bhattacharyya")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("bhattacharyya")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("bhattacharyya")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # BC = sqrt(1*0) + sqrt(0*1) = 0, so result is inf
        assert d.distance(h1, h2) == float("inf")

    def test_known_value(self):
        d = distance_function_registry.create("bhattacharyya")
        h1 = Histogram({Event("a"): 1, Event("b"): 1})  # a=0.5, b=0.5
        h2 = Histogram({Event("a"): 3, Event("b"): 1})  # a=0.75, b=0.25
        # BC = sqrt(0.5*0.75) + sqrt(0.5*0.25) = sqrt(0.375) + sqrt(0.125)
        bc = math.sqrt(0.375) + math.sqrt(0.125)
        expected = -math.log(bc)
        assert abs(d.distance(h1, h2) - expected) < 1e-6


class TestHellingerDistance:
    def test_identical(self):
        d = distance_function_registry.create("hellinger")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("hellinger")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("hellinger")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # (1/sqrt(2)) * sqrt((sqrt(1)-0)^2 + (0-sqrt(1))^2) = (1/sqrt(2))*sqrt(2) = 1
        assert abs(d.distance(h1, h2) - 1.0) < 1e-6

    def test_range(self):
        d = distance_function_registry.create("hellinger")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        dist = d.distance(h1, h2)
        assert 0.0 <= dist <= 1.0


class TestIntersectionDistance:
    def test_identical(self):
        d = distance_function_registry.create("intersection")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("intersection")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("intersection")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # min(1,0) + min(0,1) = 0, so 1 - 0 = 1
        assert abs(d.distance(h1, h2) - 1.0) < 1e-6

    def test_range(self):
        d = distance_function_registry.create("intersection")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        dist = d.distance(h1, h2)
        assert 0.0 <= dist <= 1.0


class TestBrayCurtisDistance:
    def test_identical(self):
        d = distance_function_registry.create("bray_curtis")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("bray_curtis")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("bray_curtis")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # numerator: |1-0| + |0-1| = 2. denominator: (1+0) + (0+1) = 2.
        # 2/2 = 1.0
        assert abs(d.distance(h1, h2) - 1.0) < 1e-6

    def test_range(self):
        d = distance_function_registry.create("bray_curtis")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        dist = d.distance(h1, h2)
        assert 0.0 <= dist <= 1.0


class TestCanberraDistance:
    def test_identical(self):
        d = distance_function_registry.create("canberra")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("canberra")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("canberra")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # event a: |1-0|/(1+0)=1. event b: |0-1|/(0+1)=1. total = 2.0
        assert abs(d.distance(h1, h2) - 2.0) < 1e-6

    def test_known_value(self):
        d = distance_function_registry.create("canberra")
        h1 = Histogram({Event("a"): 1, Event("b"): 1})  # a=0.5, b=0.5
        h2 = Histogram({Event("a"): 3, Event("b"): 1})  # a=0.75, b=0.25
        # event a: |0.5-0.75|/(0.5+0.75) = 0.25/1.25 = 0.2
        # event b: |0.5-0.25|/(0.5+0.25) = 0.25/0.75 = 1/3
        expected = 0.2 + 1.0 / 3.0
        assert abs(d.distance(h1, h2) - expected) < 1e-6


class TestKendallCorrelationDistance:
    def test_identical(self):
        d = distance_function_registry.create("kendall_correlation")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("kendall_correlation")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("kendall_correlation")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # events sorted: [a, b]. vals1=[1,0], vals2=[0,1]
        # pair (a,b): diff1=1-0=1, diff2=0-1=-1, product=-1 => discordant
        # tau = (0-1)/1 = -1. distance = (1-(-1))/2 = 1.0
        assert abs(d.distance(h1, h2) - 1.0) < 1e-6

    def test_range(self):
        d = distance_function_registry.create("kendall_correlation")
        h1 = Histogram({Event("a"): 3, Event("b"): 1, Event("c"): 2})
        h2 = Histogram({Event("a"): 1, Event("b"): 3, Event("c"): 2})
        dist = d.distance(h1, h2)
        assert 0.0 <= dist <= 1.0


class TestPearsonCorrelationDistance:
    def test_identical(self):
        d = distance_function_registry.create("pearson_correlation")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("pearson_correlation")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("pearson_correlation")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # vals1=[1,0] mean=0.5; vals2=[0,1] mean=0.5
        # cov=(1-0.5)*(0-0.5)+(0-0.5)*(1-0.5) = -0.25 + -0.25 = -0.5
        # std1=std2=sqrt(0.5). r = -0.5/0.5 = -1. distance = 1-(-1) = 2.0
        assert abs(d.distance(h1, h2) - 2.0) < 1e-6

    def test_range(self):
        d = distance_function_registry.create("pearson_correlation")
        h1 = Histogram({Event("a"): 3, Event("b"): 1, Event("c"): 2})
        h2 = Histogram({Event("a"): 1, Event("b"): 3, Event("c"): 2})
        dist = d.distance(h1, h2)
        # Pearson distance in [0, 2]
        assert 0.0 <= dist <= 2.0


class TestAngularSeparationDistance:
    def test_identical(self):
        d = distance_function_registry.create("angular_separation")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("angular_separation")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("angular_separation")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # cosine_similarity = 0, arccos(0)/pi = (pi/2)/pi = 0.5
        assert abs(d.distance(h1, h2) - 0.5) < 1e-6

    def test_range(self):
        d = distance_function_registry.create("angular_separation")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        dist = d.distance(h1, h2)
        assert 0.0 <= dist <= 1.0


class TestChordDistance:
    def test_identical(self):
        d = distance_function_registry.create("chord")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("chord")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("chord")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # cosine_similarity = 0, sqrt(2*(1-0)) = sqrt(2)
        assert abs(d.distance(h1, h2) - math.sqrt(2.0)) < 1e-6

    def test_range(self):
        d = distance_function_registry.create("chord")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        dist = d.distance(h1, h2)
        assert 0.0 <= dist <= math.sqrt(2.0)


class TestHistogramIntersectionDistance:
    def test_identical(self):
        d = distance_function_registry.create("histogram_intersection")
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert abs(d.distance(h, h)) < 1e-6

    def test_symmetric(self):
        d = distance_function_registry.create("histogram_intersection")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})
        h2 = Histogram({Event("a"): 1, Event("b"): 3})
        assert abs(d.distance(h1, h2) - d.distance(h2, h1)) < 1e-6

    def test_disjoint(self):
        d = distance_function_registry.create("histogram_intersection")
        h1 = Histogram({Event("a"): 1})
        h2 = Histogram({Event("b"): 1})
        # no overlap: min(1,0)+min(0,1)=0. min_total=1. 1 - 0/1 = 1.0
        assert abs(d.distance(h1, h2) - 1.0) < 1e-6

    def test_known_value(self):
        d = distance_function_registry.create("histogram_intersection")
        h1 = Histogram({Event("a"): 3, Event("b"): 1})  # total=4
        h2 = Histogram({Event("a"): 1, Event("b"): 3})  # total=4
        # min(3,1) + min(1,3) = 1 + 1 = 2. min_total=4. 1 - 2/4 = 0.5
        assert abs(d.distance(h1, h2) - 0.5) < 1e-6
