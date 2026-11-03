"""
Shared source parsing for Objective 2.

One parser per project language, used by every consumer so "parseable" means
the same thing everywhere:
  * Scripts/universe.py   -> per-file parse_status (RQ2 feasibility, the
                             parseable-only evaluation condition)
  * src/flim/              -> function units + identifier fields for IR features
  * src/blaze/data_prep.py -> tree-sitter parser for dynamic chunking

Python files: CPython `ast` (the native parser). Java files: tree-sitter-java
(error-tolerant, supports records / text blocks / switch expressions, which
javalang 0.13 does not). Every other file type has no parser for either
technique -> status "no_parser".

Note: `tree_sitter_languages` 1.10.2 is incompatible with the installed
tree_sitter 0.25 (`Language.__init__` signature changed), so it is not used;
the per-language wheels `tree-sitter-java` / `tree-sitter-python` are.
"""

import ast
import io
import os
import re
import tokenize
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List

PARSE_OK = "ok"                 # parsed, >=1 function/method
PARSE_PARTIAL = "partial"       # Java: syntax errors, but >=1 method recovered
PARSE_NOFUNC = "ok_nofunc"      # parsed, no function (module/class body only)
PARSE_ERROR = "parse_error"     # file of the project language the parser rejects
NO_PARSER = "no_parser"         # not the project language (YAML, JSON, XML, ...)
PARSEABLE = {PARSE_OK, PARSE_PARTIAL, PARSE_NOFUNC}

LANG_EXT = {"python": (".py",), "java": (".java",)}

MIN_UNIT_CHARS = 10


@dataclass
class ParsedFile:
    status: str
    units: List[str] = field(default_factory=list)       # function / method source
    unit_spans: List[tuple] = field(default_factory=list)  # (first_line, last_line), 1-based
    class_names: List[str] = field(default_factory=list)
    method_names: List[str] = field(default_factory=list)
    var_names: List[str] = field(default_factory=list)
    comments: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)      # dotted module / type names
    package: str = ""                                     # Java package


def file_language(path: str, project_language: str):
    """Project language if the file belongs to it, else None."""
    lang = project_language.lower()
    return lang if path.lower().endswith(LANG_EXT.get(lang, ())) else None


@lru_cache(maxsize=None)
def ts_parser(language: str):
    """tree-sitter Parser for 'java' or 'python' (None if unavailable)."""
    try:
        import tree_sitter as ts
        if language == "java":
            import tree_sitter_java as m
        elif language == "python":
            import tree_sitter_python as m
        else:
            return None
        return ts.Parser(ts.Language(m.language()))
    except Exception:
        return None


# ---------------------------------------------------------------------------
def _parse_python(code: str) -> ParsedFile:
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, RecursionError, MemoryError):
        return ParsedFile(PARSE_ERROR)
    pf = ParsedFile(PARSE_OK)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            pf.method_names.append(node.name)
            seg = ast.get_source_segment(code, node)
            if seg and len(seg.strip()) > MIN_UNIT_CHARS:
                pf.units.append(seg.strip())
                pf.unit_spans.append((node.lineno, getattr(node, "end_lineno", node.lineno)))
            for a in node.args.args + node.args.kwonlyargs:
                pf.var_names.append(a.arg)
            ds = ast.get_docstring(node)
            if ds:
                pf.comments.append(ds)
        elif isinstance(node, ast.ClassDef):
            pf.class_names.append(node.name)
            ds = ast.get_docstring(node)
            if ds:
                pf.comments.append(ds)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            pf.var_names.append(node.id)
        elif isinstance(node, ast.Import):
            pf.imports.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = ("." * node.level) + (node.module or "")
            pf.imports.append(base)
            pf.imports.extend(f"{base}.{a.name}" for a in node.names if a.name != "*")
    ds = ast.get_docstring(tree)
    if ds:
        pf.comments.append(ds)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type == tokenize.COMMENT:
                pf.comments.append(tok.string.lstrip("#").strip())
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    if not pf.units:
        pf.status = PARSE_NOFUNC
    return pf


_JAVA_TYPE_DECLS = {"class_declaration", "interface_declaration", "enum_declaration",
                    "record_declaration", "annotation_type_declaration"}
_JAVA_METHODS = {"method_declaration", "constructor_declaration",
                 "compact_constructor_declaration"}


def _parse_java(code: str) -> ParsedFile:
    parser = ts_parser("java")
    if parser is None:
        return ParsedFile(PARSE_ERROR)
    data = code.encode("utf-8", "replace")
    try:
        tree = parser.parse(data)
    except Exception:
        return ParsedFile(PARSE_ERROR)
    root = tree.root_node
    pf = ParsedFile(PARSE_OK)

    def text(n):
        return data[n.start_byte:n.end_byte].decode("utf-8", "replace")

    stack = [root]
    while stack:
        n = stack.pop()
        t = n.type
        if t in _JAVA_TYPE_DECLS:
            nm = n.child_by_field_name("name")
            if nm is not None:
                pf.class_names.append(text(nm))
        elif t in _JAVA_METHODS:
            nm = n.child_by_field_name("name")
            if nm is not None:
                pf.method_names.append(text(nm))
            if n.child_by_field_name("body") is not None:
                seg = text(n).strip()
                if len(seg) > MIN_UNIT_CHARS:
                    pf.units.append(seg)
                    pf.unit_spans.append((n.start_point[0] + 1, n.end_point[0] + 1))
        elif t == "variable_declarator" or t == "formal_parameter":
            nm = n.child_by_field_name("name")
            if nm is not None:
                pf.var_names.append(text(nm))
        elif t in ("line_comment", "block_comment"):
            pf.comments.append(text(n).strip("/* \n\t"))
        elif t == "import_declaration":
            pf.imports.append(re.sub(r"^import\s+(static\s+)?|;\s*$", "", text(n).strip()).strip())
        elif t == "package_declaration":
            pf.package = re.sub(r"^package\s+|;\s*$", "", text(n).strip()).strip()
        stack.extend(reversed(n.children))

    if root.has_error:
        pf.status = PARSE_PARTIAL if pf.units else PARSE_ERROR
    elif not pf.units:
        pf.status = PARSE_NOFUNC
    return pf


def parse_file(path: str, code: str, project_language: str) -> ParsedFile:
    """Parse one file with the project-language parser."""
    lang = file_language(path, project_language)
    if lang is None:
        return ParsedFile(NO_PARSER)
    if not code:
        return ParsedFile(PARSE_NOFUNC)
    return _parse_python(code) if lang == "python" else _parse_java(code)


if __name__ == "__main__":
    j = parse_file("A.java", 'package a.b;\nimport java.util.List;\n'
                   'public class A { /** doc */ int x; public A(){} int f(int y){ return y; } '
                   'record R(int z){} }', "java")
    print(j.status, j.class_names, j.method_names, j.var_names, j.imports, j.package, len(j.units))
    p = parse_file("a.py", 'import os\nfrom x.y import z\n# hi\nclass C:\n  """d"""\n'
                   '  def m(self, q):\n    r = q\n    return r\n', "python")
    print(p.status, p.class_names, p.method_names, p.var_names, p.imports, p.comments, len(p.units))
    print(parse_file("a.yml", "a: 1", "python").status, parse_file("a.py", "def (", "python").status)
