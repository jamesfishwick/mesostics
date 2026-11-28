"""Every number the documentation asserts, checked against live measurement.

A figure in a README is a claim, and claims rot. This file recomputes each one
and asserts the text still says it, so changing the code without changing the
prose fails here rather than in somebody's reading.

Written after two stale figures reached main: a markdown formatter re-pads
tables on commit, so an edit matching the unformatted text silently did
nothing and the old number survived. A test does not care how the table is
padded.
"""

import re
import warnings
from pathlib import Path

import pytest

HERE = Path(__file__).parent
DOCS = {name: (HERE / name).read_text(encoding="utf-8")
        for name in ("README.md", "FINDINGS.md")}


def claimed(figure, where):
    """True when `figure` appears in that document."""
    return figure in re.sub(r"[ \t]+", " ", DOCS[where])


def assert_claimed(figure, what, *where):
    """Assert the figure appears in EVERY document named.

    Naming them individually matters. An earlier version accepted the figure
    in any document, which passes while one file is stale and another is
    right, and a stale file is exactly the failure this guards against.
    """
    assert where, "name the documents that carry this figure"
    stale = [name for name in where if not claimed(figure, name)]
    assert not stale, (
        f"{', '.join(stale)} no longer says {figure!r} for {what}; "
        f"recompute and update the prose"
    )


class TestSyllableFigures:
    def test_count_accuracy(self):
        import re as _re

        import cmudict

        import syllables as S
        ok = total = 0
        for word in cmudict.dict():
            if not _re.fullmatch(r"[a-z']+", word):
                continue
            n = S.cmu_syllable_count(word)
            if n is None:
                continue
            total += 1
            ok += len(S.syllabify(word)) == max(1, n)
        assert_claimed(f"{100 * ok / total:.1f}%", "count agreement with CMU",
                       "README.md", "FINDINGS.md")
        assert_claimed(f"{total:,}", "scoreable CMU entries", "README.md", "FINDINGS.md")

    def test_pyphen_alone_is_the_stated_baseline(self):
        import re as _re

        import cmudict

        import syllables as S
        ok = total = 0
        for word in cmudict.dict():
            if not _re.fullmatch(r"[a-z']+", word):
                continue
            n = S.cmu_syllable_count(word)
            if n is None:
                continue
            total += 1
            ok += len(S._pyphen_split(word)) == max(1, n)
        assert_claimed(f"{100 * ok / total:.1f}%", "pyphen's count agreement",
                       "README.md")


class TestCageFigures:
    def test_wing_audit(self):
        import analysis
        ok, bad, _ = analysis.audit_wings()
        assert_claimed(f"{ok} of {ok + bad}", "wing words obeying his rule", "FINDINGS.md")
        assert bad == 3, "three slips; if this moves, re-read the lines"

    def test_presentation_count(self):
        import cage
        total = sum(len(cage.presentations(line)) for _, line in cage.load_reference())
        assert_claimed(f"{total}", "his spine presentations", "FINDINGS.md")

    def test_line_count(self):
        import cage
        assert_claimed(f"{len(cage.load_reference())}", "his mesostic lines", "FINDINGS.md")

    def test_agreement(self):
        import analysis
        compared, agreed, _ = analysis.agreement()
        assert_claimed(f"**{compared}**", "choices compared", "FINDINGS.md")
        assert_claimed(f"**{agreed} ({100 * agreed / compared:.0f}%)**", "where we match him",
                       "FINDINGS.md")

    def test_oracle_walk(self):
        import analysis
        rows, agreed, deviations = analysis.oracle_walk()
        assert_claimed(f"**{agreed} of {len(rows)}**", "first-try agreement", "FINDINGS.md")
        assert_claimed(f"**{deviations}**", "independent deviations", "FINDINGS.md")


class TestOutputFigures:
    @pytest.mark.parametrize("rule", ["100%", "50%", "0%"])
    def test_strictness_character_counts(self, rule):
        import mesostics
        before = mesostics.MESOSTIC_RULE, mesostics.WING_MODE
        try:
            mesostics.MESOSTIC_RULE = rule
            # The strictness table is about what the prohibition admits, so it
            # is measured with the draw off.
            mesostics.WING_MODE = "SHOW_ALL"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                size = sum(len(line) for line in mesostics.generate_mesostic())
        finally:
            mesostics.MESOSTIC_RULE, mesostics.WING_MODE = before
        assert_claimed(f"{size} characters", f"output size at {rule}", "README.md")

    def test_the_sample_output_is_the_real_output(self):
        """The README prints the poem. It has to be the poem the code makes."""
        import mesostics
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            lines = mesostics.generate_mesostic()
        for line in lines:
            assert line in DOCS["README.md"], f"README no longer shows: {line[:60]}"
