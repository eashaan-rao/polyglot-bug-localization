#!/bin/bash
# SweRank reranker on the extended corpus (tmux rerank_all), restart of step 3 of
# run_night.sh. vLLM 0.8.5 (SweRank's pin) counts other processes' GPU memory
# against gpu_memory_utilization, so the share is set to (memory used by others
# + 20 GiB) / total: our process gets ~20 GiB (14.2 weights + KV cache).
set -uo pipefail
cd "$(dirname "$0")/../.."
PY=third_party/venv_swerank/bin/python; OBJ1=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
LOG=results/obj2/logs; export HF_HUB_OFFLINE=1
share() { read F T < <(nvidia-smi --query-gpu=memory.free,memory.total --format=csv,noheader,nounits | head -1 | tr -d ','); python3 -c "print(round(min(0.95, ($T - $F + 20480) / $T), 2))"; }
wait_free() { while [ "$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)" -lt 22528 ]; do echo "$(date '+%T') waiting for 22 GiB free"; sleep 300; done; }
ok=1
for F in 1 2; do
  wait_free
  U=$(share); echo "$(date '+%F %T') fold $F: SWERANK_GPU_UTIL=$U"
  SWERANK_GPU_UTIL=$U $PY -u -W ignore Scripts/swerank/run_swerank.py rerank --fold $F \
    --src-name retrieval_all_top --out-name rerank_all --determinism 0 > $LOG/rerank_all_fold$F.log 2>&1
  rc=$?; echo "exit $rc" >> $LOG/rerank_all_fold$F.log
  n=$(ls data/obj2/swerank/rerank_all/fold$F 2>/dev/null | wc -l)
  want=$(wc -l < data/obj2/locagent/instances/fold$F/test.jsonl)
  echo "fold $F: exit $rc, $n of $want reranked"
  if [ $rc -eq 0 ] && [ "$n" -eq "$want" ]; then
    $PY -u -W ignore Scripts/swerank/extend_corpus.py --fold $F --rerank-scores >> $LOG/rerank_all_fold$F.log 2>&1
  else ok=0; fi
done
if [ $ok -eq 1 ]; then
  $OBJ1 -u -W ignore Scripts/analysis/append_eval.py SweRankAll > $LOG/append_eval_swerankall_rr.log 2>&1
  $OBJ1 -W ignore Scripts/analysis/obj2_stats.py > $LOG/stats_after_rerank_all.log 2>&1
  echo "$(date '+%F %T') done"
else
  echo "reranking incomplete; no scores written"
fi
