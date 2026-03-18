"""Tests for the parameter system."""

import pytest

from mowen.exceptions import ParameterError
from mowen.parameters import Configurable, ParamDef


class TestParamDef:
    def test_basic_validation(self):
        p = ParamDef(name="n", description="count", param_type=int, default=5)
        assert p.validate(3) == 3
        assert p.validate("7") == 7

    def test_min_max(self):
        p = ParamDef(
            name="n",
            description="count",
            param_type=int,
            default=5,
            min_value=1,
            max_value=10,
        )
        assert p.validate(5) == 5
        with pytest.raises(ParameterError, match="minimum"):
            p.validate(0)
        with pytest.raises(ParameterError, match="maximum"):
            p.validate(11)

    def test_choices(self):
        p = ParamDef(
            name="mode",
            description="mode",
            param_type=str,
            default="a",
            choices=["a", "b"],
        )
        assert p.validate("a") == "a"
        with pytest.raises(ParameterError, match="not in"):
            p.validate("c")

    def test_type_coercion_failure(self):
        p = ParamDef(name="n", description="count", param_type=int, default=5)
        with pytest.raises(ParameterError, match="expected int"):
            p.validate("not_a_number")


class TestConfigurable:
    def test_set_and_get_params(self):
        class MyComp(Configurable):
            @classmethod
            def param_defs(cls):
                return [ParamDef("n", "count", int, 5, min_value=1)]

        c = MyComp()
        c.set_params({"n": 3})
        assert c.get_param("n") == 3

    def test_default_params(self):
        class MyComp(Configurable):
            @classmethod
            def param_defs(cls):
                return [ParamDef("n", "count", int, 5)]

        c = MyComp()
        assert c.get_param("n") == 5

    def test_unknown_param_set(self):
        class MyComp(Configurable):
            @classmethod
            def param_defs(cls):
                return []

        c = MyComp()
        with pytest.raises(ParameterError, match="Unknown"):
            c.set_params({"bogus": 1})

    def test_unknown_param_get(self):
        c = Configurable()
        with pytest.raises(ParameterError, match="Unknown"):
            c.get_param("bogus")

    def test_get_param_info(self):
        class MyComp(Configurable):
            @classmethod
            def param_defs(cls):
                return [ParamDef("n", "count", int, 5, min_value=1, max_value=10)]

        info = MyComp().get_param_info()
        assert len(info) == 1
        assert info[0]["name"] == "n"
        assert info[0]["type"] == "int"
        assert info[0]["default"] == 5
