"""Event driver components for the mowen pipeline."""

from mowen.event_drivers.base import EventDriver, event_driver_registry

# Import implementation modules so their @register decorators execute.
# Ordered: best-performing / most commonly used first, niche last.

# --- Tier 1: State-of-the-art / commonly used in competitions ---
from mowen.event_drivers import character_ngram as character_ngram  # noqa: F401
from mowen.event_drivers import word_events as word_events  # noqa: F401
from mowen.event_drivers import word_ngram as word_ngram  # noqa: F401
from mowen.event_drivers import function_words as function_words  # noqa: F401

# --- Tier 2: Strong features, widely cited ---
from mowen.event_drivers import word_length as word_length  # noqa: F401
from mowen.event_drivers import sentence_length as sentence_length  # noqa: F401
from mowen.event_drivers import character_events as character_events  # noqa: F401
from mowen.event_drivers import punctuation as punctuation  # noqa: F401
from mowen.event_drivers import punctuation_ngram as punctuation_ngram  # noqa: F401
from mowen.event_drivers import mw_function_words as mw_function_words  # noqa: F401
from mowen.event_drivers import pos_tags as pos_tags  # noqa: F401

# --- Tier 3: Useful variants ---
from mowen.event_drivers import leave_k_out_ngram as leave_k_out_ngram  # noqa: F401
from mowen.event_drivers import sorted_ngram as sorted_ngram  # noqa: F401
from mowen.event_drivers import k_skip_ngram as k_skip_ngram  # noqa: F401
from mowen.event_drivers import suffix as suffix  # noqa: F401
from mowen.event_drivers import porter_stemmer as porter_stemmer  # noqa: F401
from mowen.event_drivers import rare_words as rare_words  # noqa: F401
from mowen.event_drivers import vowel_initial_words as vowel_initial_words  # noqa: F401

# --- Tier 4: Structural / metadata features ---
from mowen.event_drivers import sentence_features as sentence_features  # noqa: F401
from mowen.event_drivers import line_features as line_features  # noqa: F401
from mowen.event_drivers import mn_letter_words as mn_letter_words  # noqa: F401
from mowen.event_drivers import vowel_mn_letter_words as vowel_mn_letter_words  # noqa: F401
from mowen.event_drivers import syllables as syllables  # noqa: F401
from mowen.event_drivers import truncated_frequency as truncated_frequency  # noqa: F401
from mowen.event_drivers import reaction_time as reaction_time  # noqa: F401

# --- Tier 5: NLP-dependent (require optional extras) ---
from mowen.event_drivers import pos_features as pos_features  # noqa: F401
from mowen.event_drivers import ner as ner  # noqa: F401
from mowen.event_drivers import definitions as definitions  # noqa: F401

try:
    from mowen.event_drivers import transformer_embeddings as transformer_embeddings  # noqa: F401
except ImportError:
    pass  # transformers/torch not installed

try:
    from mowen.event_drivers import selma_embeddings as selma_embeddings  # noqa: F401
except ImportError:
    pass  # transformers/torch not installed

try:
    from mowen.event_drivers import perplexity as perplexity  # noqa: F401
except ImportError:
    pass  # transformers/torch not installed

__all__ = ["EventDriver", "event_driver_registry"]
