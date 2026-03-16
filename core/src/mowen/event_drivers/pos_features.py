"""Part-of-speech derived event drivers."""

from __future__ import annotations

from dataclasses import dataclass, field

from mowen.event_drivers.base import EventDriver, event_driver_registry
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
class CoarsePOSTags(EventDriver):
    """Simplify POS tags to broad categories (N, V, J, R, etc.).

    Reduces sparsity compared to fine-grained POS tags by grouping
    related tags (e.g., NOUN and PROPN both map to "N").

    Requires the ``spacy`` package and a downloaded language model.
    """

    display_name = "Coarse POS Tags"
    description = "Broad POS categories (N, V, J, R, ...) via spaCy."

    _nlp: object = field(default=None, init=False, repr=False)
    _nlp_model_name: str = field(default="", init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="model",
                description="spaCy language model to use.",
                param_type=str,
                default="en_core_web_sm",
            ),
        ]

    def create_event_set(self, text: str) -> EventSet:
        try:
            import spacy
        except ImportError as e:
            raise ImportError(
                "The 'spacy' package is required for Coarse POS Tags. "
                "Install with: pip install spacy && python -m spacy download en_core_web_sm"
            ) from e

        model_name: str = self.get_param("model")
        if self._nlp is None or self._nlp_model_name != model_name:
            self._nlp = spacy.load(model_name)
            self._nlp_model_name = model_name
        doc = self._nlp(text)
        events = EventSet()
        for token in doc:
            coarse = _COARSE_MAP.get(token.pos_, "X")
            events.append(Event(data=coarse))
        return events


@event_driver_registry.register("pos_ngram")
@dataclass
class POSNGram(EventDriver):
    """N-grams of POS tags — captures syntactic patterns independent of vocabulary.

    First tags each token with its POS tag, then extracts sliding-window
    n-grams of the tag sequence.

    Requires the ``spacy`` package and a downloaded language model.
    """

    display_name = "POS N-Gram"
    description = "N-grams of part-of-speech tags via spaCy."

    _nlp: object = field(default=None, init=False, repr=False)
    _nlp_model_name: str = field(default="", init=False, repr=False)

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(name="n", description="N-gram size.", param_type=int, default=2, min_value=1, max_value=10),
            ParamDef(
                name="model",
                description="spaCy language model to use.",
                param_type=str,
                default="en_core_web_sm",
            ),
        ]

    def create_event_set(self, text: str) -> EventSet:
        try:
            import spacy
        except ImportError as e:
            raise ImportError(
                "The 'spacy' package is required for POS N-Gram. "
                "Install with: pip install spacy && python -m spacy download en_core_web_sm"
            ) from e

        model_name: str = self.get_param("model")
        if self._nlp is None or self._nlp_model_name != model_name:
            self._nlp = spacy.load(model_name)
            self._nlp_model_name = model_name

        n: int = self.get_param("n")
        doc = self._nlp(text)
        tags = [token.pos_ for token in doc]

        events = EventSet()
        for i in range(len(tags) - n + 1):
            events.append(Event(data=" ".join(tags[i:i + n])))
        return events
