# Premise note — do non-source files appear as legitimate localization targets?

**Resolution (for the introduction). Checked 2026-09-06.**

## The question

A SANER reviewer wrote that they would not expect a bug-localization tool to
identify test files, and questioned the motivating example on that basis. Do
existing IR-based bug-localization (IRBL) benchmarks treat non-source files
(configuration, test data, schemas, build scripts) as ground-truth localization
targets?

## What the evidence says

**Mainstream IRBL benchmarks are source-only by construction.** Bench4BL — the
standard reproducibility benchmark, 51 Java projects, ~10,000 bug reports,
~61,000 files — indexes and scores **Java files only**; its ground truth is the
set of `.java` files changed by the fix. Earlier IRFL datasets (moreBugs, the
five "classic" projects) are likewise single-language.

**The dataset-quality literature actively treats non-source and test files in
ground truth as noise to be removed.** Work on whether IRBL datasets are
trustworthy reports that a substantial share of bug reports are linked to
non-buggy files, and that **test files in ground truth are a recognised data
quality issue** — including them changes MAP by up to +21 % and MRR by up to
−13 %. The recommended practice is to distinguish production bugs from
test-related bugs and to validate ground-truth entries, i.e. to *narrow* ground
truth toward source code, not widen it.

**BeetleBox is the deliberate exception.** It is the only public IRBL dataset
whose ground truth spans multiple languages and file types (source, scripting,
build, configuration, data, schema, test/spec), which is why this study uses it.
In our six projects, **every counted secondary file is also a ground-truth
localization target** — the polyglot files are what the developer had to locate
and change, not incidental edits.

## Consequence for the framing

The study does **not** claim that a localization tool *ought* to rank a
`.yml`/`.json`/`.sql` file. The mainstream field has not asked tools to. The
claim is narrower and descriptive:

> A class of fix exists whose ground truth spans languages. When a benchmark's
> ground truth includes such files (BeetleBox does), techniques that parse source
> into a structured representation cannot represent them at all, whereas classical
> retrieval can. The gap is between **what a fix contains** and **what an
> evaluation reaches**, not between what a tool does and what it should do.

The introduction states this explicitly, and positions the motivating example as
"here is a real fix whose ground truth, as recorded by the dataset's authors,
crosses file types" — not "here is something a tool is failing to do."
