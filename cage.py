"""Check this implementation against Cage's own text.

`Writing Through the Cantos` runs to 363 lines in *X: Writings '79-'82*, and
each pair carries a margin reference to the page of *The Cantos* it was drawn
from. Those references run from 2 to 781, so Cage wrote through the whole book
while `corpus/canto_i.txt` holds pages 3 to 5. Exactly one pair of his lines is
therefore reproducible from our corpus, and it is the pair quoted below.

The rest of his text stays out of this repository: it is a copyrighted 1982
work and committing all 363 lines would republish it. `extract_from_pdf` will
rebuild the full reference from a copy of the book for anyone who has one, and
`REFERENCE_PATH` is where it lands, outside version control.
"""

import os
import re
import subprocess
import warnings

import mesostics

SPINE = "EZRAPOUND"
REFERENCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "reference", "writing_through_the_cantos.tsv")

# Verified character for character against X: Writings '79-'82, p. 109. The
# margin reference "3-4" is the page of The Cantos, which is Canto I.
CANTO_I = [
    ("3-4", "and thEn with bronZe lance heads beaRing yet Arms"),
    ("3-4", "sheeP slain Of plUto stroNg praiseD"),
]


def presentations(line):
    """(spine letter, word carrying it), in order. A word may carry two."""
    return [(char, word) for word in line.split()
            for char in word if char.isupper()]


def is_spine_line(line):
    """True when the line's capitals spell one complete half of the name.

    This is what separates Cage's mesostic from everything around it. The
    headnotes have incidental capitals, and the pieces either side of it in the
    book are mesostics on other names, so neither spells EZRA or POUND.
    """
    marked = "".join(letter for letter, _ in presentations(line))
    return marked in ("EZRA", "POUND")


def spine_words(lines):
    """The marked words of a mesostic, in spine order.

    A spine word is the one carrying the capital Cage added to present a
    letter; every other word on the line is wing.
    """
    return [word for _, line in lines for word in line.split()
            if any(char.isupper() for char in word)]


def bare(word):
    """A word reduced to letters, so "arms," and "Arms" compare equal."""
    return re.sub(r"[^a-z]", "", word.lower())


def compare(reference=None):
    """Run the generator and match its spine against Cage's, letter by letter.

    Returns a list of (letter, cage_word, our_word, agree) in spine order,
    truncated to whichever sequence is shorter.
    """
    reference = CANTO_I if reference is None else reference
    cage = spine_words(reference)

    ours = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mesostics.generate_mesostic(ours)

    rows = []
    for (letter, our_word), cage_word in zip(ours, cage):
        rows.append((letter, cage_word, our_word, bare(our_word) == bare(cage_word)))
    return rows


def extract_from_pdf(pdf_path):
    """Rebuild the full 363-line reference from a copy of the book.

    Shells out to pdftotext because the margin references sit in a right-hand
    column and only a layout-preserving extraction keeps them on their line;
    pypdf reflows the page and loses them. Writes REFERENCE_PATH and returns
    the rows, so the comparison can widen once the corpus grows past Canto I.
    """
    try:
        text = subprocess.run(
            ["pdftotext", "-layout", pdf_path, "-"],
            check=True, capture_output=True, text=True,
        ).stdout
    except FileNotFoundError:
        raise RuntimeError(
            "pdftotext is needed to keep the margin references on their line "
            "(brew install poppler)"
        ) from None

    body = text.split("W R I T I N G THROUGH THE CANTOS", 1)
    if len(body) < 2:
        raise ValueError(f"{pdf_path} does not contain Writing Through the Cantos")
    body = body[1].split("COMPOSITION IN RETROSPECT", 1)[0]

    rows, page = [], "?"
    for raw in body.split("\n"):
        stripped = raw.rstrip()
        if not stripped.strip():
            continue
        # The margin reference is a page of The Cantos, set off by wide space.
        # Reading it off the scan turns some into letters -- 11 comes through
        # as n -- and inheriting the previous page would be worse than
        # admitting we do not know.
        reference = re.search(r"\s{3,}(\S{1,7})\s*$", stripped)
        if reference:
            token = reference.group(1)
            page = token if re.fullmatch(r"\d+(?:-\d+)?", token) else "?"
            stripped = stripped[:reference.start()]
        line = " ".join(stripped.split())
        if not is_spine_line(line):
            continue
        rows.append((page, line))

    os.makedirs(os.path.dirname(REFERENCE_PATH), exist_ok=True)
    with open(REFERENCE_PATH, "w", encoding="utf-8") as out:
        for page, line in rows:
            out.write(f"{page}\t{line}\n")
    return rows


def load_reference():
    """The full reference if it has been extracted, else the Canto I pair."""
    if not os.path.exists(REFERENCE_PATH):
        return CANTO_I
    with open(REFERENCE_PATH, encoding="utf-8") as source:
        return [tuple(line.split("\t", 1)) for line in source.read().splitlines()]


def report():
    """Print the letter-by-letter comparison."""
    rows = compare()
    print(f"{'letter':<8}{'Cage':<16}{'ours':<16}")
    for letter, cage_word, our_word, agree in rows:
        print(f"{letter:<8}{cage_word:<16}{our_word:<16}{'match' if agree else 'DIFFERS'}")
    agreed = sum(1 for *_, agree in rows if agree)
    print(f"\n{agreed}/{len(rows)} spine letters agree with Cage")
    if not os.path.exists(REFERENCE_PATH):
        print("\nComparing against the one pair of Cage's 363 lines that Canto I can\n"
              "produce. Add more of The Cantos to corpus/ to widen this, and run\n"
              "extract_from_pdf() against the book to get the rest of his text.")


if __name__ == "__main__":
    report()
