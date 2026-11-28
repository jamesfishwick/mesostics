# What Cage did

Measured from _Writing Through the Cantos_ (_X: Writings '79-'82_, pp. 109-116) against Pound's _Cantos_. Every figure here is recomputed by `test_documented_figures.py` and checked against this text, so a number cannot go stale without the suite noticing.

## The rule set

| # | rule                                                       | evidence                                                  | standing         |
| - | ---------------------------------------------------------- | --------------------------------------------------------- | ---------------- |
| 1 | Read the source once, forward, never returning             | his page references climb 2 to 781 with one backward step | certain          |
| 2 | Spell EZRAPOUND down the page, four letters then five      | 112 EZRA lines, 110 POUND                                 | certain          |
| 3 | A word may present two letters at once                     | once, in Pound's `Ritz-Carlton`, carrying Z and R         | certain          |
| 4 | Never present a letter with a syllable already spent on it | 998 presentations, one reuse                              | certain, 1 slip  |
| 5 | Between two spine letters, print no word carrying either   | 532 of 535 printed wing words                             | certain, 3 slips |
| 6 | Recase, so the mark is the only capital                    | `And`→`and`, `Pluto`→`plUto`                              | certain          |
| 7 | Of the words that could present a letter, take one         | a draw made per letter                                    | **modelled**     |
| 8 | Of the words you may print beside it, print some           | a draw made per span                                      | **modelled**     |

Rules 5 and the second half of 4 are the two he wrote down. The other six are in the poem and not in his sentence.

## What he stated

Two sentences, page 109:

> I did not permit the appearance of either letter between two of the name.

> I kept an index of the syllables used to present a given letter of the name and I did not permit repetition of these syllables.

The first governs the page, not the reading. He walks past forbidden words without printing them: nine of the seventeen source spans between his first eighteen spine words contain a word carrying a letter he could not print, `Pallor` and `upon` among them. Read as a claim about the source text it would be false of his own work.

## Rule 7, which word presents a letter

Drawn afresh at every letter. Three times in four he takes a candidate at 0.60; otherwise at 0.23, walking past five or six.

| rank of his choice | the rule | Cage  |
| ------------------ | -------- | ----- |
| first              | 51.1%    | 53.6% |
| second             | 21.9%    | 19.1% |
| third              | 10.5%    | 12.8% |
| seventh            | 1.3%     | 1.3%  |
| twelfth or deeper  | 1.5%     | 1.6%  |

One rate will not do: fitted to his distribution it scores chi-square 26.1 on 6 degrees of freedom, p=0.0002, against 6.6 on 5 for two.

Two components are not two moods. A mood persists, and a runs test puts his alternation within one standard deviation of independence at every threshold tried, z between -0.34 and +1.15. Whatever sets his selectiveness is consulted once per letter and forgotten, which is a procedure rather than a temperament, and chance operations were his practice for thirty years before this piece. The measurement gives the shape of the draw and not the procedure behind it.

No property of the words separates the 678 candidates he declined from the 319 he took. A rate explains a distribution and never an instance: asking why he took one word rather than another is asking which atom decays next.

**11 of 18** letters are ones this implementation picks first as well, with **7** independent deviations, measured on his first four lines with the cursor anchored to his position so no single disagreement drags the rest.

One weak tendency does survive: comparing the word he took against the candidates he declined beside it, his is the less-capitalised one in 55 spans of 81, p=0.0017. It is not a rule. 84 of his 323 choices are capitalised in Pound, `Pluto` among them.

## Rule 8, the wings

|                          |                             |
| ------------------------ | --------------------------- |
| allowed wing words       | 15,189                      |
| printed                  | 224, or 1.5%                |
| spans receiving any wing | 50 of 287, about one in six |

Whether a span is decorated is drawn per span, a runs test placing it at z=-1.15. How many words go in is a two-component draw, one rate scoring chi-square 12.5 on 3 degrees of freedom against 1.5 on 1. Where they sit is not uniform: the last fifth of a span holds 62 of 217 printed words against 43 expected, p=0.011, so he leans toward the words just before the next spine word.

These rest on 50 decorated spans where rule 7 rests on 315 choices. Read them as the shape of the thing rather than its measurement.

## Where he slipped

Four times in 1,533 opportunities.

| rule | slip                                                                      |
| ---- | ------------------------------------------------------------------------- |
| 5    | `in` carries N between N and D                                            |
| 5    | `bull-dog` carries U between U and N, a word already printed on that line |
| 5    | `in` carries N between U and N                                            |
| 4    | `Pit` presents P twice                                                    |

## Two claims his text denies

**A 45-character limit per wing.** The README takes it from two secondary sources and the generator applied it on every mode until this was measured. Against his own 471 non-empty wings:

