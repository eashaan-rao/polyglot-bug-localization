#!/bin/bash
# LocAgent run-to-run variance (decided 2026-11-01). LocAgent samples at
# temperature 1.0, so two runs on the same bug can differ. On a fixed random
# subset of fold-1 instances (seeded), LocAgent is run REPEATS more times; the
# repeats are stored as technique "LocAgentRep" (seed = repeat index), apart
# from the main run (LocAgent, seed 0), and compared with it bug by bug.
#
#   bash Scripts/locagent/run_variance.sh [N=100] [REPEATS=2]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT"
PY=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
N="${1:-100}"; REPEATS="${2:-2}"
INST=data/obj2/locagent/instances_variance
$PY -W ignore Scripts/locagent/export_instances.py --folds 1 --subset "$N" --out "$INST"
third_party/venv_locagent/bin/python Scripts/locagent/build_indexes.py \
    --instances "$INST/fold1/test.jsonl" --workers 16
for k in $(seq 1 "$REPEATS"); do
    OUT="results/obj2/locagent/variance_fold1_rep$k"
    LOCAGENT_PROBE=0 Scripts/locagent/run_locagent.sh "$INST/fold1" "$OUT" "${LOCAGENT_NPROC:-2}"
    $PY Scripts/locagent/to_scores.py --instances "$INST/fold1/test.jsonl" \
        --outputs "$OUT/merged_loc_outputs_mrr.jsonl" --fold 1 --seed "$k" --tech LocAgentRep
done
echo "variance repeats done: scores/LocAgentRep/fold1/seed{1..$REPEATS}"
