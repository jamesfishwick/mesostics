"""Cage's method as a procedure you can run.

Six steps reproduce what he did. Five are deterministic and were read off his
own text. The sixth, which word presents a letter when several could, is a
rate rather than a reason:

    1. Read the source once, forward. Never go back.
    2. Spell EZRAPOUND down the page, four letters then five.
    3. For each letter, walk forward through the words carrying it whose
       syllable has not already been spent on that letter, and take one.
       How selective he is varies, and it is drawn afresh at every letter:
       three times in four he takes a candidate at READING, otherwise at
       CHOOSING, walking past five or six. The draw does not persist. It is
       not a mood he settles into for a stretch; each letter gets its own.
    4. Record its syllable; never present that letter with it again.
    5. Between two spine words, decide whether to print anything at all,
       which happens for about one span in six and is decided afresh each
       time. If so, draw how many words to print the same way selectiveness
       is drawn, mostly one and occasionally many. Favour the words nearest
       the spine words, most of all those just before the next one.
    6. Recase so the mark is the only capital.

Step 3 is the finding. Eight word features were tested against the 678
candidates Cage declined and none separates them from the 319 he took, which
is what a process with no per-word reason looks like from outside.

A single rate will not do. Fitted to his rank distribution it is destroyed by
the tail, chi-square 26.1 on 6 degrees of freedom, p=0.0002. Two components
fit at 6.6 on 5.

Two components are not two modes. A mode would persist, and his do not: a
runs test on the sequence of choices puts the observed alternation within one
standard deviation of independence at every threshold tried, z between -0.34
and +1.15. Whatever sets his selectiveness is consulted once per letter and
forgotten.

That is the signature of a chance operation rather than a temperament, and
chance operations were Cage's practice for thirty years before this piece.
This measures the shape of the draw; it does not show which procedure he
used, and nothing here could.

A rate explains a distribution and never an instance. Asking why he took one
word rather than another is asking which atom decays next.
"""

import collections
import random

import analysis
import cage
from syllables import extract_syllable_with_letter

SPINE = "EZRAPOUND"

# How selective he is, drawn afresh at each letter rather than held for a
# stretch. Reading through, he takes the first thing that works; choosing, he
# walks past five or six.
READING = 0.60
CHOOSING = 0.23
P_READING = 0.75

# The wings, fitted the same way and on far less data: 50 decorated spans.
# Whether a span is decorated at all is drawn per span, and a runs test puts
# that within noise of independence at z=-1.15. How many words go in is a
# two-component draw like the spine's, one rate fitting at chi-square 12.5 on
# 3 degrees of freedom against 1.5 on 1. Where they sit is not uniform: the
# last fifth of a span holds 62 of 217 against 43 expected, chi-square 13.2 on
# 4, p=0.011.
P_DECORATE = 0.17
WING_BRIEF = 0.85
WING_LONG = 0.07
P_WING_BRIEF = 0.55


def walk_spine(words, letters=319, seed=None):
    """Run step 3 over a source text. Returns the rank of each word taken."""
    rng = random.Random(seed)
    index, cursor, ranks = {}, 0, []
    for n in range(letters):
        letter = SPINE[n % len(SPINE)]
        # Drawn per letter. The runs test says it does not carry over.
        accept = READING if rng.random() < P_READING else CHOOSING
        rank = 0
        for i in range(cursor, len(words)):
            if letter not in words[i].upper():
                continue
            syllable = extract_syllable_with_letter(words[i], letter)
            if syllable in index.get(letter, []):
                continue
            rank += 1
            if rng.random() < accept:
                index.setdefault(letter, []).append(syllable)
                ranks.append(rank)
                cursor = i + 1
                break
        else:
            break
    return ranks


def cage_ranks(words=None):
    """Where Cage's own choice sat among the words available to him."""
    words = analysis.corpus_words(analysis.PP3_152) if words is None else words
    index, cursor, ranks = {}, 0, []
    poisoned = False
    for letter, wanted in analysis.cage_choices():
        his = next((i for i in range(cursor, len(words))
                    if cage.bare(words[i]) == wanted
                    and letter in words[i].upper()), None)
        if his is None:
            # The scan lost this word. The cursor stays put, so the next rank
            # would be counted from hundreds of words too early: one lost word
            # once produced an apparent reach of 175. Discard the next one.
            poisoned = True
            continue
        available = [
            i for i in range(cursor, his + 1)
            if letter in words[i].upper()
            and extract_syllable_with_letter(words[i], letter) not in index.get(letter, [])
        ]
        if his in available and not poisoned:
            ranks.append(available.index(his) + 1)
        poisoned = False
        index.setdefault(letter, []).append(
            extract_syllable_with_letter(words[his], letter))
        cursor = his + 1
    return ranks


def compare(runs=40):
    """The model's rank distribution against Cage's, as percentages."""
    words = analysis.corpus_words(analysis.PP3_152)
    simulated = collections.Counter()
    for seed in range(runs):
        simulated.update(walk_spine(words, seed=seed))
    observed = collections.Counter(cage_ranks(words))
    total, his = sum(simulated.values()), sum(observed.values())
    return {rank: (100 * simulated[rank] / total, 100 * observed[rank] / his)
            for rank in range(1, 8)}


