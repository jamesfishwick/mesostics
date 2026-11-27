# Mesostics

A Python implementation of John Cage's mesostic text generation method.

## What is a Mesostic?

A mesostic is a poetic form where a vertical "spine" runs down the middle of the text. John Cage used this technique to "write through" existing texts, creating new works by reading source material according to strict rules.

This implementation generates mesostics from Ezra Pound's _Canto I_ using the spine word "EZRAPOUND".

`corpus/` also carries printed pages 3 to 152 of the New Directions _Cantos_, Cantos I to XXX, which covers 313 of Cage's 884 spine choices. Those cantos were published in 1925 and 1930 and are out of copyright in the US. See [FINDINGS.md](FINDINGS.md) for what comparing against him shows.

## Cage's Rules

### Primary Source

From Cage's _X: Writings '79-'82_ (Wesleyan University Press, 1982), page 109:

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
pip install pyphen cmudict
```

## Usage

```bash
just run                   # generate the mesostic
just test                  # run the test suite
just lint                  # ruff
just                       # list every recipe
```

Or without `just`:

```bash
uv run python mesostics.py
uv run pytest
```

## Configuration

Edit the configuration variables in `mesostics.py`:

```python
WING_CHAR_LIMIT = 45       # Character limit per wing
MESOSTIC_RULE = "100%"     # Between-letter strictness
WING_MODE = "SHOW_ALL"     # Wing word selection mode
```

### Strictness

`MESOSTIC_RULE` sets which letters a wing word may not contain.

| Setting | Prohibited between spine letters                        | Canto I output |
| ------- | ------------------------------------------------------- | -------------- |
| `100%`  | both the previous spine letter and the one being sought | 209 characters |
| `50%`   | only the letter being sought                            | 457 characters |
| `0%`    | neither, so only the spine itself constrains the text   | 796 characters |

`100%` is the rule Cage states and the default. The looser settings are this implementation's reading of a knob the source material does not define, and they exist to show what the prohibition is doing. Any other value raises.

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

- Implements proper between-letter prohibition
- Tracks syllable usage to prevent repetition
- Enforces 45-character wing limits per Cage's method

### Syllable extraction

Cage's index records the syllable that presents a letter, so the split has to be right or the constraint misfires in both directions: words that should be allowed get rejected, and genuine repeats go unnoticed.

`pyphen` alone cannot supply that split. Hyphenation answers "where may a line break," and the answer is deliberately conservative, so it refuses to break `about`, `ago` or `money` at all and hands back the whole word. Measured against the CMU Pronouncing Dictionary across its 124,892 scoreable entries, pyphen agrees with the syllable count **53.4%** of the time.

`syllables.py` keeps pyphen but stops trusting it on its own. CMU supplies the authoritative count, and the boundaries come from whichever orthographic splitter agrees with it:

| Step                          | Role                                                                                                                                           |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| CMU Pronouncing Dictionary    | Counts nuclei. Supplies no character offsets, so it arbitrates rather than splits.                                                             |
| Maximal onset                 | First candidate. Gives each syllable the longest onset English allows, which is the phonological convention an index keyed on sound wants.     |
| `pyphen`                      | Second. Its patterns respect morpheme boundaries, which read well when they are right, but they are hyphenation points rather than syllables.  |
| Sonority sequencing (SSP)     | Ranks each character by sonority and cuts at every trough. Splits short words that pyphen will not.                                            |
| Silent `e` / `-ed` correction | SSP reads orthography, so it hears a nucleus in every written vowel. This removes the two English endings that are written but not pronounced. |
| Merge or hiatus split         | Closes the gap when no candidate hits the count.                                                                                               |

Two different claims live here and this project kept blurring them.

**How many** syllables a word has: CMU settles it, and agreement rises from 53.4% to **98.9%**, with no word losing characters to the split. The residue is initialisms such as `abc`, which are three syllables aloud and offer no orthographic boundary to find.

**Where** the boundaries fall: CMU says nothing, so this needs its own ground truth. The convention is maximal onset, and `test_boundaries.py` measures it against hand-checked words. Getting the count right does not get the cut right: pyphen offers `car-din-al`, which is a fair place to break a line and the wrong place to split a syllable. It collided with `jar-din` in the index and blocked one of Cage's own words, which is how the confusion surfaced.

Words outside CMU (proper nouns, Pound's coinages like `napenerve` and `closewebbed`) have no authoritative count, and fall back to the corrected SSP split.

Tokens are normalized before indexing, so `bronZe` and `bronZe,` present the same syllable to E rather than hiding a repeat behind a comma.

## Tests

```bash
just test
```

`test_documented_figures.py` recomputes every number quoted in this file and in `FINDINGS.md` and asserts the text still says it, so a figure cannot go stale without the suite noticing.

`test_syllables.py` covers the splitting and the index, `test_mesostics.py` the generator's state machine. The `test` and `lint` recipes are named for the global git hooks, which look for those two names and run them before a commit or push.

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
ointmEnt,
```

The third line is where the text runs out. Every Z-bearing word in Canto I is `bronze`, and the no-repeat rule has already spent that syllable, so Z can never be presented a second time. The script says as much on stderr:

```
spine incomplete: 'Z' of 'EZRAPOUND' was never presented because the source text ran out
```

### Checking against Cage

```bash
just compare
```

`cage.py` runs the generator and matches its spine against Cage's, letter by letter. The score is **4 of 9**: the EZRA line is exact and the POUND line agrees on nothing. Both outcomes are pinned by tests, so a change that fixes POUND will be noticed rather than missed.

The reference is verified character for character against _X: Writings '79-'82_, p. 109.

Only that one pair of Cage's lines is comparable. _Writing Through the Cantos_ runs to 198 mesostic lines, and each carries a margin reference to the page of _The Cantos_ it was drawn from; those references run from 3 to 782, so Cage wrote through the whole book while `corpus/canto_i.txt` holds pages 3 to 5. Every later line needs words we do not have. Those page references are also the roadmap for widening the comparison: add page 11 to the corpus and line 3 becomes checkable, and so on.

Cage's remaining lines are not in this repository. They are a copyrighted 1982 work and committing all 198 would republish it. `cage.extract_from_pdf()` rebuilds them from a copy of the book into `reference/`, which is outside version control.

### The Pallor vs. sheeP Problem

Our implementation takes the first word that can present a letter. Cage did too, six times out of nine, which is why the EZRA line matches him exactly. At P he passed over `Pallor` and `upon` to reach `sheep`, and the rest of the POUND line follows from that one decision.

Two explanations stood here for a while and both are now disproved by Cage's own text: that a spine word may carry no letter still to come (his `bronZe` carries R, `beaRing` carries A), and that he skipped words already capitalised in the source (he used `Pluto`). See [FINDINGS.md](FINDINGS.md) for the measurements and for what is still open.

## References

- Cage, John. _X: Writings '79'82_. Middletown, Conn.: Wesleyan University Press, 1982.
- Pound, Ezra. _The Cantos_. Various editions.

## License

Educational/experimental implementation for studying Cage's compositional methods.
