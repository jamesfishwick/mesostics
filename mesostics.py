import os
import sys
import warnings

from syllables import extract_syllable_with_letter

CORPUS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "corpus", "canto_i.txt")


def capitalize_letter(word, letter):
    """Capitalize the first occurrence of the specified letter in the word."""
    upper_word = word.upper()
    letter_upper = letter.upper()

    for i, char in enumerate(upper_word):
        if char == letter_upper:
            return word[:i] + word[i].upper() + word[i+1:]
    return word


# Read the source text from the file
with open(CORPUS_PATH, "r", encoding="utf-8") as file:
    canto_1 = file.read()

source_text = canto_1.split()
target_name = "EZRAPOUND"

# Configuration
WING_CHAR_LIMIT = 45  # Maximum characters on each side of spine word
MESOSTIC_RULE = "100%"  # "100%", "50%", or "0%" - see prohibited_letters
WING_MODE = "SHOW_ALL"  # "SHOW_ALL", "MAX", "RANDOM", "MINIMAL", "INTERACTIVE"
RANDOM_WORD_COUNT = (1, 3)  # (min, max) words for RANDOM mode

def prohibited_letters(other_letter, current_letter):
    """Letters a wing word may not contain, at the configured strictness.

    "100%" is the rule Cage quotes in the README: between two letters of the
    name, neither of them may appear. "50%" keeps only the prohibition on the
    letter being sought, and "0%" drops both, leaving nothing but the spine
    itself. The looser settings are this implementation's reading of a knob the
    source material does not define; 100% is the one Cage states.
    """
    if MESOSTIC_RULE == "0%":
        return set()
    if MESOSTIC_RULE == "50%":
        return {current_letter}
    if MESOSTIC_RULE != "100%":
        raise ValueError(
            f"MESOSTIC_RULE must be '100%', '50%' or '0%', not {MESOSTIC_RULE!r}"
        )
    return {letter for letter in (other_letter, current_letter) if letter}


def extract_consecutive_left_wing(word_history, exclude_letters, char_limit):
    """
    Extract consecutive valid words working backward from the most recent word.
    Stops at first invalid word or when char limit is exceeded.

    Args:
        word_history: List of (word, letters_in_word) tuples in chronological order
        exclude_letters: Set of letters that make a word invalid
        char_limit: Maximum total characters (including spaces)

    Returns:
        List of consecutive valid words in chronological order (earliest to latest)
    """
    if not word_history:
        return []

    consecutive_chain = []
    char_count = 0

    # Work backward through history
    for word, letters in reversed(word_history):
        # Check if word is valid (no excluded letters)
        if letters & exclude_letters:
            break  # Stop at first invalid word

        # Check if adding this word would exceed char limit
        word_len = len(word) + (1 if consecutive_chain else 0)  # +1 for space between words
        if char_count + word_len > char_limit:
            break  # Stop at char limit

        # Valid word, add to front of chain
        consecutive_chain.insert(0, word)
        char_count += word_len

    return consecutive_chain

def select_wing_words(candidates, mode):
    """
    Select which words to include in wing based on mode.

    candidates: list of words that fit within the 45-char limit
    mode: WING_MODE setting

    Returns: list of selected words or formatted string for SHOW_ALL
    """
    if not candidates:
        return []

    if mode == "SHOW_ALL":
        # Show all candidates in brackets with pipe separators
        return f"[{' | '.join(candidates)}]"

    elif mode == "MAX":
        # Include all words
        return candidates

    elif mode == "RANDOM":
        # Random selection
        import random
        min_count, max_count = RANDOM_WORD_COUNT
        count = random.randint(min_count, min(max_count, len(candidates)))
        return random.sample(candidates, count)

    elif mode == "MINIMAL":
        # Take only 1-2 content words, prefer longer ones
        stopwords = {'the', 'a', 'an', 'to', 'of', 'in', 'on', 'at', 'for', 'and', 'or', 'with', 'by'}
        content_words = [w for w in candidates if w.lower() not in stopwords]

        if content_words:
            # Take up to 2 longest content words
            sorted_words = sorted(content_words, key=lambda x: len(x), reverse=True)
            return sorted_words[:min(2, len(sorted_words))]
        else:
            # Fallback to first word if no content words
            return [candidates[0]] if candidates else []

    elif mode == "INTERACTIVE":
        # Placeholder - for now, return MAX behavior
        print(f"Available wing words: {candidates}")
        # TODO: Implement user selection
        return candidates

    else:
        # Default to MAX
        return candidates

