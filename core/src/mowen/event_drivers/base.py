"""Base class for event drivers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from mowen.parameters import Configurable
from mowen.registry import Registry
from mowen.types import EventSet


@dataclass
class EventDriver(ABC, Configurable):
    """Abstract base class for event drivers.

    An event driver transforms raw text into an :class:`~mowen.types.EventSet`
    -- the fundamental unit of stylistic evidence in the analysis pipeline.

    Subclasses must set ``display_name`` and ``description`` and implement
    :meth:`create_event_set`.
    """

    display_name: str = ""
    description: str = ""

    @abstractmethod
    def create_event_set(self, text: str) -> EventSet:
        """Transform *text* into an ordered sequence of events.

        Parameters
        ----------
        text:
            The (possibly canonicized) document text.

        Returns
        -------
        EventSet
            The events extracted from *text*.
        """


event_driver_registry: Registry[EventDriver] = Registry("event_driver")
