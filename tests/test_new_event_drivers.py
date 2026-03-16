"""Tests for Phase 2 event drivers."""

from mowen.event_drivers import event_driver_registry
from mowen.types import Event


class TestKSkipCharacterNGram:
    def test_default(self):
        d = event_driver_registry.create("k_skip_character_ngram")
        es = d.create_event_set("abcde")
        # n=2, k=1: pairs with 1 char skipped: ac, bd, ce
        assert Event("ac") in es
        assert Event("bd") in es
        assert Event("ce") in es

    def test_k_zero_is_standard_ngram(self):
        d = event_driver_registry.create("k_skip_character_ngram", {"n": 2, "k": 0})
        es = d.create_event_set("abcd")
        assert Event("ab") in es
        assert Event("bc") in es
        assert Event("cd") in es
        assert len(es) == 3

    def test_empty(self):
        d = event_driver_registry.create("k_skip_character_ngram")
        assert len(d.create_event_set("")) == 0


class TestKSkipWordNGram:
    def test_default(self):
        d = event_driver_registry.create("k_skip_word_ngram")
        es = d.create_event_set("one two three four five")
        # n=2, k=1: skip 1 word between each: "one three", "two four", "three five"
        assert Event("one three") in es
        assert Event("two four") in es
        assert Event("three five") in es

    def test_k_zero(self):
        d = event_driver_registry.create("k_skip_word_ngram", {"n": 2, "k": 0})
        es = d.create_event_set("the quick brown")
        assert Event("the quick") in es
        assert Event("quick brown") in es

    def test_empty(self):
        d = event_driver_registry.create("k_skip_word_ngram")
        assert len(d.create_event_set("")) == 0


class TestSortedCharacterNGram:
    def test_basic(self):
        d = event_driver_registry.create("sorted_character_ngram", {"n": 3})
        es = d.create_event_set("cba")
        # "cba" sorted -> "abc"
        assert Event("abc") in es
        assert len(es) == 1

    def test_order_invariance(self):
        d = event_driver_registry.create("sorted_character_ngram", {"n": 2})
        es1 = d.create_event_set("ab")
        es2 = d.create_event_set("ba")
        assert es1[0] == es2[0]

    def test_empty(self):
        d = event_driver_registry.create("sorted_character_ngram")
        assert len(d.create_event_set("")) == 0


class TestSortedWordNGram:
    def test_basic(self):
        d = event_driver_registry.create("sorted_word_ngram", {"n": 2})
        es = d.create_event_set("cat bat")
        # "cat bat" sorted -> "bat cat"
        assert Event("bat cat") in es

    def test_order_invariance(self):
        d = event_driver_registry.create("sorted_word_ngram", {"n": 2})
        es1 = d.create_event_set("hello world")
        es2 = d.create_event_set("world hello")
        assert es1[0] == es2[0]

    def test_empty(self):
        d = event_driver_registry.create("sorted_word_ngram")
        assert len(d.create_event_set("")) == 0


class TestMNLetterWords:
    def test_default(self):
        d = event_driver_registry.create("mn_letter_words")
        es = d.create_event_set("I am a fine person")
        # Default m=1, n=3: words len 1-3
        assert Event("I") in es
        assert Event("am") in es
        assert Event("a") in es
        assert Event("person") not in es
        assert Event("fine") not in es

    def test_custom_range(self):
        d = event_driver_registry.create("mn_letter_words", {"m": 4, "n": 6})
        es = d.create_event_set("I am a fine person today")
        assert Event("fine") in es
        assert Event("person") in es
        assert Event("today") in es
        assert Event("I") not in es
        assert Event("am") not in es

    def test_empty(self):
        d = event_driver_registry.create("mn_letter_words")
        assert len(d.create_event_set("")) == 0


class TestFirstWordInSentence:
    def test_basic(self):
        d = event_driver_registry.create("first_word_in_sentence")
        es = d.create_event_set("Hello world. Goodbye everyone!")
        assert Event("Hello") in es
        assert Event("Goodbye") in es
        assert len(es) == 2

    def test_single_sentence(self):
        d = event_driver_registry.create("first_word_in_sentence")
        es = d.create_event_set("Just one sentence")
        assert Event("Just") in es
        assert len(es) == 1

    def test_empty(self):
        d = event_driver_registry.create("first_word_in_sentence")
        assert len(d.create_event_set("")) == 0


class TestSentenceEvents:
    def test_basic(self):
        d = event_driver_registry.create("sentence_events")
        es = d.create_event_set("Hello world. Goodbye!")
        assert len(es) == 2
        assert Event("Hello world.") in es
        assert Event("Goodbye!") in es

    def test_single_sentence(self):
        d = event_driver_registry.create("sentence_events")
        es = d.create_event_set("Just one.")
        assert len(es) == 1

    def test_empty(self):
        d = event_driver_registry.create("sentence_events")
        assert len(d.create_event_set("")) == 0


class TestPorterStemmer:
    def test_basic_stems(self):
        d = event_driver_registry.create("porter_stemmer")
        es = d.create_event_set("running jumps played")
        stems = [e.data for e in es]
        assert "run" in stems
        assert "jump" in stems
        assert "plai" in stems  # standard Porter output for "played"

    def test_short_words_unchanged(self):
        d = event_driver_registry.create("porter_stemmer")
        es = d.create_event_set("a I go")
        stems = [e.data for e in es]
        assert "a" in stems
        assert "i" in stems  # lowercased
        assert "go" in stems

    def test_empty(self):
        d = event_driver_registry.create("porter_stemmer")
        assert len(d.create_event_set("")) == 0

    def test_known_stems(self):
        d = event_driver_registry.create("porter_stemmer")
        # Classic Porter test cases
        cases = [
            ("caresses", "caress"),
            ("ponies", "poni"),
            ("cats", "cat"),
            ("feed", "feed"),
            ("agreed", "agre"),
            ("plastered", "plaster"),
            ("bled", "bled"),
            ("motoring", "motor"),
            ("sing", "sing"),
        ]
        for word, expected in cases:
            es = d.create_event_set(word)
            assert es[0].data == expected, f"stem({word!r}) = {es[0].data!r}, expected {expected!r}"


class TestMWFunctionWords:
    def test_basic(self):
        d = event_driver_registry.create("mw_function_words")
        es = d.create_event_set("The government must be strong to protect liberty")
        # "the", "must", "be", "to" are MW function words
        assert Event("the") in es
        assert Event("must") in es
        assert Event("be") in es
        assert Event("to") in es
        # "government", "strong", "protect", "liberty" are not
        assert Event("government") not in es
        assert Event("strong") not in es

    def test_case_insensitive(self):
        d = event_driver_registry.create("mw_function_words")
        es = d.create_event_set("The THE the")
        assert len(es) == 3
        assert all(e.data == "the" for e in es)

    def test_empty(self):
        d = event_driver_registry.create("mw_function_words")
        assert len(d.create_event_set("")) == 0

    def test_no_function_words(self):
        d = event_driver_registry.create("mw_function_words")
        es = d.create_event_set("government strong protect")
        assert len(es) == 0
