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
