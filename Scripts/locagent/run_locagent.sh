#!/bin/bash
# LocAgent adapter, step 3: serve LocAgent's fine-tuned model with vLLM and run
# LocAgent unmodified on exported instances whose indexes are pre-built.
#
#   Scripts/locagent/run_locagent.sh <instances_dir> <output_dir> [num_processes]
#
# Model (LocAgent paper's fine-tuned Qwen2.5-Coder), LOCAGENT_SIZE=7b|32b:
#   7b  czlll/Qwen2.5-Coder-7B-CL,  bf16 (15 GB), no quantization   [default]
#   32b czlll/Qwen2.5-Coder-32B-CL, bf16 weights are 65.5 GB; would need FP8
#       weights + FP8 KV cache. On the shared 44.4 GiB L40 it ran out of memory
#       while loading (2026-10-30: 39.5 GiB used by vLLM + 4.9 GiB by another
#       user's processes), so it is not used for the main runs.
# Sampling = LocAgent defaults
# (temperature 1.0, top_p 0.8, repetition_penalty 1.05, 2 samples merged by MRR).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INST_DIR="$(realpath "$1")"; OUT="$(realpath -m "$2")"; NPROC="${3:-4}"
SIZE="${LOCAGENT_SIZE:-7b}"
if [ "$SIZE" = "32b" ]; then
    MODEL=czlll/Qwen2.5-Coder-32B-CL; REV=2c5334fe175b708fd8faa27df06e8b296c40cfaf
    QUANT=(--quantization fp8 --kv-cache-dtype fp8); NAME=ft-qwen-32B-128k
else
    MODEL=czlll/Qwen2.5-Coder-7B-CL; REV=28e5a47fc0436a8bd18999262eea7e0464341c23
    QUANT=(); NAME=ft-qwen-7B-128k
fi
# LocAgent only accepts a fixed list of --model names; the authors served their
# fine-tuned models behind an OpenAI-compatible endpoint as openai/ft-qwen-7B /
# openai/ft-qwen-32B (these route through LocAgent's Qwen prompting path).
PORT="${LOCAGENT_PORT:-8011}"
# 128k context, as in the paper (fine-tuned with max_token 128k; config allows
# 131072 positions via linear RoPE scaling x4). 32k overflowed on airflow.
MAXLEN="${LOCAGENT_MAXLEN:-131072}"
mkdir -p "$OUT"
echo "LocAgent model: $MODEL @ $REV"

# Shared GPU: wait until enough memory is free, then size vLLM's share of the
# card to what is actually free (vLLM refuses to start if util*total > free).
# 7B bf16 needs ~14.4 GiB weights + ~7.3 GiB KV for one 128k-token request.
NEED_GIB="${LOCAGENT_MIN_FREE_GIB:-24}"
read FREE_MIB TOTAL_MIB < <(nvidia-smi --query-gpu=memory.free,memory.total --format=csv,noheader,nounits | head -1 | tr -d ',')
while [ $((FREE_MIB / 1024)) -lt "$NEED_GIB" ]; do
    echo "$(date '+%F %T') waiting for GPU: $((FREE_MIB / 1024)) GiB free, need $NEED_GIB GiB"
    sleep 120
    read FREE_MIB TOTAL_MIB < <(nvidia-smi --query-gpu=memory.free,memory.total --format=csv,noheader,nounits | head -1 | tr -d ',')
done
GPU_UTIL="${LOCAGENT_GPU_UTIL:-$(python3 -c "print(round(min(0.70, ($FREE_MIB - 1536) / $TOTAL_MIB), 2))")}"
echo "GPU: $((FREE_MIB / 1024)) GiB free -> gpu-memory-utilization $GPU_UTIL"

"$ROOT/third_party/venv_vllm/bin/vllm" serve "$MODEL" --revision "$REV" \
    --served-model-name "$NAME" "${QUANT[@]}" --max-model-len "$MAXLEN" --seed 0 \
    --gpu-memory-utilization "$GPU_UTIL" --enable-prefix-caching \
    --port "$PORT" > "$OUT/vllm_server.log" 2>&1 &
VLLM_PID=$!
trap 'kill $VLLM_PID 2>/dev/null || true' EXIT
echo "waiting for vLLM (pid $VLLM_PID) ..."
until curl -sf "http://localhost:$PORT/v1/models" >/dev/null; do
    kill -0 $VLLM_PID 2>/dev/null || { echo "vLLM exited, see $OUT/vllm_server.log"; exit 1; }
    sleep 10
