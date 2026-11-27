"""Measurements for working out what Cage was actually doing.

Everything here reads Cage's published text, our corpus, or both. The point is
to let a hypothesis be tested in one run rather than argued about: state it as
a filter, score it, see whether it beats taking the first available word.

`cage.extract_from_pdf()` has to have been run first for the audits that need
all 198 of his lines. The Canto I measurements work without it.
"""

import itertools
import re

import cage
from syllables import extract_syllable_with_letter

SPINE = "EZRAPOUND"
SEGMENT = {letter: ("EZRA" if letter in "EZRA" else "POUND") for letter in SPINE}

# Cage's choices for the one pair of lines our corpus can produce.
CAGE_CANTO_I = ["then", "bronze", "bearing", "arms",
                "sheep", "of", "pluto", "strong", "praised"]


def corpus_words():
    with open(cage.os.path.join(cage.os.path.dirname(cage.os.path.abspath(__file__)),
                                "corpus", "canto_i.txt"), encoding="utf-8") as text:
        return text.read().split()


# --- candidate filters, each True when the word should be rejected -----------

def invisible_mark(word, letter):
    """The word's own initial capital IS the spine letter, so marking shows nothing."""
    only = re.sub(r"[^A-Za-z]", "", word)
    return bool(only) and only[0].isupper() and only[0].upper() == letter


def segment_future(word, letter):
    """Carries a letter still to come in this line's half of the name."""
    seg = SEGMENT[letter]
    return bool(set(word.upper()) & set(seg[seg.index(letter) + 1:]))


def name_future(word, letter):
    """Carries a letter still to come anywhere in the name."""
    return bool(set(word.upper()) & set(SPINE[SPINE.index(letter) + 1:]))


def next_spine_letter(word, letter):
    """Carries the very next letter of the name."""
    i = SPINE.index(letter)
    return i + 1 < len(SPINE) and SPINE[i + 1] in word.upper()


FILTERS = {
    "invisible-mark": invisible_mark,
    "segment-future": segment_future,
    "name-future": name_future,
    "next-letter": next_spine_letter,
}


# --- audits over Cage's own text ---------------------------------------------

def audit_wings(rows=None):
    """Test Cage's stated rule against his own wings.

    "I did not permit the appearance of either letter between two of the name."
    Returns (obeying, violating, examples).
    """
    rows = cage.load_reference() if rows is None else rows
    ok, violations = 0, []
    for _, line in rows:
        words = line.split()
        marks = [(i, c) for i, w in enumerate(words) for c in w if c.isupper()]
        for (i1, first), (i2, second) in zip(marks, marks[1:]):
            for word in words[i1 + 1:i2]:
                carried = set(word.upper()) & {first, second}
                if carried:
                    violations.append((line, word, "".join(sorted(carried))))
                else:
                    ok += 1
    return ok, len(violations), violations


# invisible-mark asks whether the source already capitalised the spine letter.
# Cage recased everything he printed, so his output cannot answer it and the
# audit below leaves it out rather than report a meaningless number.
SOURCE_ONLY_FILTERS = {"invisible-mark"}


def audit_spine_letters(rows=None):
    """How often each candidate filter would have rejected Cage's own choices.

    A filter that is really a rule should never reject one.
    """
    rows = cage.load_reference() if rows is None else rows
    testable = {n: f for n, f in FILTERS.items() if n not in SOURCE_ONLY_FILTERS}
    kept = dict.fromkeys(testable, 0)
    total = 0
    for _, line in rows:
        words = line.split()
        marks = [(i, c) for i, w in enumerate(words) for c in w if c.isupper()]
        for idx, letter in marks:
            total += 1
            for name, test in testable.items():
                kept[name] += not test(words[idx], letter)
    return total, kept


# --- measurements against Canto I --------------------------------------------

def walk(active=(), words=None):
    """Take the first admissible word for each spine letter, in order.

    `active` names filters to apply. Returns the chosen words, bare.
    """
    words = corpus_words() if words is None else words
    index, cursor, picked = {}, 0, []
    for letter in SPINE:
        for i in range(cursor, len(words)):
            word = words[i]
            if letter not in word.upper():
                continue
            if any(FILTERS[name](word, letter) for name in active):
                continue
            syllable = extract_syllable_with_letter(word, letter)
            if syllable in index.get(letter, []):
                continue
            index.setdefault(letter, []).append(syllable)
            picked.append(cage.bare(word))
            cursor = i + 1
            break
        else:
            picked.append("--")
    return picked


def score(active=()):
    """How many of Cage's nine choices this filter set reproduces."""
    return sum(1 for ours, theirs in zip(walk(active), CAGE_CANTO_I) if ours == theirs)


def search():
    """Score every combination of filters, best first."""
    out = []
    for n in range(len(FILTERS) + 1):
        for combo in itertools.combinations(FILTERS, n):
            out.append((score(combo), combo, walk(combo)))
    return sorted(out, key=lambda row: -row[0])


def candidate_ranks(words=None):
    """For each letter, where Cage's choice sat among the admissible words.

    Rank 1 means he took the first one available, which is what this
    implementation always does.
    """
    words = corpus_words() if words is None else words
    index, cursor, out = {}, 0, []
    for letter, chosen in zip(SPINE, CAGE_CANTO_I):
        candidates = [
            (i, cage.bare(words[i])) for i in range(cursor, len(words))
            if letter in words[i].upper()
            and extract_syllable_with_letter(words[i], letter) not in index.get(letter, [])
        ]
        rank = next((n for n, (_, w) in enumerate(candidates, 1) if w == chosen), None)
        passed = [w for _, w in candidates[:(rank or 1) - 1]]
        out.append((letter, chosen, rank, len(candidates), passed))
        position = next(i for i, w in candidates if w == chosen)
        index.setdefault(letter, []).append(
            extract_syllable_with_letter(words[position], letter))
        cursor = position + 1
    return out


def report():
    print("CAGE'S STATED RULE, against his own wings")
    try:
        ok, bad, examples = audit_wings()
        print(f"  {ok}/{ok + bad} wing words obey it ({100 * ok / (ok + bad):.1f}%)")
        for line, word, carried in examples:
            print(f"    {word!r} carries {carried}  --  {line}")
    except FileNotFoundError:
        print("  needs cage.extract_from_pdf() first")

    print("\nCANDIDATE FILTERS, against Cage's own spine words")
    print("  (invisible-mark needs source capitalisation, which his text lost)")
    try:
        total, kept = audit_spine_letters()
        for name, n in sorted(kept.items(), key=lambda kv: -kv[1]):
            print(f"  {name:<16} {n:4d}/{total}  {100 * n / total:5.1f}% survive")
    except FileNotFoundError:
        print("  needs cage.extract_from_pdf() first")

    print("\nHOW MUCH CHOICE CAGE HAD, in Canto I")
    for letter, chosen, rank, total, passed in candidate_ranks():
        note = "first available" if rank == 1 else "passed over " + ", ".join(passed)
        print(f"  {letter}  {chosen:<9} rank {rank} of {total:<4} {note}")

    print("\nFILTER COMBINATIONS, scored against Cage")
    for value, combo, picked in search()[:5]:
        print(f"  {value}/9  {' + '.join(combo) or '(none)':<32} {' '.join(picked)}")


if __name__ == "__main__":
    report()
