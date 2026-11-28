"""Pin the agreement with Cage's published text.

The EZRA line is the one thing this implementation gets exactly right, so it
is worth a regression guard. The POUND line is the open problem.
"""

import collections

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
        for name in ("TEXT_LAYER_PATH", "OCR_PATH", "REFERENCE_PATH"):
            monkeypatch.setattr(cage, name, "/nonexistent/cantos.tsv")
        assert cage.load_reference() == cage.CANTO_I
        assert cage.load_structure() == cage.CANTO_I


class TestAnalysis:
    """The measurements behind FINDINGS.md, pinned so the document stays true."""

    def test_cage_took_the_first_candidate_six_times_in_nine(self):
        import analysis
        ranks = [rank for _, _, rank, _, _ in analysis.candidate_ranks()]
        assert ranks == [1, 1, 1, 1, 3, 1, 2, 1, 2]

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

    def test_he_takes_the_first_admissible_word_just_over_half_the_time(self):
        import analysis
        compared, agreed, unalignable = analysis.agreement()
        assert (compared, agreed, unalignable) == (315, 168, 4)

    @pytest.mark.parametrize("lines", [2, 4, 16, 30])
    def test_the_trace_accounts_for_every_word(self, lines):
        """Every source word Cage covered gets exactly one verdict."""
        import trace as cage_trace
        rows, _ = cage_trace.walk(lines)
        positions = [p for _, p, _, verdict, _ in rows if verdict != "MISSING"]
        assert positions == sorted(positions), "the walk must run forward"
        assert len(positions) == len(set(positions)), "no word classified twice"
        assert positions == list(range(positions[0], positions[-1] + 1)), "no gaps"
        verdicts = {v for *_, v, _ in rows}
        assert verdicts <= {"SPINE", "BLOCKED", "PASSED", "PRINTED",
                            "TIED", "MISSING", "DECLINED", "SPENT"}

    def test_almost_every_word_is_placed(self):
        """A word he printed can usually be placed, because wings keep source order."""
        import trace as cage_trace
        rows, _ = cage_trace.walk(30)
        tied = sum(1 for *_, v, _ in rows if v == "TIED")
        assert (len(rows), tied) == (11287, 79)
        assert 100 * (len(rows) - tied) / len(rows) > 99

    def test_a_tie_is_provenance_not_an_open_decision(self):
        """Every tied word is one he printed, and the counts either side are known."""
        import re
        import trace as cage_trace
        rows, wings = cage_trace.walk(4)
        printed = {w for wing in wings for w in wing}
        ties = [r for r in rows if r[3] == "TIED"]
        assert ties
        for _, _, word, _, note in ties:
            assert cage.bare(word) in printed, "a tie must be a word he printed"
            mine, same, passed = map(int, re.findall(r"\d+", note))
            assert mine + passed == same, "the counts either side must add up"

    def test_an_unfindable_word_is_reported_not_dropped(self):
        """Silently skipping a row would make the totals a lie."""
        import trace as cage_trace
        rows, _ = cage_trace.walk(30)
        missing = [r for r in rows if r[3] == "MISSING"]
        assert missing, "the eight OCR variants must show up somewhere"
        assert all(r[1] == -1 for r in missing)

    @pytest.mark.parametrize("lines", [2, 4, 30])
    def test_the_trace_renders_as_a_table(self, lines):
        """Ragged rows break a markdown table silently; so does exceeding 512 KB."""
        import trace as cage_trace
        rows, wings = cage_trace.walk(lines)
        text = cage_trace.as_markdown(rows, wings)

        tables, run = [], []
        for line in text.split("\n"):
            if line.startswith("|"):
                run.append(line)
            elif run:
                tables.append(run)
                run = []
        if run:
            tables.append(run)
        assert tables
        for table in tables:
            assert len({r.count("|") for r in table}) == 1, "ragged table"
        assert len(text.encode()) < 512 * 1024, "GitHub truncates beyond 512 KB"

    def test_collapsing_runs_loses_no_word(self):
        import trace as cage_trace
        rows, _ = cage_trace.walk(4)
        collapsed = sum(len(group) for _, _, group, _, _ in cage_trace.runs(rows))
        assert collapsed == len(rows)

    def test_declined_candidates_are_shown(self):
        """The words he could have used and did not are the whole question."""
        import trace as cage_trace
        rows, _ = cage_trace.walk(2)
        declined = [(w, note) for _, _, w, v, note in rows if v == "DECLINED"]
        assert ("Pallor", "could have presented P as 'pal'") in declined
        assert ("upon", "could have presented P as 'pon'") in declined

    def test_no_declined_word_was_printed_in_its_own_span(self):
        """It carries the letter in play, so printing it would break his rule.

        Per span, not globally: he prints "and" in many wings, and that says
        nothing about the "and" he declined forty spans later.
        """
        import trace as cage_trace
        rows, wings = cage_trace.walk(30)
        span, leaks, declined = 0, [], 0
        for _, _, word, verdict, _ in rows:
            if verdict in ("SPINE", "MISSING"):
                span += 1
            elif verdict == "DECLINED":
                declined += 1
                wing = wings[span] if span < len(wings) else []
                if cage.bare(word) in wing:
                    leaks.append(word)
        assert declined > 300, "the check must actually examine something"
        assert leaks == []

    def test_spent_is_his_rule_and_declined_is_his_choice(self):
        import trace as cage_trace
        rows, _ = cage_trace.walk(30)
        counts = collections.Counter(v for *_, v, _ in rows)
        assert (counts["DECLINED"], counts["SPENT"]) == (379, 26)

    def test_he_leans_away_from_source_capitals(self):
        import analysis
        higher, lower, _, p = analysis.within_span_preference(
            analysis.source_capitalised)
        assert (higher, lower) == (24, 56)
        assert p < 0.017, "below the Bonferroni threshold for three tests"

    def test_the_lean_is_a_bias_not_a_rule(self):
        """He takes capitalised words often enough that no rule can forbid them."""
        import analysis
        taken = analysis.cage_spine_words()
        caps = sum(analysis.source_capitalised(w) for w in taken)
        assert (caps, len(taken)) == (84, 323)

    def test_pooling_across_spans_would_mislead(self):
        """Four declined per taken, so a pooled count is dominated by the bigger group."""
        import trace as cage_trace
        rows, _ = cage_trace.walk(200)
        declined = sum(1 for *_, v, _ in rows if v == "DECLINED")
        taken = sum(1 for *_, v, _ in rows if v == "SPINE")
        assert declined > 2 * taken

    def test_walking_past_a_word_does_not_burn_it(self):
        """README rule 4 once claimed the opposite. Cage refutes it ten times."""
        import trace as cage_trace
        rows, _ = cage_trace.walk(200)
        seen, reused = {}, []
        for letter, _, word, verdict, _ in rows:
            if verdict == "DECLINED":
                seen.setdefault(letter, set()).add(cage.bare(word))
            elif verdict == "SPINE" and cage.bare(word) in seen.get(letter, ()):
                reused.append((letter, cage.bare(word)))
        assert len(reused) == 10
        assert ("R", "from") in reused

    def test_the_45_character_wing_limit_never_binds(self):
        """Secondary sources give it as a rule. His text never approaches it."""
        import analysis
        lengths = analysis.wing_lengths()
        assert len(lengths) == 471
        assert max(lengths) == 28, "if this ever passes 45 the limit may be real"
        assert sorted(lengths)[len(lengths) // 2] == 4

    def test_rule_four_has_exactly_one_exception(self):
        """Read at 400 dpi, 998 presentations hold one repeat: Pit for P, twice.

        The text layer missed it by losing 24 lines. One slip in 998 sits
        alongside the three in his wing prohibition.
        """
        import collections
        pairs = [(letter, cage.bare(word))
                 for _, line in cage.load_structure()
                 for letter, word in cage.presentations(line)]
        repeats = {k: v for k, v in collections.Counter(pairs).items() if v > 1}
        assert repeats == {("P", "pit"): 2}

    def test_a_word_may_present_different_letters(self):
        """Rule 4 is per letter, so the same word elsewhere is allowed."""
        import collections
        words = [cage.bare(w) for _, line in cage.load_reference()
                 for _, w in cage.presentations(line)]
        reused = {k: v for k, v in collections.Counter(words).items() if v > 1}
        assert len(reused) > 30, "he reuses words across letters freely"
