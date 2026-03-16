"""Tests for canonicizer implementations."""

from mowen.canonicizers import canonicizer_registry


class TestUnifyCase:
    def test_lowercase(self):
        c = canonicizer_registry.create("unify_case")
        assert c.process("Hello WORLD") == "hello world"

    def test_already_lower(self):
        c = canonicizer_registry.create("unify_case")
        assert c.process("hello") == "hello"

    def test_empty(self):
        c = canonicizer_registry.create("unify_case")
        assert c.process("") == ""


class TestNormalizeWhitespace:
    def test_collapses_spaces(self):
        c = canonicizer_registry.create("normalize_whitespace")
        assert c.process("hello   world") == "hello world"

    def test_collapses_mixed(self):
        c = canonicizer_registry.create("normalize_whitespace")
        assert c.process("hello\t\n  world") == "hello world"

    def test_strips_edges(self):
        c = canonicizer_registry.create("normalize_whitespace")
        assert c.process("  hello  ") == "hello"

    def test_empty(self):
        c = canonicizer_registry.create("normalize_whitespace")
        assert c.process("") == ""


class TestStripPunctuation:
    def test_removes_punctuation(self):
        c = canonicizer_registry.create("strip_punctuation")
        result = c.process("Hello, world! How's it going?")
        assert "," not in result
        assert "!" not in result
        assert "?" not in result
        assert "'" not in result

    def test_preserves_letters_and_spaces(self):
        c = canonicizer_registry.create("strip_punctuation")
        assert c.process("hello world") == "hello world"

    def test_empty(self):
        c = canonicizer_registry.create("strip_punctuation")
        assert c.process("") == ""


class TestStripNumbers:
    def test_removes_digits(self):
        c = canonicizer_registry.create("strip_numbers")
        assert c.process("abc123def456") == "abcdef"

    def test_preserves_non_digits(self):
        c = canonicizer_registry.create("strip_numbers")
        assert c.process("hello world!") == "hello world!"

    def test_all_digits(self):
        c = canonicizer_registry.create("strip_numbers")
        assert c.process("0123456789") == ""

    def test_mixed_content(self):
        c = canonicizer_registry.create("strip_numbers")
        assert c.process("Room 101, Floor 3.") == "Room , Floor ."

    def test_empty(self):
        c = canonicizer_registry.create("strip_numbers")
        assert c.process("") == ""


class TestNormalizeAscii:
    def test_smart_quotes(self):
        c = canonicizer_registry.create("normalize_ascii")
        assert c.process("\u2018hello\u2019") == "'hello'"
        assert c.process("\u201chello\u201d") == '"hello"'

    def test_dashes(self):
        c = canonicizer_registry.create("normalize_ascii")
        assert c.process("word\u2014word") == "word-word"
        assert c.process("word\u2013word") == "word-word"

    def test_ellipsis(self):
        c = canonicizer_registry.create("normalize_ascii")
        assert c.process("wait\u2026") == "wait..."

    def test_accented_characters(self):
        c = canonicizer_registry.create("normalize_ascii")
        assert c.process("caf\u00e9") == "cafe"
        assert c.process("na\u00efve") == "naive"

    def test_plain_ascii_unchanged(self):
        c = canonicizer_registry.create("normalize_ascii")
        assert c.process("hello world 123") == "hello world 123"

    def test_empty(self):
        c = canonicizer_registry.create("normalize_ascii")
        assert c.process("") == ""


class TestPunctuationSeparator:
    def test_separates_punctuation(self):
        c = canonicizer_registry.create("punctuation_separator")
        result = c.process("hello,world")
        assert result == "hello , world"

    def test_multiple_punctuation(self):
        c = canonicizer_registry.create("punctuation_separator")
        result = c.process("wait...what?!")
        assert " . " in result
        assert " ? " in result
        assert " ! " in result

    def test_no_punctuation(self):
        c = canonicizer_registry.create("punctuation_separator")
        assert c.process("hello world") == "hello world"

    def test_already_separated(self):
        c = canonicizer_registry.create("punctuation_separator")
        result = c.process("hello , world")
        # The comma gets spaces around it, which adds extra spacing
        assert "," in result

    def test_empty(self):
        c = canonicizer_registry.create("punctuation_separator")
        assert c.process("") == ""


