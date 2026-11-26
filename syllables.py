"""Orthographic syllabification for the mesostic syllable index.

Cage's rule needs the syllable that presents a spine letter, and it needs that
syllable to be stable across the whole text so a repeat can be recognised. A
hyphenator cannot supply it: hyphenation answers "where may a line break," and
the answer is deliberately conservative, so pyphen hands back "about" and "ago"
whole. Indexing a whole word under a letter both rejects words that should be
allowed and lets genuine repeats through.

So the count comes from the CMU Pronouncing Dictionary, which knows how many
nuclei a word has, and the boundaries come from whichever orthographic splitter
agrees with that count. CMU supplies no character offsets of its own, which is
why it arbitrates rather than splits.

Measured over the 124,892 scoreable entries in CMU, pyphen alone agrees with the
CMU count 53.4% of the time. What follows agrees 97.9%, and no split loses a
character. The residue is initialisms such as "abc", three syllables aloud with
no orthographic boundary to find.
"""

import functools
import re
import unicodedata

import cmudict
import pyphen

_pyphen_dic = pyphen.Pyphen(lang="en")
_cmu_entries = None


def _cmu():
    """The CMU dictionary, built on first use.

    Building it costs a quarter of a second and some eight megabytes, which is
    too much to charge an importer that only wants normalize().
    """
    global _cmu_entries
    if _cmu_entries is None:
        _cmu_entries = cmudict.dict()
    return _cmu_entries

# Sonority ranks, quietest to loudest. A syllable nucleus is a local peak, so a
# boundary belongs at each trough between two peaks.
_SONORITY = {}
for _rank, _chars in enumerate(("bcdgtkpqxhj", "zvsf", "lmnrw", "aeiouy")):
    for _char in _chars:
        _SONORITY[_char] = _rank
_VOWEL_RANK = 3
_VOWELS = frozenset("aeiouy")

_PUNCTUATION = re.compile(r"[^a-z']")


def normalize(word):
    """Reduce a source token to the letters that carry pronunciation.

    Punctuation must not reach the index: "bronZe" and "bronZe," present the
    same syllable to E, and Cage's constraint should see them as the same.
    Accents are folded rather than dropped, so a source text richer than Canto I
    does not quietly lose the letter underneath one.
    """
    folded = unicodedata.normalize("NFKD", word.lower().replace("\u2019", "'"))
    return _PUNCTUATION.sub("", folded).strip("'")


def cmu_syllable_count(word):
    """Number of syllables per CMU, or None when the word is not in CMU.

    ARPABET marks every vowel phoneme with a stress digit, so counting digits
    counts nuclei. Words with several pronunciations take the smallest count,
    which is the one a reader is most likely to hear.
    """
    pronunciations = _cmu().get(normalize(word))
    if not pronunciations:
        return None
    return min(
        sum(1 for phoneme in pronunciation if phoneme[-1].isdigit())
        for pronunciation in pronunciations
    )


def _pyphen_split(word):
    return [piece for piece in _pyphen_dic.inserted(word).split("-") if piece]


def _ssp_split(word):
    """Split by the sonority sequencing principle: cut at every sonority trough."""
    ranks = [_SONORITY.get(char, 0) for char in word]
    if sum(1 for rank in ranks if rank == _VOWEL_RANK) < 2:
        return [word]

    cuts = []
    for i in range(1, len(word) - 1):
        previous, current, following = ranks[i - 1], ranks[i], ranks[i + 1]
        if current < previous and current < following:
            cuts.append(i)  # trough: the rising onset starts here
        elif current == following and current <= previous:
            cuts.append(i + 1)  # plateau or fall into a flat run: cut after it

    parts, start = [], 0
    for cut in cuts:
        parts.append(word[start:cut])
        start = cut
    parts.append(word[start:])
    return _attach_vowelless(parts)


def _attach_vowelless(parts):
    """Fuse any piece without a vowel into a neighbour; a syllable needs a nucleus."""
    out, leading = [], ""
    for part in parts:
        if not _VOWELS.intersection(part):
            if out:
                out[-1] += part
            else:
                leading += part
        elif out:
            out.append(part)
        else:
            out.append(leading + part)
            leading = ""
    if leading and not out:
        out = [leading]
    return [part for part in out if part]


