#!/bin/bash
# Overnight GPU chain (tmux night), 2026-11-16. Shared L40: every step waits for
# enough free memory and sizes vLLM to what is free.
#  1. extended-corpus SweRank retrieval, storing the top-100 documents
#  2. closed-book contamination probe of the LocAgent model on all Python test bugs
#  3. SweRank's reranker on the extended corpus (sequential path) -> SweRankAll
#  4. scores, evaluation (appended), statistics
set -uo pipefail
cd "$(dirname "$0")/../.."
PY=third_party/venv_swerank/bin/python; OBJ1=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
LOG=results/obj2/logs; export HF_HUB_OFFLINE=1
free_mib() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1; }
wait_free() { while [ "$(free_mib)" -lt "$1" ]; do echo "$(date '+%T') waiting: $(free_mib) MiB free, need $1"; sleep 300; done; }
util() { read F T < <(nvidia-smi --query-gpu=memory.free,memory.total --format=csv,noheader,nounits | head -1 | tr -d ','); python3 -c "print(round(min(0.5, ($F - 1536) / $T), 2))"; }

echo "$(date '+%F %T') 1. retrieval with top-100"
for F in 1 2; do
  wait_free 4096
  SWERANK_EMBED_BATCH=16 $PY -u -W ignore Scripts/swerank/extend_corpus.py --fold $F --with-top > $LOG/night_retrieval_top_fold$F.log 2>&1
  echo "exit $?" >> $LOG/night_retrieval_top_fold$F.log
done

echo "$(date '+%F %T') 2. contamination probe"
wait_free 22000
U=$(util); echo "vLLM gpu util $U"
third_party/venv_vllm/bin/vllm serve czlll/Qwen2.5-Coder-7B-CL --revision 28e5a47fc0436a8bd18999262eea7e0464341c23 \
  --served-model-name ft-qwen-7B-128k --max-model-len 32768 --seed 0 --gpu-memory-utilization $U \
  --port 8011 > $LOG/night_probe_vllm.log 2>&1 &
VP=$!
for i in $(seq 1 90); do curl -sf http://localhost:8011/v1/models >/dev/null && break; kill -0 $VP 2>/dev/null || break; sleep 10; done
if curl -sf http://localhost:8011/v1/models >/dev/null; then
  for F in 1 2; do
    $OBJ1 -u -W ignore Scripts/locagent/contamination_probe.py --instances data/obj2/locagent/instances/fold$F/test.jsonl \
      --out results/obj2/locagent/contamination_probe_all_fold$F.csv --port 8011 > $LOG/night_probe_fold$F.log 2>&1
    echo "exit $?" >> $LOG/night_probe_fold$F.log
  done
else
  echo "vLLM did not start; see night_probe_vllm.log"
fi
kill $VP 2>/dev/null; sleep 30

echo "$(date '+%F %T') 3. reranker on the extended corpus"
for F in 1 2; do
  wait_free 22000
  SWERANK_GPU_UTIL=$(util) $PY -u -W ignore Scripts/swerank/run_swerank.py rerank --fold $F \
    --src-name retrieval_all_top --out-name rerank_all --determinism 0 > $LOG/night_rerank_all_fold$F.log 2>&1
  echo "exit $?" >> $LOG/night_rerank_all_fold$F.log
  $PY -u -W ignore Scripts/swerank/extend_corpus.py --fold $F --rerank-scores >> $LOG/night_rerank_all_fold$F.log 2>&1
done

echo "$(date '+%F %T') 4. evaluation and statistics"
while tmux has-session -t stats 2>/dev/null; do sleep 60; done
$OBJ1 -u -W ignore Scripts/analysis/append_eval.py SweRankAll > $LOG/night_append_eval.log 2>&1
$OBJ1 -W ignore Scripts/analysis/obj2_stats.py > $LOG/night_stats.log 2>&1
echo "$(date '+%F %T') night chain done"
