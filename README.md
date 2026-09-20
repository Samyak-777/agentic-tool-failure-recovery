# 🛡️ Agentic Tool Failure Recovery (CARE)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![CUDA 12.1](https://img.shields.io/badge/CUDA-12.1-green.svg)](https://developer.nvidia.com/cuda-toolkit)

**Final Year Capstone Project — B.Tech Computer Science & Engineering**  
*Research & Implementation of Cost-Aware Recovery and Semantic Validation for Fault-Tolerant LLM Tool Agents.*

---

## 👥 Team & Roles
* **Samyak** — Architecture, Deployment & SOV
* **Mrunmayee** — Evaluation, Metrics & RL Exploration
* **Anupam Ayush** — Agent Modeling & Experimentation

---

## 🎯 Project Overview
Autonomous LLM agents fail drastically under real-world tool execution perturbations (silent corrupted returns, transient network drops, permanent service outages). Current models either hallucinate on corrupted outputs or enter infinite trial-and-error loops that blow up token cost.

This repository implements:
1. **ToolMaze Benchmark Harness**: Automated evaluation across 2,000 perturbed tasks ($C1$–$C4 \times P0$–$P4$) with 270 simulated tools.
2. **SOV (Semantic Output Validation)**: Pre-reasoning verification layer catching silent $P3$/$P4$ errors before LLM hallucination.
3. **CARE (Cost-Aware Recovery Engine)**: Dynamic DAG topological rerouter optimizing Recovery Cost ($RC$) and token efficiency.

---

## 🔄 Team Collaboration Workflow (Preventing Server Conflicts)

> ⚠️ **CRITICAL RULE:** **DO NOT** edit code directly on the college server!  
> Direct edits on the server lead to file conflicts, overwritten work, and broken test runs.

### Standard Development Cycle:
```
1. Clone / Pull repo on your local machine
   git pull origin main

2. Create a feature branch for your work
   git checkout -b feature/yourname-feature-description

3. Make your code changes & test locally
   git add .
   git commit -m "feat(agent): add semantic type check in sov"

4. Push your branch to GitHub
   git push origin feature/yourname-feature-description

5. Open a Pull Request on GitHub & merge into main

6. On the Server: Only pull clean commits to run experiments!
   cd /mnt/data/toolmaze_project/agentic-tool-failure-recovery
   git pull origin main
```

---

## 🖥️ Server Environment & Paths (`10.18.1.16`)

The project environment is deployed on the server's 3.6 TB storage partition:

| Component | Path on Server |
|---|---|
| **Project Codebase** | `/mnt/data/toolmaze_project/agentic-tool-failure-recovery` |
| **Python 3.10 Env** | `/mnt/data/toolmaze_project/envs/toolmaze` |
| **Python Executable** | `/mnt/data/toolmaze_project/envs/toolmaze/bin/python` |
| **Benchmark Dataset** | `/mnt/data/toolmaze_project/ToolMaze/data` (2,000 tasks, 400 templates) |
| **Model Weights** | `/mnt/data/toolmaze_project/models` |
| **GPU Specs** | NVIDIA TITAN RTX (24 GB VRAM) + 128 GB System RAM |

### Activating Environment on the Server:
```bash
ssh <username>@10.18.1.16
source /mnt/data/toolmaze_project/miniconda3/bin/activate /mnt/data/toolmaze_project/envs/toolmaze
cd /mnt/data/toolmaze_project/agentic-tool-failure-recovery
```

---

## 📂 Repository Layout
```
├── architecture/       # B.L.A.S.T. Layer 1: SOPs and architectural specifications
├── ToolMaze/           # Core benchmark runtime, tool corpus (270 tools), and evaluation engine
│   ├── toolmaze/       # ExecutionContext and ToolExecutor
│   ├── tools/          # Tool definitions (YAML) and plugins (Python)
│   └── evaluation/     # Agents (OpenAI, Anthropic, vLLM, CARE), sandbox, judge, metrics
├── tools/              # Server management and deployment automation scripts
├── gemini.md           # Project Constitution & Data Schemas
├── task_plan.md        # Master checklist and phase tracking
├── findings.md         # Research findings and gap analysis
└── progress.md         # Milestones and progress log
```
