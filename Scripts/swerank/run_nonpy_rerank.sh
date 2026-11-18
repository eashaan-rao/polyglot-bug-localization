#!/bin/bash
# Third internal review, 2.4: full SweRank (retriever + reranker) on the
# "+ non-Python files only" corpus (SweRankNonPy). Same settings as SweRankAll.
set -uo pipefail
cd "$(dirname "$0")/../.."
PY=third_party/venv_swerank/bin/python; OBJ1=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
LOG=results/obj2/logs; export HF_HUB_OFFLINE=1 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True SWERANK_EMBED_BATCH=16
free() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1; }
wait_mb() { while [ "$(free)" -lt "$1" ]; do echo "$(date '+%T') waiting for $1 MiB free"; sleep 300; done; }
share() { read F T < <(nvidia-smi --query-gpu=memory.free,memory.total --format=csv,noheader,nounits | head -1 | tr -d ','); python3 -c "print(round(min(0.95, ($T - $F + 20480) / $T), 2))"; }
ok=1
for F in 1 2; do
  for attempt in 1 2 3; do
    wait_mb 6144
    SWERANK_ADD=nonpy $PY -u -W ignore Scripts/swerank/extend_corpus.py --fold $F --variant nonpy_top --with-top >> $LOG/nonpy_rerank_retrieve.log 2>&1 && break
  done
  want=$(wc -l < data/obj2/locagent/instances/fold$F/test.jsonl)
  for attempt in 1 2 3; do
    wait_mb 22528
    U=$(share); echo "$(date '+%F %T') fold $F rerank attempt $attempt: SWERANK_GPU_UTIL=$U"
    SWERANK_GPU_UTIL=$U $PY -u -W ignore Scripts/swerank/run_swerank.py rerank --fold $F \
      --src-name retrieval_nonpy_top --out-name rerank_nonpy_top --determinism 0 >> $LOG/nonpy_rerank_fold$F.log 2>&1
    n=$(ls data/obj2/swerank/rerank_nonpy_top/fold$F 2>/dev/null | wc -l)
    echo "fold $F: $n of $want reranked"
    [ "$n" -eq "$want" ] && break
  done
  if [ "$n" -eq "$want" ]; then
    $PY -u -W ignore Scripts/swerank/extend_corpus.py --fold $F --rerank-scores --variant nonpy_top --tech SweRankNonPy >> $LOG/nonpy_rerank_fold$F.log 2>&1
  else ok=0; fi
done
if [ $ok -eq 1 ]; then
  $OBJ1 -u -W ignore Scripts/analysis/append_eval.py SweRankNonPy > $LOG/append_eval_swerank_nonpy.log 2>&1
  echo "$(date '+%F %T') done"
else
  echo "reranking incomplete; no evaluation"
fi