def _corrected_ssp_split(word):
    """SSP, with the two endings English spells but does not pronounce.

    SSP reads orthography, so it hears a nucleus in every written vowel. Final
    silent "e" and the "-ed" of a regular past tense are written vowels that are
    not syllables, and they are where SSP over-splits: "ste-ri-le", "co-ve-red".
    """
    parts = _ssp_split(word)

    while len(parts) > 1:
        last = parts[-1]
        if not (last.endswith("e") and _VOWELS.intersection(last) == {"e"}):
            break
        if len(last) > 3 or last.endswith(("ee", "ye", "oe")):
            break
        # A consonant before "-le" makes it syllabic: "ta-ble", "sim-ple".
        if last.endswith("le") and parts[-2] and parts[-2][-1] not in _VOWELS:
            break
        parts = parts[:-2] + [parts[-2] + last]

    if len(parts) > 1:
        last = parts[-1]
        if last.endswith("ed") and _VOWELS.intersection(last) == {"e"}:
            # "-ed" is only its own syllable after t or d: "want-ed", "need-ed".
            stem = "".join(parts[:-1]) + last[:-2]
            if stem and stem[-1] not in "td":
                parts = parts[:-2] + [parts[-2] + last]

    return parts


def _merge_to_count(parts, target):
    """Drop boundaries until `parts` has `target` pieces.

    Each pass fuses the shortest piece into its shorter neighbour, which undoes
    the orphan fragments an over-split produces without disturbing the rest.
    """
    parts = list(parts)
    while len(parts) > max(1, target):
        i = min(range(len(parts)), key=lambda n: (len(parts[n]), n))
        if i == 0:
            j = 1
        elif i == len(parts) - 1:
            j = i - 1
        else:
            j = i - 1 if len(parts[i - 1]) <= len(parts[i + 1]) else i + 1
        low, high = min(i, j), max(i, j)
        parts[low:high + 1] = [parts[low] + parts[high]]
    return parts


def _split_vowel_runs(parts, target):
    """Open a run of written vowels that is really two nuclei: "cha-os", "bo-a".

    Every splitter above reads a vowel run as one nucleus, so hiatus is the one
    place they all under-split and hand back a whole word. Each pass cuts the
    longest run after its first vowel. A word with no run left to open keeps
    whatever pieces it has: initialisms like "abc" are three syllables aloud and
    offer no boundary to find.
    """
    parts = list(parts)
    while len(parts) < target:
        best = None  # (run length, index of part, offset to cut at)
        for index, part in enumerate(parts):
            for run in re.finditer(r"[aeiouy]{2,}", part):
                if run.start() + 1 >= len(part):
                    continue
                if best is None or run.end() - run.start() > best[0]:
                    best = (run.end() - run.start(), index, run.start() + 1)
        if best is None:
            break
        _, index, offset = best
        part = parts[index]
        parts[index:index + 1] = [part[:offset], part[offset:]]
    return parts


def syllabify(word):
    """Split a word into syllables whose concatenation is the normalized word.

    Candidates are tried in order and the first one matching the CMU count wins.
    pyphen leads because its patterns respect morpheme boundaries, which read
    better when they happen to be right. With no CMU entry (proper nouns, Pound's
    coinages) the corrected SSP split stands on its own, since it is the
    candidate that does not under-split short words.
    """
    normalized = normalize(word)
    if not normalized:
        return [word.lower()] if word else []
    return list(_syllabify_normalized(normalized))


@functools.lru_cache(maxsize=8192)
def _syllabify_normalized(normalized):
    """The split itself, memoized.

    A third of the tokens in a source text are repeats. The tuple keeps the
    cached value immutable so a caller mutating its list cannot poison it.
    """
    candidates = (
        _pyphen_split(normalized),
        _corrected_ssp_split(normalized),
        _ssp_split(normalized),
    )

    target = cmu_syllable_count(normalized)
    if target is None:
        return tuple(candidates[1])
    # "hmm" and "shh" are all consonant, so CMU counts no nuclei. Every word
    # still has to yield at least one piece for the index to hold.
    target = max(1, target)

    for candidate in candidates:
        if len(candidate) == target:
            return tuple(candidate)

    # No candidate hits the count. Take the one with the most pieces and close
    # the gap from whichever side it falls on.
    richest = max(candidates, key=len)
    if len(richest) > target:
        return tuple(_merge_to_count(richest, target))
    return tuple(_split_vowel_runs(richest, target))


def syllable_count(word):
    """Syllables in a word, from CMU where it knows the word and the split otherwise."""
    count = cmu_syllable_count(word)
    if count is None:
        return len(syllabify(word))
    return max(1, count)  # all-consonant words such as "hmm" still take a slot


def extract_syllable_with_letter(word, letter):
    """Return the syllable that presents `letter`, for the syllable index.

    The result is normalized (lowercased, punctuation stripped) so the index
    compares syllables and not typography.
    """
    target = letter.lower()
    for syllable in syllabify(word):
        if target in syllable:
            return syllable
    return normalize(word) or word.lower()
