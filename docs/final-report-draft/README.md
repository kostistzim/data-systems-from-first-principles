# Final Report Draft

This folder contains a compact LaTeX draft for the final MLStore-Lite report.

The user's DTU template imports:

```tex
\import{}{Content/Part1.tex}
\import{}{Content/Part2.tex}
```

The files in this folder follow that structure:

- `Content/Part1.tex`
- `Content/Part2.tex`
- `final-report.md`
- `results.md`
- `sequential-recommender.md`
- `model-card.md`

The draft is intentionally concise so it can fit within a 10-page limit after
front page, table of contents, and formatting are applied.

Suggested page budget:

- front page and table of contents: template-controlled
- Part 1: about 3-4 pages
- Part 2: about 3-4 pages
- optional references/appendix: only if required

Avoid adding long code listings to the main report. Use short architectural
snippets and refer to the repository for implementation details.

The sequential recommender material is optional report material. It is useful
if the final submission needs a stronger AI extension, but it should still be
summarized briefly to stay within the 10-page limit.

For reproducing the local results, use the project runbook:

```text
../runbook.md
```

The shortest verification command is:

```bash
make quick
```

The full local verification command is:

```bash
make all
```
