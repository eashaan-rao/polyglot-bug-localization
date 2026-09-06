# Mono-fix or Poly-fix? On the Prevalence and Localizability of Multi-Language Bug Fixes

Objective 2 of the thesis. An exploratory study of how bug-localization
techniques behave when a single bug fix touches files in more than one
programming language.

- **Design spec:** `obj2/Polyglot_BL_FSE_Brief.pdf`
- **Superseded:** `obj2/BL-Polyglot.pdf` (rejected SANER 2026 registered report; background only)
- **Working notes:** `CLAUDE.md`

## Study in four steps

1. **Prevalence** — what proportion of fixes are Poly-fix, and what file types do
   the additional files belong to. Descriptive; no model.
2. **Architectural feasibility** — for each technique, which Poly-fix file types
   can it ingest at all. Binary per technique per file type.
3. **Within-project performance** — Mono-fix vs Poly-fix localization, controlled
   by comparing within the same project; plus a same-language cross-project arm.
4. **Classical baseline** — on Poly-fix bugs, does classical retrieval hold where
   the parsing techniques fail or degrade.

Retrieval recall by class is reported as a property of the setup, not a research
question.

## Data

Six BeetleBox projects (3 Java, 3 Python). Repos, fp32 BGE embeddings and the bug
report table are copied under `data/` (git-ignored). See `Scripts/paths.py`.

## Reproducing

```bash
source /home/cs21d002_eashaan/PhD/Objective1/obj1/bin/activate
pip install rank_bm25 pyyaml
python Scripts/extract_fix_commits.py
# freeze Scripts/classification_rules.py + docs/CLASSIFICATION_RULES.md, then:
python Scripts/classify_bugs.py
python Scripts/prevalence_report.py
python Scripts/boundary_sensitivity.py
python Scripts/feasibility_matrix.py
python Scripts/retrieval_recall_by_class.py
python Scripts/run_obj2_experiments.py
python Scripts/analysis/obj2_wp_analysis.py
python Scripts/analysis/obj2_classical_vs_parsing.py
```

## Artifact

The labelled Mono-fix/Poly-fix classification for every bug in the six projects
(`results/obj2/bug_classification.csv`) is the reusable asset and is released
independently of the model results.
