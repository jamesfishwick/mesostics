# What was Cage actually doing?

Notes from comparing this implementation against _Writing Through the Cantos_ (_X: Writings '79-'82_, pp. 109-116). Every number here comes from `just analyse`, which reads Cage's own text rather than anybody's recollection of it.

## What Cage did

Stated as a procedure, with every step backed by a measurement over his own text. Where he made a choice the rule does not force, the step says so rather than inventing a reason.

1. **Read the source once, forward.** One continuous pass through _The Cantos_, front to back, never returning. His margin references climb from page 2 to page 781 with two backward steps in about 190, and his third line pulls `narrow` from page 4 while the rest of that line sits on page 11.

2. **Spell EZRAPOUND down the page, four letters then five.** EZRA on one line, POUND on the next, repeating. 106 EZRA lines and 92 POUND lines.

3. **To present a letter, take some later word containing it and capitalise that letter.** The rest of the word is unconstrained. Every letter-membership rule we tested rejects between 104 and 483 of his own 884 choices: `bronZe` carries R, `beaRing` carries A, `thEn` carries N. ◆ _Which_ word is his choice. He takes the first available one about 60% of the time.

4. **A word may present two letters at once.** Three times across the piece, as in `sEa-jauZionda`.

5. **Never present the same letter with the same word twice.** Across all 884 presentations, zero exceptions.

6. **Between two consecutive spine letters, print no word containing either of them.** 476 of 479 printed wing words obey. ◆ _How many_ of the admissible words to print is his choice: between `bronZe` and `beaRing` the rule allows four and he printed two; after `Arms` it allowed one and he printed none.

7. **The prohibition governs the page, not the path.** He reads straight past prohibited words without printing them. Nine of the seventeen source spans between his first eighteen spine words contain a word carrying a forbidden letter, including the `Pallor` and `upon` he walked over to reach `sheeP`.

8. **Recase everything.** Source capitals are dropped and only the spine letter is capitalised, so the mark is the only capital. Pound's `And` becomes `and`; his `Pluto` becomes `plUto`.

Steps 1, 2, 4, 5, 6 and 8 are mechanical and this implementation now follows all of them. Steps 3 and 6 each carry a ◆, and those two choices are the whole of the remaining gap.

### Three places he slipped

Step 6 holds in 476 of 479 printed wing words. The exceptions:

| word       | carries | line                                                      |
| ---------- | ------- | --------------------------------------------------------- |
| `in`       | N       | `Praise Or sextUs had seeN her in lyDia walks with`       |
| `bull-dog` | U       | `mr P. his bull-dOg me stUrge m;s bull-dog taberNam Dish` |
| `in`       | N       | `toPaze a thrOne having it sqUsh in his excelleNt Dum`    |

Two are the word `in`; the third is a word already printed once on its own line. Small, repeated, easy to skim past when you are doing this by hand.

### What is not yet stated, and why

Which admissible word he picked, and which admissible wing words he printed.

That is a statement about this investigation, not about Cage. He was doing something; we have not found it. Two of his seven independent deviations are words whose own capital is the spine letter, where marking would show nothing. The other five resist every rule tried so far.

The obstacle is statistical power. We can score a hypothesis against eighteen of his choices, because eighteen is as far as the corpus reaches, and six candidate filters over eighteen points will fit noise readily. They do. Widening the search from letter-membership rules to source position and word shape turns up `line-initial + very-short`, which lifts the end-to-end score from 4 of 18 to 7 of 18 and looks like a result.

It is not one. Run that filter against his full output and it rejects 109 of his own 884 spine words, among them `Of`, `thE`, `As`, `tO`, `rUy` and `oN` — several of which sit inside the eighteen it was fitted to. A rule Cage followed cannot reject words Cage chose.

So his 884 presentations are the test set, and `analysis.disqualify()` applies them to any proposed filter:

| filter         | rejects | verdict                                      |
| -------------- | ------- | -------------------------------------------- |
| next-letter    | 104/884 | disqualified                                 |
| segment-future | 298/884 | disqualified                                 |
| name-future    | 483/884 | disqualified                                 |
| invisible-mark | —       | untestable: he recased everything he printed |

Nothing yet survives. `invisible-mark` is the one live candidate and the one we cannot check, because his text does not record which words Pound had capitalised.

What would settle it is more source. Every eight pages or so of _The Cantos_ adds roughly eighteen more of his choices to the training half, while the 884 stay available to disqualify whatever the search turns up. At that point a filter surviving both halves would be worth believing.

