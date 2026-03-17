"""Function-word event driver with multi-language support."""

from __future__ import annotations

from mowen.data import load_function_words
from mowen.event_drivers.base import EventDriver, event_driver_registry
from mowen.parameters import ParamDef
from mowen.tokenizers import TOKENIZER_PARAM, tokenize_text
from mowen.types import Event, EventSet


@event_driver_registry.register("function_words")
class FunctionWords(EventDriver):
    """Extract function (closed-class) words from the text.

    Words are lowercased and compared against a built-in function word
    list for the specified language.  Supports English, Chinese, Spanish,
    French, German, Portuguese, Italian, Russian, Arabic, and Japanese.
    """

    display_name = "Function Words"
    description = "Extract function words for a given language."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="language",
                description="Language for the function word list.",
                param_type=str,
                default="english",
            ),
            TOKENIZER_PARAM,
        ]

    def create_event_set(self, text: str) -> EventSet:
        language: str = self.get_param("language")
        tok: str = self.get_param("tokenizer")
        word_set = load_function_words(language)
        events = EventSet()
        for word in tokenize_text(text, tok):
            lower = word.lower()
            if lower in word_set:
                events.append(Event(data=lower))
        return events
