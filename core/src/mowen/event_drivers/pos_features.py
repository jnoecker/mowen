"""Part-of-speech derived event drivers."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.event_drivers.base import (
    SpacyEventDriver,
    _SPACY_MODEL_PARAM,
    event_driver_registry,
    generate_ngrams,
)
from mowen.parameters import ParamDef
from mowen.types import Event, EventSet


# Coarse POS mapping: maps fine-grained Universal POS tags to broad categories.
# Compatible with spaCy's Universal POS tagset.
_COARSE_MAP: dict[str, str] = {
    # Nouns
    "NOUN": "N", "PROPN": "N",
    # Verbs
    "VERB": "V", "AUX": "V",
    # Adjectives
    "ADJ": "J",
    # Adverbs
    "ADV": "R",
    # Pronouns / Determiners
    "PRON": "D", "DET": "D",
    # Prepositions / Conjunctions
    "ADP": "P", "CCONJ": "C", "SCONJ": "C",
    # Particles / Interjections / Other
    "PART": "T", "INTJ": "I", "NUM": "M",
    # Punctuation / Symbols / Other
    "PUNCT": ".", "SYM": ".", "X": "X", "SPACE": "_",
}


@event_driver_registry.register("coarse_pos_tags")
@dataclass
class CoarsePOSTags(SpacyEventDriver):
    """Simplify POS tags to broad categories (N, V, J, R, etc.).

    Reduces sparsity compared to fine-grained POS tags by grouping
    related tags (e.g., NOUN and PROPN both map to "N").

    Requires the ``spacy`` package and a downloaded language model.
    """

    display_name = "Coarse POS Tags"
    description = "Broad POS categories (N, V, J, R, ...) via spaCy."

    def create_event_set(self, text: str) -> EventSet:
        doc = self._get_nlp()(text)
        return EventSet(
            Event(data=_COARSE_MAP.get(token.pos_, "X")) for token in doc
        )


@event_driver_registry.register("pos_ngram")
@dataclass
class POSNGram(SpacyEventDriver):
    """N-grams of POS tags — captures syntactic patterns independent of vocabulary.

    First tags each token with its POS tag, then extracts sliding-window
    n-grams of the tag sequence.

    Requires the ``spacy`` package and a downloaded language model.
    """

    display_name = "POS N-Gram"
    description = "N-grams of part-of-speech tags via spaCy."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(name="n", description="N-gram size.", param_type=int, default=2, min_value=1, max_value=10),
            _SPACY_MODEL_PARAM,
        ]

    def create_event_set(self, text: str) -> EventSet:
        n: int = self.get_param("n")
        doc = self._get_nlp()(text)
        tags = [token.pos_ for token in doc]
        return generate_ngrams(tags, n)
