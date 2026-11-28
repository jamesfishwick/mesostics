"""Cage's method as a procedure you can run.

Six steps reproduce what he did. Five are deterministic and were read off his
own text. The sixth, which word presents a letter when several could, is a
rate rather than a reason:

    1. Read the source once, forward. Never go back.
    2. Spell EZRAPOUND down the page, four letters then five.
    3. For each letter, walk forward through the words carrying it whose
       syllable has not already been spent on that letter. Take each with
       probability ACCEPT. Otherwise keep walking.
    4. Record its syllable; never present that letter with it again.
    5. Between two spine words, print some subsequence of the words carrying
       neither letter.
    6. Recase so the mark is the only capital.

Step 3 is the finding. Eight word features were tested against the 678
candidates Cage declined and none separates them from the 319 he took, which
is what a memoryless process looks like from outside. ACCEPT is his own
first-match rate, and the model reproduces his rank distribution through rank
six. It does not reproduce his tail: he reaches rank seven or beyond at 5.8%
where the rate predicts 1.1%, and those occasions are the only part of his
selection still unaccounted for. Some of that gap is an artifact of counting
every occurrence of a repeated word as a fresh candidate, since he walks past
"bezants" three times running; counting distinct syllables instead brings it
to 4.5%, which is closer and still not the rate.

A rate explains a distribution and never an instance. Asking why he took one
word rather than another is asking which atom decays next.
"""

import collections
import random

import analysis
import cage
from syllables import extract_syllable_with_letter

SPINE = "EZRAPOUND"
ACCEPT = 0.529  # his own rate of taking the first admissible word


def walk_spine(words, accept=ACCEPT, letters=319, seed=None):
    """Run step 3 over a source text. Returns the rank of each word taken."""
    rng = random.Random(seed)
    index, cursor, ranks = {}, 0, []
    for n in range(letters):
        letter = SPINE[n % len(SPINE)]
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
        if his in available:
            ranks.append(available.index(his) + 1)
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
    print(f"\n    ACCEPT = {ACCEPT}\n")
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
