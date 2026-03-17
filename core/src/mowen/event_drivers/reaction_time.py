"""Reaction time event driver using English Lexicon Project data."""

from __future__ import annotations

from pathlib import Path

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Module-level caches — loaded once on first use.
_RT_MAP: dict[str, str] | None = None
_FREQ_MAP: dict[str, str] | None = None


def _load_elp_file(filename: str) -> dict[str, str]:
    """Load an ELP .dat file with /word/value/ format."""
    result: dict[str, str] = {}
    path = _DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Format: /word/value/
            parts = line.strip("/").split("/")
            if len(parts) == 2:
                word, value = parts
                result[word.lower()] = value
    return result


def _get_rt_map() -> dict[str, str]:
    global _RT_MAP
    if _RT_MAP is None:
        _RT_MAP = _load_elp_file("elp_reaction_times.dat")
    return _RT_MAP


def _get_freq_map() -> dict[str, str]:
    global _FREQ_MAP
    if _FREQ_MAP is None:
        _FREQ_MAP = _load_elp_file("elp_frequencies.dat")
    return _FREQ_MAP


@event_driver_registry.register("reaction_time")
class ReactionTime(EventDriver):
    """Replace words with lexical decision reaction times.

    Uses the English Lexicon Project (ELP) database to convert each
    word to its mean lexical decision reaction time (in milliseconds).
    Words not found in the database are silently dropped.

    This captures the cognitive complexity profile of an author's
    vocabulary — authors who prefer common, quickly-recognized words
    will produce different distributions from those who use obscure
    or complex vocabulary.

    English-only.  ~40,000 word entries.
    """

    display_name = "Reaction Time (ELP)"
    description = "Words replaced by lexical decision reaction times from the English Lexicon Project."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="measure",
                description="ELP measure: 'rt' (reaction time) or 'freq' (log HAL frequency).",
                param_type=str,
                default="rt",
            ),
            TOKENIZER_PARAM,
        ]

    def create_event_set(self, text: str) -> EventSet:
        measure: str = self.get_param("measure")
        tok: str = self.get_param("tokenizer")

        if measure == "freq":
            lookup = _get_freq_map()
        else:
            lookup = _get_rt_map()

        words = tokenize_text(text, tok)
        events: list[Event] = []
        for w in words:
            value = lookup.get(w.lower())
            if value is not None:
                events.append(Event(data=value))
        return EventSet(events)
