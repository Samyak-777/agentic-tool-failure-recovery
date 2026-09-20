#!/bin/bash
# Batch evaluation script for configured task category

# Run evaluation for all modes
python3 evaluation/scripts/run_eval.py \
    --config evaluation/configs/openai_eval_config.yaml \
    --modes P0 P1 P2 P3 P4
