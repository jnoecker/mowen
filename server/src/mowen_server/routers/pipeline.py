"""Pipeline component discovery endpoints."""

from fastapi import APIRouter

from mowen.canonicizers import canonicizer_registry
from mowen.event_drivers import event_driver_registry
from mowen.event_cullers import event_culler_registry
from mowen.distance_functions import distance_function_registry
from mowen.analysis_methods import analysis_method_registry
from mowen.parameters import Configurable
from mowen.registry import Registry

from ..schemas import ComponentInfo, ParamInfo

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


def _list_registry(registry: Registry) -> list[ComponentInfo]:
    """Convert every entry in a registry to a ComponentInfo schema."""
    components: list[ComponentInfo] = []
    for name, cls in registry.list_all().items():
        # Build parameter info if the class is Configurable
        params: list[ParamInfo] | None = None
        if issubclass(cls, Configurable):
            pdefs = cls.param_defs()
            if pdefs:
                params = [
                    ParamInfo(
                        name=p.name,
                        type=p.param_type.__name__,
                        default=p.default,
                        description=p.description,
                        min_value=p.min_value,
                        max_value=p.max_value,
                        choices=[str(c) for c in p.choices] if p.choices else None,
                    )
                    for p in pdefs
                ]

        components.append(
            ComponentInfo(
                name=name,
                display_name=getattr(cls, "display_name", name),
                description=getattr(cls, "description", ""),
                params=params,
            )
        )
    return components


@router.get("/canonicizers", response_model=list[ComponentInfo])
def list_canonicizers() -> list[ComponentInfo]:
    """Return all registered canonicizers."""
    return _list_registry(canonicizer_registry)


@router.get("/event-drivers", response_model=list[ComponentInfo])
def list_event_drivers() -> list[ComponentInfo]:
    """Return all registered event drivers."""
    return _list_registry(event_driver_registry)


@router.get("/event-cullers", response_model=list[ComponentInfo])
def list_event_cullers() -> list[ComponentInfo]:
    """Return all registered event cullers."""
    return _list_registry(event_culler_registry)


@router.get("/distance-functions", response_model=list[ComponentInfo])
def list_distance_functions() -> list[ComponentInfo]:
    """Return all registered distance functions."""
    return _list_registry(distance_function_registry)


@router.get("/analysis-methods", response_model=list[ComponentInfo])
def list_analysis_methods() -> list[ComponentInfo]:
    """Return all registered analysis methods."""
    return _list_registry(analysis_method_registry)
