#!/bin/bash

BASE_DIR="/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze"
PY="/mnt/data/toolmaze_project/envs/toolmaze/bin/python"
cd "$BASE_DIR"

echo "=========================================================="
echo "STARTING FULL 4,000 TASK BENCHMARK: GEMINI 3 FLASH PREVIEW"
echo "Date: $(date)"
echo "Base Directory: $BASE_DIR"
echo "=========================================================="

CATEGORIES=("c1" "c2" "c3" "c4")
AGENTS=("baseline" "care")

for cat in "${CATEGORIES[@]}"; do
    for agent in "${AGENTS[@]}"; do
        RUN_ID="gemini_${agent}_${cat}_full"
        echo ""
        echo "----------------------------------------------------------"
        echo "LAUNCHING: Agent=$agent | Category=$cat | RunID=$RUN_ID"
        echo "Time: $(date)"
        echo "----------------------------------------------------------"

        $PY evaluation/scripts/run_eval_care.py \
            --config "evaluation/configs/gemini_eval_config_${cat}.yaml" \
            --backend gemini \
            --model gemini-3-flash-preview \
            --agent-type "$agent" \
            --category "$cat" \
            --max-workers 2 \
            --no-resume \
            --run-id "$RUN_ID" || {
                echo "WARNING: $RUN_ID encountered an exit code error at $(date). Proceeding to next batch..."
            }

        echo "COMPLETED: $RUN_ID at $(date)"
    done
done

echo "=========================================================="
echo "ALL 4,000 TASKS GEMINI BENCHMARK COMPLETED!"
echo "Date: $(date)"
echo "=========================================================="