done
echo "vLLM ready"

export OPENAI_API_BASE="http://localhost:$PORT/v1"
export OPENAI_API_KEY="none"
export GRAPH_INDEX_DIR="$ROOT/data/obj2/locagent/index/graph_index"
export BM25_INDEX_DIR="$ROOT/data/obj2/locagent/index/BM25_index"
cd "$ROOT/third_party/LocAgent"
# Local fix to LocAgent (Scripts/locagent/locagent_obj2.patch, 2026-11-05): its tool-output
# eval() fell back only on SyntaxError, so outputs like "lib/ansible/..." raised NameError,
# killed the worker and blocked the parent forever. Applied if not yet applied.
PATCH="$ROOT/Scripts/locagent/locagent_obj2.patch"
git apply --reverse --check "$PATCH" 2>/dev/null || git apply "$PATCH" \
    || { echo "LocAgent patch does not apply"; exit 1; }
export PYTHONPATH="$(pwd)"
# Watchdog. In the 2026-10-31 pilot one LocAgent worker blocked forever after a
# normal LLM reply (futex wait; LocAgent's own --timeout never fired) and held
# the run for 7 h. LocAgent therefore runs in its own process group; if its log
# does not change for LOCAGENT_STALL_MIN minutes the group is killed and
# LocAgent is restarted -- it skips instances already in loc_outputs.jsonl, so
# only unfinished ones are retried (each hang costs ~LOCAGENT_STALL_MIN; the
# 2026-11-04 fold-1 run hung at start, so the budget is 20, not 2). After
# LOCAGENT_MAX_RESTARTS restarts the remaining instances are left without
# output (scored as misses, and listed; resume them before evaluating).
STALL_S=$(( ${LOCAGENT_STALL_MIN:-30} * 60 ))
MAX_RESTARTS="${LOCAGENT_MAX_RESTARTS:-20}"
PYLOC="$ROOT/third_party/venv_locagent/bin/python"
COMMON=(--dataset "$INST_DIR" --split test --model "openai/$NAME" --output_folder "$OUT"
        --num_processes "$NPROC" --use_function_calling --simple_desc)
for attempt in $(seq 1 $((MAX_RESTARTS + 1))); do
    echo "$(date '+%F %T') LocAgent localize, attempt $attempt"
    setsid "$PYLOC" auto_search_main.py "${COMMON[@]}" --localize >> "$OUT/locagent_run.log" 2>&1 &
    AGENT=$!
    STALLED=0
    while kill -0 "$AGENT" 2>/dev/null; do
        sleep 60
        LAST=$(stat -c %Y "$OUT/localize.log" 2>/dev/null || date +%s)
        if [ $(( $(date +%s) - LAST )) -gt "$STALL_S" ]; then
            echo "$(date '+%F %T') LocAgent stalled > ${LOCAGENT_STALL_MIN:-30} min -- killing process group $AGENT"
            kill -TERM -- "-$AGENT" 2>/dev/null || true
            sleep 15
            kill -KILL -- "-$AGENT" 2>/dev/null || true
            STALLED=1
            break
        fi
    done
    wait "$AGENT" 2>/dev/null || true
    [ "$STALLED" = "0" ] && break
done
echo "$(date '+%F %T') LocAgent merge"
"$PYLOC" auto_search_main.py "${COMMON[@]}" --merge >> "$OUT/locagent_run.log" 2>&1
"$ROOT/../Objective1/obj1/bin/python" - "$INST_DIR/test.jsonl" "$OUT/loc_outputs.jsonl" <<'PYEOF'
import json, sys
inst = [json.loads(l)["instance_id"] for l in open(sys.argv[1])]
done = set()
try:
    done = {json.loads(l)["instance_id"] for l in open(sys.argv[2])}
except FileNotFoundError:
    pass
miss = [i for i in inst if i not in done]
print(f"LocAgent: {len(inst) - len(miss)}/{len(inst)} instances with output"
      + (f"; without output: {miss}" if miss else ""))
PYEOF

if [ "${LOCAGENT_PROBE:-1}" = "1" ]; then
    echo "contamination probe ..."
    "$ROOT/../Objective1/obj1/bin/python" "$ROOT/Scripts/locagent/contamination_probe.py" \
        --instances "$INST_DIR/test.jsonl" --out "$OUT/contamination_probe.csv" --port "$PORT" \
        --model "$NAME"
fi
