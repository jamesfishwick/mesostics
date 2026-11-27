"""A word-by-word account of Cage's walk through the source.

Everything the rule says can be checked against the text, word by word. For
each word between one of his spine words and the next, exactly one of these
happened:

  SPINE     he marked it, and it presents a letter of the name
  BLOCKED   it carries one of the two letters in play, so the rule forbade
            printing it, and he read straight past
  ALLOWED   the rule permitted it as a wing word

A tenth kind of row, MISSING, is printed where one of his spine words cannot
be found in the scan at all. Eight of his choices are in that state, mostly
OCR variants of hyphenated words. They are reported rather than skipped,
because a trace that quietly drops a row is not an account of anything.

Each span then says how many of its ALLOWED words he actually printed. That
count is reliable; which ones is not, because a word like "and" occurs too
often in a span to be aligned to a position with any confidence.

ALLOWED is the only column the rule does not settle. It is where his taste
lives, and it is the column to read to see what is still unknown.

    uv run python trace.py            # the first four lines
    uv run python trace.py 12         # the first twelve
"""

import sys

import cage
from analysis import PP3_152, SPINE, cage_choices, corpus_words
from syllables import extract_syllable_with_letter

SPINE_MARK, BLOCKED, ALLOWED, MISSING = "SPINE", "BLOCKED", "ALLOWED", "MISSING"


def walk(limit_lines=4):
    """Classify every source word Cage covered, in order.

    Returns a list of (segment, letter, position, word, verdict, note).
    """
    words = corpus_words(PP3_152)
    choices = cage_choices()
    # How many words he printed between each pair of spine words. Counting is
    # sound even where aligning the individual words is not.
    wing_counts = []
    for _, line in cage.load_reference()[:limit_lines]:
        tokens = line.split()
        marks = [i for i, w in enumerate(tokens) if any(c.isupper() for c in w)]
        wing_counts.append(len(tokens[:marks[0]]) if marks else 0)
        wing_counts.extend(b - a - 1 for a, b in zip(marks, marks[1:]))

    out, index, cursor, previous = [], {}, 0, None
    for letter, wanted in choices[:limit_lines * 5]:
        position = next((i for i in range(cursor, len(words))
                         if cage.bare(words[i]) == wanted
                         and letter in words[i].upper()), None)
        if position is None:
            # His word is not in the scan. Say so; do not drop the row.
            out.append((letter, -1, wanted, MISSING,
                        "not found in the scan, probably an OCR variant"))
            continue

        forbidden = {previous, letter} - {None}
        for i in range(cursor, position):
            word = words[i]
            carried = sorted(set(word.upper()) & forbidden)
            if carried:
                verdict, note = BLOCKED, "carries " + ",".join(carried)
            else:
                verdict, note = ALLOWED, "rule permits it as a wing"
            out.append((letter, i, word, verdict, note))

        syllable = extract_syllable_with_letter(words[position], letter)
        repeat = syllable in index.get(letter, [])
        index.setdefault(letter, []).append(syllable)
        out.append((letter, position, words[position], SPINE_MARK,
                    f"presents {letter} with syllable {syllable!r}"
                    + ("  REPEAT" if repeat else "")))
        cursor, previous = position + 1, letter
    return out, wing_counts


def as_markdown(rows, wing_counts=()):
    """One table per spine letter, which is the unit the rule operates on."""
    lines, current, span = [], None, -1
    for letter, position, word, verdict, note in rows:
        if letter != current:
            current = letter
            span += 1
            allowed = sum(1 for r in rows if r[0] == letter and r[3] == ALLOWED)
            printed = wing_counts[span] if span < len(wing_counts) else "?"
            tally = (f"The rule allowed {allowed} wing words here. "
                     f"He printed {printed}.")
            lines += ["", f"### Seeking **{letter}**", "", tally, "",
                      "| # | word | what happened | why |",
                      "| --- | --- | --- | --- |"]
        where = "-" if position < 0 else position
        lines.append(f"| {where} | `{word}` | {verdict} | {note} |")
    return "\n".join(lines)


def summary(rows):
    counts = {}
    for *_, verdict, _ in rows:
        counts[verdict] = counts.get(verdict, 0) + 1
    total = sum(counts.values())
    out = ["", "## Totals", "", "| outcome | words | share |", "| --- | --- | --- |"]
    for verdict in (SPINE_MARK, BLOCKED, ALLOWED, MISSING):
        n = counts.get(verdict, 0)
        out.append(f"| {verdict} | {n} | {100 * n / total:.0f}% |")
    accounted = total - counts.get(ALLOWED, 0)
    share = 100 * accounted / total
    verdict = (f"The rule accounts for {accounted} of {total} words "
               f"({share:.0f}%). The rest is his choice.")
    out += ["", verdict]
    return "\n".join(out)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    rows, wings = walk(n)
    print(f"# Cage's walk, first {n} lines\n")
    print(f"Spine: {SPINE}.  Source: printed pages 3-152 of *The Cantos*.")
    print(as_markdown(rows, wings))
    print(summary(rows))
