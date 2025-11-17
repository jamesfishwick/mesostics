# Mesostics

A Python implementation of John Cage's mesostic text generation method.

## What is a Mesostic?

A mesostic is a poetic form where a vertical "spine" runs down the middle of the text. John Cage used this technique to "write through" existing texts, creating new works by reading source material according to strict rules.

This implementation generates mesostics from Ezra Pound's *Canto I* using the spine word "EZRAPOUND".

## Cage's Rules

### Primary Source

From Cage's *X: Writings '79-'82* (Wesleyan University Press, 1982), page 109:

> "To write the following text I followed the rule given me by Louis Mink, which I also followed in Writing for the Third (and Fourth) Time through Finnegans Wake, that is, I did not permit the appearance of either letter between two of the name. As in Writing for the Fourth Time Through Finnegans Wake, I kept an index of the syllables used to present a given letter of the name and I did not permit repetition of these syllables."

### Rule Interpretation

Through analysis of Cage's output compared to source text, we've identified these working rules:

1. **Sequential letter selection**: Move through source text linearly, spelling out the spine word (EZRAPOUND) with capitalized letters

2. **Between-letter prohibition**: Between spine letter N and spine letter N+1, no words may contain either of those two letters
   - Example: Between E (from "thEn") and Z (from "bronZe"), skip all words containing E or Z
   - This applies to potential spine words AND wing words

3. **Syllable indexing**: When a word is used to "present" a letter from the spine:
   - Extract the syllable containing that letter
   - Index that syllable to that letter
   - Cannot reuse that syllable for the same letter later
   - Example: "thEn" indexes syllable "then" to E; can't use "then" again for E

4. **Words containing spine letters**: Any word containing a letter from the spine word "presents" that letter
   - Words with spine letters must be used in proper sequence (or skipped)
   - Cannot use a word that would present a letter out of order
   - Example: Skip "down" (contains D) while seeking Z, because using it would burn the syllable "down" for D

5. **Neutral words**: Words containing NO letters from the spine word can appear as wing words without constraint

6. **Source capitalization** (hypothesis): Cannot use words already capitalized in source text
   - Mesostic marking requires adding capitalization
   - If word is already capitalized, the marking isn't distinctive
   - Example: "Pallor" (capitalized in Pound) → skip; "sheep" (lowercase) → use as "sheeP"

### Additional Documentation

**Wing word concept** documented in:
- [Virginia Silence mailing list discussion](https://lists.virginia.edu/sympa/arc/silence/2019-01/msg00024/mesostic_demo.pdf)
- [Platonic Music Engine implementation](https://www.platonicmusicengine.com/mesostic.html)

These sources specify the **45-character limit**: Maximum 45 characters of wing words on either side of each spine word.

## Installation

```bash
# Using uv (recommended)
uv sync

# Or with pip
pip install pyphen
```

## Usage

```bash
# Run with default settings
uv run python mesostics.py

# Or with regular python
python mesostics.py
```

## Configuration

Edit the configuration variables in `mesostics.py`:

```python
WING_CHAR_LIMIT = 45       # Character limit per wing
MESOSTIC_RULE = "100%"     # Between-letter strictness
WING_MODE = "SHOW_ALL"     # Wing word selection mode
```

### Wing Modes

**SHOW_ALL** - Shows all valid options in brackets (within 45-char limit):
```
And thEn [who | had | much; | Souls | with | girls | many, | with] bronZe [lance | heads, | Battle | spoil,] beaRing yet Arms, These
```

**MAX** - Include all valid words (within 45-char limit):
```
And thEn who had much; Souls with girls many, with bronZe lance heads, Battle spoil, beaRing yet Arms, These
```

**MINIMAL** - Sparse, Cage-like output (1-2 words per wing):
```
And thEn bronZe heads, Battle beaRing Arms
```

**RANDOM** - Random selection (1-3 words per wing):
```
And thEn Souls bronZe spoil, beaRing yet Arms
```

## Output

The script generates mesostic lines:
- **EZRA** lines contain the first 4 letters (E-Z-R-A)
- **POUND** lines contain the last 5 letters (P-O-U-N-D)
- Lines alternate between the two names

## Technical Notes

- Uses `pyphen` for syllable extraction
- Implements proper between-letter prohibition
- Tracks syllable usage to prevent repetition
- Enforces 45-character wing limits per Cage's method

## Current Implementation Status

### Known Divergence from Cage's Output

Our implementation currently produces output that diverges from Cage's published mesostic at the second line:

**Cage's output:**
```
and thEn with bronZe lance heads beaRing yet Arms
sheeP slain Of plUto stroNg praiseD
```

**Our output:**
```
[And] thEn [with] bronZe [lance | heads, | Battle | spoil,] beaRing [yet] Arms, [These]
[me; | with | shouting,] Pallor upOn [me, | cried] [beasts;] SlaUghtered [the | herds, | sheep] slaiN [of] PoureD
```

### The Pallor vs. sheeP Problem

The first line matches perfectly, but at the second line (spelling POUND), our implementation selects "Pallor" for P while Cage uses "sheeP".

**Analysis:**
- Both words occur in Pound's source text after "Arms" (the previous spine word)
- "Pallor" appears first: "Pallor upon me, cried to my men for more beasts; / Slaughtered the herds, sheep slain of bronze"
- Source capitalization doesn't explain it: "upon" (lowercase) comes between them and also contains P

**Letter composition:**
- "Pallor" = P-a-l-l-**o**-r (contains **o**, a future letter in POUND)
- "upon" = **u**-p-**o**-**n** (contains **u**, **o**, **n** all future letters)
- "sheeP" = s-h-e-e-p (contains only **p** target + **e** previous, no future letters)

**Revised Hypothesis:**
A spine word can contain:
- The target letter (required)
- Previous spine letters already used (allowed, as in "bronZe" containing e)
- But NO future spine letters (would burn syllables prematurely)

This explains why Cage skips both "Pallor" (has future O) and "upon" (has future O, U, N) to reach "sheeP" (clean, only target + previous).

**Next Step:**
Implement filter to reject spine words containing any letters from EZRAPOUND that haven't been presented yet in sequence.

## References

- Cage, John. *X: Writings '79'82*. Middletown, Conn.: Wesleyan University Press, 1982.
- Pound, Ezra. *The Cantos*. Various editions.

## License

Educational/experimental implementation for studying Cage's compositional methods.
