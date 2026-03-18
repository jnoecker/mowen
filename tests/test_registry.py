"""Tests for the component registry."""

import pytest

from mowen.exceptions import ComponentNotFoundError, DuplicateComponentError
from mowen.parameters import Configurable, ParamDef
from mowen.registry import Registry


class TestRegistry:
    def test_register_and_get(self):
        reg = Registry("test")

        @reg.register("foo")
        class Foo:
            pass

        assert reg.get("foo") is Foo

    def test_not_found(self):
        reg = Registry("test")
        with pytest.raises(ComponentNotFoundError, match="not found"):
            reg.get("missing")

    def test_duplicate_registration(self):
        reg = Registry("test")

        @reg.register("dup")
        class First:
            pass

        with pytest.raises(DuplicateComponentError, match="already registered"):

            @reg.register("dup")
            class Second:
                pass

    def test_create_with_params(self):
        reg = Registry("test")

        @reg.register("configurable")
        class Comp(Configurable):
            @classmethod
            def param_defs(cls):
                return [ParamDef("n", "count", int, 5)]

        instance = reg.create("configurable", {"n": 10})
        assert instance.get_param("n") == 10

    def test_create_without_params(self):
        reg = Registry("test")

        @reg.register("simple")
        class Simple:
            pass

        instance = reg.create("simple")
        assert isinstance(instance, Simple)

    def test_list_all(self):
        reg = Registry("test")

        @reg.register("a")
        class A:
            pass

        @reg.register("b")
        class B:
            pass

        assert set(reg.names()) == {"a", "b"}
        assert len(reg.list_all()) == 2
