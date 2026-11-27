"""A word-by-word account of Cage's walk through the source.

Everything the rule says can be checked against the text, word by word. For
each word between one of his spine words and the next, exactly one of these
happened:

  SPINE     he marked it, and it presents a letter of the name
  BLOCKED   it carries one of the two letters in play, so the rule forbade
            printing it, and he read straight past
  PASSED    the rule allowed it and he demonstrably did not print it
  PRINTED   the rule allowed it and he printed it
  UNSETTLED the rule allowed it, he printed a word spelt the same, and the
            span holds more than one, so which occurrence is his is unknown

PASSED and PRINTED are decided by subsequence alignment. The words he printed
in a wing appear in source order, so they embed into that span's allowed words
as a subsequence; where that embedding is unique the placement is forced, and
where a word of his does not occur at all he plainly did not print it. Only a
repeated common word inside one span leaves a choice, and that is UNSETTLED.

Over Cantos I-XXX this settles 99.3% of the words he covered. MISSING marks a
spine word absent from the scan, four cases in thirty lines, reported rather
than skipped: a trace that drops a row is not an account of anything.

    uv run python trace.py            # the first four lines
    uv run python trace.py 12         # the first twelve
"""

import sys

import cage
from analysis import PP3_152, SPINE, cage_choices, corpus_words
from syllables import extract_syllable_with_letter

SPINE_MARK, BLOCKED, MISSING = "SPINE", "BLOCKED", "MISSING"
PASSED, PRINTED, UNSETTLED = "PASSED", "PRINTED", "UNSETTLED"


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
            if carried:
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
                out.append(row[:3] + (PASSED, "allowed, he printed it not"))
            elif forced:
                out.append(row[:3] + (PRINTED, "allowed, and his wing fixes it here"))
            else:
                out.append(row[:3] + (UNSETTLED,
                                      "he printed this word, but the span holds more than one"))

        syllable = extract_syllable_with_letter(words[position], letter)
        repeat = syllable in index.get(letter, [])
        index.setdefault(letter, []).append(syllable)
        out.append((letter, position, words[position], SPINE_MARK,
                    f"presents {letter} with syllable {syllable!r}"
                    + ("  REPEAT" if repeat else "")))
        cursor, previous = position + 1, letter
    return out, wings


def as_markdown(rows, wing_counts=()):
    """One table per spine letter, which is the unit the rule operates on."""
    lines, current, span = [], None, -1
    for letter, position, word, verdict, note in rows:
        if letter != current:
            current = letter
            span += 1
            allowed = sum(1 for r in rows if r[0] == letter
                          and r[3] in (PASSED, PRINTED, UNSETTLED))
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
    for verdict in (SPINE_MARK, BLOCKED, PASSED, PRINTED, UNSETTLED, MISSING):
        n = counts.get(verdict, 0)
        out.append(f"| {verdict} | {n} | {100 * n / total:.0f}% |")
    settled = total - counts.get(UNSETTLED, 0)
    open_ = counts.get(UNSETTLED, 0)
    by_rule = counts.get(BLOCKED, 0) + counts.get(SPINE_MARK, 0)
    first = (f"The rule decides {by_rule} of {total} words "
             f"({100 * by_rule / total:.0f}%): it marked them or forbade them.")
    second = (f"Alignment decides most of the rest, leaving {open_} genuinely "
              f"open. {settled} of {total} ({100 * settled / total:.1f}%) "
              f"are settled.")
    out += ["", first, "", second]
    return "\n".join(out)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    rows, wings = walk(n)
    print(f"# Cage's walk, first {n} lines\n")
    print(f"Spine: {SPINE}.  Source: printed pages 3-152 of *The Cantos*.")
    print(as_markdown(rows, wings))
    print(summary(rows))
