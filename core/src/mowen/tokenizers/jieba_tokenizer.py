"""Chinese word segmentation tokenizer using jieba."""

from __future__ import annotations

from dataclasses import dataclass

from mowen.parameters import ParamDef
from mowen.tokenizers.base import Tokenizer, tokenizer_registry


@tokenizer_registry.register("jieba")
@dataclass
class JiebaTokenizer(Tokenizer):
    """Segment Chinese text into words using the jieba library.

    Supports three segmentation modes:

    * ``accurate`` (default) — attempts to cut the sentence into the
      most accurate segmentation.
    * ``full`` — scans all possible words, faster but may over-segment.
    * ``search`` — based on accurate mode, with additional long-word
      splitting for search engine indexing.

    Requires the ``jieba`` package.  Install with::

        pip install 'mowen[chinese]'
    """

    display_name = "Jieba (Chinese)"
    description = "Chinese word segmentation via jieba."

    @classmethod
    def param_defs(cls) -> list[ParamDef]:
        return [
            ParamDef(
                name="mode",
                description="Segmentation mode: accurate, full, or search.",
                param_type=str,
                default="accurate",
                choices=["accurate", "full", "search"],
            ),
        ]

    def tokenize(self, text: str) -> list[str]:
        try:
            import jieba  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ImportError(
                "Chinese tokenization requires the jieba library. "
                "Install with: pip install 'mowen[chinese]'"
            ) from exc

        mode: str = self.get_param("mode")
        if mode == "full":
            tokens = jieba.cut(text, cut_all=True)
        elif mode == "search":
            tokens = jieba.cut_for_search(text)
        else:
            tokens = jieba.cut(text, cut_all=False)

        return [t for t in tokens if t.strip()]
