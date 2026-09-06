# Premise note — do non-source files appear as legitimate localization targets?

**To be settled in one paragraph before the introduction is drafted.**

A SANER reviewer wrote that they would not expect a bug-localization tool to
identify test files, and questioned the motivating example on that basis. This
note answers the objection with evidence rather than leaving it.

## The question

Do existing IR-based bug-localization benchmarks already treat non-source files
(configuration, test data, schemas, build scripts) as ground-truth localization
targets — or is the study asking tools to find files the field has never asked
them to find?

## Evidence to assemble

1. **BeetleBox ground truth.** Tabulate the extension distribution of
   `ground_truth_files` across the six projects (already sketched during
   exploration: `.json`, `.yml`, `.sql`, `.xml`, `.gradle` all appear in
   thousands of ground-truth entries). This shows the dataset's own authors
   included them.
2. **Bench4BL / prior IRBL datasets.** Check whether their ground truth is
   source-only by construction (filtered to `.java`) or admits other types.
3. **The localization literature's own filtering.** Several IRBL papers restrict
   ground truth to the primary language explicitly; cite them. This is the
   "monolingual assumption" the study names.

## The two framings, and which the evidence supports

- **If non-source files do appear** as ground truth in existing benchmarks, the
  study reports what techniques do with files the benchmarks already contain —
  a measurement of current practice.
- **If they do not** (source-only by construction everywhere), the framing
  narrows: the study is about what *fixes contain*, and the gap is between what a
  fix touches and what an evaluation reaches, not about what a tool "should" find.

Either way the study is descriptive. State the resolution here, cite it in the
introduction, and do not claim tools "ought to" find these files unless the
literature already does.