### A confusion the larger corpus exposed, since fixed

This project reported 97.9% agreement with CMU without saying what agreed. CMU settles **how many** syllables a word has and says nothing about **where** the boundaries fall, and the two were being quoted as one number.

The cost was not theoretical. Taking pyphen whenever its count matched meant recording `car-din-al`, which indexes `din` for N. The syllabification is `car-di-nal`, which indexes `nal`. So `cardinal` and `jardin` both indexed `din`, the run called the second a repeat, and one of Cage's own words was blocked. That is how the confusion surfaced.

Both halves are now measured separately:

| claim                         | ground truth                      | result               |
| ----------------------------- | --------------------------------- | -------------------- |
| how many syllables a word has | CMU, 124,892 entries              | **98.9%**            |
| where the cut falls           | maximal onset, hand-checked words | `test_boundaries.py` |

A maximal-onset splitter now leads the candidates, so the cut goes where the phonology puts it rather than where a printer may break a line. Count agreement rose from 97.9% to 98.9% as a side effect.

The word-level result above, that Cage never reused a word to present a letter, rests on exact string equality and was never affected. Syllable-level claims now rest on a stated convention rather than an unexamined one.

## The evidence base

198 mesostic lines, 106 spelling EZRA and 92 spelling POUND, carrying 884 spine presentations between them. Each pair of lines carries a margin reference to the page of _The Cantos_ it was drawn from, and those references run from 3 to 782.

`corpus/cantos_pp3-152.txt` carries printed pages 3 to 152 of the New Directions edition, Cantos I to XXX, 28,387 words. Those cantos were published in 1925 and 1930 and are out of US copyright. They cover 313 of Cage's 884 spine choices, up from the 18 that Canto I alone could reach. The rest of the evidence is structural: what his choices have in common, not what we could have chosen instead.

**He read the source continuously.** The margin reference marks where a pair _ends_, not a window he jumped to. His third line opens `thE narrow glaZes the uptuRned nipple As`, and `narrow` is not on page 11 at all: it is Canto I's "Unsheathed the narrow sword", back on page 4. The rest of that line is page 11. So he carried straight on from where the previous pair stopped.

## Cage kept his own rule, and we can say how closely

> I did not permit the appearance of either letter between two of the name.

Of the 479 words Cage printed between two spine letters, **476 obey this**. Three do not:

| word       | carries | line                                                      |
| ---------- | ------- | --------------------------------------------------------- |
| `in`       | N       | `Praise Or sextUs had seeN her in lyDia walks with`       |
| `bull-dog` | U       | `mr P. his bull-dOg me stUrge m;s bull-dog taberNam Dish` |
| `in`       | N       | `toPaze a thrOne having it sqUsh in his excelleNt Dum`    |

Two are the word `in`, and the third is a word already used once on its own line. These read as oversights rather than a hidden sub-rule: small, repeated, easy to skim past when you are doing this by hand in 1982.

> I kept an index of the syllables used to present a given letter of the name and I did not permit repetition of these syllables.

Across all 884 presentations, **no word is ever reused to present the same letter**. Not once. At the syllable level our splitter finds 38 apparent repeats (`zes` four times across `bonzes`, `bonzesses`, `glazes`, `prizes`), but that test is confounded: Cage indexed by ear and we cannot know that his syllable boundaries were ours. The word-level result is the airtight one, and it is perfect.

So the rule is real, Cage followed it, and his hand-accuracy over 800 pages of Pound was 99.4% on the part we can check exactly.

## Nothing constrains which word presents a letter

The obvious hypothesis is that a spine word may not carry letters it has no business carrying. Tested against Cage's own 884 choices, every version of that idea fails:

| proposed rule                                            | Cage's own words that survive it |
| -------------------------------------------------------- | -------------------------------- |
| does not carry the very next letter of the name          | 780/884 (88.2%)                  |
| carries no letter from later in its own half of the name | 586/884 (66.3%)                  |
| carries no letter from later anywhere in the name        | 401/884 (45.4%)                  |

A rule should reject none of his choices. These reject between 104 and 483 of them. `bronZe` carries R, `beaRing` carries A, `thEn` carries N. There is no letter-membership test here.

This kills the hypothesis the README carried for a long time, and it kills it using Cage's text rather than argument.

## So what did he do? He chose.

For the one pair we can reproduce, here is where Cage's choice sat among the words the rule actually allowed him:

