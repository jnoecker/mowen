"""Decorator-based plugin registry for pipeline components."""

from __future__ import annotations

from typing import Any, TypeVar

from mowen.exceptions import ComponentNotFoundError, DuplicateComponentError
from mowen.parameters import Configurable

T = TypeVar("T")


class Registry[T]:
    """Registry for a category of pipeline components.

    Usage:
        canonicizer_registry = Registry[Canonicizer]("canonicizer")

        @canonicizer_registry.register("unify_case")
        class UnifyCase(Canonicizer):
            ...
    """

    def __init__(self, kind: str) -> None:
        self.kind = kind
        self._components: dict[str, type[T]] = {}

    def register(self, name: str):  # noqa: ANN201
        """Class decorator that registers a component under the given name."""
        def decorator(cls: type[T]) -> type[T]:
            if name in self._components:
                raise DuplicateComponentError(self.kind, name)
            self._components[name] = cls
            cls.registry_name = name  # type: ignore[attr-defined]
            return cls
        return decorator

    def get(self, name: str) -> type[T]:
        """Return the class registered under `name`."""
        if name not in self._components:
            raise ComponentNotFoundError(self.kind, name)
        return self._components[name]

    def create(self, name: str, params: dict[str, Any] | None = None) -> T:
        """Instantiate a component by name, optionally setting parameters."""
        cls = self.get(name)
        instance = cls()
        if params and isinstance(instance, Configurable):
            instance.set_params(params)
        return instance

    def list_all(self) -> dict[str, type[T]]:
        """Return all registered components."""
        return dict(self._components)

    def names(self) -> list[str]:
        """Return all registered component names."""
        return list(self._components.keys())

    def describe_components(self) -> list[dict[str, Any]]:
        """Return structured metadata for all registered components."""
        result: list[dict[str, Any]] = []
        for name, cls in self._components.items():
            entry: dict[str, Any] = {
                "name": name,
                "display_name": getattr(cls, "display_name", name),
                "description": getattr(cls, "description", ""),
            }
            if isinstance(cls, type) and issubclass(cls, Configurable):
                pdefs = cls.param_defs()
                if pdefs:
                    entry["params"] = [
                        {
                            "name": p.name,
                            "type": p.param_type.__name__,
                            "default": p.default,
                            "description": p.description,
                            "min_value": p.min_value,
                            "max_value": p.max_value,
                            "choices": p.choices,
                        }
                        for p in pdefs
                    ]
            result.append(entry)
        return result
