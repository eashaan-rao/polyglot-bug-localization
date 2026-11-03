#!/bin/bash
# Phase C pilot: one Python project, fold 1, one seed, all four techniques,
# then evaluation and statistics. Writes to the normal score locations, so a
# passing pilot is not repeated by the full run (the driver skips existing
# score files).
#
#   tmux new -s obj2_pilot "bash Scripts/run_pilot.sh 2>&1 | tee results/obj2/logs/pilot.log"
#
# Resumable: techniques whose score file exists are skipped; GPU runs wait for
# free memory on the shared L40 (OBJ2_GPU_MIN_FREE_GIB_BLAZE=30, _FLIM=12,
# LOCAGENT_MIN_FREE_GIB=24).
#
# Gates checked afterwards (docs/JOURNAL_PLAN.md):
#   G-a every run finishes, manifests written      G-b best epoch < cap / loss flattens
#   G-c LR selection on validation MAP recorded (lr_selection_*.json) for BLAZE and FLIM
#   G-d LocAgent: indexes built, >90 % instances with output, throughput measured
#   G-e evaluate.py + obj2_stats.py run end to end; scores above the random baseline
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
PY=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
PROJECT="${PILOT_PROJECT:-localstack/localstack}"
SEED="${PILOT_SEED:-13}"
mkdir -p results/obj2/logs

echo "== BM25 (CPU) =="
OBJ2_TECHS=BM25 OBJ2_PROJECTS="$PROJECT" OBJ2_FOLDS=1 $PY -u -W ignore Scripts/run_obj2_experiments.py

echo "== FLIM (GPU): LR grid {2e-5,5e-5}, selected on validation MAP =="
OBJ2_TECHS=FLIM OBJ2_PROJECTS="$PROJECT" OBJ2_FOLDS=1 OBJ2_SEEDS="$SEED" \
    $PY -u -W ignore Scripts/run_obj2_experiments.py

echo "== BLAZE (GPU): LR grid {2e-7,2e-6,2e-5}, selected on validation MAP =="
OBJ2_TECHS=BLAZE OBJ2_PROJECTS="$PROJECT" OBJ2_FOLDS=1 OBJ2_SEEDS="$SEED" \
    $PY -u -W ignore Scripts/run_obj2_experiments.py

echo "== LocAgent (GPU, vLLM) =="
# a LocAgent failure (e.g. the shared GPU stays full) must not block evaluation
(
    set -e
    INST=data/obj2/locagent/instances_pilot
    $PY -W ignore Scripts/locagent/export_instances.py --folds 1 --projects "$PROJECT" --out "$INST"
    third_party/venv_locagent/bin/python Scripts/locagent/build_indexes.py \
        --instances "$INST/fold1/test.jsonl" --workers 16
    OUT=results/obj2/locagent/pilot_fold1
    Scripts/locagent/run_locagent.sh "$INST/fold1" "$OUT" "${LOCAGENT_NPROC:-2}"
    $PY Scripts/locagent/to_scores.py --instances "$INST/fold1/test.jsonl" \
        --outputs "$OUT/merged_loc_outputs_mrr.jsonl" --fold 1
) || echo "!! LocAgent step failed -- continuing with evaluation"

echo "== evaluate + statistics =="
$PY -W ignore Scripts/evaluate.py
$PY -W ignore Scripts/analysis/obj2_stats.py
echo "== pilot done =="
