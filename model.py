"""Cage's method as a procedure you can run.

Six steps reproduce what he did. Five are deterministic and were read off his
own text. The sixth, which word presents a letter when several could, is a
rate rather than a reason:

    1. Read the source once, forward. Never go back.
    2. Spell EZRAPOUND down the page, four letters then five.
    3. For each letter, walk forward through the words carrying it whose
       syllable has not already been spent on that letter, and take one.
       He does this in two states. Four times in five he is reading through
       and takes a candidate at READING. The fifth time he is choosing, and
       takes one at CHOOSING, walking past five or six on average.
    4. Record its syllable; never present that letter with it again.
    5. Between two spine words, print some subsequence of the words carrying
       neither letter.
    6. Recase so the mark is the only capital.

Step 3 is the finding. Eight word features were tested against the 678
candidates Cage declined and none separates them from the 319 he took, which
is what a process with no per-word reason looks like from outside.

A single rate will not do. Fitted at his own first-match frequency it is
destroyed by the tail: he reaches rank twelve or deeper eight times where one
rate predicts 0.1, chi-square 108.7 on 5 degrees of freedom. Two states fit,
chi-square 13.2 on 6, and predict that tail at 8.0 against his 8.

So the rule is that he works in two modes and the deep reaches are not
anomalies but the tail of the second. A rate explains a distribution and
never an instance: asking why he took one word rather than another is asking
which atom decays next, and asking why he was choosing rather than reading at
that moment is the same question one level up.
"""

import collections
import random

import analysis
import cage
from syllables import extract_syllable_with_letter

SPINE = "EZRAPOUND"

# Two states, fitted to his rank distribution. Reading through, he takes the
# first thing that works; choosing, he walks past five or six.
READING = 0.60
CHOOSING = 0.23
P_READING = 0.75


def walk_spine(words, letters=319, seed=None):
    """Run step 3 over a source text. Returns the rank of each word taken."""
    rng = random.Random(seed)
    index, cursor, ranks = {}, 0, []
    for n in range(letters):
        letter = SPINE[n % len(SPINE)]
        # Which state is he in for this letter?
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

    deep = deep_reaches()
    print(f"\nTHE RESIDUE: {len(deep)} places he reached rank 7 or beyond\n")
    for letter, word, rank, passed in deep:
        print(f"  {letter}  took {word!r} at rank {rank}, "
              f"past {', '.join(passed[:6])}{' ...' if len(passed) > 6 else ''}")


if __name__ == "__main__":
    report()
