"""Boundary placement, measured rather than assumed.

Counting syllables correctly and cutting them in the right place are separate
claims. The CMU dictionary settles the first and says nothing about the second,
so the second needs its own ground truth.

The convention here is maximal onset: the consonants between two vowels join
the following syllable as far as English phonotactics allow, and whatever is
left closes the syllable before. That is the phonological convention, and it
is the one an index keyed on sound wants. A hyphenator answers a different
question, which is why pyphen offers "car-din-al".
"""

import pytest

from syllables import syllabify

# Hand-checked. Each entry is uncontroversial under maximal onset.
GOLD = {
    "about": "a-bout", "abdicate": "ab-di-cate", "address": "ad-dress",
    "aardvark": "aard-vark", "agenda": "a-gen-da", "apple": "ap-ple",
    "astronaut": "as-tro-naut", "attract": "at-tract", "cardinal": "car-di-nal",
    "central": "cen-tral", "children": "chil-dren", "complete": "com-plete",
    "degree": "de-gree", "deny": "de-ny", "disgrace": "dis-grace",
    "doctor": "doc-tor", "extra": "ex-tra", "glazes": "gla-zes",
    "hamster": "ham-ster", "happy": "hap-py", "hundred": "hun-dred",
    "jardin": "jar-din", "mattress": "mat-tress", "mister": "mis-ter",
    "money": "mo-ney", "monster": "mon-ster", "nostril": "nos-tril",
    "panther": "pan-ther", "pilgrim": "pil-grim", "pluto": "plu-to",
    "regret": "re-gret", "repay": "re-pay", "secret": "se-cret",
    "silent": "si-lent", "table": "ta-ble", "umbrella": "um-brel-la",
    "window": "win-dow",
}


@pytest.mark.parametrize("word", sorted(GOLD))
def test_boundary_placement(word):
    assert "-".join(syllabify(word)) == GOLD[word]


def test_a_medial_s_closes_the_syllable_before_it():
    """"st" opens a word but not a syllable inside one."""
    assert syllabify("mister") == ["mis", "ter"]
    assert syllabify("stop") == ["stop"]


def test_a_doubled_consonant_splits():
    assert syllabify("happy") == ["hap", "py"]
    assert syllabify("table") == ["ta", "ble"]


def test_hyphenation_points_are_not_syllable_boundaries():
    """The case that exposed the difference: it collided with "jar-din"."""
    assert syllabify("cardinal") == ["car", "di", "nal"]
