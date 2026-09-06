"""
Step 0 (part 2) — the classification rule catalog. SINGLE SOURCE OF TRUTH.

Frozen before any bug is classified (Phase C). `docs/CLASSIFICATION_RULES.md`
is the prose form and must agree with this file. Both carry RULESET_VERSION.

Public API
----------
    classify_fix(files, project_language, toggles=DEFAULT_TOGGLES) -> FixClass

`files` is a list of dicts {"path": str, "ext": str, "change_type": str} as
produced by Scripts/extract_fix_commits.py.

The rules are deliberately path-aware, not purely extension-based: changelog
fragments, test code, CI config and generated/codegen files are identified by
path and can be present with any extension.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Optional

RULESET_VERSION = "0.2.0"   # FROZEN 2026-09-06 — bump to 0.2.1 if the 50-bug check finds a rule error

# ---------------------------------------------------------------------------
# 1. Extension -> (language_id, category)
#    category in: source | data-config | build | schema | style | docs | test-data | other
#    "language_id" collapses dialect/extension variants of one language.
# ---------------------------------------------------------------------------
EXT_LANG = {
    # ---- programming languages (category "source") -----------------------
    "py": ("Python", "source"), "pyi": ("Python", "source"), "pyx": ("Cython", "source"),
    "java": ("Java", "source"),
    "kt": ("Kotlin", "source"), "kts": ("Kotlin", "source"),
    "groovy": ("Groovy", "source"),
    "scala": ("Scala", "source"),
    "ts": ("TypeScript", "source"), "tsx": ("TypeScript", "source"), "mts": ("TypeScript", "source"),
    "cts": ("TypeScript", "source"),
    "js": ("JavaScript", "source"), "jsx": ("JavaScript", "source"),
    "mjs": ("JavaScript", "source"), "cjs": ("JavaScript", "source"),
    "vue": ("Vue", "source"),
    "sh": ("Shell", "source"), "bash": ("Shell", "source"),
    "ps1": ("PowerShell", "source"), "psm1": ("PowerShell", "source"),
    "bat": ("Batch", "source"), "cmd": ("Batch", "source"),
    "cs": ("C#", "source"),
    "go": ("Go", "source"),
    "rb": ("Ruby", "source"),
    "sql": ("SQL", "schema"),          # DDL/DML schema files -> counts, tagged schema
    "g4": ("ANTLR", "schema"),
    "jj": ("JavaCC", "schema"),
    "proto": ("Protobuf", "schema"),
    "xsd": ("XML-Schema", "schema"),
    # ---- structured data / configuration (category "data-config") -------
    "yml": ("YAML", "data-config"), "yaml": ("YAML", "data-config"),
    "json": ("JSON", "data-config"), "json5": ("JSON", "data-config"),
    "xml": ("XML", "data-config"),
    "toml": ("TOML", "data-config"),
    "ini": ("INI", "data-config"), "cfg": ("INI", "data-config"),
    "conf": ("INI", "data-config"), "properties": ("INI", "data-config"),
    "cnf": ("INI", "data-config"), "config": ("INI", "data-config"),
    "inventory": ("INI", "data-config"),   # ansible inventory files
    "j2": ("Jinja", "data-config"), "jinja2": ("Jinja", "data-config"),
    "tpl": ("Template", "data-config"), "mustache": ("Template", "data-config"),
    "env": ("Env", "data-config"),
    "kubernetes-helm-yaml": ("YAML", "data-config"),
    "tf": ("Terraform", "data-config"), "tfvars": ("Terraform", "data-config"),
    "policy": ("Policy", "data-config"),   # Java security .policy
    "acl": ("ACL", "data-config"),
    # ---- build (category "build") --------------------------------------
    "gradle": ("Gradle", "build"),
    "dockerfile": ("Docker", "build"),
    "csproj": ("MSBuild", "build"), "sln": ("MSBuild", "build"), "vcxproj": ("MSBuild", "build"),
    "install4j": ("Installer", "build"),
    "in": ("Autotools", "build"),          # MANIFEST.in etc.; sanity.*.in is caught by path rule first
    # ---- styling ----------------------------------------------------
    "css": ("CSS", "style"), "scss": ("CSS", "style"), "less": ("CSS", "style"),
    # ---- documentation (category "docs") ------------------------------
    "md": ("Markdown", "docs"), "markdown": ("Markdown", "docs"),
    "rst": ("reST", "docs"),
    "asciidoc": ("AsciiDoc", "docs"), "adoc": ("AsciiDoc", "docs"),
    "html": ("HTML", "docs"), "htm": ("HTML", "docs"),
    "inv": ("SphinxInventory", "docs"),
    # ---- test-data / fixtures (category "test-data") -----------------
    "csv-spec": ("TestData", "test-data"), "sql-spec": ("TestData", "test-data"),
    "expected": ("TestData", "test-data"),
    "stdout": ("TestData", "test-data"), "stderr": ("TestData", "test-data"),
    "interp": ("TestData", "test-data"),
    "snap": ("TestData", "test-data"), "ambr": ("TestData", "test-data"),
    "sha1": ("TestData", "test-data"), "sha256": ("TestData", "test-data"),
    "golden": ("TestData", "test-data"),
    # ---- known non-targets: binary / media / vcs (category "other", excluded) --
    "png": ("Binary", "other"), "jpg": ("Binary", "other"), "jpeg": ("Binary", "other"),
    "gif": ("Binary", "other"), "svg": ("Binary", "other"), "ico": ("Binary", "other"),
    "mp4": ("Binary", "other"), "mkv": ("Binary", "other"), "pdf": ("Binary", "other"),
    "zip": ("Binary", "other"), "tgz": ("Binary", "other"), "gz": ("Binary", "other"),
    "jar": ("Binary", "other"), "class": ("Binary", "other"), "war": ("Binary", "other"),
    "crt": ("Cert", "other"), "key": ("Cert", "other"), "pem": ("Cert", "other"),
    "st": ("CodegenTemplate", "other"),   # X-Block.java.st -> generates .java
    "csv": ("CSV", "data-config"),         # plain CSV data
    "txt": ("Text", "docs"),               # default; path rule promotes/demotes
}

# ---------------------------------------------------------------------------
# 2. Special filenames with no usable extension
# ---------------------------------------------------------------------------
SPECIAL_BASENAMES = {
    "dockerfile": ("Docker", "build"),
    "makefile": ("Make", "build"),
    "manifest.in": ("Autotools", "build"),
    "jenkinsfile": ("CI", "ci"),
    "vagrantfile": ("Ruby", "build"),
    "license": ("License", "docs"),
    "notice": ("License", "docs"),
    "changelog": ("Changelog", "docs"),
    "readme": ("Doc", "docs"),
    "codeowners": ("VCS", "vcs"),
}
SPECIAL_PREFIXES = {          # basename.startswith(prefix)
    "dockerfile": ("Docker", "build"),      # Dockerfile.base, Dockerfile.ci
}

# ---------------------------------------------------------------------------
# 3. Path rules (checked before the extension map). Each returns a category
#    override and/or an exclusion, plus a boundary flag.
# ---------------------------------------------------------------------------
_RE_CHANGELOG_FRAGMENT = re.compile(
    r"(^|/)(changelogs?/fragments?|newsfragments|\.changes|docs/changelog|"
    r"docs/release-notes|release_notes)/", re.I)
_RE_TEST_PATH = re.compile(
    r"(^|/)(tests?|__tests__|testsuite|testdata|test-fixtures|testfixtures|"
    r"it|qa|integration-tests?)/|"
    r"(^|/)src/(test|integ|internalClusterTest|yamlRestTest|javaRestTest|"
    r"internalTest)[A-Za-z]*/|"
    r"(_test\.py|_tests\.py|test_[^/]*\.py|[A-Za-z0-9]+Test\.java|[A-Za-z0-9]+IT\.java|"
    r"[A-Za-z0-9]+Spec\.groovy)$", re.I)
_RE_CI_PATH = re.compile(
    r"(^|/)(\.github|\.gitlab|\.azure-pipelines|\.circleci|\.buildkite|\.ci)/|"
    r"(^|/)(\.gitlab-ci\.yml|\.travis\.yml|azure-pipelines\.yml|appveyor\.yml|"
    r"\.pre-commit-config\.ya?ml|Jenkinsfile[^/]*)$", re.I)
_RE_DEVTOOLING = re.compile(
    r"(^|/)(\.flake8|\.coveragerc|\.editorconfig|\.eslintrc[^/]*|\.eslintignore|"
    r"\.prettierrc[^/]*|\.prettierignore|\.babelrc[^/]*|\.stylelintrc[^/]*|"
    r"\.rat-excludes|\.dockerignore|\.gitattributes|\.gitmodules|\.gitignore|"
    r"\.mailmap|\.npmignore|\.yamllint|tox\.ini|setup\.cfg|mypy\.ini|"
    r"sanity\.[^/]*\.in|constraints\.txt|\.env(\.[^/]*)?)$", re.I)
_RE_LOCKFILE = re.compile(
    r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Pipfile\.lock|"
    r"Cargo\.lock|go\.sum|composer\.lock|Gemfile\.lock)$|\.lock$", re.I)
_RE_VENDORED = re.compile(
    r"(^|/)(vendor|third_party|third-party|node_modules|\.venv|bundled|external)/", re.I)
_RE_GENERATED = re.compile(
    r"(^|/)generated/|(\.pb\.go|_pb2\.pyi?|\.g\.dart|\.generated\.[A-Za-z]+|"
    r"\.java\.st|\.designer\.cs)$", re.I)
_RE_DOCS_PATH = re.compile(r"(^|/)(docs?|documentation|site|www)/", re.I)
_RE_SPI = re.compile(r"(^|/)META-INF/services/", re.I)


@dataclass(frozen=True)
class Toggles:
    """Each toggle is False for the HEADLINE configuration."""
    STRICT_SOURCE_ONLY: bool = False        # Poly-fix needs >=2 programming languages
    EXCLUDE_TESTS: bool = False             # drop test code + test data
    INCLUDE_DOCS: bool = False              # docs count as a language ("Docs")
    INCLUDE_CHANGELOG_FRAGMENTS: bool = False
    INCLUDE_LOCKFILES: bool = False
    INCLUDE_GENERATED: bool = False
    INCLUDE_VENDORED: bool = False
    INCLUDE_CI: bool = False
    COLLAPSE_DATA_CONFIG: bool = False      # all data-config -> one language "Config"
    COLLAPSE_ALL_NONSOURCE: bool = False    # all non-source -> one language "NonSource"
    COUNT_DELETIONS: bool = False           # include purely-deleted files


DEFAULT_TOGGLES = Toggles()

# categories that a "programming language" belongs to
_PROGRAMMING = {"source"}
# categories that count toward Mono/Poly in the headline config
_COUNTING_HEADLINE = {"source", "data-config", "build", "schema", "style", "test-data"}


@dataclass
class FileVerdict:
    path: str
    ext: str
    language: Optional[str]
    category: str          # resolved category, or "excluded:<reason>"
    counts: bool           # contributes to the language set
    flags: list = field(default_factory=list)


# ---------------------------------------------------------------------------
# Secondary-language admission (advisor decision).
#
#   C1  formal grammar        -> a parser for it could exist
#   C2  not parseable by the evaluated AST techniques (i.e. not Java/Python) -- checked at use site
#   C3  behaviour-bearing     -> baked into category: docs are already excluded upstream
#   C4  attested as ground truth -> checked in classify_bugs against the dataset
#   C5  >=15 poly-fix bugs / >=2 projects -> only governs whether a type gets its OWN stats row
#
# A language passes C1+C3 iff it is in GRAMMAR_LANGUAGES below. INI/properties,
# plain-text fixtures, SPI class lists, CSV etc. fail C1 (a format, not a language).
# ---------------------------------------------------------------------------
GRAMMAR_LANGUAGES = {
    # programming languages
    "Python", "Java", "TypeScript", "JavaScript", "Vue", "Groovy", "Scala",
    "Kotlin", "Shell", "PowerShell", "Batch", "C#", "Go", "Ruby", "Cython",
    # schema / IDL / grammar
    "SQL", "ANTLR", "JavaCC", "Protobuf", "XML-Schema",
    # structured data / config with a grammar
    "YAML", "JSON", "XML", "TOML", "Jinja", "Template", "Terraform", "Policy",
    # styling
    "CSS",
    # build
    "Gradle", "Docker", "Make", "MSBuild", "Installer", "Autotools",
}
# the four types that additionally pass C5 in this dataset -> the HEADLINE grain
TIER1_SECONDARY = {"YAML", "JSON", "XML", "SQL"}
# reported as named qualitative cases (C1-C4 pass, C5 fails: single project / small N)
TIER2_SECONDARY = {"Gradle", "Groovy", "TypeScript", "Vue", "JavaScript",
                   "ANTLR", "JavaCC", "Docker", "Make", "XML-Schema"}


@dataclass
class FixClass:
    label: str                     # Mono-fix | Poly-fix | Other-fix | Excluded
    languages: list                # sorted list of language ids that counted
    primary_language: Optional[str]
    n_files_raw: int
    n_files_counted: int
    boundary_flags: list           # union of all per-file flags
    per_file: list                 # list[FileVerdict]
    programming_languages: list = field(default_factory=list)   # counted, category == source
    secondary_languages: list = field(default_factory=list)     # counted, != primary, in GRAMMAR_LANGUAGES
    grains: dict = field(default_factory=dict)   # {headline, broad, strict, tier3_only} -> bool


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _ext_lookup(ext: str, basename: str):
    if ext in EXT_LANG:
        return EXT_LANG[ext]
    b = basename.lower()
    if b in SPECIAL_BASENAMES:
        return SPECIAL_BASENAMES[b]
    for pref, val in SPECIAL_PREFIXES.items():
        if b.startswith(pref):
            return val
    return (None, "other")


def classify_file(path: str, ext: str, change_type: str, tg: Toggles) -> FileVerdict:
    base = _basename(path)
    flags = []

    # --- path rules first (a file can be a changelog fragment with any ext) ---
    if _RE_CHANGELOG_FRAGMENT.search(path):
        flags.append("changelog_fragment")
        if not tg.INCLUDE_CHANGELOG_FRAGMENTS:
            return FileVerdict(path, ext, None, "excluded:changelog_fragment", False, flags)
    if _RE_LOCKFILE.search(path):
        flags.append("lockfile")
        if not tg.INCLUDE_LOCKFILES:
            return FileVerdict(path, ext, None, "excluded:lockfile", False, flags)
    if _RE_VENDORED.search(path):
        flags.append("vendored")
        if not tg.INCLUDE_VENDORED:
            return FileVerdict(path, ext, None, "excluded:vendored", False, flags)
    if _RE_GENERATED.search(path):
        flags.append("generated")
        if not tg.INCLUDE_GENERATED:
            return FileVerdict(path, ext, None, "excluded:generated", False, flags)
    if _RE_CI_PATH.search(path):
        flags.append("ci_config")
        if not tg.INCLUDE_CI:
            return FileVerdict(path, ext, None, "excluded:ci_config", False, flags)
    if _RE_DEVTOOLING.search(path):
        flags.append("devtooling")
        return FileVerdict(path, ext, None, "excluded:devtooling", False, flags)
    if _RE_SPI.search(path):
        flags.append("spi_registration")           # META-INF/services/*
        # SPI files are config; keep as data-config unless collapsed away
        return FileVerdict(path, ext, "SPI", "data-config",
                           "data-config" in _COUNTING_HEADLINE, flags)

    lang, cat = _ext_lookup(ext, base)

    # docs promotion/demotion by path
    if cat == "docs" or ext == "txt":
        flags.append("documentation")
        if not tg.INCLUDE_DOCS:
            return FileVerdict(path, ext, None, "excluded:documentation", False, flags)
        lang, cat = "Docs", "docs"      # collapse all doc formats to one language

    if cat == "other":
        # binary / cert / codegen-template / unknown -> never counts
        reason = {"Binary": "binary", "Cert": "certificate",
                  "CodegenTemplate": "codegen_template"}.get(lang, "unclassified")
        if reason == "unclassified":
            flags.append("unclassified_ext")
        return FileVerdict(path, ext, None, f"excluded:{reason}", False, flags)

    # test scoping
    is_test = bool(_RE_TEST_PATH.search(path))
    if is_test:
        flags.append("test" if cat == "source" else "test_asset")
        if tg.EXCLUDE_TESTS:
            return FileVerdict(path, ext, None, "excluded:test", False, flags)

    # deletions
    if change_type == "D" and not tg.COUNT_DELETIONS:
        flags.append("deletion")
        return FileVerdict(path, ext, lang, f"excluded:deletion", False, flags)

    # language collapsing toggles
    if tg.COLLAPSE_ALL_NONSOURCE and cat != "source":
        lang = "NonSource"
    elif tg.COLLAPSE_DATA_CONFIG and cat in ("data-config", "schema", "style"):
        lang = "Config"

    counts = cat in _COUNTING_HEADLINE
    return FileVerdict(path, ext, lang, cat, counts, flags)


def classify_fix(files: list, project_language: str,
                 toggles: Toggles = DEFAULT_TOGGLES) -> FixClass:
    verdicts = [classify_file(f["path"], f.get("ext", ""), f.get("change_type", "M"), toggles)
                for f in files]
    counted = [v for v in verdicts if v.counts and v.language]

    if toggles.STRICT_SOURCE_ONLY:
        counted = [v for v in counted if v.category == "source"]

    langs = sorted({v.language for v in counted})
    prog_langs = sorted({v.language for v in counted if v.category == "source"})
    all_flags = sorted({fl for v in verdicts for fl in v.flags})

    if not counted:
        label = "Excluded"
        primary = None
    elif not prog_langs and not toggles.STRICT_SOURCE_ONLY:
        # in-scope files exist but none is a programming language
        label = "Other-fix"
        primary = None
    elif len(langs) == 1:
        label = "Mono-fix"
        primary = prog_langs[0] if prog_langs else langs[0]
    else:
        label = "Poly-fix"
        primary = prog_langs[0] if prog_langs else langs[0]

    # tie-break primary language toward the project's own language
    proj = {"java": "Java", "python": "Python"}.get((project_language or "").lower())
    if proj and proj in prog_langs:
        primary = proj

    secondaries = sorted({l for l in langs
                          if l != primary and l in GRAMMAR_LANGUAGES})
    grains = {
        "headline": label == "Poly-fix" and bool(set(secondaries) & TIER1_SECONDARY),
        "broad":    label == "Poly-fix" and len(secondaries) >= 1,
        "strict":   label == "Poly-fix" and len(prog_langs) >= 2,
        "tier3_only": (label == "Poly-fix"
                       and not secondaries and len(prog_langs) < 2),
    }

    return FixClass(
        label=label, languages=langs, primary_language=primary,
        n_files_raw=len(files), n_files_counted=len(counted),
        boundary_flags=all_flags, per_file=verdicts,
        programming_languages=prog_langs, secondary_languages=secondaries,
        grains=grains,
    )


def keep_bug(fc: FixClass, project_language: str) -> bool:
    """
    Bug-level filter (separate from language admission): keep a bug only if its
    fix touches >=1 file in the project's primary language, so the parsing
    technique always has a parseable localization target.
    """
    proj = {"java": "Java", "python": "Python"}.get((project_language or "").lower())
    return proj is not None and proj in fc.programming_languages


# named toggle sets for the sensitivity sweep -------------------------------
SENSITIVITY_SETS = {
    "headline": DEFAULT_TOGGLES,
    "strict_source_only": replace(DEFAULT_TOGGLES, STRICT_SOURCE_ONLY=True),
    "exclude_tests": replace(DEFAULT_TOGGLES, EXCLUDE_TESTS=True),
    "include_docs": replace(DEFAULT_TOGGLES, INCLUDE_DOCS=True),
    "include_changelog_fragments": replace(DEFAULT_TOGGLES, INCLUDE_CHANGELOG_FRAGMENTS=True),
    "collapse_data_config": replace(DEFAULT_TOGGLES, COLLAPSE_DATA_CONFIG=True),
    "collapse_all_nonsource": replace(DEFAULT_TOGGLES, COLLAPSE_ALL_NONSOURCE=True),
    "count_deletions": replace(DEFAULT_TOGGLES, COUNT_DELETIONS=True),
}


if __name__ == "__main__":
    # tiny self-test on the motivating example + a few real shapes
    ex = [
        ("localstack .py + .json snapshot",
         [{"path": "localstack/services/s3/provider.py", "ext": "py", "change_type": "M"},
          {"path": "tests/aws/services/s3/test_s3.py", "ext": "py", "change_type": "M"},
          {"path": "tests/aws/services/s3/test_s3.snapshot.json", "ext": "json", "change_type": "M"}],
         "python"),
        ("ansible .py + changelog fragment only (headline)",
         [{"path": "lib/ansible/plugins/action/assemble.py", "ext": "py", "change_type": "M"},
          {"path": "changelogs/fragments/82359_x.yml", "ext": "yml", "change_type": "A"}],
         "python"),
        ("es .java + yamlRestTest .yml",
         [{"path": "server/src/main/java/org/e/Foo.java", "ext": "java", "change_type": "M"},
          {"path": "rest-api-spec/src/yamlRestTest/resources/rest-api-spec/test/x/10.yml",
           "ext": "yml", "change_type": "M"}],
         "java"),
        ("dolphinscheduler .java + .sql schema",
         [{"path": "dolphinscheduler-dao/src/main/java/o/Mapper.java", "ext": "java", "change_type": "M"},
          {"path": "dolphinscheduler-dao/src/main/resources/sql/dolphinscheduler_mysql.sql",
           "ext": "sql", "change_type": "M"}],
         "java"),
        ("java only + build.gradle",
         [{"path": "x-pack/plugin/esql/compute/build.gradle", "ext": "gradle", "change_type": "M"},
          {"path": "x-pack/plugin/esql/compute/src/main/java/o/A.java", "ext": "java", "change_type": "M"}],
         "java"),
    ]
    for name, files, lang in ex:
        r = classify_fix(files, lang)
        g = [k for k, v in r.grains.items() if v]
        print(f"{name}\n  -> {r.label}  langs={r.languages}  primary={r.primary_language}  "
              f"secondary={r.secondary_languages}  grains={g}  keep={keep_bug(r, lang)}  "
              f"flags={r.boundary_flags}")
