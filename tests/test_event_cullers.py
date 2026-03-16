"""Tests for event culler implementations."""

from mowen.event_cullers import event_culler_registry
from mowen.types import Event, EventSet


class TestMostCommon:
    def test_keeps_top_n(self):
        c = event_culler_registry.create("most_common", {"n": 2})
        es1 = EventSet([Event("a"), Event("a"), Event("b"), Event("b"), Event("c")])
        es2 = EventSet([Event("a"), Event("b"), Event("c")])
        c.init([es1, es2])
        # 'a' appears 3 times, 'b' appears 3 times, 'c' appears 2 times
        # top-2 should be 'a' and 'b'
        culled = c.cull(es1)
        events_data = {e.data for e in culled}
        assert "a" in events_data
        assert "b" in events_data
        assert "c" not in events_data

    def test_preserves_order(self):
        c = event_culler_registry.create("most_common", {"n": 1})
        es = EventSet([Event("rare"), Event("common"), Event("common"), Event("common")])
        c.init([es])
        culled = c.cull(es)
        assert all(e.data == "common" for e in culled)
        assert len(culled) == 3

    def test_n_larger_than_vocab(self):
        c = event_culler_registry.create("most_common", {"n": 100})
        es = EventSet([Event("a"), Event("b")])
        c.init([es])
        culled = c.cull(es)
        assert len(culled) == 2


class TestLeastCommon:
    def test_keeps_bottom_n(self):
        c = event_culler_registry.create("least_common", {"n": 1})
        es1 = EventSet([Event("a"), Event("a"), Event("b"), Event("b"), Event("c")])
        es2 = EventSet([Event("a"), Event("b"), Event("c")])
        c.init([es1, es2])
        # a=3, b=3, c=2 => least common is c
        culled = c.cull(es1)
        events_data = {e.data for e in culled}
        assert events_data == {"c"}

    def test_preserves_all_occurrences(self):
        c = event_culler_registry.create("least_common", {"n": 1})
        es = EventSet([Event("rare"), Event("common"), Event("common"), Event("common")])
        c.init([es])
        culled = c.cull(es)
        assert all(e.data == "rare" for e in culled)
        assert len(culled) == 1

    def test_n_larger_than_vocab(self):
        c = event_culler_registry.create("least_common", {"n": 100})
        es = EventSet([Event("a"), Event("b")])
        c.init([es])
        culled = c.cull(es)
        assert len(culled) == 2


class TestRangeCuller:
    def test_keeps_events_in_doc_range(self):
        c = event_culler_registry.create("range", {"min_count": 2, "max_count": 2})
        es1 = EventSet([Event("a"), Event("b")])
        es2 = EventSet([Event("a"), Event("c")])
        es3 = EventSet([Event("a"), Event("b")])
        c.init([es1, es2, es3])
        # doc freq: a=3, b=2, c=1 => only b is in [2,2]
        culled = c.cull(es1)
        events_data = {e.data for e in culled}
        assert events_data == {"b"}

    def test_excludes_too_rare_and_too_common(self):
        c = event_culler_registry.create("range", {"min_count": 2, "max_count": 3})
        es1 = EventSet([Event("a"), Event("b"), Event("c"), Event("d")])
        es2 = EventSet([Event("a"), Event("b"), Event("c")])
        es3 = EventSet([Event("a"), Event("b")])
        es4 = EventSet([Event("a")])
        c.init([es1, es2, es3, es4])
        # doc freq: a=4, b=3, c=2, d=1 => keep b(3) and c(2)
        culled = c.cull(es1)
        events_data = {e.data for e in culled}
        assert events_data == {"b", "c"}

    def test_all_events_in_range(self):
        c = event_culler_registry.create("range", {"min_count": 1, "max_count": 100})
        es = EventSet([Event("a"), Event("b")])
        c.init([es])
        culled = c.cull(es)
        assert len(culled) == 2


