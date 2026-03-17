"""Built-in canonicizers for the mowen pipeline."""

from mowen.canonicizers.base import Canonicizer, canonicizer_registry

# Import implementation modules so their @register decorators execute.
# Ordered by frequency of use: common preprocessing first, niche last.
from mowen.canonicizers import unify_case as unify_case
from mowen.canonicizers import normalize_whitespace as normalize_whitespace
from mowen.canonicizers import strip_punctuation as strip_punctuation
from mowen.canonicizers import strip_numbers as strip_numbers
from mowen.canonicizers import normalize_ascii as normalize_ascii
from mowen.canonicizers import smash_i as smash_i
from mowen.canonicizers import punctuation_separator as punctuation_separator
from mowen.canonicizers import strip_comments as strip_comments
from mowen.canonicizers import strip_null_chars as strip_null_chars
from mowen.canonicizers import strip_non_punctuation as strip_non_punctuation

__all__ = ["Canonicizer", "canonicizer_registry"]
