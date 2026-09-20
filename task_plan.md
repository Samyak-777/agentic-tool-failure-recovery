# Task Plan — ToolMaze Enhancement Project

## Phase 1: Environment Setup & Baseline (Weeks 1–3)
- [ ] SSH into server (10.18.1.16) from campus, gather full hardware specs
- [ ] Install Python 3.10+, CUDA, PyTorch, vLLM/Ollama
- [ ] Clone ToolMaze repo: `git clone https://github.com/Zhudongsheng75/ToolMaze.git`
- [ ] Install ToolMaze dependencies: `pip install -r requirements.txt`
- [ ] Download Qwen-2.5-7B-Instruct model weights
- [ ] Run ToolMaze baseline evaluation on Qwen-2.5-7B
- [ ] Record baseline TSR, PRR, RC numbers
- [ ] Document any reproducibility discrepancies vs. paper

## Phase 2: Agent Framework Implementation (Weeks 4–5)
- [ ] Implement ReAct-style agent adapter for ToolMaze
- [ ] Implement SWE-Agent-inspired ACI agent adapter
- [ ] Add token counting + latency instrumentation layer
- [ ] Run both agents on ToolMaze, compare with Phase 1 baseline

## Phase 3: Core Improvements (Weeks 6–9)
### 3A: Semantic Output Validation (SOV)
- [ ] Implement 5 validation checks (range, type, schema, temporal, cross-ref)
- [ ] Integrate SOV into agent pipeline
- [ ] Test detection rate on P3/P4 perturbations

### 3B: Cost-Aware Recovery Engine (CARE)
- [ ] Implement recovery budget system
- [ ] Implement strategy router (retry → reroute → backtrack → give-up)
- [ ] Implement DAG-aware rerouting logic
- [ ] Integrate with both agent frameworks

### 3C: Extended Perturbations
- [ ] Design cascading failure mode (P5)
- [ ] Implement in ToolMaze perturbation engine
- [ ] Generate P5 test cases

### 3D: Recovery Strategy Classification
- [ ] Implement action tagger per step
- [ ] Implement detection latency metric
- [ ] Generate strategy distribution visualizations

## Phase 4: Full Evaluation (Weeks 10–11)
- [ ] Run: 2–4 models × 5 perturbation modes × 4 complexity levels × 3 seeds
- [ ] Compute all metrics (TSR, PRR, PRR_cost, RC_calls, RC_tokens, RC_time)
- [ ] Statistical significance tests (p < 0.05)
- [ ] Generate paper figures (bar charts, heatmaps, radar charts)
- [ ] Run ablation studies (SOV-only, CARE-only, SOV+CARE)

## Phase 5: Cloud RCA Demo (Weeks 12–13) — Stretch Goal
- [ ] Deploy tools as HTTP microservices (FastAPI)
- [ ] Add real-world failure injection (latency, rate limits)
- [ ] Run improved agent on live endpoints
- [ ] Build RCA dashboard

## Phase 6: Paper Writing (Weeks 13–16)
- [ ] Write LaTeX paper (8 pages, ACL format)
- [ ] Create reproducibility checklist
- [ ] Internal review and revision
- [ ] Final submission
