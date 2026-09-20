#!/bin/bash
# ToolMaze Server Setup Script
# Run this on the college server (10.18.1.16) after SSH login
# Usage: bash setup_server.sh

set -e

echo "========================================="
echo "ToolMaze Enhancement — Server Setup"
echo "========================================="

# Step 1: System Info
echo ""
echo "=== Step 1: Gathering System Info ==="
echo "--- OS ---"
cat /etc/os-release 2>/dev/null || echo "Unknown OS"
echo "--- CPU ---"
lscpu 2>/dev/null | head -15 || echo "lscpu not available"
echo "--- RAM ---"
free -h 2>/dev/null || echo "free not available"
echo "--- GPU ---"
nvidia-smi 2>/dev/null || echo "!! NO NVIDIA GPU DETECTED — this is a CRITICAL blocker"
echo "--- CUDA ---"
nvcc --version 2>/dev/null || echo "CUDA toolkit not installed"
echo "--- Disk ---"
df -h / 2>/dev/null
echo "--- Python ---"
python3 --version 2>/dev/null || echo "Python3 not installed"
echo "--- Docker ---"
docker --version 2>/dev/null || echo "Docker not installed"

echo ""
echo "=== SAVE THE OUTPUT ABOVE — needed for project planning ==="
echo ""

# Step 2: Create project directory
echo "=== Step 2: Setting up project directory ==="
PROJECT_DIR="$HOME/toolmaze_enhanced"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Step 3: Create conda environment (if conda available)
echo "=== Step 3: Python environment ==="
if command -v conda &> /dev/null; then
    echo "Conda found. Creating environment..."
    conda create -n toolmaze python=3.10 -y 2>/dev/null || echo "Conda env may already exist"
    echo "Activate with: conda activate toolmaze"
else
    echo "Conda not found. Using system Python or venv..."
    python3 -m venv venv 2>/dev/null || echo "venv creation failed — install python3-venv"
    echo "Activate with: source venv/bin/activate"
fi

# Step 4: Clone ToolMaze
echo "=== Step 4: Cloning ToolMaze ==="
if [ ! -d "ToolMaze" ]; then
    git clone https://github.com/Zhudongsheng75/ToolMaze.git
else
    echo "ToolMaze already cloned"
fi

# Step 5: Install dependencies
echo "=== Step 5: Installing dependencies ==="
cd ToolMaze
pip install -r requirements.txt 2>/dev/null || echo "pip install failed — activate venv first"
pip install -r evaluation/requirements.txt 2>/dev/null || echo "evaluation deps failed"

# Step 6: Install vLLM for local model serving
echo "=== Step 6: Installing vLLM ==="
pip install vllm 2>/dev/null || echo "vLLM install failed — may need CUDA"

# Step 7: Download dataset from HuggingFace
echo "=== Step 7: Downloading ToolMaze dataset ==="
pip install huggingface_hub 2>/dev/null
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(repo_id='dongsheng/ToolMaze', repo_type='dataset', local_dir='data')
print('Dataset downloaded successfully!')
" 2>/dev/null || echo "Dataset download failed — check huggingface_hub"

echo ""
echo "========================================="
echo "Setup complete! Next steps:"
echo "1. Check GPU info above — critical for model serving"
echo "2. Activate environment: conda activate toolmaze (or source venv/bin/activate)"
echo "3. Start vLLM server: python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen2.5-7B-Instruct --port 8000"
echo "4. Run baseline: python evaluation/scripts/run_eval.py --agent-type vllm --model Qwen2.5-7B-Instruct --modes P0"
echo "========================================="