def generate_mesostic():
    """Walk the source text once, spelling the spine word down the page."""
    syllable_index = {}  # {letter: [used_syllables]}
    blocked = {}  # {letter: [syllables rejected because already indexed]}
    result_lines = []  # Each element is a complete line
    current_letter_idx = 0
    previous_letter = None  # Track the spine letter we just used
    left_wing_history = []  # History of (word, letters_in_word) tuples for consecutive chain extraction
    current_line_segments = []  # Accumulate segments for current line (EZRA or POUND)
    collecting_right_wing = False  # Are we collecting words after a spine word?
    right_wing_candidates = []  # Consecutive valid words for right wing
    right_wing_chars = 0  # Running character count of right wing candidates
    line_complete = False  # Track when we've completed a name segment (EZRA or POUND)

    for word_idx, word in enumerate(source_text):
        letters_in_word = set(word.upper())

        # Get current position in the cycle (0-8, then reset)
        position_in_name = current_letter_idx % len(target_name)
        current_letter = target_name[position_in_name]

        # STATE 1: Currently collecting right wing after a spine word
        if collecting_right_wing:
            # Check if this word can be added to right wing
            forbidden = prohibited_letters(previous_letter, current_letter)
            if not letters_in_word & forbidden:
                word_len = len(word) + 1  # +1 for space
                if right_wing_chars + word_len <= WING_CHAR_LIMIT:
                    right_wing_candidates.append(word)
                    right_wing_chars += word_len
                    continue  # Continue collecting right wing
            # Either hit a forbidden word or reached char limit - finish right wing
            # Apply wing mode selection
            selected_right = select_wing_words(right_wing_candidates, WING_MODE)

            # Add selected right wing to line segments
            if isinstance(selected_right, str):  # SHOW_ALL returns a string
                current_line_segments.append(selected_right)
            else:
                current_line_segments.extend(selected_right)

            # Check if this completes the line
            if line_complete:
                # Output the complete line
                result_lines.append(' '.join(current_line_segments))
                # Reset everything for new line
                current_line_segments = []
                # DON'T reset previous_letter - we need it for between-letter prohibition
                line_complete = False

            # Reset for next spine word
            left_wing_history = []
            right_wing_candidates = []
            right_wing_chars = 0
            collecting_right_wing = False

            # Fall through to process current word normally

        # STATE 2: Word contains current target letter - this is a spine word
        if current_letter in word.upper():
            syllable = extract_syllable_with_letter(word, current_letter)
            if syllable not in syllable_index.get(current_letter, []):
                # Found spine word!
                spine_word = capitalize_letter(word, current_letter)

                # Before the first spine letter there is no previous letter,
                # so the next one stands in its place.
                if previous_letter is None:
                    next_position = (position_in_name + 1) % len(target_name)
                    other_letter = target_name[next_position]
                else:
                    other_letter = previous_letter
                exclude_letters = prohibited_letters(other_letter, current_letter)

                # Extract consecutive left wing chain working backward from current position
                left_wing_consecutive = extract_consecutive_left_wing(
                    left_wing_history,
                    exclude_letters,
                    WING_CHAR_LIMIT
                )

                # Apply wing mode selection to consecutive left wing
                selected_left = select_wing_words(left_wing_consecutive, WING_MODE)

                # Add left wing + spine word to segments
                if isinstance(selected_left, str):  # SHOW_ALL returns a string
                    current_line_segments.append(selected_left)
                    current_line_segments.append(spine_word)
                else:
                    current_line_segments.extend(selected_left)
                    current_line_segments.append(spine_word)

                syllable_index.setdefault(current_letter, []).append(syllable)
                previous_letter = current_letter
                current_letter_idx += 1

                # Start collecting right wing
                collecting_right_wing = True
                left_wing_history = []
                right_wing_candidates = []
                right_wing_chars = 0

                # Check if we completed a name segment (EZRA or POUND)
                new_position = current_letter_idx % len(target_name)
                if new_position == 4 or new_position == 0:
                    # Mark that line will be complete after collecting right wing
                    line_complete = True
            else:
                # The word presents the letter but its syllable is spent. Keep
                # it so the end of the walk can say what blocked the spine.
                blocked.setdefault(current_letter, []).append(syllable)
                # It still stood here in the source, so the left wing has to
                # break at it the way it would for any other word carrying a
                # prohibited letter. Dropping it outright let the chain span a
                # gap and call words consecutive that never were.
                if not collecting_right_wing:
                    left_wing_history.append((word, letters_in_word))
                continue

        # STATE 3: Build word history for consecutive left wing extraction
        elif not collecting_right_wing:
            # Store word in history (will be filtered for consecutive chain when spine word is found)
            left_wing_history.append((word, letters_in_word))

    # Handle any remaining segments at end of text
    if collecting_right_wing:
        selected_right = select_wing_words(right_wing_candidates, WING_MODE)
        if isinstance(selected_right, str):
            current_line_segments.append(selected_right)
        else:
            current_line_segments.extend(selected_right)

    # A line that never reached its final spine letter is still work done, and
    # dropping it loses every letter already presented on it.
    if current_line_segments:
        result_lines.append(' '.join(current_line_segments).strip())

    _warn_if_spine_incomplete(current_letter_idx, blocked)
    return result_lines


def _warn_if_spine_incomplete(current_letter_idx, blocked):
    """Say which letter the walk stopped on, and why, instead of stopping quietly.

    Cage's no-repeat rule can exhaust a letter outright: every Z in Canto I is
    "bronze", so a second pass over the text can never present Z again. Without
    this the generator reads to the end of the source and returns a short poem
    with no indication that anything went wrong.
    """
    position = current_letter_idx % len(target_name)
    if not position:
        return

    letter = target_name[position]
    spent = blocked.get(letter)
    if spent:
        reused = ", ".join(sorted(set(spent)))
        reason = f"every remaining word presenting it reuses an indexed syllable ({reused})"
    else:
        reason = "the source text ran out"
    warnings.warn(
        f"spine incomplete: {letter!r} of {target_name!r} was never presented "
        f"because {reason}",
        stacklevel=3,
    )


if __name__ == "__main__":
    # Hold the warning until the poem is printed, and show it without the
    # file-and-line preamble the default formatter adds.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        mesostic_lines = generate_mesostic()
    for line in mesostic_lines:
        print(line)
    for warning in caught:
        print(warning.message, file=sys.stderr)
