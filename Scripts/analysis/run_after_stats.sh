#!/bin/bash
cd "$(dirname "$0")/../.."
PY=/home/cs21d002_eashaan/PhD/Objective1/obj1/bin/python; LOG=results/obj2/logs
while tmux has-session -t stats 2>/dev/null; do sleep 30; done
tail -1 $LOG/stats_ablation.log | grep -q "exit 0" || { echo "stats failed"; exit 1; }
for s in review_checks review_checks2 paper_tables paper_figures; do
  $PY -W ignore Scripts/analysis/$s.py > $LOG/$s.log 2>&1 || { echo "$s failed"; tail -20 $LOG/$s.log; exit 1; }
  echo "$s ok"
done
