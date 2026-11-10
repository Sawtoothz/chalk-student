# Highlight spec

The annotated PDF is how Aun reads the chapter. The highlights decide what he looks at; the notes
decide what he thinks while looking. Both are produced from `highlights.json` by
`scripts/highlight_pdf.py`.

## File shape

```json
{
  "book": "thrun-pr", "chapter": 3, "printed_pages": [39, 84], "page_offset": 21,
  "colors": {"define": "#9FE1CB", "key": "#FAC775", "derive": "#F09595", "pitfall": "#F5C4B3", "link": "#B5D4F4", "section": "#D3D1C7"},
  "items": [
    {"page": 41, "kind": "key", "anchor": "exact words from the page", "note": "..."},
    {"page": 41, "kind": "derive", "equation": "3.4", "note": "..."},
    {"page": 42, "kind": "derive", "anchor": "Table 3.1", "note": "..."},
    {"page": 43, "kind": "section", "anchor": "3.2.2", "note": "Must read. ..."}
  ]
}
```

`page` is the printed page. `anchor` is copied from `page.get_text()` of that page, ligatures and
hyphenation as they come (the script normalises). `equation` boxes the block that carries the label
`(3.4)`. A table is boxed by anchoring its caption (`"Table 3.1"`).

## Categories

| kind | colour | use for |
| --- | --- | --- |
| define | green | a definition, an assumption, a symbol's meaning and shape |
| key | yellow | the sentence that carries an idea, a result, a figure caption worth reading twice |
| derive | red box | an equation or algorithm table Aun will implement or derive by hand |
| pitfall | orange | where the method fails, an assumption that robots violate, a classic bug |
| link | blue | an explicit bridge to another lesson, a library (GTSAM, acados), or one of Aun's projects |
| section | gray note icon | one per section heading: the verdict and the one thing to take |

## Density

- Must-read pages: 3–6 items. Skim pages: 1–2. Skip pages: the section note only.
- Never more than about 15% of a page's text. A page that is half yellow teaches nothing.
- Every boxed equation that the exercises implement, every algorithm table, every figure caption
  that the lecture refers to.

## Notes

A note is 1–4 sentences. It says why the passage matters, not what it says. Use the labelled
structure when there is more than one thing to say; the Reader renders the labels in bold:

- `WHY:` the idea behind the passage, in Aun's terms.
- `ROBOT:` where this bites on the tracked robot, quadruped, drone, FORGE, or the RoboCup map.
- `CODE:` the card (`C2`) or function (`kf_update`) where it lives.
- `TEST:` the test that proves it.
- `FIGURE:` how to read a figure, panel by panel.
- `COST:`, `PITFALL:`, `DEFINE:`, `SHAPES:`, `SESSION:`, `READING:`, `EXERCISE:` as needed.

A section note starts with the verdict: `Must read, 15 min.`, `Skim.`, `Skip for now; covered in
t2.6.` and then the one thing to take.

## Rules

1. Anchor words, not paraphrases. If `highlight_pdf.py` reports UNMATCHED, look at the page text and
   copy the exact run of words.
2. Anchors are unique on their page and at least four words long, unless the anchor is a heading,
   a table caption, or a margin keyword.
3. The note must be about what the anchored sentence says. A note about symmetry loss on a sentence
   about cost is wrong even if both are true (reviewer catch, ch. 3).
4. A note that quotes a number states where the number comes from (book page, or a run).
5. Attribute: if the note says "the book says", it must; if it is common practice from elsewhere
   (UKF α ranges, NEES bands), say so.
6. Flag print errors in the book when you find them (ch. 3 eq. 3.64 Σ̄ₜ₋₁ for Σ̄ₜ).

## Checklist before running the script

- [ ] Every must-read section has a section note.
- [ ] Every algorithm table is boxed.
- [ ] Every equation listed under "implement" in `map.md` is boxed with a note naming its card.
- [ ] Every figure the lecture refers to has a FIGURE note on its caption.
- [ ] The chapter's exercises each have a note pointing to where the package handles them.
