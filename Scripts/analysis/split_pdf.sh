#!/bin/bash
# Split paper/main.pdf into the manuscript (up to the references) and the
# supplementary appendices (from Appendix A), using the page of label app:related.
# Run after compiling main.tex.
set -euo pipefail
cd "$(dirname "$0")/../../paper"
first=$(grep -oE 'newlabel\{app:related\}\{\{[^}]*\}\{[0-9]+\}' main.aux | grep -oE '[0-9]+\}$' | tr -d '}')
last=$(pdfinfo main.pdf | awk '/^Pages:/{print $2}')
tmp=$(mktemp -d)
pdfseparate main.pdf "$tmp/p-%03d.pdf" 2>/dev/null
pdfunite $(for i in $(seq 1 $((first-1))); do printf "$tmp/p-%03d.pdf " $i; done) manuscript.pdf 2>/dev/null
pdfunite $(for i in $(seq $first $last); do printf "$tmp/p-%03d.pdf " $i; done) supplementary_appendices.pdf 2>/dev/null
rm -rf "$tmp"
echo "manuscript.pdf: pages 1-$((first-1)); supplementary_appendices.pdf: pages $first-$last of main.pdf"
