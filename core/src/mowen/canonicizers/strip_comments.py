"""Canonicizer that removes common code comment patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass

from mowen.canonicizers.base import Canonicizer, canonicizer_registry
from mowen.parameters import ParamDef

# C-style: // line comments and /* */ block comments.
_C_LINE_COMMENT = re.compile(r"//[^\n]*")
_C_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)

# Python-style: # to end of line.
_PYTHON_COMMENT = re.compile(r"#[^\n]*")

# HTML-style: <!-- --> comments.
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def _strip_c(text: str) -> str:
    """Remove C-style line and block comments."""
    text = _C_BLOCK_COMMENT.sub("", text)
    return _C_LINE_COMMENT.sub("", text)


def _strip_python(text: str) -> str:
    """Remove Python-style line comments."""
    return _PYTHON_COMMENT.sub("", text)


def _strip_html(text: str) -> str:
    """Remove HTML-style comments."""
    return _HTML_COMMENT.sub("", text)


_STRIPPERS: dict[str, list[callable]] = {
    "c": [_strip_c],
    "python": [_strip_python],
    "html": [_strip_html],
    "auto": [_strip_c, _strip_python, _strip_html],
}


@canonicizer_registry.register("strip_comments")
@dataclass
class StripComments(Canonicizer):
    """Remove common code comment patterns from the text."""

    display_name: str = "Strip Comments"
    description: str = "Removes code comments in C, Python, and/or HTML style."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        """Declare the comment-style parameter."""
        return [
            ParamDef(
                name="style",
                description=(
                    "Comment style to strip: 'c' for // and /* */, "
                    "'python' for #, 'html' for <!-- -->, "
                    "or 'auto' for all three."
                ),
                param_type=str,
                default="auto",
                choices=["auto", "c", "python", "html"],
            ),
        ]

    def process(self, text: str) -> str:
        """Return *text* with comments removed according to the configured style."""
        style: str = self.get_param("style")
        for fn in _STRIPPERS[style]:
            text = fn(text)
        return text
