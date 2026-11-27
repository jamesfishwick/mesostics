"""Tests for the syllable index's splitting.

The cases in `PYPHEN_UNDER_SPLITS` are the ones that motivated this module: a
hyphenator refuses to break them, so the index recorded a whole word where a
syllable belonged.
"""

import os
import re

import pytest

from syllables import (
    cmu_syllable_count,
    extract_syllable_with_letter,
    normalize,
    syllabify,
    syllable_count,
)

# word -> (expected syllables, spine letter, syllable that presents it)
PYPHEN_UNDER_SPLITS = {
    "about": (2, "b", "bout"),
    "ago": (2, "g", "go"),
    "money": (2, "n", "ney"),
    "watery": (3, "t", "te"),
}

MONOSYLLABLES = ["sheep", "then", "strong", "bronze", "praised", "poured", "arms"]


@pytest.mark.parametrize("word", sorted(PYPHEN_UNDER_SPLITS))
def test_short_words_are_split(word):
    expected_count, _, _ = PYPHEN_UNDER_SPLITS[word]
    assert len(syllabify(word)) == expected_count


@pytest.mark.parametrize("word", sorted(PYPHEN_UNDER_SPLITS))
def test_extract_returns_a_syllable_not_the_word(word):
    _, letter, expected = PYPHEN_UNDER_SPLITS[word]
    assert extract_syllable_with_letter(word, letter) == expected


def test_issue_repro():
    assert extract_syllable_with_letter("about", "b") == "bout"


@pytest.mark.parametrize("word", MONOSYLLABLES)
def test_monosyllables_stay_whole(word):
    assert syllabify(word) == [word]


@pytest.mark.parametrize(
    "word,expected",
    [
        ("interest", ["in", "terest"]),
        ("particular", ["par", "ti", "cu", "lar"]),
        ("slaughtered", ["slaugh", "tered"]),
        ("chaos", ["cha", "os"]),
    ],
)
def test_known_splits(word, expected):
    assert syllabify(word) == expected


class TestNormalization:
    """Punctuation must not reach the index, or a repeat hides behind a comma."""

    @pytest.mark.parametrize(
        "token,expected",
        [("bronZe,", "bronze"), ("companions.”", "companions"),
         ("“Odysseus", "odysseus"), ("o’er", "o'er"), ("'", "")],
    )
    def test_normalize(self, token, expected):
        assert normalize(token) == expected

    def test_punctuation_does_not_change_the_indexed_syllable(self):
        assert (extract_syllable_with_letter("bronZe,", "z")
                == extract_syllable_with_letter("bronze", "z"))

    def test_a_repeat_behind_punctuation_is_still_a_repeat(self):
        index = {extract_syllable_with_letter("then", "e")}
        assert extract_syllable_with_letter("thEn,", "e") in index


class TestCmuArbitration:
    def test_counts_come_from_cmu(self):
        assert cmu_syllable_count("about") == 2
        assert cmu_syllable_count("particular") == 4

    def test_unknown_words_report_no_count(self):
        assert cmu_syllable_count("elpenor") is None

    def test_syllable_count_falls_back_to_the_split(self):
        # Pound's coinages are not in CMU; the count still has to come out.
        assert syllable_count("napenerve") == len(syllabify("napenerve"))

    @pytest.mark.parametrize("word", ["elpenor", "eurylochus", "sunless", "closewebbed"])
    def test_out_of_vocabulary_words_still_split(self, word):
        assert len(syllabify(word)) > 1


class TestInvariants:
    """Properties that must hold for every word in the source text."""

    CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "corpus", "canto_i.txt")

    @classmethod
    def corpus_words(cls):
        # Anchored to this file, not the working directory: pytest can be
        # invoked from anywhere.
        with open(cls.CORPUS, encoding="utf-8") as source:
            return sorted({normalize(word) for word in source.read().split()} - {""})

    def test_split_reconstructs_the_word(self):
        for word in self.corpus_words():
            assert "".join(syllabify(word)) == word, word

    def test_no_empty_syllables(self):
        for word in self.corpus_words():
            assert all(syllabify(word)), word

    def test_count_matches_cmu_where_cmu_knows_the_word(self):
        mismatched = [
            word for word in self.corpus_words()
            if cmu_syllable_count(word) is not None
            and len(syllabify(word)) != cmu_syllable_count(word)
        ]
        assert mismatched == []

    def test_polysyllabic_words_are_never_returned_whole(self):
        for word in self.corpus_words():
            count = cmu_syllable_count(word)
            if count and count > 1:
                assert len(syllabify(word)) > 1, word

    def test_extract_returns_a_substring_of_the_word(self):
        for word in self.corpus_words():
            for letter in set(word):
                if letter.isalpha():
                    assert extract_syllable_with_letter(word, letter) in word

    def test_extract_result_contains_the_letter(self):
        for word in self.corpus_words():
            for letter in set(word):
                if letter.isalpha():
                    assert letter in extract_syllable_with_letter(word, letter)


class TestEdgeCases:
    @pytest.mark.parametrize("word", ["hmm", "shh", "abc"])
    def test_words_without_splittable_nuclei_survive(self, word):
        assert syllabify(word) == [word]

    def test_empty_input(self):
        assert syllabify("") == []
        assert syllabify("---") == ["---"]

    def test_letter_absent_from_the_word(self):
        assert extract_syllable_with_letter("sheep", "z") == "sheep"

    def test_extraction_is_case_insensitive(self):
        assert (extract_syllable_with_letter("bronZe", "Z")
                == extract_syllable_with_letter("bronze", "z"))


def test_the_generator_still_runs():
    """Importing the script must not run it, and the run must still produce lines."""
    import mesostics

    lines = mesostics.generate_mesostic()
    assert lines and all(line.strip() for line in lines)
    assert re.search(r"[A-Z]", lines[0])
