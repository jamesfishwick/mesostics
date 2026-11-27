# What was Cage actually doing?

Notes from comparing this implementation against _Writing Through the Cantos_ (_X: Writings '79-'82_, pp. 109-116). Every number here comes from `just analyse`, which reads Cage's own text rather than anybody's recollection of it.

## The evidence base

198 mesostic lines, 106 spelling EZRA and 92 spelling POUND, carrying 884 spine presentations between them. Each pair of lines carries a margin reference to the page of _The Cantos_ it was drawn from, and those references run from 3 to 782.

Our corpus is Canto I, pages 3 to 5. So exactly one of Cage's pairs is reproducible here, and the rest of the evidence is structural: what his choices have in common, not what we could have chosen instead.

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

Three times he did not, and no filter we have tried explains those three. Searching all sixteen combinations of the four candidate filters, nothing beats taking the first word:

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
