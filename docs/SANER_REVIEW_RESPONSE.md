# Response to the SANER 2026 reviews

Submission 351, "The Monolingual Assumption: A Diagnostic Study of Bug
Localization in Polyglot Software Systems" — rejected (R1 -2, R2 -2, R3 0).
The idea was not rejected: R1 and R2 called the topic interesting and relevant,
R3 called it original and relevant. The objections were to the protocol and the
writing. Each is mapped below to a concrete change in the rebuilt design.

| # | Objection | Reviewer(s) | Resolution |
|---|---|---|---|
| 1 | RQ0 "retrieval ceiling" is incoherent given ground-truth files are force-included in the candidate set | R1, R2 | RQ0 removed. Retrieval recall is computed per class and **reported as a property of the setup**, before any reranker result, never as a research question. |
| 2 | The 95% byte-count threshold is arbitrary; a project labelled "monolingual" (elastic/elasticsearch) still contains Poly-fix bugs — an internal-validity threat to H1.2 | R1 | Project-level classification is **dropped**. The unit of analysis is the fix. Mono/Poly is decided from the files in the fix commit. A project of any language composition can contain Poly-fix bugs without contradiction. |
| 3 | A controlled experiment is the wrong design for diagnostic/exploratory questions; the paper is undecided between exploratory and confirmatory | R2 | The study is **declared exploratory**. Descriptive research questions; no hypothesis tree; effect sizes with confidence intervals; a statistical test only where a specific comparison calls for one. |
| 4 | Hypotheses assume the outcome of earlier hypotheses (H3.1 depends on H2.1) | R2 | Four **independent** steps. Each is answerable and reportable on its own; a null result at any step is a finding. |
| 5 | The data-leakage threat (BeetleBox was built alongside BLAZE) is not acknowledged | R3 | Handled in the **method**, not in threats. BLAZE is retained but reported in its own column and never aggregated with the other techniques. The choice is stated where the techniques are introduced. |
| 6 | The Java/Python-only restriction is not motivated — technical constraint or design choice? C++ excluded without explanation | R1, R2, R3 | `PROJECT_SELECTION.md` states it as a **design choice** (one statically-typed, one dynamically-typed mainstream ecosystem) and records the **technical** note that the parsing techniques ship Python and Java AST support. The C++/Go/JS exclusion and its rationale are recorded. |
| 7 | Terms used before or without definition: "valid", "extension", FAISS, C@K, Top-K, Perf_AST/Perf_Text/Perf, "architectural limitation", "non-parsable", "unsafe", cold start, lexical gap | R1, R2, R3 | `GLOSSARY.md` defines every term before first use; `REGISTER_RULES.md` enforces define-before-use. Unused formal notation is removed. |
| 8 | FLIM is labelled language-agnostic although it parses ASTs, contradicting the paper's own definition | R1 | Directly resolved: FLIM **is used and is classified as a parsing / structure-dependent technique**, because it requires an AST parser. The three categories are defined precisely — classical IR (BM25), language-agnostic (BLAZE, ranks raw tokens), parsing (FLIM, COOBA). |
| 9 | "96% of projects are polyglot" — does the figure count markdown and documentation? | R2 | Where the prevalence of polyglotism is cited, the paper states exactly what is counted. The study's own prevalence figure excludes documentation, generated and vendored files per the boundary rules, and is reported with a sensitivity range. |
| 10 | The motivating example (a localization tool identifying test files) is unconvincing — "I would not expect a tool to identify test files" | R1 | `PREMISE_NOTE.md` settles, from existing benchmarks' own ground truth, whether non-source files already appear as legitimate localization targets. If they do not, the framing narrows to what fixes contain rather than what tools should find. Written before the introduction. |
| 11 | "models" and "techniques" are used interchangeably | R1 | One term ("technique") used throughout. |
| 12 | No structured abstract | R2, R3 | A registered-report requirement; the target venue is not a registered-report track. The venue's abstract format is followed; the point is noted so a SANER-aware reader is not surprised. |
| 13 | Sample size / power: with 17 projects, is the study powered? | R2 | The study is descriptive. Effect sizes with confidence intervals replace power analysis. Scope (6 projects, 2 languages, 1 dataset) is stated as a narrow-generalisation limitation, not defended as powered. |
| 14 | "First comprehensive investigation", "will reveal key limitations" — claims before any result | R2, brief | Removed. See `REGISTER_RULES.md`. |
| 15 | Set-difference written as division; equations in Section IV never used again | R1, R3 | Formal notation kept only where it is used; natural-language definitions otherwise. |

## Objections not fully resolved (stated honestly)

- **Single dataset (BeetleBox).** Still the only public dataset with multi-language
  fix ground truth. Acknowledged; generalisation claimed narrowly.
- **One parsing technique per arm** (FLIM within-project, COOBA cross-project)
  rather than one technique across both. A consequence of COOBA's transfer-only
  architecture. Recorded in threats to validity.
