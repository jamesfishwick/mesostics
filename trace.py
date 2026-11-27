"""A word-by-word account of Cage's walk through the source.

Everything the rule says can be checked against the text, word by word. For
each word between one of his spine words and the next, exactly one of these
happened:

  SPINE     he marked it, and it presents a letter of the name
  BLOCKED   it carries one of the two letters in play, so the rule forbade
            printing it, and he read straight past
  DECLINED  it could have presented the letter he was seeking, with a syllable
            he had not spent, and he walked past it anyway
  SPENT     it carries the letter he was seeking but its syllable was already
            indexed, so his own no-repeat rule ruled it out
  PASSED    the rule allowed it and he demonstrably did not print it
  PRINTED   the rule allowed it and he printed it
  TIED      the rule allowed it, he printed a word spelt the same, and the
            span holds several, so one of them is his and the rest were
            passed over; which is which has no effect on the poem

PASSED and PRINTED are decided by subsequence alignment. The words he printed
in a wing appear in source order, so they embed into that span's allowed words
as a subsequence; where that embedding is unique the placement is forced, and
where a word of his does not occur at all he plainly did not print it. Only a
repeated common word inside one span leaves a choice, and that is UNSETTLED.

Every decision Cage made is recoverable: which word presents each letter, and
which words stand in each wing, with their multiplicity. TIED is not an open
decision but open provenance. Where his wing holds one "with" and the span
holds ten, exactly one was printed and nine were passed; the counts are fixed
by his own text and the two readings produce the same line.

MISSING marks a spine word absent from the scan, four cases in thirty lines,
reported rather than skipped: a trace that drops a row is not an account of
anything.

    uv run python trace.py            # the first four lines
    uv run python trace.py 12         # the first twelve
"""

import sys

import cage
from analysis import PP3_152, SPINE, cage_choices, corpus_words
from syllables import extract_syllable_with_letter

SPINE_MARK, BLOCKED, MISSING = "SPINE", "BLOCKED", "MISSING"
PASSED, PRINTED, TIED = "PASSED", "PRINTED", "TIED"
DECLINED, SPENT = "DECLINED", "SPENT"


def embeddings(allowed, printed):
    """How many distinct ways `printed` sits inside `allowed` as a subsequence.

    One means his wing can only have come from one set of positions, so every
    word in the span is decided.
    """
    total = [1] + [0] * len(printed)
    for word in allowed:
        for j in range(len(printed), 0, -1):
            if printed[j - 1] == word:
                total[j] += total[j - 1]
    return total[len(printed)]


def printed_wings(limit_lines):
    """The words he printed in each wing, in order, one list per span."""
    out = []
    for _, line in cage.load_reference()[:limit_lines]:
        tokens = line.split()
        marks = [i for i, w in enumerate(tokens) if any(c.isupper() for c in w)]
        out.append([cage.bare(w) for w in tokens[:marks[0]]])
        out.extend([cage.bare(w) for w in tokens[a + 1:b]]
                   for a, b in zip(marks, marks[1:]))
    return out


def walk(limit_lines=4):
    """Classify every source word Cage covered, in order.

    Returns a list of (segment, letter, position, word, verdict, note).
    """
    words = corpus_words(PP3_152)
    choices = cage_choices()
    wings = printed_wings(limit_lines)

    out, index, cursor, previous = [], {}, 0, None
    for span, (letter, wanted) in enumerate(choices[:limit_lines * 5]):
        printed = wings[span] if span < len(wings) else []
        position = next((i for i in range(cursor, len(words))
                         if cage.bare(words[i]) == wanted
                         and letter in words[i].upper()), None)
        if position is None:
            # His word is not in the scan. Say so; do not drop the row.
            out.append((letter, -1, wanted, MISSING,
                        "not found in the scan, probably an OCR variant"))
            continue

        forbidden = {previous, letter} - {None}
        span_rows, allowed = [], []
        for i in range(cursor, position):
            word = words[i]
            carried = sorted(set(word.upper()) & forbidden)
            if letter in word.upper():
                # It could have presented the letter. Say whether his own rule
                # stopped him or he simply did not take it: this is the only
                # column where his choice is visible.
                spent = extract_syllable_with_letter(word, letter)
                if spent in index.get(letter, []):
                    span_rows.append((letter, i, word, SPENT,
                                      f"syllable {spent!r} already presented {letter}"))
                else:
                    span_rows.append((letter, i, word, DECLINED,
                                      f"could have presented {letter} as {spent!r}"))
            elif carried:
                span_rows.append((letter, i, word, BLOCKED,
                                  "carries " + ",".join(carried)))
            else:
                allowed.append(cage.bare(word))
                span_rows.append((letter, i, word, None, ""))

        forced = bool(printed) and embeddings(allowed, printed) == 1
        for n, row in enumerate(span_rows):
            if row[3] is not None:
                out.append(row)
                continue
            bare = cage.bare(row[2])
            if bare not in printed:
                out.append(row[:3] + (PASSED, "allowed; he did not print it"))
            elif forced:
                out.append(row[:3] + (PRINTED, "allowed, and his wing fixes it here"))
            else:
                same = allowed.count(bare)
                mine = printed.count(bare)
                note = (f"{mine} of these {same} identical words went into "
                        f"his wing, {same - mine} passed")
                out.append(row[:3] + (TIED, note))

        syllable = extract_syllable_with_letter(words[position], letter)
        repeat = syllable in index.get(letter, [])
        index.setdefault(letter, []).append(syllable)
        out.append((letter, position, words[position], SPINE_MARK,
                    f"presents {letter} with syllable {syllable!r}"
                    + ("  REPEAT" if repeat else "")))
        cursor, previous = position + 1, letter
    return out, wings


