"""Tests for the perplexity / surprisal event driver."""

import pytest


class TestPerplexityDriver:
    def test_registered(self):
        pytest.importorskip("transformers")
        from mowen.event_drivers import event_driver_registry

        assert "perplexity" in event_driver_registry.names()

    def test_param_defs(self):
        pytest.importorskip("transformers")
        from mowen.event_drivers import event_driver_registry

        driver = event_driver_registry.create("perplexity")
        param_names = {p.name for p in driver.param_defs()}
        assert "model_name" in param_names
        assert "max_length" in param_names

    def test_default_model(self):
        pytest.importorskip("transformers")
        from mowen.event_drivers import event_driver_registry

        driver = event_driver_registry.create("perplexity")
        assert driver.get_param("model_name") == "gpt2"

    def test_produces_four_features(self):
        pytest.importorskip("transformers")
        from mowen.event_drivers import event_driver_registry
        from mowen.types import NumericEventSet

        driver = event_driver_registry.create("perplexity")
        result = driver.create_event_set("The quick brown fox jumps over the lazy dog.")
        assert isinstance(result, NumericEventSet)
        assert len(result) == 4  # mean, variance, skewness, kurtosis

    def test_different_texts_different_features(self):
        pytest.importorskip("transformers")
        from mowen.event_drivers import event_driver_registry

        driver = event_driver_registry.create("perplexity")
        r1 = driver.create_event_set("The quick brown fox jumps over the lazy dog.")
        r2 = driver.create_event_set("xyzzy plugh zork quux corge grault garply")
        # At least one feature should differ
        assert any(a != b for a, b in zip(r1, r2))


def test_statistics_helper():
    """Test the pure-Python statistics function."""
    from mowen.event_drivers.perplexity import _statistics

    mean, var, skew, kurt = _statistics([1.0, 2.0, 3.0, 4.0, 5.0])
    assert abs(mean - 3.0) < 1e-6
    assert var > 0
    # Empty input
    m, v, s, k = _statistics([])
    assert m == 0.0
    # Single value
    m, v, s, k = _statistics([42.0])
    assert m == 42.0
    assert v == 0.0
