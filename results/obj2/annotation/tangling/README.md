# Tangling audit

Question: is each counted fix file part of the fix for its bug, or there for
another reason (a "tangled" commit; Herzig and Zeller 2013)? In the study every
counted file of the fix commit is ground truth and decides the class, so an
unrelated secondary file would both create a Poly-fix bug and add to its penalty.

| Path | What |
|---|---|
| `sample.csv` | the sampled test bugs: 5 Poly-fix + 3 Mono-fix per project, 48 bugs, seed 20261122 |
| `handout/tangling_A.xlsx` | all 48 bugs, 175 files: the main audit (one author) |
| `handout/tangling_B.xlsx` | 12-bug subset (8 Poly-fix, 4 Mono-fix), 37 files: independent second coder |
| `returned/` | put the filled workbooks here, names unchanged |

Workbook sheets: `Start here` (instructions and the yes/no/unsure criteria),
`1_files` (one row per file with a direct link to its diff on GitHub, line
counts, role; fill `part_of_fix`, `unrelated_kind` if no, `notes`), `2_bugs`
(report title and excerpt, issue and commit links, commit message; fill
`commit_tangled`), `log`.

## Steps

1. Coder A (author) fills `tangling_A.xlsx` (about 2-3 h). Coder B fills
   `tangling_B.xlsx` alone (about 40 min). No discussion before both return.
2. Save both into `returned/` and run

       python Scripts/tangling_workbook.py import

   It writes `tangling_report.md`: share of unrelated files (primary vs
   secondary, Poly-fix vs Mono-fix), Poly-fix bugs whose class would change,
   Cohen's kappa A vs B on the 37 overlapping files, and each technique's
   Poly-fix minus Mono-fix MAP on the audited bugs before and after removing the
   unrelated files from the ground truth.
3. The result replaces the PENDING marker in the paper's Threats (construct
   validity).

Built by `python Scripts/tangling_workbook.py make`.