| letter | took    | rank  | options | passed over  |
| ------ | ------- | ----- | ------- | ------------ |
| E      | then    | 1     | 276     |              |
| Z      | bronze  | 1     | 2       |              |
| R      | bearing | 1     | 84      |              |
| A      | arms    | 1     | 105     |              |
| P      | sheep   | **3** | 35      | pallor, upon |
| O      | of      | 1     | 88      |              |
| U      | pluto   | **2** | 48      | poured       |
| N      | strong  | 1     | 97      |              |
| D      | praised | **2** | 69      | and          |

**Six times out of nine he took the first word available.** That is what this implementation does, and it is why the EZRA line comes out exactly right.

### Scoring a whole run understates the agreement

Run end to end against his first four lines, this implementation scores 4 of 18. That number is close to meaningless. One different choice moves the cursor, and every later letter is then picked from a different stretch of text, so a single disagreement at P drags eighteen letters down with it.

Correcting as we go separates the decisions Cage really made differently from the cascade behind them:

|                                      |              |
| ------------------------------------ | ------------ |
| letters where we pick his word first | **11 of 18** |
| independent deviations               | **7**        |

Over the full Cantos I-XXX corpus, with the cursor anchored to his position at every step so no disagreement can drag later letters with it:

|                                                    |               |
| -------------------------------------------------- | ------------- |
| choices compared                                   | **313**       |
| where we would pick his word                       | **164 (52%)** |
| not alignable (absent from the scan, OCR variants) | 8             |

The eighteen-letter sample said 61%. At 313 it is 52%, so the small sample was mildly optimistic but not misleading. He takes the first admissible word slightly more often than not, and the implementation is far closer to him than a naive end-to-end score suggests.

### The seven deviations

| letter | he took | he passed over |
| ------ | ------- | -------------- |
| P      | sheep   | `Pallor`, upon |
| U      | Pluto   | `Poured`       |
| D      | praised | and            |
| E      | the     | `Proserpine;`  |
| Z      | glazes  | azure          |
| P      | speak   | `Poggio`       |
| D      | goods,  | and            |

Two of the seven are words whose own initial capital _is_ the spine letter, so marking them would show nothing: `Pallor` and `Poggio`. That is a real pattern and it covers the case this project has argued about longest. It does not cover the other five.

What the other five have in common is softer. Cage's lines read as near-continuous source phrases: `glaZes the uptuRned nipple As` is a straight lift from "The silvery water glazes the upturned nipple. As Poggio has remarked", and `sPeak tO rUy oN his gooDs` runs along "no man speak to, feed, help Ruy Diaz, On pain... and all his goods sequestered". The words he passed over are scattered earlier in the text and would have broken the phrase. That is an aesthetic criterion, not a mechanical one, and this project cannot test it.

Searching all sixteen combinations of the four candidate filters, nothing beats taking the first word:

```
4/9  (none)
4/9  invisible-mark
1/9  segment-future
1/9  next-letter
```

The wings tell the same story. Between `bronZe` and `beaRing` the rule permits four words; Cage printed two. After `Arms` it permits one; he printed none. Nothing in his stated rule picks `lance heads` over `Battle spoil`.

## The conclusion

Cage's method is a constraint plus a choice, and only the constraint is written down. He told us what he would not permit. He never claimed the rule determined the result, and the evidence says it did not: it left him 35 ways to present P and he took the third.

That reframes what this program can be. A faithful implementation reproduces the _admissible set_ — and ours does, since Cage's choices are inside our candidate lists every time. It cannot reproduce the selection, because the selection was Cage's.

4 of 9 is therefore not obviously a bug. It is what first-match scoring looks like against a poet who took the first match two thirds of the time.

## Still open

Why those three? `pallor` is the one candidate in Canto I whose own initial capital is the spine letter, so marking it would be invisible — an appealing explanation, and all nine of Cage's picks avoid that property. But it only rules out `pallor`; the implementation then takes `upon`, and the score does not move. It also cannot be checked against his wider text, because he recased everything he printed.

Testing this properly needs more corpus. The margin references say exactly which pages to add: page 11 unlocks his third line, pages 14-15 the fifth, and so on.

## Reproducing all of this

```bash
just compare    # our spine against Cage's, letter by letter
just analyse    # every measurement in this document
```

The audits over all 198 lines need Cage's text, which is not in this repository: it is a copyrighted 1982 work. `cage.extract_from_pdf()` rebuilds it from a copy of the book into `reference/`, which is outside version control.
