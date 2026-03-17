"""Pipeline component discovery endpoints."""

from fastapi import APIRouter
from mowen.analysis_methods import analysis_method_registry
from mowen.analysis_methods.sklearn_base import SklearnAnalysisMethod
from mowen.canonicizers import canonicizer_registry
from mowen.distance_functions import distance_function_registry
from mowen.event_cullers import event_culler_registry
from mowen.event_drivers import event_driver_registry
from mowen.registry import Registry
from mowen.types import NumericEventSet

from ..schemas import ComponentInfo, ParamInfo

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])


def _build_params(raw_params: list[dict] | None) -> list[ParamInfo] | None:
    """Convert raw param dicts to ParamInfo schemas."""
    if not raw_params:
        return None
    return [
        ParamInfo(
            name=p["name"],
            type=p["type"],
            default=p["default"],
            description=p["description"],
            min_value=p["min_value"],
            max_value=p["max_value"],
            choices=[str(c) for c in p["choices"]] if p["choices"] else None,
        )
        for p in raw_params
    ]


def _list_registry(registry: Registry) -> list[ComponentInfo]:
    """Convert every entry in a registry to a ComponentInfo schema."""
    return [
        ComponentInfo(
            name=comp["name"],
            display_name=comp["display_name"],
            description=comp["description"],
            params=_build_params(comp.get("params")),
        )
        for comp in registry.describe_components()
    ]


@router.get("/canonicizers", response_model=list[ComponentInfo])
def list_canonicizers() -> list[ComponentInfo]:
    """Return all registered canonicizers."""
    return _list_registry(canonicizer_registry)


@router.get("/event-drivers", response_model=list[ComponentInfo])
def list_event_drivers() -> list[ComponentInfo]:
    """Return all registered event drivers with numeric flag.

    Drivers that produce ``NumericEventSet`` (e.g. transformer embeddings)
    are tagged with ``numeric: true``.  All others are ``numeric: false``.
    """
    results: list[ComponentInfo] = []
    for comp in event_driver_registry.describe_components():
        cls = event_driver_registry.get(comp["name"])
        # Probe whether this driver produces NumericEventSet
        is_numeric = False
        try:
            from typing import get_type_hints
            hints = get_type_hints(cls.create_event_set)
            ret = hints.get("return")
            if ret is NumericEventSet:
                is_numeric = True
        except Exception:
            pass
        results.append(
            ComponentInfo(
                name=comp["name"],
                display_name=comp["display_name"],
                description=comp["description"],
                params=_build_params(comp.get("params")),
                numeric=is_numeric,
            )
        )
    return results


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
    """Return all registered analysis methods with numeric compatibility flag.

    Methods that support numeric mode (sklearn-based) are tagged with
    ``numeric: true``.  Distance-based methods are ``numeric: false``.
    """
    results: list[ComponentInfo] = []
    for comp in analysis_method_registry.describe_components():
        cls = analysis_method_registry.get(comp["name"])
        is_numeric = issubclass(cls, SklearnAnalysisMethod)
        results.append(
            ComponentInfo(
                name=comp["name"],
                display_name=comp["display_name"],
                description=comp["description"],
                params=_build_params(comp.get("params")),
                numeric=is_numeric,
            )
        )
    return results
