# Mesostics

A Python implementation of John Cage's mesostic text generation method.

## What is a Mesostic?

A mesostic is a poetic form where a vertical "spine" runs down the middle of the text. John Cage used this technique to "write through" existing texts, creating new works by reading source material according to strict rules.

This implementation generates mesostics from Ezra Pound's *Canto I* using the spine word "EZRAPOUND".

## Cage's Rules

Based on Cage's description in *X: Writings '79'82* (Wesleyan University Press, 1982):

1. **Between-letter prohibition**: Between two spine letters (e.g., E and Z), neither letter may appear
2. **Syllable index**: Track syllables containing each letter; don't repeat syllables for the same letter
3. **First occurrence**: Use the first word encountered that contains the target letter
4. **45-character limit**: Maximum 45 characters of "wing words" on each side of a spine word

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

## References

- Cage, John. *X: Writings '79'82*. Middletown, Conn.: Wesleyan University Press, 1982.
- Pound, Ezra. *The Cantos*. Various editions.

## License

Educational/experimental implementation for studying Cage's compositional methods.
