#!/bin/bash
# Java stage (decided 2026-11-01), elasticsearch -- the largest Java project.
#
#   J0  smoke checks (small split, full-size snapshots; ~1 GPU-hour):
#       BM25, FLIM, BLAZE, BLAZE_ALL on elasticsearch      -> Java parsing / chunking paths
#       FLIM fold 2 on liquibase                          -> rolling-origin split
#       BLAZE seed 42 on elasticsearch                    -> recorded-LR path for later seeds
#       peak RAM of every step (/usr/bin/time -v)
#   J1  the real run, kept for the paper: elasticsearch, fold 1, seed 13,
#       BM25 -> FLIM -> BLAZE (LR grid) -> BLAZE_ALL ablation -> evaluate -> stats.
#       Starts only if J0 finished without errors.
#
#   tmux new -s obj2_java "bash Scripts/run_pilot_java.sh 2>&1 | tee results/obj2/logs/pilot_java.log"
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
PY=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
ES=elastic/elasticsearch
FAIL=0
run() {   # run <label> <env...> -- python args ; records peak RSS and failures
    local label="$1"; shift
    echo "== $label =="
    if ! env "$@" /usr/bin/time -f "   [$label] wall %e s, peak RSS %M KB" \
            $PY -u -W ignore Scripts/run_obj2_experiments.py; then
        echo "!! $label exited non-zero"; FAIL=1
    fi
}
check_errors() {  # driver logs ERROR lines instead of exiting
    if grep -qE "  ERROR \(attempt" "results/obj2/logs/pilot_java.log" 2>/dev/null; then
        echo "!! ERROR lines in the log"; FAIL=1
    fi
}

echo "######## J0 smoke ########"
run "J0 BM25 ES"      OBJ2_SMOKE=1 OBJ2_TECHS=BM25      OBJ2_PROJECTS=$ES
run "J0 FLIM ES"      OBJ2_SMOKE=1 OBJ2_TECHS=FLIM      OBJ2_PROJECTS=$ES OBJ2_SEEDS=13
run "J0 BLAZE ES"     OBJ2_SMOKE=1 OBJ2_TECHS=BLAZE     OBJ2_PROJECTS=$ES OBJ2_SEEDS=13
run "J0 BLAZE_ALL ES" OBJ2_SMOKE=1 OBJ2_TECHS=BLAZE_ALL OBJ2_PROJECTS=$ES OBJ2_SEEDS=13
run "J0 BLAZE ES s42" OBJ2_SMOKE=1 OBJ2_TECHS=BLAZE     OBJ2_PROJECTS=$ES OBJ2_SEEDS=42
run "J0 FLIM liq f2"  OBJ2_SMOKE=1 OBJ2_TECHS=FLIM      OBJ2_PROJECTS=liquibase/liquibase OBJ2_FOLDS=2 OBJ2_SEEDS=13
echo "== J0 evaluate + stats =="
OBJ2_SMOKE=1 $PY -W ignore Scripts/evaluate.py || FAIL=1
OBJ2_SMOKE=1 $PY -W ignore Scripts/analysis/obj2_stats.py > /dev/null || FAIL=1
check_errors
if [ "$FAIL" != "0" ]; then echo "######## J0 FAILED -- J1 not started ########"; exit 1; fi
echo "######## J0 passed ########"

echo "######## J1 elasticsearch fold 1 seed 13 ########"
run "J1 BM25"      OBJ2_TECHS=BM25      OBJ2_PROJECTS=$ES OBJ2_FOLDS=1
run "J1 FLIM"      OBJ2_TECHS=FLIM      OBJ2_PROJECTS=$ES OBJ2_FOLDS=1 OBJ2_SEEDS=13
run "J1 BLAZE"     OBJ2_TECHS=BLAZE     OBJ2_PROJECTS=$ES OBJ2_FOLDS=1 OBJ2_SEEDS=13
run "J1 BLAZE_ALL" OBJ2_TECHS=BLAZE_ALL OBJ2_PROJECTS=$ES OBJ2_FOLDS=1 OBJ2_SEEDS=13
echo "== J1 evaluate + stats =="
$PY -W ignore Scripts/evaluate.py
$PY -W ignore Scripts/analysis/obj2_stats.py > /dev/null
echo "######## Java stage done (FAIL=$FAIL) ########"
