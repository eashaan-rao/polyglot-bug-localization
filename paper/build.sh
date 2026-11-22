#!/bin/bash
# Build the paper (main.pdf) and the supplementary material (supplement.pdf).
# They cross-reference each other through xr, so both are compiled twice.
set -e
cd "$(dirname "$0")"
run() { pdflatex -interaction=nonstopmode -halt-on-error "$1.tex" > /dev/null || { echo "LaTeX error in $1.tex (see $1.log)"; exit 1; }; }
run main; run supplement
bibtex main > /dev/null; bibtex supplement > /dev/null
run main; run supplement; run main; run supplement
for f in main supplement; do
  echo "$f.pdf: $(pdfinfo $f.pdf | awk '/^Pages:/{print $2}') pages, $(grep -c 'undefined' $f.log) undefined references"
done
pdflatex -interaction=nonstopmode replication_tables.tex > /dev/null && pdflatex -interaction=nonstopmode replication_tables.tex > /dev/null && echo "replication_tables.pdf: $(pdfinfo replication_tables.pdf | awk '/^Pages:/{print $2}') pages"
