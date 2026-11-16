#!/bin/bash
# SweRank, stages after retrieval (tmux swerank_rerank):
#   wait for the retrieval session -> rerank fold 1, 2 (SweRank's sequential path) -> scores.
# vLLM counts every process's GPU memory against its budget, so reranking
# starts only after retrieval has released the GPU.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
PY=third_party/venv_swerank/bin/python
LOG=results/obj2/logs
export HF_HUB_OFFLINE=1

while tmux has-session -t swerank_retrieve 2>/dev/null; do sleep 30; done
for F in 1 2; do
    grep -q "^exit 0" $LOG/swerank_retrieve_fold$F.log || { echo "retrieval fold $F did not finish cleanly"; exit 1; }
done

# share of the shared L40: at most 0.55, at most what is free now
read FREE TOTAL < <(nvidia-smi --query-gpu=memory.free,memory.total --format=csv,noheader,nounits | head -1 | tr -d ',')
export SWERANK_GPU_UTIL=$(python3 -c "print(round(min(0.55, ($FREE - 1536) / $TOTAL), 2))")
echo "$(date '+%F %T') GPU free $((FREE / 1024)) GiB -> SWERANK_GPU_UTIL=$SWERANK_GPU_UTIL"

# verify (2026-11-08): batched loop != sequential (0/6 identical) -> main run uses the sequential path

for F in 1 2; do
    $PY -u -W ignore Scripts/swerank/run_swerank.py rerank --fold $F --determinism 3 > $LOG/swerank_rerank_fold$F.log 2>&1
    echo "exit $?" >> $LOG/swerank_rerank_fold$F.log
    $PY -u -W ignore Scripts/swerank/run_swerank.py scores --fold $F > $LOG/swerank_scores_fold$F.log 2>&1
    echo "exit $?" >> $LOG/swerank_scores_fold$F.log
done
echo "$(date '+%F %T') SweRank done"
