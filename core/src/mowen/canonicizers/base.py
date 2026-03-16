"""Base canonicizer class and registry for text canonicization components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from mowen.parameters import Configurable
from mowen.registry import Registry


@dataclass
class Canonicizer(ABC, Configurable):
    """Abstract base class for all canonicizers.

    A canonicizer transforms raw document text into a normalized form
    before event-driver processing.  Subclasses must implement
    :meth:`process` and set the ``display_name`` and ``description``
    class attributes.
    """

    display_name: str = ""
    description: str = ""

    @abstractmethod
    def process(self, text: str) -> str:
        """Transform *text* into its canonicized form.

        Parameters
        ----------
        text:
            The raw document text.

        Returns
        -------
        str
            The canonicized text.
        """


canonicizer_registry: Registry[Canonicizer] = Registry[Canonicizer]("canonicizer")
