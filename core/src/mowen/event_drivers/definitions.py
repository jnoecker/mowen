"""Definition-based event driver using WordNet via NLTK."""

from __future__ import annotations

import re

from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet

# Common stop words to filter from definitions.
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "can",
        "could",
        "must",
        "of",
        "in",
        "to",
        "for",
        "with",
        "on",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "and",
        "but",
        "or",
        "nor",
        "not",
        "so",
        "yet",
        "if",
        "that",
        "it",
    }
)


@event_driver_registry.register("definitions")
class DefinitionEvents(EventDriver):
    """Replace words with content words from their WordNet definitions.

    For each word, looks up the first synset in WordNet, extracts the
    gloss (definition text), filters stop words, and emits the remaining
    definition words as events.  Words not found in WordNet are skipped.

    This captures semantic similarity between authors' vocabulary
    choices — two authors using different words with similar meanings
    will produce overlapping definition events.

    Requires the ``nltk`` package with WordNet data downloaded::

        pip install nltk
        python -c "import nltk; nltk.download('wordnet')"
    """

    display_name = "Definition Events"
    description = "Content words from WordNet definitions of each word."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [TOKENIZER_PARAM]

    def create_event_set(self, text: str) -> EventSet:
        try:
            from nltk.corpus import wordnet  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "Definition events require NLTK with WordNet. "
                "Install with: pip install nltk && "
                "python -c \"import nltk; nltk.download('wordnet')\""
            ) from exc

        tok: str = self.get_param("tokenizer")
        events = EventSet()
        for word in tokenize_text(text, tok):
            synsets = wordnet.synsets(word.lower())
            if not synsets:
                continue
            # Use the first (most common) sense.
            gloss = synsets[0].definition()
            # Extract content words from the definition.
            for def_word in gloss.split():
                cleaned = re.sub(r"[^a-zA-Z]", "", def_word).lower()
                if cleaned and cleaned not in _STOP_WORDS and len(cleaned) > 1:
                    events.append(Event(data=cleaned))
        return events
