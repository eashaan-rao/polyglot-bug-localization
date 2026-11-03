#!/bin/bash
# Full run (method frozen 2026-11-03; docs/JOURNAL_PLAN.md D1-D16).
# Resumable and ordered so that partial progress is already usable: fold 1
# first, then fold 2, then extra seeds, then the LocAgent variance repeats.
# Every step skips runs whose score file exists; GPU steps wait for free
# memory on the shared L40; one failing step does not stop the queue.
#
#   tmux new -s obj2_full "bash Scripts/run_full.sh 2>&1 | tee -a results/obj2/logs/full_run.log"
#
# Already done before this script (kept, not repeated):
#   localstack fold 1: BM25, FLIM, BLAZE (seed 13), LocAgent
#   elasticsearch fold 1: BM25, FLIM, BLAZE, BLAZE_ALL (seed 13)
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
PY=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
PYLOC=third_party/venv_locagent/bin/python
ALL=elastic/elasticsearch,liquibase/liquibase,apache/dolphinscheduler,ansible/ansible,apache/airflow,localstack/localstack
SEED_PROJECTS="${SEED_PROJECTS:-localstack/localstack,apache/dolphinscheduler,liquibase/liquibase}"
RUN_VARIANCE="${RUN_VARIANCE:-1}"
mkdir -p results/obj2/logs

step() { echo; echo "######## $(date '+%F %T') $1 ########"; }
drv()  { env "$@" $PY -u -W ignore Scripts/run_obj2_experiments.py || echo "!! step failed: $*"; }
locagent() {  # locagent <fold> <projects> <out-name>
    local fold="$1" projects="$2" name="$3"
    local INST="data/obj2/locagent/instances_$name"
    $PY -W ignore Scripts/locagent/export_instances.py --folds "$fold" --projects "$projects" --out "$INST" &&
    $PYLOC Scripts/locagent/build_indexes.py --instances "$INST/fold$fold/test.jsonl" --workers 16 &&
    Scripts/locagent/run_locagent.sh "$INST/fold$fold" "results/obj2/locagent/$name" "${LOCAGENT_NPROC:-2}" &&
    $PY Scripts/locagent/to_scores.py --instances "$INST/fold$fold/test.jsonl" \
        --outputs "results/obj2/locagent/$name/merged_loc_outputs_mrr.jsonl" --fold "$fold" \
    || echo "!! LocAgent $name failed"
}

step "1 BM25, all projects, folds 1-2 (CPU)"
drv OBJ2_TECHS=BM25 OBJ2_FOLDS=1,2 OBJ2_PROJECTS=$ALL

step "2 fold 1, seed 13: FLIM + BLAZE"
drv OBJ2_TECHS=FLIM,BLAZE OBJ2_FOLDS=1 OBJ2_SEEDS=13 OBJ2_PROJECTS=$ALL

step "3 fold 1, seed 13: BLAZE_ALL ablation"
drv OBJ2_TECHS=BLAZE_ALL OBJ2_FOLDS=1 OBJ2_SEEDS=13 OBJ2_PROJECTS=$ALL

step "4 LocAgent fold 1 (ansible, airflow; localstack done in the pilot)"
locagent 1 ansible/ansible,apache/airflow fold1_rest

step "5 fold 2, seed 13: FLIM + BLAZE"
drv OBJ2_TECHS=FLIM,BLAZE OBJ2_FOLDS=2 OBJ2_SEEDS=13 OBJ2_PROJECTS=$ALL

step "6 LocAgent fold 2 (three Python projects)"
locagent 2 ansible/ansible,apache/airflow,localstack/localstack fold2

step "7 seeds 42, 2027 on fold 1 ($SEED_PROJECTS)"
drv OBJ2_TECHS=FLIM,BLAZE OBJ2_FOLDS=1 OBJ2_SEEDS=42,2027 OBJ2_PROJECTS=$SEED_PROJECTS

if [ "$RUN_VARIANCE" = "1" ]; then
    step "8 LocAgent variance repeats (2 x 100 fold-1 bugs)"
    bash Scripts/locagent/run_variance.sh 100 2 || echo "!! LocAgent variance failed"
fi

step "9 evaluate + statistics"
$PY -W ignore Scripts/evaluate.py && $PY -W ignore Scripts/analysis/obj2_stats.py > /dev/null
echo "######## $(date '+%F %T') full run done ########"
grep -c "^!! " results/obj2/logs/full_run.log 2>/dev/null | xargs -I{} echo "failed steps: {}"
