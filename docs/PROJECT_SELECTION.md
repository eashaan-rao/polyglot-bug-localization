# Project selection

## The six projects

| Project | Language | BeetleBox bug reports (in `bug_reports_clean.parquet`) |
|---|---|---|
| elastic/elasticsearch | Java | 970 |
| liquibase/liquibase | Java | 241 |
| apache/dolphinscheduler | Java | 1369 |
| ansible/ansible | Python | 768 |
| apache/airflow | Python | 1648 |
| localstack/localstack | Python | 472 |

(Counts are the raw parquet totals; the classification pipeline filters to bugs
with recoverable fix commits and in-scope ground-truth files.)

## Inclusion criteria (applied before selection)

1. Source dataset is BeetleBox (the only public dataset with multi-language fix
   ground truth).
2. Project primary language is Java or Python.
3. At least 100 bug reports, so each of the Mono-fix and Poly-fix partitions is
   large enough for within-project comparison after balanced subsampling.
4. Repository and fp32 BGE embedding database already built (from Objective 1),
   so the retrieval stage needs no new multi-day embedding runs.
5. Both a Mono-fix and a Poly-fix partition are populated (checked after
   classification; a crude extension-count proxy put the multi-extension fix
   share at 30–66% for all six).

## Language scope — a design choice, and a technical note

**Summary of the justification (as in the paper, 2026-10-30).**
1. These are the languages in which bug localization is evaluated: Java for
   IR-based benchmarks (Bench4BL, Ye et al.), Python for LLM-agent localizers
   (SWE-bench). A gap found here concerns the results the field reports.
2. The parser-dependent techniques were built for them (FLIM on Java,
   LocAgent on Python). Another language would need our port of their
   parsers, and a failure would then measure the port, not the technique.
3. One statically and one dynamically typed ecosystem.
Not a data-availability argument: in our copy of BeetleBox, C++ has 5 268 bugs
and JavaScript 3 783, against Java 3 707 and Python 3 759.

**Design choice.** The study covers one statically-typed and one dynamically-typed
mainstream ecosystem (Java, Python). This is a deliberate scoping decision for a
first study of fix composition, not a claim that other ecosystems are
uninteresting. Generalisation to C++, Go, JavaScript, Kotlin and others is left
to future work and stated as a limitation.

**Technical note.** The parsing techniques evaluated here (FLIM, COOBA) ship
Python and Java AST support in their available implementations; other languages
are only reachable through a tree-sitter fallback that changes the technique.
Restricting to Java and Python keeps the feasibility comparison about the
technique rather than about a fallback.

## Languages present in BeetleBox but excluded

C++, Go, JavaScript. Excluded by the Java-or-Python primary-language criterion
above. The exclusion is a scoping decision; the reason is recorded here so it is
not read as an unexplained omission (a SANER reviewer asked whether the earlier
C++ exclusion was technical or by design).

## Not random sampling

The six are a purposive selection meeting the criteria above, chosen for data
readiness and class balance. This is stated as a limitation: findings describe
these six projects and are generalised narrowly.