class TestPercentageRange:
    def test_filters_by_relative_frequency(self):
        c = event_culler_registry.create("percentage_range", {"min_percent": 0.0, "max_percent": 25.0})
        # 10 events total: a=5 (50%), b=3 (30%), c=2 (20%)
        es = EventSet(
            [Event("a")] * 5 + [Event("b")] * 3 + [Event("c")] * 2
        )
        c.init([es])
        culled = c.cull(es)
        # only c (20%) falls within [0%, 25%]
        events_data = {e.data for e in culled}
        assert events_data == {"c"}

    def test_full_range_keeps_all(self):
        c = event_culler_registry.create("percentage_range", {"min_percent": 0.0, "max_percent": 100.0})
        es = EventSet([Event("a"), Event("b"), Event("c")])
        c.init([es])
        culled = c.cull(es)
        assert len(culled) == 3

    def test_empty_event_set(self):
        c = event_culler_registry.create("percentage_range", {"min_percent": 0.0, "max_percent": 100.0})
        es = EventSet([])
        c.init([es])
        culled = c.cull(es)
        assert len(culled) == 0


class TestStdDeviation:
    def test_removes_outliers(self):
        c = event_culler_registry.create("std_deviation", {"n": 1.0})
        # frequencies: a=10, b=10, c=10, d=100
        # mean=32.5, d is a clear outlier
        es = EventSet(
            [Event("a")] * 10 + [Event("b")] * 10
            + [Event("c")] * 10 + [Event("d")] * 100
        )
        c.init([es])
        culled = c.cull(es)
        events_data = {e.data for e in culled}
        assert "d" not in events_data
        assert "a" in events_data

    def test_wide_n_keeps_all(self):
        c = event_culler_registry.create("std_deviation", {"n": 100.0})
        es = EventSet([Event("a"), Event("b"), Event("b")])
        c.init([es])
        culled = c.cull(es)
        assert len(culled) == 3

    def test_uniform_frequencies(self):
        c = event_culler_registry.create("std_deviation", {"n": 0.0})
        # All events have the same frequency, std_dev = 0, range = [mean, mean]
        es = EventSet([Event("a"), Event("a"), Event("b"), Event("b")])
        c.init([es])
        culled = c.cull(es)
        assert len(culled) == 4


class TestVariance:
    def test_keeps_high_variance_events(self):
        c = event_culler_registry.create("variance", {"min_variance": 0.0})
        # doc1: a=5, b=1; doc2: a=1, b=1
        # a: counts=[5,1], mean=3, var=4 => kept (>0)
        # b: counts=[1,1], mean=1, var=0 => not kept
        es1 = EventSet([Event("a")] * 5 + [Event("b")])
        es2 = EventSet([Event("a"), Event("b")])
        c.init([es1, es2])
        culled = c.cull(es1)
        events_data = {e.data for e in culled}
        assert "a" in events_data
        assert "b" not in events_data

    def test_high_threshold_filters_all(self):
        c = event_culler_registry.create("variance", {"min_variance": 9999.0})
        es1 = EventSet([Event("a"), Event("b")])
        es2 = EventSet([Event("a"), Event("b")])
        c.init([es1, es2])
        culled = c.cull(es1)
        assert len(culled) == 0

    def test_zero_variance_same_counts(self):
        c = event_culler_registry.create("variance", {"min_variance": 0.0})
        # Both docs have identical counts, variance = 0 for all events
        es1 = EventSet([Event("a"), Event("b")])
        es2 = EventSet([Event("a"), Event("b")])
        c.init([es1, es2])
        culled = c.cull(es1)
        # variance=0 is not > 0, so nothing is kept
        assert len(culled) == 0


class TestIQR:
    def test_removes_high_frequency_outlier(self):
        c = event_culler_registry.create("iqr", {"factor": 1.5})
        # frequencies: a=1, b=2, c=3, d=4, e=100
        # e is a clear outlier above Q3 + 1.5*IQR
        es = EventSet(
            [Event("a")] * 1 + [Event("b")] * 2 + [Event("c")] * 3
            + [Event("d")] * 4 + [Event("e")] * 100
        )
        c.init([es])
        culled = c.cull(es)
        events_data = {e.data for e in culled}
        assert "e" not in events_data
        assert "c" in events_data

    def test_large_factor_keeps_all(self):
        c = event_culler_registry.create("iqr", {"factor": 1000.0})
        es = EventSet([Event("a"), Event("b")] * 50 + [Event("c")])
        c.init([es])
        culled = c.cull(es)
        events_data = {e.data for e in culled}
        assert "a" in events_data
        assert "b" in events_data
        assert "c" in events_data

    def test_single_event_type(self):
        c = event_culler_registry.create("iqr", {"factor": 1.5})
        es = EventSet([Event("a"), Event("a"), Event("a")])
        c.init([es])
        culled = c.cull(es)
        # Only one event type, IQR=0, so bounds are [Q1, Q3] which equals [3,3]
        assert len(culled) == 3


