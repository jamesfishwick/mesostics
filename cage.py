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
_HERE = os.path.dirname(os.path.abspath(__file__))

# Two readings of his eight pages, each better at a different thing.
#
# The PDF's own text layer gets words right and loses capitals, and a capital
# is what marks the spine: one line arrives as "papEr ... braZilian ... s.A."
# with the R gone. 198 lines survive that.
#
# Rendering the pages at 400 dpi and reading them with tesseract recovers the
# capitals, 222 lines and 998 presentations, every margin reference legible
# where only 141 of 198 were before. It pays for that with word errors of its
# own, "pluto" as "piuto" and "lust" as "ust", which break an alignment
# against Pound: 205 choices unplaceable against 4.
#
# So questions about his own text are asked of the OCR reading, and questions
# that align him to Pound are asked of the text layer.
TEXT_LAYER_PATH = os.path.join(_HERE, "reference", "by_text_layer.tsv")
OCR_PATH = os.path.join(_HERE, "reference", "by_ocr.tsv")
REFERENCE_PATH = os.path.join(_HERE, "reference",
                              "writing_through_the_cantos.tsv")

# Verified character for character against X: Writings '79-'82, p. 109. The
# margin reference "3-4" is the page of The Cantos, which is Canto I.
CANTO_I = [
    ("3-4", "and thEn with bronZe lance heads beaRing yet Arms"),
    ("3-4", "sheeP slain Of plUto stroNg praiseD"),
]


def presentations(line):
    """(spine letter, word carrying it), in order.

    A token here may carry two capitals, and that is not always one of Pound's
    words. Checked against a full text of the Cantos, "ritz-carlton" is his
    and genuinely presents both Z and R, while "sea-jauzionda" and "up-other"
    are not: the first is "sea" from page 21 beside "jauzionda" from page 22,
    the second "up" from "up-stairs" beside "other", each pair joined by a
    hyphen Cage put there because no wing fell between them.

    They are left joined all the same. Splitting them makes the alignment hunt
    for "sea" and "up", which occur everywhere in Pound, and it matched the
    wrong ones: 100 lost alignments against 4. So one word of the three really
    does present two letters, and the count below treats all three as if they
    did.
    """
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


# Words this project's own reading of Cage's pages gets wrong. Each was
# checked against his printed line and against Pound's text, which supplies
# the spelling. These are errors in extracting his book, not his.
EXTRACTION_ERRORS = {
    "rotterdm": "rotterdam",   # the a is in his line and in Pound's "Rotterdam"
}


def bare(word):
    """A word reduced to letters, so "arms," and "Arms" compare equal."""
    stripped = re.sub(r"[^a-z]", "", word.lower())
    return EXTRACTION_ERRORS.get(stripped, stripped)


def compare(reference=None):
    """Run the generator and match its spine against Cage's, letter by letter.

    Returns a list of (letter, cage_word, our_word, agree) in spine order,
    truncated to whichever sequence is shorter.
    """
    reference = CANTO_I if reference is None else reference
    cage = spine_words(reference)

    # The comparison asks whether his word is the first one admissible, which
    # is a question about the rule and not about his chance draw. SHOW_ALL
    # turns the draw off, so the walk takes the first candidate every time.
    ours, mode = [], mesostics.WING_MODE
    try:
        mesostics.WING_MODE = "SHOW_ALL"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            mesostics.generate_mesostic(ours)
    finally:
        mesostics.WING_MODE = mode

    rows = []
    for (letter, our_word), cage_word in zip(ours, cage):
        rows.append((letter, cage_word, our_word, bare(our_word) == bare(cage_word)))
    return rows


def _render_and_read(pdf_path, first, last, dpi, scratch):
    """Render each page to PNG and read it with tesseract. Returns text lines.

    tesseract will not take a PNG on stdin, so the render goes to a file.
    """
    lines = []
    for number in range(first, last + 1):
        stem = os.path.join(scratch, f"pg{number}")
        subprocess.run(["pdftoppm", "-r", str(dpi), "-gray", "-f", str(number),
                        "-l", str(number), "-png", "-singlefile", pdf_path, stem],
                       check=True, capture_output=True)
        # tesseract exits non-zero on warnings while still producing output,
        # so its status is not checked; an empty read is the real failure.
        read = subprocess.run(["tesseract", stem + ".png", "-", "--psm", "6"],
                              capture_output=True, check=False)
        text = read.stdout.decode("utf-8", "replace")
        if not text.strip():
            raise RuntimeError(f"tesseract read nothing from page {number}: "
                               f"{read.stderr.decode('utf-8', 'replace')[:200]}")
        lines += text.split("\n")
    return lines


def extract_by_ocr(pdf_path, first=115, last=123, dpi=400):
    """Re-read his pages from the page images rather than the PDF's text layer.

    The embedded layer drops capitals, and a capital is the whole point: it is
    what marks the spine. One line comes through as "papEr ... braZilian ...
    s.A." with the R gone, which spells EZA, so the line is unusable and the
    EZRA/POUND alternation appears to break. Rendered at 400 dpi and read
    again it is "secuRities", and the line is fine.

    Recovers 222 clean lines against 198 from the text layer, and brings the
    segment counts to 112 EZRA and 110 POUND from 106 and 92.
    """
    # The renders go beside the extracted text rather than into a fresh
    # temporary directory: tesseract could not open files there under the
    # sandbox this runs in, reporting the image as missing while it existed.
    scratch = os.path.join(os.path.dirname(REFERENCE_PATH), "pages")
    os.makedirs(scratch, exist_ok=True)
    rows, page = [], "?"
    pages = _render_and_read(pdf_path, first, last, dpi, scratch)
    for raw in pages:
        line = re.sub(r"^[|\s]+", "", raw.rstrip())
        reference = re.search(r"\s+(\d{1,3}(?:-\d{1,3})?)\s*$", line)
        if reference:
            page = reference.group(1)
            line = line[:reference.start()]
        line = " ".join(line.split())
        if is_spine_line(line):
            rows.append((page, line))

    os.makedirs(os.path.dirname(REFERENCE_PATH), exist_ok=True)
    with open(REFERENCE_PATH, "w", encoding="utf-8") as out:
        for page, line in rows:
            out.write(f"{page}\t{line}\n")
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


def _load(path):
    if not os.path.exists(path):
        return CANTO_I
    with open(path, encoding="utf-8") as source:
        return [tuple(line.split("\t", 1)) for line in source.read().splitlines()]


def load_reference():
    """His lines as the PDF's text layer gives them: good words, lost capitals.

    This is the one to align against Pound, because a wrong word desyncs a
    forward-only walk and the OCR reading has more of them.
    """
    for path in (TEXT_LAYER_PATH, REFERENCE_PATH):
        if os.path.exists(path):
            return _load(path)
    return CANTO_I


def load_structure():
    """His lines as a 400 dpi re-read gives them: every capital, some bad words.

    This is the one for questions about his own text, where the capitals are
    the evidence and no alignment to Pound is involved.
    """
    for path in (OCR_PATH, REFERENCE_PATH):
        if os.path.exists(path):
            return _load(path)
    return CANTO_I


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
