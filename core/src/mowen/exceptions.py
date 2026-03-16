"""Mowen exception hierarchy."""


class MowenError(Exception):
    """Base exception for all mowen errors."""


class RegistryError(MowenError):
    """Error looking up a component in the registry."""


class ComponentNotFoundError(RegistryError):
    """A requested component name was not found in its registry."""

    def __init__(self, kind: str, name: str) -> None:
        self.kind = kind
        self.name = name
        super().__init__(f"{kind} not found: {name!r}")


class DuplicateComponentError(RegistryError):
    """A component with the same name is already registered."""

    def __init__(self, kind: str, name: str) -> None:
        self.kind = kind
        self.name = name
        super().__init__(f"{kind} already registered: {name!r}")


class ParameterError(MowenError):
    """Invalid parameter value."""


class PipelineError(MowenError):
    """Error during pipeline execution."""


class DocumentLoadError(MowenError):
    """Error loading a document from a file."""


class EvaluationError(MowenError):
    """Error during evaluation (e.g., insufficient documents)."""
