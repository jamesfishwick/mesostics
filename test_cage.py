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


class TestAnalysis:
    """The measurements behind FINDINGS.md, pinned so the document stays true."""

    def test_cage_took_the_first_candidate_six_times_in_nine(self):
        import analysis
        ranks = [rank for _, _, rank, _, _ in analysis.candidate_ranks()]
        assert ranks == [1, 1, 1, 1, 3, 1, 2, 1, 2]

    def test_no_filter_combination_beats_taking_the_first_word(self):
        import analysis
        best = analysis.search()[0][0]
        assert best == analysis.score(()) == 4

    def test_pallor_is_the_only_invisible_mark_among_our_picks(self):
        import analysis
        words = analysis.corpus_words()
        ours = analysis.walk()
        invisible = [w for w, letter in zip(ours, analysis.SPINE)
                     if any(analysis.invisible_mark(src, letter)
                            for src in words if cage.bare(src) == w)]
        assert invisible == ["pallor"]

    def test_the_cascade_accounts_for_most_of_the_divergence(self):
        import analysis
        rows, agreed, deviations = analysis.oracle_walk()
        assert (len(rows), agreed, deviations) == (18, 11, 7)

    def test_cage_read_the_source_continuously(self):
        """His line 3 pulls "narrow" from page 4 and the rest from page 11."""
        import analysis
        words = [cage.bare(w) for w in analysis.corpus_words(analysis.PP3_11)]
        narrow, glazes = words.index("narrow"), words.index("glazes")
        assert narrow < 400, "narrow should sit in Canto I, on page 4"
        assert glazes > 1500, "glazes should sit on page 11"

    def test_the_prohibition_governs_printing_not_reading(self):
        """He walks past forbidden words in the source without printing them."""
        import itertools

        import analysis
        from syllables import extract_syllable_with_letter as syl
        words = analysis.corpus_words(analysis.PP3_11)
        index, cursor, picks = {}, 0, []
        for letter, wanted in zip(itertools.cycle(analysis.SPINE), analysis.CAGE_PP3_11):
            pos = next((i for i in range(cursor, len(words))
                        if letter in words[i].upper()
                        and cage.bare(words[i]) == wanted
                        and syl(words[i], letter) not in index.get(letter, [])), None)
            if pos is None:
                break
            picks.append((letter, pos))
            index.setdefault(letter, []).append(syl(words[pos], letter))
            cursor = pos + 1

        dirty = sum(
            any(set(w.upper()) & {l1, l2} for w in words[p1 + 1:p2])
            for (l1, p1), (l2, p2) in zip(picks, picks[1:])
        )
        assert (len(picks), dirty) == (18, 9)

    def test_every_letter_filter_is_disqualified_by_cages_own_words(self):
        import analysis
        for name in analysis.FILTERS:
            counts, _ = analysis.disqualify(name)
            if counts is None:
                continue  # needs source capitalisation, which his text lost
            rejected, total = counts
            assert rejected > 0, f"{name} now survives {total} choices: re-examine it"
