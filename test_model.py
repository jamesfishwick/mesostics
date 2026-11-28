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


def test_the_rule_reproduces_his_tail(rows):
    """A single rate predicts 0.03% here against his 2.6%. Two states do not."""
    import collections

    import analysis
    words = analysis.corpus_words(analysis.PP3_152)
    simulated = collections.Counter()
    for seed in range(60):
        simulated.update(model.walk_spine(words, seed=seed))
    total = sum(simulated.values())
    deep = sum(v for k, v in simulated.items() if k >= 12) / total
    his = collections.Counter(model.cage_ranks())
    his_deep = sum(v for k, v in his.items() if k >= 12) / sum(his.values())
    assert abs(deep - his_deep) < 0.015, f"{deep:.3f} vs {his_deep:.3f}"


def test_one_rate_cannot_do_it(rows):
    """Kept as the reason the model has two states and not one."""
    n = len(model.cage_ranks())
    single = sum(n * 0.43 * (1 - 0.43) ** (r - 1) for r in range(12, 300))
    assert single < 1, "a single rate puts almost nothing past rank 12"


def test_the_states_are_distinct():
    """If these converge the two-state story collapses into one rate.

    Half is the bar, not a round number: at that separation the choosing
    state still produces the rank 12-and-deeper band a single rate cannot.
    """
    assert model.CHOOSING < model.READING / 2


def test_the_residue_is_small_and_named():
    deep = model.deep_reaches()
    assert 10 <= len(deep) <= 25
    letters = {letter for letter, *_ in deep}
    assert letters <= set(model.SPINE)


def test_his_rate_is_what_the_model_uses():
    ranks = model.cage_ranks()
    first = collections.Counter(ranks)[1] / len(ranks)
    assert abs(first - 0.540) < 0.01


def test_a_lost_word_does_not_manufacture_a_deep_reach():
    """One missing word once produced an apparent reach of 175.

    "sEa-jauZionda" presents both E and Z and the scan lost it, so the cursor
    could not advance and R was then counted from hundreds of words too early.
    Ranks measured straight after a lost word are discarded.
    """
    assert max(model.cage_ranks()) < 100


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
        expected = len(ranks) * (1 - 0.529) ** 6
        assert deep > 4 * expected


def test_selectiveness_does_not_carry_over():
    """Two components are not two modes. A mode would persist; his does not."""
    for threshold in (2, 3, 4, 5, 7):
        _, _, z = model.independence(threshold)
        assert abs(z) < 2, f"rank>={threshold} clusters at z={z:+.2f}; it is a mode after all"


class TestWings:
    """The wings, measured the same way as the spine and on far less data."""

    def test_decorating_a_span_is_decided_per_span(self):
        """A mood would persist across neighbouring spans. This does not."""
        import random
        import statistics
        import trace as cage_trace
        rows, _ = cage_trace.walk(200)
        seq, current = [], []
        for _, _, _, verdict, _ in rows:
            if verdict in (cage_trace.PASSED, cage_trace.PRINTED, cage_trace.TIED):
                current.append(verdict != cage_trace.PASSED)
            elif verdict in (cage_trace.SPINE_MARK, cage_trace.MISSING):
                if current:
                    seq.append(1 if any(current) else 0)
                current = []
        count = lambda s: 1 + sum(1 for a, b in zip(s, s[1:]) if a != b)
        observed = count(seq)
        rng = random.Random(0)
        sampled = []
        for _ in range(4000):
            shuffled = seq[:]
            rng.shuffle(shuffled)
            sampled.append(count(shuffled))
        mean = statistics.mean(sampled)
        sd = statistics.pstdev(sampled)
        assert abs((observed - mean) / sd) < 2, "span decoration clusters after all"

    def test_he_decorates_about_one_span_in_six(self):
        spans, decorated, _, _ = model.wing_fit()
        assert (spans, decorated) == (287, 50)

    def test_printed_words_favour_the_end_of_their_span(self):
        """Not uniform: the last fifth is over-represented."""
        *_, end_heavy = model.wing_fit()
        assert end_heavy > 0.25, "the end-of-span preference has gone"

    def test_most_decorated_spans_get_one_or_two_words(self):
        *_, counts, _ = model.wing_fit()
        brief = sum(1 for c in counts if c <= 2)
        assert brief / len(counts) > 0.55
