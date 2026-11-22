"""
Human two-person round of the 50-bug classification agreement check
(docs/ANNOTATION_PROTOCOL.md, protocol rev. 2.1, ruleset 0.2.0) in Excel.

  make     one workbook per annotator, from the blank sheets of the AI round
           (results/obj2/annotation/v2/{bugs,files}_blank.csv: same 50 bugs,
           178 files), written to results/obj2/annotation/human/handout/.
           The workbook holds the instructions, the two answer sheets with
           drop-down lists, and the protocol's look-up tables (Appendices A-C,
           worked cases). It contains no answers.
  import   reads the returned workbooks from results/obj2/annotation/human/returned/,
           checks that every answer cell is filled with an allowed value, writes
           {bugs,files}_annotator_<NAME>.csv and steps_<NAME>.md to
           results/obj2/annotation/human/, and runs Scripts/score_annotation.py
           (Cohen's kappa A vs B and each vs the frozen ruleset).

    python Scripts/annotation_workbook.py make --names Eashaan Annotator2
    python Scripts/annotation_workbook.py import            # after both are returned
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2 = os.path.join(ROOT, "results", "obj2", "annotation", "v2")
HUMAN = os.path.join(ROOT, "results", "obj2", "annotation", "human")
HANDOUT, RETURNED = os.path.join(HUMAN, "handout"), os.path.join(HUMAN, "returned")
PROTOCOL = os.path.join(ROOT, "docs", "ANNOTATION_PROTOCOL.md")

YES_NO = ["yes", "no"]
REASONS = ["changelog_fragment", "lockfile", "vendored", "generated", "ci_config", "devtooling",
           "documentation", "binary", "certificate", "codegen_template", "unclassified", "deletion"]
CATEGORIES = ["source", "schema", "data-config", "build", "style", "test-data", "docs", "other", "ci", "vcs"]
LABELS = ["Mono-fix", "Poly-fix", "Other-fix", "Excluded"]
SUBTYPES = ["behaviour-bearing", "test-asset-only"]
FILE_GIVEN = ["repo_name", "bug_id", "primary_language", "path", "change_type"]
FILE_ANS = ["counts", "excluded_reason", "language", "category", "is_test", "notes"]
BUG_GIVEN = ["repo_name", "bug_id", "primary_language", "commit_summary", "n_files", "github_commit"]
BUG_ANS = ["label", "keep", "secondary_languages", "poly_subtype", "notes"]

GREY, YELLOW, HEAD = PatternFill("solid", fgColor="EDEDED"), PatternFill("solid", fgColor="FFF7D6"), PatternFill("solid", fgColor="1F4E79")
BAND = PatternFill("solid", fgColor="F7F7F7")
THIN = Side(style="thin", color="BFBFBF")


# ------------------------------------------------------------------ protocol tables
def protocol_tables():
    """Appendix A/B/C and the worked-cases table, parsed from the protocol itself."""
    text = open(PROTOCOL, encoding="utf-8").read()

    def table_after(heading):
        part = text[text.index(heading):]
        # stop at the first blank line after the table
        out, started = [], False
        for l in part.splitlines()[1:]:
            if l.startswith("|"):
                started = True
                if re.match(r"^\|\s*:?-+", l):
                    continue
                out.append([c.strip().replace("\\|", "|").strip("`") for c in re.split(r"(?<!\\)\|", l)[1:-1]])
            elif started:
                break
        return out

    return {"Appendix A": table_after("## Appendix A"), "Appendix B": table_after("## Appendix B"),
            "Appendix C": table_after("## Appendix C"), "Worked cases": table_after("### 3.1 Worked cases")}


def languages(tables):
    langs = {r[0] for r in tables["Appendix A"][1:]} | {r[1] for r in tables["Appendix B"][1:]}
    return sorted(langs | {"SPI"}, key=str.lower)


# ------------------------------------------------------------------ make
INSTRUCTIONS = [
    ("50-bug classification agreement check: human round", "title"),
    ("Ruleset 0.2.0, protocol rev. 2.1 (docs/ANNOTATION_PROTOCOL.md). Work alone; do not discuss cases with the other annotator until both workbooks are returned.", ""),
    ("", ""),
    ("Before you start (about 30 min)", "h"),
    ("1. Read docs/ANNOTATION_PROTOCOL.md sections 1-3 and docs/CLASSIFICATION_RULES.md sections 1-4 and the admission criteria C1-C5.", ""),
    ("2. The sheets 'Appendix A', 'Appendix B', 'Appendix C' and 'Worked cases' in this workbook are copies of the protocol's tables, for look-up.", ""),
    ("3. Do NOT open key_*.csv, Scripts/classification_rules.py, data/obj2/bug_classification.parquet, results/obj2/bug_classification.csv or the other annotator's workbook.", ""),
    ("", ""),
    ("Step 1: sheet '1_files' (178 rows, about 1.5 h)", "h"),
    ("Fill the yellow columns for every row: counts, excluded_reason, language, category, is_test, notes. Grey columns are given; do not change them.", ""),
    ("Apply the rules in the protocol's order (path rules -> language/category -> test scope -> deletion). The first rule that excludes a file decides.", ""),
    ("counts = no: fill excluded_reason; is_test = no; keep the language only for deletions (step 4); leave category empty for deletions.", ""),
    ("counts = yes: leave excluded_reason empty; fill language, category and is_test.", ""),
    ("Decide from the path and change type. Open a file's contents only if a rule cannot be applied from the path, and then say so in notes.", ""),
    ("Write a note on every file that needed thought (which rule you applied and why). Rows of one bug share a shade; working bug by bug helps.", ""),
    ("", ""),
    ("Step 2: sheet '2_bugs' (50 rows, about 30 min)", "h"),
    ("Derive each bug's answers from YOUR OWN rows in '1_files' (the 'counted files' column counts them for you):", ""),
    ("label: no counted file -> Excluded; counted files but none of category 'source' -> Other-fix; all counted files in one language -> Mono-fix; two or more languages -> Poly-fix.", ""),
    ("keep: yes if at least one counted file is in the primary language (column primary_language), else no.", ""),
    ("secondary_languages (Poly-fix only): the counted languages other than the primary one, separated by '; ' (e.g. JSON; YAML). Empty otherwise.", ""),
    ("poly_subtype (kept Poly-fix only, and only if a secondary language has grammar = yes in Appendix A): behaviour-bearing if at least one secondary file has is_test = no, else test-asset-only. Empty otherwise.", ""),
    ("github_commit opens the fix commit on GitHub if you need context; the decision still comes from the rules.", ""),
    ("", ""),
    ("Step 3: sheet 'log', then return", "h"),
    ("Fill your name, the dates and the time spent, and list every ambiguity (file, rule applied). Save the workbook (keep the .xlsx format and the file name) and send it back.", ""),
    ("", ""),
    ("Pass criterion: Cohen's kappa >= 0.80 between the two annotators on the bug label and on the per-file 'counts' decision. Disagreements are resolved by amending a rule, never by adjudicating a single case.", "note"),
]


def style_header(ws, row, ncol):
    for c in range(1, ncol + 1):
        cell = ws.cell(row=row, column=c)
        cell.font, cell.fill = Font(bold=True, color="FFFFFF"), HEAD
        cell.alignment = Alignment(vertical="center", wrap_text=True)


def add_list(ws_lists, col, name, values):
    ws_lists.cell(row=1, column=col, value=name).font = Font(bold=True)
    for i, v in enumerate(values, 2):
        ws_lists.cell(row=i, column=col, value=v)
    L = get_column_letter(col)
    return f"lists!${L}$2:${L}${len(values) + 1}"


def make_workbook(name, files, bugs, tables, out):
    wb = Workbook()
    ws0 = wb.active
    ws0.title = "Start here"
    ws0.column_dimensions["A"].width = 110
    for i, (t, kind) in enumerate(INSTRUCTIONS, 1):
        c = ws0.cell(row=i, column=1, value=t)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        if kind == "title":
            c.font = Font(bold=True, size=14)
        elif kind == "h":
            c.font = Font(bold=True, size=12, color="1F4E79")
        elif kind == "note":
            c.font = Font(italic=True)
    ws0.cell(row=len(INSTRUCTIONS) + 2, column=1, value=f"Workbook prepared for: {name}").font = Font(bold=True)

    lists = wb.create_sheet("lists")
    rng = {"yn": add_list(lists, 1, "yes/no", YES_NO), "reason": add_list(lists, 2, "excluded_reason", REASONS),
           "lang": add_list(lists, 3, "language", languages(tables)), "cat": add_list(lists, 4, "category", CATEGORIES),
           "label": add_list(lists, 5, "label", LABELS), "sub": add_list(lists, 6, "poly_subtype", SUBTYPES)}

    # ---- files sheet
    wf = wb.create_sheet("1_files")
    cols = FILE_GIVEN + FILE_ANS
    wf.append(cols)
    style_header(wf, 1, len(cols))
    prim = dict(zip(zip(bugs.repo_name, bugs.bug_id), bugs.primary_language))
    shade, last = False, None
    for r in files.itertuples():
        key = (r.repo_name, r.bug_id)
        if key != last:
            shade, last = not shade, key
        wf.append([r.repo_name, r.bug_id, prim[key], r.path, r.change_type] + [""] * len(FILE_ANS))
        row = wf.max_row
        for c in range(1, len(cols) + 1):
            cell = wf.cell(row=row, column=c)
            cell.border = Border(bottom=THIN)
            cell.fill = (BAND if shade else GREY) if c <= len(FILE_GIVEN) else YELLOW
    n = wf.max_row
    for col, key, prompt in (("F", "yn", "yes / no"), ("G", "reason", "only if counts = no"), ("H", "lang", "Appendix A/B"),
                             ("I", "cat", "empty for deletions and excluded files"), ("J", "yn", "yes / no")):
        dv = DataValidation(type="list", formula1=f"={rng[key]}", allow_blank=True, showErrorMessage=True,
                            errorTitle="Not an allowed value", error="Choose a value from the list.",
                            promptTitle=col, prompt=prompt, showInputMessage=True)
        wf.add_data_validation(dv)
        dv.add(f"{col}2:{col}{n}")
    for col, w in zip("ABCDEFGHIJK", (22, 9, 10, 80, 7, 8, 19, 13, 12, 8, 50)):
        wf.column_dimensions[col].width = w
    wf.freeze_panes = "F2"
    wf.auto_filter.ref = f"A1:K{n}"

    # ---- bugs sheet
    wbs = wb.create_sheet("2_bugs")
    cols = BUG_GIVEN + ["counted files (from 1_files)", "files filled"] + BUG_ANS
    wbs.append(cols)
    style_header(wbs, 1, len(cols))
    for r in bugs.itertuples():
        url = f"https://github.com/{r.repo_name}/commit/{r.fix_commit_sha}"
        wbs.append([r.repo_name, r.bug_id, r.primary_language, r.commit_summary, int(r.n_files), url, None, None] + [""] * len(BUG_ANS))
        row = wbs.max_row
        wbs.cell(row=row, column=6).hyperlink = url
        wbs.cell(row=row, column=6).font = Font(color="0563C1", underline="single")
        wbs.cell(row=row, column=7, value=f'=COUNTIFS(\'1_files\'!$A:$A,A{row},\'1_files\'!$B:$B,B{row},\'1_files\'!$F:$F,"yes")')
        wbs.cell(row=row, column=8, value=f'=COUNTIFS(\'1_files\'!$A:$A,A{row},\'1_files\'!$B:$B,B{row},\'1_files\'!$F:$F,"?*")&" of "&E{row}')
        for c in range(1, len(cols) + 1):
            cell = wbs.cell(row=row, column=c)
            cell.border = Border(bottom=THIN)
            cell.fill = GREY if c <= len(BUG_GIVEN) + 2 else YELLOW
            if c == 4:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
    n = wbs.max_row
    for col, key, prompt in (("I", "label", "Mono-fix / Poly-fix / Other-fix / Excluded"), ("J", "yn", "yes / no"),
                             ("L", "sub", "kept Poly-fix with a grammar language only; else empty")):
        dv = DataValidation(type="list", formula1=f"={rng[key]}", allow_blank=True, showErrorMessage=True,
                            errorTitle="Not an allowed value", error="Choose a value from the list.",
                            prompt=prompt, showInputMessage=True)
        wbs.add_data_validation(dv)
        dv.add(f"{col}2:{col}{n}")
    dv = DataValidation(type="custom", formula1="TRUE", allow_blank=True, showInputMessage=True,
                        prompt="Poly-fix only: languages other than the primary, separated by '; ' (e.g. JSON; YAML)")
    wbs.add_data_validation(dv)
    dv.add(f"K2:K{n}")
    for col, w in zip("ABCDEFGHIJKLM", (22, 9, 10, 55, 7, 16, 11, 10, 11, 7, 22, 18, 50)):
        wbs.column_dimensions[col].width = w
    wbs.freeze_panes = "I2"

    # ---- log sheet
    wl = wb.create_sheet("log")
    for i, (k, v) in enumerate((("annotator", name), ("started (date)", ""), ("finished (date)", ""),
                                ("time spent, reading the protocol (min)", ""), ("time spent, files (min)", ""),
                                ("time spent, bugs (min)", ""), ("how you worked (free text)", "")), 1):
        wl.cell(row=i, column=1, value=k).font = Font(bold=True)
        wl.cell(row=i, column=2, value=v).fill = YELLOW
    wl.cell(row=9, column=1, value="Ambiguities: one row each (the same notes may also be in the sheets)").font = Font(bold=True, color="1F4E79")
    for c, h in enumerate(("repo_name", "bug_id", "path (if a file)", "rule applied / question"), 1):
        wl.cell(row=10, column=c, value=h)
    style_header(wl, 10, 4)
    for r in range(11, 41):
        for c in range(1, 5):
            wl.cell(row=r, column=c).fill = YELLOW
    for col, w in zip("ABCD", (34, 12, 60, 80)):
        wl.column_dimensions[col].width = w

    # ---- reference sheets
    for title, rows in tables.items():
        ws = wb.create_sheet(title)
        for r in rows:
            ws.append(r)
        style_header(ws, 1, len(rows[0]))
        for i in range(1, len(rows[0]) + 1):
            ws.column_dimensions[get_column_letter(i)].width = 60 if title in ("Appendix C", "Worked cases") else 22
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.freeze_panes = "A2"
    lists.sheet_state = "hidden"
    wb.active = 0
    wb.save(out)


def cmd_make(a):
    files = pd.read_csv(os.path.join(V2, "files_blank.csv"), dtype=str, keep_default_na=False)
    bugs = pd.read_csv(os.path.join(V2, "bugs_blank.csv"), dtype=str, keep_default_na=False)
    tables = protocol_tables()
    os.makedirs(HANDOUT, exist_ok=True)
    os.makedirs(RETURNED, exist_ok=True)
    for name in a.names:
        out = os.path.join(HANDOUT, f"annotation_{name}.xlsx")
        make_workbook(name, files, bugs, tables, out)
        print("wrote", out)


# ------------------------------------------------------------------ import
def read_sheet(ws, ncols):
    rows = list(ws.iter_rows(values_only=True))
    head = [str(h) for h in rows[0][:ncols]]
    data = [["" if v is None else str(v).strip() for v in r[:ncols]] for r in rows[1:] if any(v not in (None, "") for v in r[:2])]
    return pd.DataFrame(data, columns=head)


def check(df, kind, name, langs):
    problems = []
    for i, r in df.iterrows():
        where = f"{name} {kind} row {i + 2} ({r.repo_name} {r.bug_id}{' ' + r.path if kind == 'files' else ''})"
        if kind == "files":
            if r.counts not in YES_NO:
                problems.append(f"{where}: counts missing")
            if r.is_test not in YES_NO:
                problems.append(f"{where}: is_test missing")
            if r.counts == "no" and r.excluded_reason not in REASONS:
                problems.append(f"{where}: counts = no but no excluded_reason")
            if r.counts == "yes" and (r.excluded_reason or r.language not in langs or r.category not in CATEGORIES):
                problems.append(f"{where}: counts = yes needs language and category and no excluded_reason")
        else:
            if r.label not in LABELS:
                problems.append(f"{where}: label missing")
            if r.keep not in YES_NO:
                problems.append(f"{where}: keep missing")
            if r.label == "Poly-fix" and not r.secondary_languages:
                problems.append(f"{where}: Poly-fix without secondary_languages")
            if r.poly_subtype and r.poly_subtype not in SUBTYPES:
                problems.append(f"{where}: poly_subtype not allowed")
    return problems


def cmd_import(a):
    books = sorted(f for f in os.listdir(RETURNED) if f.endswith(".xlsx") and not f.startswith("~$"))
    if len(books) != 2 and not a.allow_one:
        sys.exit(f"expected two returned workbooks in {RETURNED}, found {books}")
    langs = set(languages(protocol_tables()))
    names, problems = [], []
    for b in books:
        name = re.sub(r"^annotation_|\.xlsx$", "", b)
        wb = load_workbook(os.path.join(RETURNED, b), data_only=True)
        files = read_sheet(wb["1_files"], len(FILE_GIVEN + FILE_ANS))
        bugs = read_sheet(wb["2_bugs"], len(BUG_GIVEN) + 2 + len(BUG_ANS))
        problems += check(files, "files", name, langs) + check(bugs, "bugs", name, langs)
        files.insert(0, "annotator", name)
        bugs.insert(0, "annotator", name)
        files[["annotator", "repo_name", "bug_id", "path", "change_type"] + FILE_ANS].to_csv(
            os.path.join(HUMAN, f"files_annotator_{name}.csv"), index=False)
        bugs[["annotator", "repo_name", "bug_id", "primary_language", "commit_summary", "n_files"] + BUG_ANS].to_csv(
            os.path.join(HUMAN, f"bugs_annotator_{name}.csv"), index=False)
        wl = wb["log"]
        L = [f"# Annotator {name}: log of the human round", ""]
        for r in range(1, 8):
            L.append(f"- **{wl.cell(row=r, column=1).value}:** {wl.cell(row=r, column=2).value or ''}")
        L += ["", "## Ambiguities", "", "| repo | bug | path | rule applied / question |", "|---|---|---|---|"]
        for r in range(11, wl.max_row + 1):
            v = [wl.cell(row=r, column=c).value for c in range(1, 5)]
            if any(v):
                L.append("| " + " | ".join("" if x is None else str(x) for x in v) + " |")
        open(os.path.join(HUMAN, f"steps_{name}.md"), "w").write("\n".join(L) + "\n")
        names.append(name)
        print(f"imported {b}: {len(files)} files, {len(bugs)} bugs")
    if problems:
        print(f"\n{len(problems)} incomplete or invalid answers (fix them in the workbook and re-run import):")
        print("\n".join(problems[:60]))
        if not a.force:
            sys.exit(1)
    for k in ("key_bugs.csv", "key_files.csv"):
        shutil.copy(os.path.join(V2, k), os.path.join(HUMAN, k))
    if len(names) == 2:
        subprocess.run([sys.executable, os.path.join(ROOT, "Scripts", "score_annotation.py"),
                        "--dir", HUMAN, "--a", names[0], "--b", names[1]], check=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--names", nargs="+", default=["annotator1", "annotator2"])
    i = sub.add_parser("import")
    i.add_argument("--force", action="store_true", help="score even if some answers are missing")
    i.add_argument("--allow-one", action="store_true", help="import a single workbook (completeness check only)")
    a = ap.parse_args()
    cmd_make(a) if a.cmd == "make" else cmd_import(a)