|               |                   |
| ------------- | ----------------- |
| median wing   | **4 characters**  |
| longest wing  | **28 characters** |
| wings over 45 | **0**             |

It never binds. Reading it as a rule gets his practice backwards: what needs explaining is why he prints so little, not what stopped him printing more.

**That walking past a word spends it.** An earlier version of the README said a word carrying the letter being sought could not be passed over and used later. He does it ten times: `from` and `over` present R, `ship` and `pay` present P, each after he had walked past them while seeking that letter. The index records what was used to present a letter, not what was seen.

## Reading the markup

`just trace 30` gives every source word he covered one verdict.

| verdict  | meaning                                                          | words |
| -------- | ---------------------------------------------------------------- | ----- |
| SPINE    | he marked it, and it presents a letter                           | 146   |
| DECLINED | it could have presented the letter sought, and he walked past it | 379   |
| SPENT    | it carries the letter sought, but that syllable was used         | 26    |
| BLOCKED  | it carries one of the two letters in play                        | 4,015 |
| PASSED   | the rule allowed it as a wing and he did not print it            | 6,612 |
| PRINTED  | the rule allowed it as a wing and he printed it                  | 28    |
| TIED     | the span holds several spelt alike, one of which he printed      | 79    |

Every decision he made is recoverable. The rule forces 36% of the words by forbidding them or having spent their syllable; alignment places the rest, since the words he printed appear in source order and embed into the span's allowed words as a subsequence. TIED is open provenance rather than an open decision: where his wing holds one `with` and the span holds ten, both counts come from his text and the two readings give the same line.

DECLINED is the column that matters. His stated rules forbade none of those 379 words, and none was printed as a wing in its own span. The P this project argued over longest is three rows:

| #   | word     | verdict                                   |
| --- | -------- | ----------------------------------------- |
| 260 | `Pallor` | DECLINED, could have presented P as `pal` |
| 261 | `upon`   | DECLINED, could have presented P as `pon` |
| 273 | `sheep`  | SPINE, presents P with syllable `sheep`   |

## The texts

`corpus/cantos_pp3-152.txt` is printed pages 3 to 152 of the New Directions _Cantos_, Cantos I to XXX, 28,365 words, from an Internet Archive scan. Those cantos were published in 1925 and 1930 and are out of US copyright. His margin references map to the scan by a constant offset of 8, confirmed at printed pages 11, 179 and 328 by finding his own words there; by page 472 the offset is 28, and that drift begins well past 152. Accuracy over the stretch where a hand-typed text exists for comparison is 99.5%. They cover **315** of his 998 spine choices, and of those this implementation would pick his word **168 (53%)** of the time, measured with the cursor anchored to his position at each step.

His own pages are read twice and neither reading is kept alone. The PDF's text layer gets words right and loses capitals, and a capital is what marks the spine: one line arrives with the R of `secuRities` gone, so it spells EZA and is unusable. Rendered at 400 dpi and read again it recovers 222 lines and 998 presentations from 198 and 884, every margin reference legible where 141 of 198 were before. It pays with word errors of its own, `pluto` as `piuto`, which desync a forward-only alignment against Pound. So questions about his own text go to the re-read and questions that align him to Pound go to the text layer.

Two of his tokens still resist placement, `sEa-jauZionda` and `uP-Other`. Neither is damage: they are two spine words each, joined by a hyphen he put between spine words that sit together with no wing between them. Pound has `sea` on page 21 and `jauzionda` on page 22, and `up-stairs` with `other` further on; neither hyphenated form occurs anywhere in the Cantos. Only `ritz-carlton` does, which is why rule 3 stands at one case rather than three.

## Syllables

Cage's index records the syllable that presents a letter, so the split has to be right or the constraint misfires in both directions. Two different claims live here and this project once blurred them.

**How many** syllables a word has: CMU settles it, and agreement rises from pyphen's 53.4% to **98.9%** over its 124,892 scoreable entries, with no word losing characters to the split. The residue is initialisms such as `abc`, three syllables aloud with no orthographic boundary to find.

**Where** the boundaries fall: CMU says nothing, so this needs its own ground truth. The convention is maximal onset, held to hand-checked words in `test_boundaries.py`. Getting the count right does not get the cut right: pyphen offers `car-din-al`, a fair place to break a line and the wrong place to split a syllable, which collided with `jar-din` in the index and blocked one of his own words.

## Reproducing all of this

```bash
just run        # generate a mesostic by his method
just compare    # our spine against his, letter by letter
just analyse    # every measurement in this document
just trace 30   # the markup, word by word
just model      # his method as a rule, against what he did
just test
```

The audits over all of his lines need his text, which is not in this repository: it is a copyrighted 1982 work. `cage.extract_by_ocr()` rebuilds it from a copy of the book into `reference/`, which is outside version control.
