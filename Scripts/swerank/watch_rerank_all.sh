#!/bin/bash
# Watchdog for tmux rerank_all: if the run ends without "done", restart it (finished
# bugs are skipped on restart; the run waits for 22 GiB free GPU memory). At most 3 restarts.
cd "$(dirname "$0")/../.."
for attempt in 1 2 3; do
  while tmux has-session -t rerank_all 2>/dev/null; do sleep 120; done
  grep -q "done$" results/obj2/logs/run_rerank_all.log && { echo "$(date '+%F %T') finished"; exit 0; }
  echo "$(date '+%F %T') rerank_all stopped without finishing; restart $attempt"
  cp results/obj2/logs/run_rerank_all.log results/obj2/logs/run_rerank_all.attempt$attempt.log
  tmux new-session -d -s rerank_all "bash Scripts/swerank/run_rerank_all.sh > results/obj2/logs/run_rerank_all.log 2>&1"
  sleep 60
done
echo "$(date '+%F %T') giving up after 3 restarts"
