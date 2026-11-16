#!/bin/bash
# Save the localstack fold-1 seed-13 FLIM and BLAZE models (decided 2026-11-08).
# The pilot (2026-10-31) ran before model saving existed, so its scores are kept
# as the reported results and only a model is produced here. Each technique is
# retrained with the pilot's recorded LR and seed 13; the pilot's score files are
# moved aside during the run (the driver skips runs whose score file exists) and
# restored afterwards. The retrain's own scores go to
# results/obj2/scores_archive/localstack_model_retrain_2026-11-08/ (never
# evaluated) so the saved model can be compared with the pilot's scores.
#
#   tmux new -d -s obj2_retrain "bash Scripts/retrain_pilot_models.sh 2>&1 | tee -a results/obj2/logs/retrain_pilot_models.log"
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
PY=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
REPO=localstack/localstack; P=localstack_localstack
S=results/obj2/scores
BACKUP=results/obj2/scores_archive/localstack_pilot_backup_2026-11-08
OUT=results/obj2/scores_archive/localstack_model_retrain_2026-11-08

echo "$(date '+%F %T') waiting for the obj2_followup session to end ..."
while tmux has-session -t obj2_followup 2>/dev/null; do sleep 300; done

# permanent copy first, so the pilot files can never be lost
mkdir -p "$BACKUP" "$OUT"
for T in FLIM BLAZE; do
    mkdir -p "$BACKUP/$T"
    cp -p "$S/$T/fold1/seed13/$P.parquet" "$S/$T/fold1/seed13/$P.json" \
          "$S/$T/fold1/lr_selection_$P.json" "$BACKUP/$T/" || { echo "!! backup failed"; exit 1; }
done

restore() {   # put the pilot files back for technique $1
    cp -p "$BACKUP/$1/$P.parquet" "$BACKUP/$1/$P.json" "$S/$1/fold1/seed13/"
    cp -p "$BACKUP/$1/lr_selection_$P.json" "$S/$1/fold1/"
}

for T in FLIM BLAZE; do
    echo "######## $(date '+%F %T') retrain $T fold1 seed13 $REPO ########"
    rm "$S/$T/fold1/seed13/$P.parquet" "$S/$T/fold1/seed13/$P.json"
    OBJ2_TECHS=$T OBJ2_FOLDS=1 OBJ2_SEEDS=13 OBJ2_PROJECTS=$REPO \
        $PY -u -W ignore Scripts/run_obj2_experiments.py || echo "!! $T retrain failed"
    mkdir -p "$OUT/$T"
    mv "$S/$T/fold1/seed13/$P.parquet" "$S/$T/fold1/seed13/$P.json" "$OUT/$T/" 2>/dev/null
    restore "$T"
    cmp -s "$BACKUP/$T/$P.parquet" "$S/$T/fold1/seed13/$P.parquet" \
        && cmp -s "$BACKUP/$T/lr_selection_$P.json" "$S/$T/fold1/lr_selection_$P.json" \
        && echo "pilot $T files restored (identical)" || echo "!! pilot $T restore mismatch"
    ls -d "data/obj2/models/$T/fold1/seed13/$P" && echo "model saved" || echo "!! no model for $T"
done
echo "######## $(date '+%F %T') retrain done ########"
