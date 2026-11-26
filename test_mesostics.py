"""Tests for the generator's state machine.

The generator reads module-level configuration, so every test that changes the
source text or a setting restores it afterwards.
"""

import warnings

import pytest

import mesostics


@pytest.fixture
def source(monkeypatch):
    """Replace the corpus with a word list for the duration of one test."""
    def use(words):
        monkeypatch.setattr(mesostics, "source_text", list(words))
    return use


class TestLineFlushing:
    def test_a_line_that_never_finishes_is_still_returned(self, source):
        # "then" presents E and advances the spine; "me" ends the right wing
        # and leaves the line short of A. The work done must survive.
        source(["then", "with", "me"])
        lines = mesostics.generate_mesostic()
        assert lines, "E was presented, so the line must not vanish"
        assert "thEn" in lines[0]

    def test_no_spine_letter_found_produces_nothing(self, source):
        source(["xyz", "xyz"])
        assert mesostics.generate_mesostic() == []

    def test_lines_are_never_blank(self, source):
        source(["then", "with", "me"])
        assert all(line.strip() for line in mesostics.generate_mesostic())


class TestIncompleteSpine:
    """A spine that cannot be finished has to say so rather than stop quietly."""

    def test_warns_when_the_spine_cannot_be_completed(self, source):
        source(["then", "with", "me"])
        with pytest.warns(UserWarning, match="spine incomplete"):
            mesostics.generate_mesostic()

    def test_the_warning_names_the_letter_it_stopped_on(self, source):
        source(["then", "with", "me"])
        with pytest.warns(UserWarning, match="'Z'"):
            mesostics.generate_mesostic()

    def test_running_out_of_text_is_reported_as_such(self, source):
        source(["then", "with", "me"])
        with pytest.warns(UserWarning, match="source text ran out"):
            mesostics.generate_mesostic()

    def test_exhausted_syllables_are_named(self, source, monkeypatch):
        # Every Z-bearing word in Canto I is "bronze". Read the text twice and
        # the second pass can never present Z again.
        with open(mesostics.CORPUS_PATH, encoding="utf-8") as corpus:
            source(corpus.read().split() * 2)
        with pytest.warns(UserWarning, match="bronze"):
            mesostics.generate_mesostic()

    def test_a_complete_spine_warns_about_nothing(self, source):
        with open(mesostics.CORPUS_PATH, encoding="utf-8") as corpus:
            words = corpus.read().split()
        # Truncate just past the "Poured" that presents D, which is the second
        # of two in the text and the point where POUND is complete.
        end = len(words) - words[::-1].index("Poured")
        source(words[:end])
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            mesostics.generate_mesostic()
