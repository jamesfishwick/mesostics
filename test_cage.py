"""Pin the agreement with Cage's published text.

The EZRA line is the one thing this implementation gets exactly right, so it
is worth a regression guard. The POUND line is the open problem.
"""

import pytest

import cage


class TestParsing:
    def test_presentations_reads_marked_words_in_order(self):
        assert cage.presentations("and thEn with bronZe") == [
            ("E", "thEn"), ("Z", "bronZe")]

    def test_a_word_can_carry_two_spine_letters(self):
        # Cage does this three times across the piece.
        assert cage.presentations("sEa-jauZionda motheR of yeArs") == [
            ("E", "sEa-jauZionda"), ("Z", "sEa-jauZionda"),
            ("R", "motheR"), ("A", "yeArs")]

    @pytest.mark.parametrize("line,expected", [
        ("and thEn with bronZe lance heads beaRing yet Arms", True),
        ("sheeP slain Of plUto stroNg praiseD", True),
        ("that fortunatEly just belonged to me", False),       # a neighbouring piece
        ("lished by the Crown Point Press, Oakland", False),   # headnote prose
        ("", False),
    ])
    def test_is_spine_line(self, line, expected):
        assert cage.is_spine_line(line) is expected

    def test_bare_ignores_case_and_punctuation(self):
        assert cage.bare("Arms,") == cage.bare("Arms") == "arms"


class TestAgreement:
    def test_the_ezra_line_matches_cage_exactly(self):
        rows = cage.compare()[:4]
        assert [letter for letter, *_ in rows] == list("EZRA")
        assert all(agree for *_, agree in rows), rows

    def test_the_pound_line_still_diverges(self):
        """Pinned so a change that fixes it is noticed rather than missed."""
        rows = cage.compare()[4:9]
        assert [letter for letter, *_ in rows] == list("POUND")
        assert not any(agree for *_, agree in rows), rows

    def test_the_divergence_begins_at_p(self):
        rows = cage.compare()
        first_bad = next(r for r in rows if not r[3])
        assert first_bad[0] == "P"
        assert cage.bare(first_bad[1]) == "sheep"

    def test_overall_score(self):
        rows = cage.compare()
        assert (sum(1 for *_, agree in rows if agree), len(rows)) == (4, 9)


class TestReference:
    def test_the_canto_i_pair_is_the_committed_reference(self):
        assert len(cage.CANTO_I) == 2
        assert cage.spine_words(cage.CANTO_I) == [
            "thEn", "bronZe", "beaRing", "Arms",
            "sheeP", "Of", "plUto", "stroNg", "praiseD"]

    def test_the_committed_pair_spells_the_spine(self):
        marked = "".join(letter for _, line in cage.CANTO_I
                         for letter, _ in cage.presentations(line))
        assert marked == cage.SPINE

    def test_load_reference_falls_back_without_an_extract(self, monkeypatch):
        monkeypatch.setattr(cage, "REFERENCE_PATH", "/nonexistent/cantos.tsv")
        assert cage.load_reference() == cage.CANTO_I
