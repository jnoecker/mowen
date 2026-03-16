"""Tests for event driver implementations."""

from mowen.event_drivers import event_driver_registry
from mowen.types import Event


class TestCharacterNGram:
    def test_default_trigrams(self):
        d = event_driver_registry.create("character_ngram")
        es = d.create_event_set("abcde")
        assert Event("abc") in es
        assert Event("bcd") in es
        assert Event("cde") in es
        assert len(es) == 3

    def test_custom_n(self):
        d = event_driver_registry.create("character_ngram", {"n": 2})
        es = d.create_event_set("abcd")
        assert Event("ab") in es
        assert Event("bc") in es
        assert Event("cd") in es
        assert len(es) == 3

    def test_text_shorter_than_n(self):
        d = event_driver_registry.create("character_ngram", {"n": 5})
        es = d.create_event_set("abc")
        assert len(es) == 0

    def test_text_equal_to_n(self):
        d = event_driver_registry.create("character_ngram", {"n": 3})
        es = d.create_event_set("abc")
        assert len(es) == 1
        assert Event("abc") in es

    def test_empty_text(self):
        d = event_driver_registry.create("character_ngram")
        es = d.create_event_set("")
        assert len(es) == 0


class TestWordEvents:
    def test_basic(self):
        d = event_driver_registry.create("word_events")
        es = d.create_event_set("the quick brown fox")
        assert len(es) == 4
        assert Event("the") in es
        assert Event("quick") in es

    def test_multiple_whitespace(self):
        d = event_driver_registry.create("word_events")
        es = d.create_event_set("hello   world")
        assert len(es) == 2

    def test_empty(self):
        d = event_driver_registry.create("word_events")
        es = d.create_event_set("")
        assert len(es) == 0


class TestWordNGram:
    def test_default_bigrams(self):
        d = event_driver_registry.create("word_ngram")
        es = d.create_event_set("the quick brown fox")
        assert Event("the quick") in es
        assert Event("quick brown") in es
        assert Event("brown fox") in es
        assert len(es) == 3

    def test_custom_n(self):
        d = event_driver_registry.create("word_ngram", {"n": 3})
        es = d.create_event_set("one two three four")
        assert Event("one two three") in es
        assert Event("two three four") in es
        assert len(es) == 2

    def test_fewer_words_than_n(self):
        d = event_driver_registry.create("word_ngram", {"n": 5})
        es = d.create_event_set("only two")
        assert len(es) == 0


class TestCharacterEvents:
    def test_basic(self):
        d = event_driver_registry.create("character_events")
        es = d.create_event_set("abc")
        assert len(es) == 3
        assert Event("a") in es
        assert Event("b") in es
        assert Event("c") in es

    def test_includes_spaces(self):
        d = event_driver_registry.create("character_events")
        es = d.create_event_set("a b")
        assert len(es) == 3
        assert Event(" ") in es

    def test_empty(self):
        d = event_driver_registry.create("character_events")
        es = d.create_event_set("")
        assert len(es) == 0


class TestWordLength:
    def test_basic(self):
        d = event_driver_registry.create("word_length")
        es = d.create_event_set("I am fine")
        assert Event("1") in es
        assert Event("2") in es
        assert Event("4") in es
        assert len(es) == 3

    def test_uniform_lengths(self):
        d = event_driver_registry.create("word_length")
        es = d.create_event_set("cat dog hat")
        assert all(e == Event("3") for e in es)
        assert len(es) == 3

    def test_empty(self):
        d = event_driver_registry.create("word_length")
        es = d.create_event_set("")
        assert len(es) == 0


class TestFunctionWords:
    def test_basic(self):
        d = event_driver_registry.create("function_words")
        es = d.create_event_set("the cat sat on the mat")
        assert Event("the") in es
        assert Event("on") in es

    def test_ignores_content_words(self):
        d = event_driver_registry.create("function_words")
        es = d.create_event_set("the cat sat on the mat")
        assert Event("cat") not in es
        assert Event("sat") not in es
        assert Event("mat") not in es

    def test_case_insensitive(self):
        d = event_driver_registry.create("function_words")
        es = d.create_event_set("The AND But")
        assert Event("the") in es
        assert Event("and") in es
        assert Event("but") in es
        assert len(es) == 3


class TestSentenceLength:
    def test_basic(self):
        d = event_driver_registry.create("sentence_length")
        es = d.create_event_set("I am here. You are there.")
        assert len(es) == 2
        assert Event("3") in es

    def test_multiple_punctuation(self):
        d = event_driver_registry.create("sentence_length")
        es = d.create_event_set("Hello world!! How are you?")
        assert Event("2") in es
        assert Event("3") in es
        assert len(es) == 2

    def test_no_sentences(self):
        d = event_driver_registry.create("sentence_length")
        es = d.create_event_set("")
        assert len(es) == 0


class TestSuffix:
    def test_default_length(self):
        d = event_driver_registry.create("suffix")
        es = d.create_event_set("running jumping walking")
        assert Event("ing") in es
        assert len(es) == 3

    def test_custom_length(self):
        d = event_driver_registry.create("suffix", {"length": 2})
        es = d.create_event_set("hello world")
        assert Event("lo") in es
        assert Event("ld") in es
        assert len(es) == 2

    def test_skips_short_words(self):
        d = event_driver_registry.create("suffix", {"length": 4})
        es = d.create_event_set("hi go running")
        assert len(es) == 1
        assert Event("ning") in es


class TestPunctuation:
    def test_basic(self):
        d = event_driver_registry.create("punctuation")
        es = d.create_event_set("Hello, world!")
        assert Event(",") in es
        assert Event("!") in es
        assert len(es) == 2

    def test_no_punctuation(self):
        d = event_driver_registry.create("punctuation")
        es = d.create_event_set("hello world")
        assert len(es) == 0

    def test_all_punctuation(self):
        d = event_driver_registry.create("punctuation")
        es = d.create_event_set(".,;:!?")
        assert len(es) == 6


class TestRareWords:
    def test_basic(self):
        d = event_driver_registry.create("rare_words")
        es = d.create_event_set("the cat and the dog")
        assert Event("cat") in es
        assert Event("and") in es
        assert Event("dog") in es
        assert Event("the") not in es

    def test_all_unique(self):
        d = event_driver_registry.create("rare_words")
        es = d.create_event_set("one two three")
        assert len(es) == 3

    def test_no_hapaxes(self):
        d = event_driver_registry.create("rare_words")
        es = d.create_event_set("go go go")
        assert len(es) == 0


class TestVowelInitialWords:
    def test_basic(self):
        d = event_driver_registry.create("vowel_initial_words")
        es = d.create_event_set("apple banana orange")
        assert Event("apple") in es
        assert Event("orange") in es
        assert Event("banana") not in es
        assert len(es) == 2

    def test_case_insensitive_vowels(self):
        d = event_driver_registry.create("vowel_initial_words")
        es = d.create_event_set("Apple Egg ice")
        assert len(es) == 3

    def test_no_vowel_initial(self):
        d = event_driver_registry.create("vowel_initial_words")
        es = d.create_event_set("the brown fox")
        assert len(es) == 0