def deep_reaches(threshold=7, words=None):
    """The places Cage walked past far more candidates than the rate predicts.

    These are the residue. Everything else about his selection is the rate.
    """
    words = analysis.corpus_words(analysis.PP3_152) if words is None else words
    index, cursor, out = {}, 0, []
    for letter, wanted in analysis.cage_choices():
        his = next((i for i in range(cursor, len(words))
                    if cage.bare(words[i]) == wanted
                    and letter in words[i].upper()), None)
        if his is None:
            continue
        available = [
            i for i in range(cursor, his + 1)
            if letter in words[i].upper()
            and extract_syllable_with_letter(words[i], letter) not in index.get(letter, [])
        ]
        if his in available and available.index(his) + 1 >= threshold:
            out.append((letter, words[his], available.index(his) + 1,
                        [cage.bare(words[i]) for i in available[:available.index(his)]]))
        index.setdefault(letter, []).append(
            extract_syllable_with_letter(words[his], letter))
        cursor = his + 1
    return out


def wing_fit():
    """What the wings look like, measured the same way as the spine.

    Returns (spans, decorated, counts, end_heavy) where counts is the number
    of words printed in each decorated span and end_heavy is the share of
    printed words falling in the last fifth of their span against 0.20 if
    they were placed uniformly.
    """
    import trace as cage_trace

    rows, _ = cage_trace.walk(200)
    spans, current = [], []
    for _, _, _, verdict, _ in rows:
        if verdict in (cage_trace.PASSED, cage_trace.PRINTED, cage_trace.TIED):
            current.append(verdict != cage_trace.PASSED)
        elif verdict in (cage_trace.SPINE_MARK, cage_trace.MISSING):
            if current:
                spans.append(current)
            current = []
    counts = [sum(s) for s in spans if any(s)]
    places = [i / (len(s) - 1) for s in spans if len(s) > 1
              for i, printed in enumerate(s) if printed]
    end_heavy = sum(1 for x in places if x >= 0.8) / len(places) if places else 0
    return len(spans), len(counts), counts, end_heavy


def independence(threshold=3, trials=8000, seed=0):
    """Does his selectiveness carry over from one letter to the next?

    A mode persists and shows fewer alternations than chance. A draw made
    afresh each time shows the chance number. Returns (observed runs,
    expected, z).
    """
    rng = random.Random(seed)
    flags = [1 if r >= threshold else 0 for r in cage_ranks()]
    count = lambda s: 1 + sum(1 for a, b in zip(s, s[1:]) if a != b)
    observed = count(flags)
    sampled = []
    for _ in range(trials):
        shuffled = flags[:]
        rng.shuffle(shuffled)
        sampled.append(count(shuffled))
    mean = sum(sampled) / len(sampled)
    sd = (sum((x - mean) ** 2 for x in sampled) / len(sampled)) ** 0.5
    return observed, mean, (observed - mean) / sd if sd else 0.0


def report():
    print("CAGE'S METHOD AS A RULE\n")
    print(__doc__.split("    1.")[1].split("Step 3 is the finding")[0].rstrip())
    print(f"\n    reading through {100 * P_READING:.0f}% of the time, "
          f"taking at {READING}")
    print(f"    choosing        {100 * (1 - P_READING):.0f}% of the time, "
          f"taking at {CHOOSING}\n")
    print("Running step 3 forty times against the same corpus:\n")
    print(f"  {'rank':<8}{'the rule':<14}{'Cage':<14}")
    rows = compare()
    for rank, (model, his) in rows.items():
        print(f"  {rank:<8}{model:<14.1f}{his:<14.1f}")

    print("\nDOES HIS SELECTIVENESS CARRY OVER BETWEEN LETTERS?\n")
    for threshold in (2, 3, 4, 5, 7):
        observed, expected, z = independence(threshold)
        print(f"  rank >= {threshold}   runs {observed:3d}   "
              f"if independent {expected:5.1f}   z={z:+.2f}")
    print("  -> within noise at every threshold: drawn afresh each letter,"
          "\n     which is a chance operation rather than a temperament")

    spans, decorated, counts, end_heavy = wing_fit()
    print("\nTHE WINGS\n")
    print(f"  spans                     {spans}, decorated {decorated} "
          f"({100 * decorated / spans:.0f}%)")
    print(f"  words per decorated span  median "
          f"{sorted(counts)[len(counts)//2]}, mean {sum(counts)/len(counts):.1f}, "
          f"max {max(counts)}")
    print(f"  in the last fifth of its span  {100 * end_heavy:.0f}% "
          f"against 20% if placed uniformly")

    deep = deep_reaches()
    print(f"\nTHE RESIDUE: {len(deep)} places he reached rank 7 or beyond\n")
    for letter, word, rank, passed in deep:
        print(f"  {letter}  took {word!r} at rank {rank}, "
              f"past {', '.join(passed[:6])}{' ...' if len(passed) > 6 else ''}")


if __name__ == "__main__":
    report()