class TestStripNonPunctuation:
    def test_keeps_only_punctuation_and_whitespace(self):
        c = canonicizer_registry.create("strip_non_punctuation")
        assert c.process("Hello, world!") == ", !"

    def test_preserves_whitespace(self):
        c = canonicizer_registry.create("strip_non_punctuation")
        result = c.process("no punctuation here")
        assert result == "  "

    def test_all_punctuation(self):
        c = canonicizer_registry.create("strip_non_punctuation")
        assert c.process("!@#$%") == "!@#$%"

    def test_mixed_content(self):
        c = canonicizer_registry.create("strip_non_punctuation")
        assert c.process("a.b,c;d") == ".,;"

    def test_empty(self):
        c = canonicizer_registry.create("strip_non_punctuation")
        assert c.process("") == ""


class TestStripNullChars:
    def test_removes_null_character(self):
        c = canonicizer_registry.create("strip_null_chars")
        assert c.process("hello\x00world") == "helloworld"

    def test_removes_control_characters(self):
        c = canonicizer_registry.create("strip_null_chars")
        assert c.process("hello\x01\x02\x03world") == "helloworld"

    def test_preserves_tab_newline_cr(self):
        c = canonicizer_registry.create("strip_null_chars")
        assert c.process("hello\t\n\rworld") == "hello\t\n\rworld"

    def test_mixed_control_chars(self):
        c = canonicizer_registry.create("strip_null_chars")
        # \x00 (null) and \x1f (unit separator) removed, \t and \n kept
        assert c.process("a\x00b\tc\x1fd\n") == "ab\tcd\n"

    def test_no_control_chars(self):
        c = canonicizer_registry.create("strip_null_chars")
        assert c.process("hello world") == "hello world"

    def test_empty(self):
        c = canonicizer_registry.create("strip_null_chars")
        assert c.process("") == ""


class TestStripComments:
    # --- C style ---
    def test_c_line_comment(self):
        c = canonicizer_registry.create("strip_comments", params={"style": "c"})
        assert c.process("code // comment\nmore") == "code \nmore"

    def test_c_block_comment(self):
        c = canonicizer_registry.create("strip_comments", params={"style": "c"})
        assert c.process("before /* block\ncomment */ after") == "before  after"

    def test_c_does_not_strip_python_comments(self):
        c = canonicizer_registry.create("strip_comments", params={"style": "c"})
        assert c.process("code # not removed") == "code # not removed"

    # --- Python style ---
    def test_python_line_comment(self):
        c = canonicizer_registry.create("strip_comments", params={"style": "python"})
        assert c.process("code # comment\nmore") == "code \nmore"

    def test_python_does_not_strip_c_comments(self):
        c = canonicizer_registry.create("strip_comments", params={"style": "python"})
        assert c.process("code // not removed") == "code // not removed"

    def test_python_does_not_strip_html_comments(self):
        c = canonicizer_registry.create("strip_comments", params={"style": "python"})
        assert c.process("<!-- kept -->") == "<!-- kept -->"

    # --- HTML style ---
    def test_html_comment(self):
        c = canonicizer_registry.create("strip_comments", params={"style": "html"})
        assert c.process("before <!-- comment --> after") == "before  after"

    def test_html_multiline_comment(self):
        c = canonicizer_registry.create("strip_comments", params={"style": "html"})
        result = c.process("before <!-- multi\nline --> after")
        assert result == "before  after"

    def test_html_does_not_strip_c_comments(self):
        c = canonicizer_registry.create("strip_comments", params={"style": "html"})
        assert c.process("code // not removed") == "code // not removed"

    # --- Auto style (all three) ---
    def test_auto_strips_all_styles(self):
        c = canonicizer_registry.create("strip_comments", params={"style": "auto"})
        text = "a // c\nb # py\nc <!-- html -->"
        result = c.process(text)
        assert "//" not in result
        assert "#" not in result
        assert "<!--" not in result

    def test_auto_is_default(self):
        c = canonicizer_registry.create("strip_comments")
        text = "a // c-comment\nb # py-comment\nc <!-- html -->"
        result = c.process(text)
        assert "//" not in result
        assert "#" not in result
        assert "<!--" not in result

    def test_empty(self):
        c = canonicizer_registry.create("strip_comments")
        assert c.process("") == ""

    def test_no_comments(self):
        c = canonicizer_registry.create("strip_comments")
        assert c.process("just code") == "just code"
