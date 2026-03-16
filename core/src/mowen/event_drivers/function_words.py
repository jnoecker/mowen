"""Function-word event driver."""

from __future__ import annotations

from mowen.types import Event, EventSet

from mowen.event_drivers.base import EventDriver, event_driver_registry

# Common English function (closed-class) words.
_FUNCTION_WORDS: frozenset[str] = frozenset({
    "the", "a", "an", "is", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "may", "might", "can", "could", "must",
    "of", "in", "to", "for", "with", "on", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "about", "against", "among", "around",
    "behind", "beside", "beyond", "despite", "down", "except",
    "inside", "like", "near", "off", "onto", "opposite", "outside",
    "over", "past", "since", "than", "toward", "towards", "under",
    "underneath", "unlike", "until", "up", "upon", "via", "within",
    "without",
    "and", "but", "or", "nor", "so", "yet", "both", "either",
    "neither", "not", "only", "very", "also", "just", "then",
    "thus", "hence", "therefore", "however", "moreover", "furthermore",
    "nevertheless", "nonetheless", "otherwise", "instead", "meanwhile",
    "accordingly", "consequently", "finally", "subsequently",
    "likewise", "similarly", "still", "already", "even", "rather",
    "quite", "too", "almost", "enough", "else", "perhaps", "indeed",
    "anyway", "besides", "certainly", "definitely", "exactly",
    "merely", "simply", "specifically",
    "i", "me", "my", "mine", "myself", "you", "your", "yours",
    "yourself", "he", "him", "his", "himself", "she", "her", "hers",
    "herself", "it", "its", "itself", "we", "us", "our", "ours",
    "ourselves", "they", "them", "their", "theirs", "themselves",
    "this", "that", "these", "those", "which", "who", "whom",
    "whose", "what", "where", "when", "how", "why",
    "all", "each", "every", "few", "many", "much", "some", "any",
    "no", "other", "another", "such",
    "if", "because", "although", "though", "while", "whereas",
    "unless", "whether", "once", "whenever", "wherever",
})


@event_driver_registry.register("function_words")
class FunctionWords(EventDriver):
    """Extract only function (closed-class) words from the text.

    Words are lowercased and compared against a built-in list of
    approximately 150 common English function words.
    """

    display_name = "Function Words"
    description = "Extract common English function words."

    def create_event_set(self, text: str) -> EventSet:
        events = EventSet()
        for word in text.split():
            lower = word.lower()
            if lower in _FUNCTION_WORDS:
                events.append(Event(data=lower))
        return events
