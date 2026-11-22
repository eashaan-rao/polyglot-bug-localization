"""Check the cross-document numbers written into main.tex (S-...) and
supplement.tex (M-...) against the labels in supplement.aux and main.aux.
Run after a build (build.sh does this)."""
import re, sys

def aux_numbers(path):
    out = {}
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"\\newlabel\{([^}]*)\}\{\{([^}]*)\}", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out

def written(path, prefix):
    pat = re.compile(r"\\newlabel\{" + prefix + r"([^}]*)\}\{\{([^}]*)\}")
    return pat.findall(open(path, encoding="utf-8").read())

bad = 0
for tex, prefix, aux in (("main.tex", "S-", "supplement.aux"), ("supplement.tex", "M-", "main.aux")):
    actual = aux_numbers(aux)
    for label, num in written(tex, prefix):
        if actual.get(label) != num:
            print(f"{tex}: {prefix}{label} is written as {num}, but {aux} has {actual.get(label)}")
            bad += 1
print("cross-document numbers: " + ("OK" if not bad else f"{bad} out of date"))
sys.exit(1 if bad else 0)