def runs(rows):
    """Collapse consecutive words that got the same verdict for the same reason.

    Every word is still named. A run of thirty BLOCKED words is thirty words
    in one cell rather than thirty rows, which is the difference between a
    table that renders and one that does not.
    """
    out = []
    for letter, position, word, verdict, note in rows:
        if out and out[-1][0] == letter and out[-1][3] == verdict \
                and out[-1][4] == note and verdict not in (SPINE_MARK, MISSING):
            out[-1][2].append(word)
            out[-1][1][1] = position
        else:
            out.append([letter, [position, position], [word], verdict, note])
    return out


def as_markdown(rows, wing_counts=()):
    """One table per spine letter, which is the unit the rule operates on."""
    lines, current, span = [], None, -1
    for letter, (first, last), group, verdict, note in runs(rows):
        if letter != current:
            current = letter
            span += 1
            allowed = sum(1 for r in rows if r[0] == letter
                          and r[3] in (PASSED, PRINTED, TIED))
            printed = wing_counts[span] if span < len(wing_counts) else "?"
            tally = (f"The rule allowed {allowed} wing words here. "
                     f"He printed {len(printed) if printed != '?' else '?'}.")
            lines += ["", f"### Seeking **{letter}**", "", tally, "",
                      "| # | words | what happened | why |",
                      "| --- | --- | --- | --- |"]
        where = "-" if first < 0 else (f"{first}" if first == last else f"{first}-{last}")
        shown = " ".join(f"`{w}`" for w in group)
        count = "" if len(group) == 1 else f" _({len(group)})_"
        lines.append(f"| {where} | {shown}{count} | {verdict} | {note} |")
    return "\n".join(lines)


def summary(rows):
    counts = {}
    for *_, verdict, _ in rows:
        counts[verdict] = counts.get(verdict, 0) + 1
    total = sum(counts.values())
    out = ["", "## Totals", "", "| outcome | words | share |", "| --- | --- | --- |"]
    for verdict in (SPINE_MARK, DECLINED, SPENT, BLOCKED,
                    PASSED, PRINTED, TIED, MISSING):
        n = counts.get(verdict, 0)
        out.append(f"| {verdict} | {n} | {100 * n / total:.0f}% |")
    tied = counts.get(TIED, 0)
    forced = counts.get(BLOCKED, 0) + counts.get(SPENT, 0)
    chose = counts.get(DECLINED, 0) + counts.get(PASSED, 0) + counts.get(PRINTED, 0) + tied
    first = (f"The rule forced {forced} of {total} words "
             f"({100 * forced / total:.0f}%): it forbade printing them, or his "
             f"own no-repeat rule had spent their syllable.")
    second = (f"He chose over the other {chose} ({100 * chose / total:.0f}%). "
              f"{counts.get(DECLINED, 0)} of those could have presented the "
              f"letter he was seeking and he walked past them; that column is "
              f"where his judgement is visible. {tied} words are tied, meaning "
              f"the span holds several spelt alike and the counts are known "
              f"but not which token is which.")
    out += ["", first, "", second]
    return "\n".join(out)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    rows, wings = walk(n)
    print(f"# Cage's walk, first {n} lines\n")
    print(f"Spine: {SPINE}.  Source: printed pages 3-152 of *The Cantos*.")
    print(as_markdown(rows, wings))
    print(summary(rows))
