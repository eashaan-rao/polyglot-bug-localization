#!/bin/bash
# Extended-corpus SweRank retriever (tmux swerank_all): both folds, scores, evaluation.
set -uo pipefail
cd "$(dirname "$0")/../.."
PY=third_party/venv_swerank/bin/python; OBJ1=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
LOG=results/obj2/logs; export HF_HUB_OFFLINE=1
until grep -q "done" $LOG/list_candidates_fold2.log 2>/dev/null; do sleep 30; done
# shared GPU: start (and restart after an out-of-memory exit) only with >= 4 GiB free;
# finished bugs are skipped on restart
wait_gpu() { while [ "$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)" -lt 4096 ]; do sleep 300; done; }
for F in 1 2; do
  for attempt in 1 2 3 4 5 6; do
    wait_gpu
    $PY -u -W ignore Scripts/swerank/extend_corpus.py --fold $F >> $LOG/swerank_all_fold$F.log 2>&1
    rc=$?; echo "exit $rc (attempt $attempt)" >> $LOG/swerank_all_fold$F.log
    [ $rc -eq 0 ] && break
  done
  [ $rc -eq 0 ] || { echo "fold $F failed"; exit 1; }
  $PY -u -W ignore Scripts/swerank/extend_corpus.py --fold $F --scores >> $LOG/swerank_all_fold$F.log 2>&1
done
# wait for the hybrid job (it rewrites the same eval files)
while tmux has-session -t hybrid 2>/dev/null; do sleep 60; done
$OBJ1 -u -W ignore Scripts/analysis/append_eval.py SweRankEmbedAll > $LOG/append_eval_swerankall.log 2>&1; echo "exit $?" >> $LOG/append_eval_swerankall.log
