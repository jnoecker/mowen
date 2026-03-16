"""Tests for core data types."""

from mowen.types import Attribution, Document, Event, EventSet, Histogram, PipelineResult


class TestEvent:
    def test_creation(self):
        e = Event(data="abc")
        assert e.data == "abc"
        assert str(e) == "abc"

    def test_hashable(self):
        e1 = Event(data="abc")
        e2 = Event(data="abc")
        assert e1 == e2
        assert hash(e1) == hash(e2)
        assert len({e1, e2}) == 1

    def test_immutable(self):
        e = Event(data="abc")
        try:
            e.data = "xyz"  # type: ignore[misc]
            assert False, "Should have raised"
        except AttributeError:
            pass


class TestEventSet:
    def test_to_histogram(self):
        events = EventSet([Event("a"), Event("b"), Event("a"), Event("c"), Event("a")])
        h = events.to_histogram()
        assert h.absolute_frequency(Event("a")) == 3
        assert h.absolute_frequency(Event("b")) == 1
        assert h.absolute_frequency(Event("c")) == 1

    def test_empty(self):
        es = EventSet()
        h = es.to_histogram()
        assert len(h) == 0
        assert h.total == 0


class TestHistogram:
    def test_frequencies(self):
        h = Histogram({Event("a"): 3, Event("b"): 1, Event("c"): 1})
        assert h.total == 5
        assert h.absolute_frequency(Event("a")) == 3
        assert abs(h.relative_frequency(Event("a")) - 0.6) < 1e-9
        assert h.absolute_frequency(Event("missing")) == 0
        assert h.relative_frequency(Event("missing")) == 0.0

    def test_unique_events(self):
        h = Histogram({Event("a"): 3, Event("b"): 1})
        assert h.unique_events() == {Event("a"), Event("b")}

    def test_normalized(self):
        h = Histogram({Event("a"): 2, Event("b"): 2})
        n = h.normalized()
        assert abs(n[Event("a")] - 0.5) < 1e-9
        assert abs(n[Event("b")] - 0.5) < 1e-9

    def test_empty_histogram(self):
        h = Histogram()
        assert h.total == 0
        assert h.relative_frequency(Event("x")) == 0.0
        assert h.normalized() == {}

    def test_contains(self):
        h = Histogram({Event("a"): 1})
        assert Event("a") in h
        assert Event("b") not in h


class TestDocument:
    def test_creation(self):
        d = Document(text="hello", author="me", title="test")
        assert d.text == "hello"
        assert d.author == "me"
        assert d.title == "test"

    def test_defaults(self):
        d = Document(text="hello")
        assert d.author is None
        assert d.title == ""
        assert d.metadata == {}


class TestAttribution:
    def test_creation(self):
        a = Attribution(author="me", score=0.5)
        assert a.author == "me"
        assert a.score == 0.5


class TestPipelineResult:
    def test_top_author(self):
        doc = Document(text="test")
        r = PipelineResult(
            unknown_document=doc,
            rankings=[Attribution("A", 0.9), Attribution("B", 0.1)],
        )
        assert r.top_author == "A"

    def test_empty_rankings(self):
        doc = Document(text="test")
        r = PipelineResult(unknown_document=doc, rankings=[])
        assert r.top_author is None
