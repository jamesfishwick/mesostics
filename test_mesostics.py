"""Tests for the generator's state machine.

The generator reads module-level configuration, so every test that changes the
source text or a setting restores it afterwards.
"""

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
