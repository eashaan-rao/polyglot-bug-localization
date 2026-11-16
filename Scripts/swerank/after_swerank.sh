#!/bin/bash
# After SweRank (tmux swerank_after): wait for tmux swerank_rerank to end, check
# both folds produced score files, back up the current evaluation/statistics,
# then re-run the evaluator (all techniques) and the statistics.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
PY=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python
LOG=results/obj2/logs
while tmux has-session -t swerank_rerank 2>/dev/null; do sleep 60; done
for F in 1 2; do
    grep -q "^exit 0" $LOG/swerank_rerank_fold$F.log && grep -q "^exit 0" $LOG/swerank_scores_fold$F.log \
        || { echo "$(date '+%F %T') SweRank fold $F incomplete, not evaluating"; exit 1; }
done
BK=results/obj2/scores_archive/eval_stats_before_swerank_$(date +%F)
mkdir -p "$BK" && cp -a results/obj2/eval results/obj2/stats "$BK"/ && echo "backup -> $BK"
echo "$(date '+%F %T') evaluate"
$PY -W ignore Scripts/evaluate.py || { echo "evaluate failed"; exit 1; }
echo "$(date '+%F %T') stats"
$PY -W ignore Scripts/analysis/obj2_stats.py > /dev/null || { echo "stats failed"; exit 1; }
echo "$(date '+%F %T') done"
