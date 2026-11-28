"""The rule, held to Cage's own numbers."""

import collections

import pytest

import model


@pytest.fixture(scope="module")
def rows():
    return model.compare()


def test_the_rule_matches_his_first_match_rate(rows):
    simulated, his = rows[1]
    assert abs(simulated - his) < 3, "rank 1 is the parameter; it must match"


@pytest.mark.parametrize("rank", [2, 3, 4, 5])
def test_the_rule_matches_the_near_ranks(rows, rank):
    simulated, his = rows[rank]
    assert abs(simulated - his) < 6, f"rank {rank}: {simulated:.1f} vs {his:.1f}"


def test_the_rule_undershoots_his_tail(rows):
    """The one place it fails, and the only part of selection unaccounted for."""
    simulated, his = rows[7]
    assert his > simulated, "if this ever reverses, the residue is gone"


def test_the_residue_is_small_and_named():
    deep = model.deep_reaches()
    assert 10 <= len(deep) <= 25
    letters = {letter for letter, *_ in deep}
    assert letters <= set(model.SPINE)


def test_his_rate_is_what_the_model_uses():
    ranks = model.cage_ranks()
    first = collections.Counter(ranks)[1] / len(ranks)
    assert abs(first - model.ACCEPT) < 0.01


class TestResidueHypotheses:
    """Three explanations for the deep reaches, each tested and dead.

    Recorded so they are not tried again. If one of these ever starts to
    hold, the residue has an explanation and FINDINGS.md is out of date.
    """

    def test_deep_reaches_are_genuinely_long_walks(self):
        """Not an artifact of candidates bunching together."""
        import statistics

        import analysis
        import cage
        from syllables import extract_syllable_with_letter as pick
        words = analysis.corpus_words(analysis.PP3_152)
        index, cursor, deep, shallow = {}, 0, [], []
        for letter, wanted in analysis.cage_choices():
            his = next((i for i in range(cursor, len(words))
                        if cage.bare(words[i]) == wanted
                        and letter in words[i].upper()), None)
            if his is None:
                continue
            available = [i for i in range(cursor, his + 1)
                         if letter in words[i].upper()
                         and pick(words[i], letter) not in index.get(letter, [])]
            if his in available:
                distance = his - cursor + 1
                (deep if available.index(his) + 1 >= 7 else shallow).append(distance)
            index.setdefault(letter, []).append(pick(words[his], letter))
            cursor = his + 1
        assert statistics.median(deep) > 10 * statistics.median(shallow)

    def test_the_excess_is_not_noise(self):
        """18 observed against about 3.4 expected is far outside chance."""
        ranks = model.cage_ranks()
        deep = sum(1 for r in ranks if r >= 7)
        expected = len(ranks) * (1 - model.ACCEPT) ** 6
        assert deep > 4 * expected
