"""Tests for the generator's state machine.

The generator reads module-level configuration, so every test that changes the
source text or a setting restores it afterwards.
"""

import random
import re
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

    def test_exhausted_syllables_are_named(self, source):
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


class TestWingContiguity:
    """A wing is described as consecutive, so a skipped word must break it."""

    @staticmethod
    def corpus():
        with open(mesostics.CORPUS_PATH, encoding="utf-8") as text:
            return text.read().split()

    def test_a_skipped_word_breaks_the_chain(self, source):
        # Canto I leaves the spine stuck on Z. Offer a spent Z word, a neutral
        # word, then a fresh one: the wing may reach the neutral word and stop.
        source(self.corpus() + ["bronze", "crawl", "zoo"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            last = mesostics.generate_mesostic()[-1]
        assert "crawl] Zoo" in last
        assert "bough" not in last, "wing reached back past the skipped word"

    def test_every_wing_is_a_contiguous_run_of_the_source(self, source):
        words = self.corpus()
        source(words)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lines = mesostics.generate_mesostic()

        for line in lines:
            for wing in re.findall(r"\[([^\]]*)\]", line):
                run = wing.split(" | ")
                assert any(words[i:i + len(run)] == run
                           for i in range(len(words) - len(run) + 1)), (
                    f"wing {run} is not contiguous in the source")


class TestMesosticRule:
    """The strictness knob was documented but never read."""

    @staticmethod
    def run(monkeypatch, rule):
        monkeypatch.setattr(mesostics, "MESOSTIC_RULE", rule)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return mesostics.generate_mesostic()

    def test_the_default_is_the_rule_cage_states(self):
        assert mesostics.MESOSTIC_RULE == "100%"

    def test_relaxing_the_rule_admits_more_wing_material(self, monkeypatch):
        sizes = [sum(len(line) for line in self.run(monkeypatch, rule))
                 for rule in ("100%", "50%", "0%")]
        assert sizes[0] < sizes[1] < sizes[2], sizes

    def test_each_level_gives_a_different_poem(self, monkeypatch):
        poems = [self.run(monkeypatch, rule) for rule in ("100%", "50%", "0%")]
        assert poems[0] != poems[1] != poems[2]

    def test_an_unknown_rule_fails_loudly(self, monkeypatch):
        with pytest.raises(ValueError, match="MESOSTIC_RULE"):
            self.run(monkeypatch, "110%")

    @pytest.mark.parametrize(
        "other,current,rule,expected",
        [("E", "Z", "100%", {"E", "Z"}),
         ("E", "Z", "50%", {"Z"}),
         ("E", "Z", "0%", set()),
         (None, "E", "100%", {"E"})],
    )
    def test_prohibited_letters(self, monkeypatch, other, current, rule, expected):
        monkeypatch.setattr(mesostics, "MESOSTIC_RULE", rule)
        assert mesostics.prohibited_letters(other, current) == expected


CANDIDATES = ["the", "bronze", "lance", "of", "heads"]


class TestWingModes:
    """select_wing_words had no coverage at all beyond SHOW_ALL."""

    def test_empty_candidates_give_an_empty_wing(self):
        for mode in ("SHOW_ALL", "MAX", "RANDOM", "MINIMAL", "INTERACTIVE"):
            assert mesostics.select_wing_words([], mode) == []

    def test_show_all_brackets_every_candidate(self):
        assert (mesostics.select_wing_words(CANDIDATES, "SHOW_ALL")
                == "[the | bronze | lance | of | heads]")

    def test_max_keeps_every_candidate_in_order(self):
        assert mesostics.select_wing_words(CANDIDATES, "MAX") == CANDIDATES

    def test_an_unknown_mode_behaves_like_max(self):
        assert (mesostics.select_wing_words(CANDIDATES, "NONSENSE")
                == CANDIDATES)

    def test_minimal_takes_the_two_longest_content_words(self):
        # "the" and "of" are stopwords and must not survive the cut. "lance"
        # and "heads" tie at five characters, and the sort is stable, so the
        # earlier one wins.
        assert (mesostics.select_wing_words(CANDIDATES, "MINIMAL")
                == ["bronze", "lance"])

    def test_minimal_falls_back_when_every_word_is_a_stopword(self):
        assert mesostics.select_wing_words(["the", "of"], "MINIMAL") == ["the"]

    @pytest.mark.parametrize("seed", range(10))
    def test_random_stays_within_the_configured_count(self, seed):
        random.seed(seed)
        chosen = mesostics.select_wing_words(CANDIDATES, "RANDOM")
        low, high = mesostics.RANDOM_WORD_COUNT
        assert low <= len(chosen) <= high
        assert set(chosen) <= set(CANDIDATES)
        assert len(set(chosen)) == len(chosen), "a word was offered twice"

    def test_interactive_is_still_a_stub_that_behaves_like_max(self):
        assert (mesostics.select_wing_words(CANDIDATES, "INTERACTIVE")
                == CANDIDATES)

    def test_interactive_does_not_write_into_the_poem(self, capsys):
        mesostics.select_wing_words(CANDIDATES, "INTERACTIVE")
        captured = capsys.readouterr()
        assert captured.out == "", "stdout carries the poem and must stay clean"
        assert "bronze" in captured.err

    @pytest.mark.parametrize("mode", ["MAX", "MINIMAL", "RANDOM"])
    def test_every_mode_produces_a_poem(self, mode, monkeypatch):
        monkeypatch.setattr(mesostics, "WING_MODE", mode)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lines = mesostics.generate_mesostic()
        assert lines and all(line.strip() for line in lines)


class TestCapitalizeLetter:
    def test_marks_the_first_occurrence(self):
        assert mesostics.capitalize_letter("bronze", "z") == "bronZe"

    def test_is_case_insensitive(self):
        assert mesostics.capitalize_letter("bronze", "Z") == "bronZe"

    def test_a_word_without_the_letter_is_returned_unchanged(self):
        assert mesostics.capitalize_letter("sheep", "z") == "sheep"


class TestTrailingRightWing:
    def test_text_ending_mid_wing_keeps_the_wing(self, source, monkeypatch):
        monkeypatch.setattr(mesostics, "WING_MODE", "MAX")
        source(["then", "with"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lines = mesostics.generate_mesostic()
        assert lines == ["thEn with"]

    def test_show_all_brackets_a_trailing_wing(self, source):
        source(["then", "with"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lines = mesostics.generate_mesostic()
        assert lines == ["thEn [with]"]
