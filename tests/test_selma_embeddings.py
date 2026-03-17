"""Tests for the SELMA instruction-tuned embedding driver."""

import pytest


class TestSELMAEmbeddings:
    def test_registered(self):
        """selma_embeddings should be in the event driver registry."""
        transformers = pytest.importorskip("transformers")
        from mowen.event_drivers import event_driver_registry

        assert "selma_embeddings" in event_driver_registry.names()

    def test_param_defs(self):
        """Should expose model_name, max_length, and instruction params."""
        transformers = pytest.importorskip("transformers")
        from mowen.event_drivers import event_driver_registry

        driver = event_driver_registry.create("selma_embeddings")
        param_names = {p.name for p in driver.param_defs()}
        assert "model_name" in param_names
        assert "max_length" in param_names
        assert "instruction" in param_names

    def test_display_name(self):
        transformers = pytest.importorskip("transformers")
        from mowen.event_drivers import event_driver_registry

        driver = event_driver_registry.create("selma_embeddings")
        assert "SELMA" in driver.display_name

    def test_default_model_name(self):
        transformers = pytest.importorskip("transformers")
        from mowen.event_drivers import event_driver_registry

        driver = event_driver_registry.create("selma_embeddings")
        assert driver.get_param("model_name") == "intfloat/e5-mistral-7b-instruct"

    def test_custom_instruction(self):
        transformers = pytest.importorskip("transformers")
        from mowen.event_drivers import event_driver_registry

        driver = event_driver_registry.create(
            "selma_embeddings",
            {"instruction": "Find text by the same author"},
        )
        assert driver.get_param("instruction") == "Find text by the same author"

    def test_produces_numeric_event_set(self):
        """With a small model, verify output is NumericEventSet."""
        transformers = pytest.importorskip("transformers")
        from mowen.event_drivers import event_driver_registry
        from mowen.types import NumericEventSet

        # Use the small MiniLM model instead of the large e5-mistral
        driver = event_driver_registry.create(
            "selma_embeddings",
            {"model_name": "sentence-transformers/all-MiniLM-L6-v2"},
        )
        result = driver.create_event_set("The quick brown fox.")
        assert isinstance(result, NumericEventSet)
        assert len(result) > 0
        # All values should be finite floats
        assert all(isinstance(v, float) for v in result)
