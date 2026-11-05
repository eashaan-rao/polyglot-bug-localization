#!/bin/bash
# Follow-up to Scripts/run_full.sh (2026-11-05).
# Step 4 of the full run (LocAgent fold 1: ansible, airflow) stopped with 5/424
# instances because of a LocAgent bug that killed workers and hung the run
# (fixed by Scripts/locagent/locagent_obj2.patch; its placeholder scores were
# archived to results/obj2/scores_archive/locagent_fold1_rest_incomplete_2026-11-05/).
# This script waits until the obj2_full tmux session has ended (no GPU
# contention), resumes that LocAgent run -- finished instances are skipped --
# rebuilds its scores and re-runs evaluation + statistics.
#
#   tmux new -d -s obj2_followup "bash Scripts/run_followup.sh 2>&1 | tee -a results/obj2/logs/followup.log"
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
PY=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
INST=data/obj2/locagent/instances_fold1_rest
OUT=results/obj2/locagent/fold1_rest

echo "$(date '+%F %T') waiting for the obj2_full session to end ..."
while tmux has-session -t obj2_full 2>/dev/null; do sleep 300; done

echo "######## $(date '+%F %T') resume LocAgent fold 1 (ansible, airflow) ########"
LOCAGENT_PROBE=0 Scripts/locagent/run_locagent.sh "$INST/fold1" "$OUT" "${LOCAGENT_NPROC:-2}" &&
$PY Scripts/locagent/to_scores.py --instances "$INST/fold1/test.jsonl" \
    --outputs "$OUT/merged_loc_outputs_mrr.jsonl" --fold 1 \
|| echo "!! LocAgent fold1_rest resume failed"

echo "######## $(date '+%F %T') evaluate + statistics ########"
$PY -W ignore Scripts/evaluate.py && $PY -W ignore Scripts/analysis/obj2_stats.py > /dev/null
echo "######## $(date '+%F %T') follow-up done ########"
