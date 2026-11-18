#!/bin/bash
# Isolating ablation for SweRank's extended corpus (second review), retriever only.
set -uo pipefail
cd "$(dirname "$0")/../.."
PY=third_party/venv_swerank/bin/python; OBJ1=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
LOG=results/obj2/logs; export HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True SWERANK_EMBED_BATCH=16
wait_free() { while [ "$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)" -lt 6144 ]; do sleep 300; done; }
run() { # variant add maxchunks tech
  for F in 1 2; do
    for attempt in 1 2 3; do
      wait_free
      SWERANK_ADD=$2 SWERANK_MAX_CHUNKS=$3 $PY -u -W ignore Scripts/swerank/extend_corpus.py --fold $F --variant $1 >> $LOG/ablation_$1.log 2>&1 && break
    done
    $PY -u -W ignore Scripts/swerank/extend_corpus.py --fold $F --variant $1 --scores --tech $4 >> $LOG/ablation_$1.log 2>&1
  done
}
run nonpy nonpy 40 SweRankEmbedNonPy
run pytest pytest 40 SweRankEmbedPyTest
run cap10 all 10 SweRankEmbedAllCap10
while tmux has-session -t rq1all 2>/dev/null || tmux has-session -t cochange 2>/dev/null; do sleep 60; done
$OBJ1 -u -W ignore Scripts/analysis/append_eval.py SweRankEmbedNonPy SweRankEmbedPyTest SweRankEmbedAllCap10 > $LOG/append_eval_ablation.log 2>&1
echo "ablation done" >> $LOG/ablation_done.log
