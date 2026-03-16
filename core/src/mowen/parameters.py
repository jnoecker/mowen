"""Configurable parameter system for pipeline components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mowen.exceptions import ParameterError


@dataclass(frozen=True)
class ParamDef:
    """Definition of a configurable parameter."""

    name: str
    description: str
    param_type: type
    default: Any
    min_value: float | None = None
    max_value: float | None = None
    choices: list[Any] | None = None

    def validate(self, value: Any) -> Any:
        """Validate and coerce a parameter value."""
        try:
            coerced = self.param_type(value)
        except (TypeError, ValueError) as e:
            raise ParameterError(
                f"Parameter {self.name!r}: expected {self.param_type.__name__}, got {value!r}"
            ) from e

        if self.min_value is not None and coerced < self.min_value:
            raise ParameterError(
                f"Parameter {self.name!r}: {coerced} < minimum {self.min_value}"
            )
        if self.max_value is not None and coerced > self.max_value:
            raise ParameterError(
                f"Parameter {self.name!r}: {coerced} > maximum {self.max_value}"
            )
        if self.choices is not None and coerced not in self.choices:
            raise ParameterError(
                f"Parameter {self.name!r}: {coerced!r} not in {self.choices}"
            )
        return coerced


@dataclass
class Configurable:
    """Mixin providing configurable parameters to pipeline components."""

    _params: dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        """Override to declare configurable parameters."""
        return []

    def set_params(self, params: dict[str, Any]) -> None:
        """Set parameters, validating against param_defs."""
        defs = {p.name: p for p in self.param_defs()}
        for name, value in params.items():
            if name not in defs:
                raise ParameterError(f"Unknown parameter: {name!r}")
            self._params[name] = defs[name].validate(value)
        # Fill defaults for unset params
        for pdef in self.param_defs():
            if pdef.name not in self._params:
                self._params[pdef.name] = pdef.default

    def get_param(self, name: str) -> Any:
        """Get a parameter value, returning default if not set."""
        if name in self._params:
            return self._params[name]
        for pdef in self.param_defs():
            if pdef.name == name:
                return pdef.default
        raise ParameterError(f"Unknown parameter: {name!r}")

    def get_param_info(self) -> list[dict[str, Any]]:
        """Return parameter definitions as serializable dicts."""
        return [
            {
                "name": p.name,
                "description": p.description,
                "type": p.param_type.__name__,
                "default": p.default,
                "min_value": p.min_value,
                "max_value": p.max_value,
                "choices": p.choices,
            }
            for p in self.param_defs()
        ]