class TestInformationGain:
    def test_keeps_high_entropy_events(self):
        c = event_culler_registry.create("information_gain", {"n": 1})
        # doc1: a=5, b=0; doc2: a=0, b=5
        # a across docs: [5, 0] => entropy = -(1*log2(1)) = 0 (only one nonzero)
        # Actually: a=[5,0], only one nonzero, entropy=0
        # b=[0,5], only one nonzero, entropy=0
        # Need more spread: doc1: a=3, b=1; doc2: a=1, b=3
        # a=[3,1], total=4, p=[0.75, 0.25], H = -0.75*log2(0.75) - 0.25*log2(0.25) ~ 0.811
        # b=[1,3], total=4, same entropy ~ 0.811
        # Add c that only appears in one doc: c=[2,0], entropy=0
        es1 = EventSet([Event("a")] * 3 + [Event("b")] + [Event("c")] * 2)
        es2 = EventSet([Event("a")] + [Event("b")] * 3)
        c.init([es1, es2])
        culled = c.cull(es1)
        events_data = {e.data for e in culled}
        # c has entropy 0, a and b have higher entropy; n=1 keeps the top one
        assert "c" not in events_data
        assert len(events_data) == 1

    def test_n_larger_than_vocab(self):
        c = event_culler_registry.create("information_gain", {"n": 100})
        es = EventSet([Event("a"), Event("b")])
        c.init([es])
        culled = c.cull(es)
        assert len(culled) == 2

    def test_uniform_distribution_high_entropy(self):
        c = event_culler_registry.create("information_gain", {"n": 1})
        # a appears equally across 3 docs, b appears only in 1
        # a=[1,1,1] => entropy = log2(3) ~ 1.585
        # b=[3,0,0] => entropy = 0 (only one nonzero)
        es1 = EventSet([Event("a"), Event("b"), Event("b"), Event("b")])
        es2 = EventSet([Event("a")])
        es3 = EventSet([Event("a")])
        c.init([es1, es2, es3])
        culled = c.cull(es1)
        events_data = {e.data for e in culled}
        assert "a" in events_data


class TestCoefficientOfVariation:
    def test_keeps_variable_events(self):
        c = event_culler_registry.create("coefficient_of_variation", {"min_cv": 0.0})
        # doc1: a=5, b=2; doc2: a=5, b=2
        # a: counts=[5,5], mean=5, var=0, std=0, cv=0 => not kept (0 > 0 is false)
        # b: counts=[2,2], mean=2, var=0, std=0, cv=0 => not kept
        # Need different counts: doc1: a=5, b=1; doc2: a=5, b=3
        # a: [5,5], mean=5, var=0, cv=0 => not kept
        # b: [1,3], mean=2, var=1, std=1, cv=0.5 => kept (>0)
        es1 = EventSet([Event("a")] * 5 + [Event("b")])
        es2 = EventSet([Event("a")] * 5 + [Event("b")] * 3)
        c.init([es1, es2])
        culled = c.cull(es1)
        events_data = {e.data for e in culled}
        assert "b" in events_data
        assert "a" not in events_data

    def test_high_threshold_filters_all(self):
        c = event_culler_registry.create("coefficient_of_variation", {"min_cv": 9999.0})
        es1 = EventSet([Event("a"), Event("b")])
        es2 = EventSet([Event("a"), Event("b")])
        c.init([es1, es2])
        culled = c.cull(es1)
        assert len(culled) == 0

    def test_event_absent_from_one_doc(self):
        c = event_culler_registry.create("coefficient_of_variation", {"min_cv": 0.5})
        # doc1: a=4; doc2: (a absent, so a=0)
        # a: [4, 0], mean=2, var=4, std=2, cv=1.0 => kept (>0.5)
        es1 = EventSet([Event("a")] * 4)
        es2 = EventSet([Event("b")])
        c.init([es1, es2])
        culled = c.cull(es1)
        events_data = {e.data for e in culled}
        assert "a" in events_data
