# 🎓 First Evaluation PPT — Complete Guide + NotebookLM Prompt

> **Project:** Enhanced ToolMaze: Improving Dynamic Replanning and Anomaly Recovery in LLM Agents with Cost-Aware Recovery  
> **Evaluation:** First Evaluation (Semester 1 — Research Proposal)  
> **Date:** Tuesday, September 2, 2026  
> **Institute:** VNIT Nagpur — CSE Department

---

## PART A: NotebookLM Prompt (Copy-Paste This Entire Prompt)

---

```
You are an expert academic presentation designer for an Indian engineering institute (VNIT Nagpur). Generate a professional, research-oriented PowerPoint presentation for a Final Year B.Tech CSE First Evaluation (Research Proposal stage). Follow every instruction precisely:

=== DESIGN RULES (MANDATORY — Apply to EVERY Slide) ===
1. Background of every slide: PURE WHITE (#FFFFFF). No gradients, no textures, no colored backgrounds.
2. Top-left corner of EVERY slide: VNIT logo (small, ~1.2 cm height). The user will insert the logo manually.
3. Slide dimensions: 16:9 widescreen.
4. Font family: Calibri or Arial only. No decorative fonts.
5. Title text: 24–28pt, bold, dark navy (#1B2A4A).
6. Body text: 16–18pt, dark charcoal (#333333).
7. Accent color for highlights, arrows, borders: deep blue (#2563EB) and teal (#0D9488).
8. Diagrams: clean vector-style boxes/arrows with thin borders. Use colors: blue (#2563EB), teal (#0D9488), amber (#D97706), red (#DC2626), green (#16A34A). NO clipart. NO stock photos.
9. Every slide must have a thin colored line (2pt, navy #1B2A4A) at the bottom spanning full width, with a small right-aligned slide number.
10. Maximum 6 bullet points per slide. Each bullet ≤ 2 lines.
11. Use diagrams, flowcharts, tables, and visual frameworks wherever possible — professors absorb visuals faster than text.
12. Tone: formal academic, third-person, research-oriented. No informal language.
13. Total slides: 28–32 slides.

=== SLIDE-BY-SLIDE CONTENT (Follow this structure exactly) ===

--- SLIDE 1: TITLE SLIDE ---
Center-aligned. No bullet points.
Line 1 (large, 28pt, bold, navy): "Enhanced ToolMaze: Reliable and Cost-Aware Recovery from Tool Failures in LLM Agents"
Line 2 (18pt, teal): "Final Year Project Proposal — First Evaluation"
Line 3 (16pt, dark gray): "Computer Science and Engineering Department"
Line 4 (16pt, dark gray): "Visvesvaraya National Institute of Technology (VNIT), Nagpur"
Below that, a clean table (no heavy borders) with two columns:

| Name                  | Roll No      |
|-----------------------|--------------|
| Anupam Ayush          | BT23CSE026   |
| Mrunmayee Limaye      | BT23CSE019   |
| Reeti Gupta           | BT23CSE013   |
| Samyak Borkar         | BT23CSE028   |

Below the table: "Under the guidance of Prof. Anshul Agrawal"
VNIT logo at top-left corner (placeholder box).

--- SLIDE 2: PRESENTATION OUTLINE ---
Title: "Presentation Outline"
A numbered vertical list (with small icons or colored circles):
1. Background & Motivation
2. Problem Statement
3. Literature Review
4. Research Gaps Identified
5. Proposed Architecture (CARE Framework)
6. Semantic Validation — What & How
7. Recovery Controller & DAG-Aware Recovery
8. Evaluation Methodology
9. Research Questions
10. Timeline & Deliverables
11. Expected Contributions
12. Risk Analysis
13. References

--- SLIDE 3: BACKGROUND — What Are LLM Agents? ---
Title: "Background: LLM-Based Agents"
Left side (60%): Explain with 4 concise bullets:
• LLM agents are autonomous systems that use Large Language Models to reason, plan, and execute multi-step tasks.
• They interact with external tools (APIs, databases, search engines) to gather information and perform actions.
• Example: An agent planning a trip calls a weather API, a flight-booking API, and a hotel API sequentially.
• Agent frameworks: ReAct, AutoGen, LangGraph, CrewAI — all rely on correct tool outputs for accurate task completion.

Right side (40%): DIAGRAM — A simple flow:
[User Query] → [LLM Agent (Reasoning)] → [Tool 1] → [Tool 2] → [Tool 3] → [Final Answer]
Show this as a horizontal pipeline with arrows connecting rounded boxes.

--- SLIDE 4: BACKGROUND — What Is Tool Failure? ---
Title: "Background: Tool Failures in Agentic Workflows"
Define two categories with a 2×2 matrix diagram:

DIAGRAM: 2×2 Matrix Table (use colored cells)
Columns: "Transient (clears on retry)" | "Permanent (persists; must reroute)"
Rows: "Explicit (error codes, exceptions)" | "Implicit (valid syntax, wrong semantics)"

Cell P1 (blue): "HTTP 429, Timeout → retry works"
Cell P2 (amber): "Tool permanently removed → must find alternative tool"
Cell P3 (teal): "Stale data, wrong values → retry with validation"
Cell P4 (red): "Consistently corrupted output → must detect + reroute"

Below the matrix: "P3 and P4 are the hardest — the tool does NOT report an error, but the output is semantically wrong."

--- SLIDE 5: THE CORE PROBLEM — Visual Example ---
Title: "The Core Problem: Silent Semantic Corruption"
A visual example spanning the full slide:

DIAGRAM: Show a 3-step agent workflow:
Step 1: Agent asks "Get weather for Tokyo" → Tool returns {"city": "Osaka", "temp": 28, "status": "sunny"} — JSON is valid!
Step 2: Agent uses this weather data to plan outdoor activities in "Tokyo"
Step 3: Agent gives final answer based on WRONG city's weather

Highlight with a red warning icon: "The JSON was syntactically valid. No error code was returned. But the result is for the WRONG CITY."
Arrow pointing to: "This is an IMPLICIT PERMANENT failure (P4) — the hardest to detect."

--- SLIDE 6: PROBLEM STATEMENT ---
Title: "Problem Statement"
A single, prominent statement in a bordered box (light blue background):

"How can we design a reliable and cost-efficient recovery mechanism for tool-using LLM agents that:
(1) Detects both explicit and implicit tool failures,
(2) Selects an appropriate recovery strategy (retry, verify, reroute, or abort),
(3) Improves Task Success Rate (TSR) and Perturbation Recovery Rate (PRR),
(4) While minimizing unnecessary Recovery Cost (RC)?"

Below: "Current agents rely entirely on LLM reasoning for recovery, which is inconsistent, expensive, and fails to detect implicit semantic corruption."

--- SLIDE 7: LITERATURE REVIEW — ToolMaze (Base Paper) ---
Title: "Literature Review: ToolMaze [Zhu et al., 2026]"
Left side (55%):
• Published: arXiv:2606.05806, June 2026
• Affiliations: Shanghai AI Lab, Baidu Inc., ECNU, Soochow U., Shandong U.
• Benchmark for evaluating agent resilience to tool failures
• 2,000 perturbed tasks across 4 complexity levels (C1–C4) × 4 perturbation modes (P1–P4)
• Metrics defined: TSR (Task Success Rate), PRR (Perturbation Recovery Rate), RC (Recovery Cost)

Right side (45%): DIAGRAM — ToolMaze Evaluation Framework
Show a 2D grid: X-axis = C1, C2, C3, C4; Y-axis = P0, P1, P2, P3, P4
Each cell represents a test configuration. Color-code by difficulty (green → yellow → orange → red).

--- SLIDE 8: KEY FINDINGS FROM TOOLMAZE ---
Title: "Critical Findings from ToolMaze"
Use a combination of bullets + a BAR CHART:

BAR CHART: "PRR Drop Under Different Perturbation Modes"
X-axis: P1 (Explicit Transient), P2 (Explicit Permanent), P3 (Implicit Transient), P4 (Implicit Permanent)
Y-axis: PRR (%)
Approximate values: P1: ~75%, P2: ~55%, P3: ~45%, P4: ~38%
Color bars from green (P1) graduating to red (P4).
Add an annotation arrow pointing to P3/P4 bars: "~37% drop — agents over-trust corrupted outputs"

Below the chart, 3 key bullet points:
• Fault-tolerance scales 3.66× slower than basic task execution as model size increases.
• Complex topologies (C3, C4) trap agents in futile trial-and-error loops.
• Failure-aware prompting helps but does NOT close the performance gap.

--- SLIDE 9: LITERATURE REVIEW — SWE-Agent & Other Related Work ---
Title: "Related Work"
A TABLE spanning the slide:

| Work | Year | Key Contribution | Relevance to Our Work |
|------|------|-------------------|----------------------|
| ToolMaze [Zhu et al.] | 2026 | Benchmark for tool-failure recovery | Base paper — provides evaluation framework |
| SWE-Agent [Yang et al.] | 2024 | Agent-Computer Interface design | ACI patterns improve error visibility |
| AgentDebug [OpenReview] | 2026 | Targeted feedback for failure modes | Complements recovery strategy classification |
| LangGraph / CrewAI | 2024–26 | Circuit breakers, retry/timeout policies | Industry patterns we adopt and formalize |
| ReAct [Yao et al.] | 2023 | Reason + Act interleaving | Baseline agent paradigm for comparison |
| Reflexion [Shinn et al.] | 2023 | Self-reflection after failure | Recovery via verbal self-correction |

--- SLIDE 10: RESEARCH GAPS IDENTIFIED ---
Title: "Research Gaps Identified in Current Literature"
Show as a numbered list with colored icons (gap → impact → our fix):

DIAGRAM: Use a 3-column layout for each gap:
Column 1 (red icon): Gap
Column 2 (amber): Impact
Column 3 (green): Our Proposed Fix

Gap 1: No cost-aware recovery optimization
→ Impact: Agents retrying 20× vs 3× get same PRR score
→ Fix: Cost-weighted PRR metric

Gap 2: Over-trust detection left to LLM's native reasoning
→ Impact: Agents blindly propagate corrupted values (PRR drops 37%)
→ Fix: Deterministic semantic validation layer

Gap 3: No recovery strategy classification
→ Impact: Cannot distinguish intelligent replanning from random walk
→ Fix: Tag & classify each recovery action (retry/reroute/backtrack/abort)

Gap 4: Static perturbation profiles only
→ Impact: Agents may memorize which tools fail
→ Fix: Dynamic/cascading perturbation mode (P5)

--- SLIDE 11: OUR NOVELTY — What Makes This Different ---
Title: "Our Contribution: The CARE Architecture"
Subtitle: "Cost-Aware Recovery Engine"

Center: A DIAGRAM showing the 7 novel components in a layered architecture:

Layer 1 (bottom, blue): "Deterministic Semantic Validation"
Layer 2 (teal): "Structured Failure Diagnosis (not just VALID/INVALID)"
Layer 3 (amber): "Failure-State Tracking & Tool Memory"
Layer 4 (green): "DAG-Aware Alternative Path Selection"
Layer 5 (purple): "Dynamic Recovery Prompts with Evidence"
Layer 6 (navy): "Cost-Aware Control: Retry Limits + Loop Detection"
Layer 7 (top, red): "Selective LLM Use for Ambiguous Cases Only"

Right side: A callout box:
"Central Research Question: Does this hybrid deterministic–LLM architecture improve PRR and TSR while controlling RC?"

--- SLIDE 12: PROPOSED ARCHITECTURE — Full System Diagram ---
Title: "Proposed System Architecture"
FULL-SLIDE FLOWCHART (the most important diagram):

[User Task] → [Main Agent (LLM)] → [Tool Call] → [Tool Response]
                                                        ↓
                                              [Semantic Validator]
                                              (Schema → Types → Ranges → Cross-field → Entity → State → Cross-tool)
                                                        ↓
                                            ┌─── PASS ──→ [Continue to next step]
                                            │
                                      [FAIL / SUSPICIOUS]
                                            ↓
                                    [Failure Diagnosis Module]
                                    (Classify: transient? permanent? semantic? stale? contradictory?)
                                            ↓
                                    [Recovery Controller]
                              ┌────┬────┬────┬────┐
                           RETRY  VERIFY  REROUTE  ABORT
                              ↓      ↓       ↓       ↓
                        [Re-call  [LLM    [DAG     [Terminate
                         same    semantic  path     with
                         tool]   check]   select]  report]
                              └────┴────┴────┘
                                      ↓
                              [Post-Recovery Validation]
                                      ↓
                              [Continue / Escalate]

Use color-coded boxes. Add a cost meter icon on the side showing "Budget Tracking."

--- SLIDE 13: SEMANTIC VALIDATION — Detailed Checks ---
Title: "Semantic Validation: The 10-Layer Check Hierarchy"
DIAGRAM: A vertical pyramid/funnel showing 10 layers from cheapest (top) to most expensive (bottom):

Level 1: Schema & Required Fields (cheapest ✓)
Level 2: Data Types & Structural Validity
Level 3: Value Ranges & Constraints
Level 4: Cross-Field Consistency
Level 5: Temporal Consistency (stale timestamps)
Level 6: Entity Consistency (request vs response)
Level 7: Consistency with Agent's Accumulated State
Level 8: Cross-Tool Consistency
Level 9: Business/Domain Rules
Level 10: Independent Verification via LLM (most expensive ✗)

Arrow on the side: "Cheap deterministic checks FIRST → Expensive LLM reasoning ONLY if needed"
Note at bottom: "Output is NOT just VALID/INVALID — it is structured evidence: {schema: PASS, range: PASS, entity: FAIL, reason: 'requested Tokyo, got Osaka', confidence: 0.96}"

--- SLIDE 14: SEMANTIC VALIDATION — Concrete Example ---
Title: "Semantic Validation: Worked Example"
Show a concrete step-by-step example:

Input Request: "Get weather for Tokyo"
Tool Response: {"city": "Osaka", "temperature": 28, "humidity": 65, "status": "sunny"}

CHECK TABLE:
| Check Layer | Result | Evidence |
|-------------|--------|----------|
| Schema | ✅ PASS | All required fields present |
| Data Types | ✅ PASS | All types correct |
| Value Range | ✅ PASS | Temperature 28°C is reasonable |
| Entity Match | ❌ FAIL | Requested "Tokyo" but response contains "Osaka" |
| Confidence | 0.96 | High confidence this is corrupted |

VERDICT: FAIL — Entity mismatch detected with high confidence.
→ Diagnosis: Implicit Permanent Failure → Action: REROUTE to alternative weather tool.

--- SLIDE 15: FAILURE DIAGNOSIS MODULE ---
Title: "Failure Diagnosis: Beyond VALID/INVALID"
Left side: DIAGRAM — Decision tree showing diagnosis flow:

[Validation Failed]
├── Error code returned? → YES → Explicit Failure
│   ├── Same error on retry? → Permanent (P2) → REROUTE
│   └── Clears on retry? → Transient (P1) → RETRY
└── No error code → Implicit Failure
    ├── Same corruption repeats? → Permanent (P4) → REROUTE
    └── Clears on retry? → Transient (P3) → RETRY with validation

Right side: Failure Memory Table
| Tool ID | Failure Count | Last Failure Type | Status |
|---------|--------------|-------------------|--------|
| weather_api_v2 | 3 | Entity mismatch | BLOCKED |
| stock_api | 1 | Timeout | ACTIVE |
| flight_search | 0 | — | TRUSTED |

--- SLIDE 16: RECOVERY CONTROLLER ---
Title: "Recovery Controller: Four Recovery Actions"
DIAGRAM: Four parallel vertical lanes, each with an icon, description, and when-to-use:

🔄 RETRY
When: Transient failure (P1, P3)
How: Re-call same tool, validate again
Budget: Max 3 retries per tool

✅ VERIFY
When: Suspicious but uncertain
How: Use LLM semantic reasoning or cross-reference with another tool
Budget: Max 1 verify per step

🔀 REROUTE
When: Persistent failure (P2, P4) or retries exhausted
How: DAG-aware alternative path selection
Budget: Must have valid alternative in task DAG

🛑 ABORT
When: No valid recovery path exists
How: Terminate gracefully with failure report
When: All alternatives exhausted or budget exceeded

Below: "Each action is LOGGED with: action type, evidence, cost (tokens + calls), and outcome."

--- SLIDE 17: DAG-AWARE RECOVERY ---
Title: "DAG-Aware Recovery: Using Task Graph Structure"
FULL-SLIDE DIAGRAM:

Show a sample DAG (Directed Acyclic Graph) for a task:
Nodes: T1 → T2 → T3 → T5 → T6 (Primary Path)
                └→ T4 → T5       (Alternative Path 1)
       T1 → T7 → T8 → T6        (Alternative Path 2)

Mark T3 with a red X: "Tool T3 FAILED (persistent)"
Show the agent's recovery:
Step 1: Remove all paths containing T3
Step 2: Enumerate remaining valid paths: [T1→T2→T4→T5→T6] and [T1→T7→T8→T6]
Step 3: Select lowest-cost alternative

Callout: "The agent uses the known DAG structure rather than asking the LLM to invent a recovery route, reducing unnecessary calls and loops."

--- SLIDE 18: DYNAMIC RECOVERY PROMPT ---
Title: "Dynamic Recovery Prompt: Evidence-Based LLM Planning"
Show a template of the recovery prompt:

PROMPT TEMPLATE (in a code-style box):
```
Task Goal: [original user request]
Failed Tool: weather_api_v2
Failure Evidence:
  - Check: entity_match → FAIL
  - Reason: Requested "Tokyo", received "Osaka"
  - Confidence: 0.96
  - Previous attempts: 2 retries, same result
Blocked Tools: [weather_api_v2]
Available Alternative Paths:
  - Path A: weather_api_v3 → [cost: 1 call]
  - Path B: web_scraper_weather → [cost: 2 calls]
Remaining Budget: 5 tool calls, 2000 tokens
Action Required: Select recovery action and justify.
```

Callout: "The LLM receives structured evidence and constrained choices, NOT 'figure out what went wrong.'"

--- SLIDE 19: COST-AWARE CONTROL ---
Title: "Cost-Aware Recovery: Preventing Wasteful Exploration"
DIAGRAM + FORMULA:

Left side: Show a "cost meter" gauge visualization:
- Green zone: 0–3 extra calls (efficient recovery)
- Yellow zone: 4–7 extra calls (acceptable)
- Red zone: 8+ extra calls (wasteful — should abort)

Right side: Formula box:
"Recovery Cost (RC) = Additional tool calls + Additional LLM calls beyond optimal path"
"Cost-Weighted PRR = PRR × (1 / log₂(1 + RC))"
"This penalizes agents that succeed but waste excessive resources."

Below: THREE mechanisms to prevent waste:
1. Retry Budget: Maximum 3 retries per tool per task
2. Loop Detection: If same state is visited twice → escalate or abort
3. Tool Memory: Persistently failing tools are temporarily blocked

--- SLIDE 20: TOPOLOGICAL COMPLEXITY LEVELS ---
Title: "Task Complexity Levels in ToolMaze"
DIAGRAM: Show 4 DAG structures side by side:

C1: Linear Chain (4 nodes) — 1 alternative path
[A] → [B] → [C] → [D]  (with one bypass)

C2: Diamond / Parallel Branches — 2–3 alternative paths
[A] → [B] → [D]
[A] → [C] → [D]

C3: Multi-Layered DAG — 3–5 alternative paths
(Show a more complex graph with multiple layers)

C4: Complex Mesh — 5+ alternative paths
(Show the most complex interconnected graph)

Below: "Recovery difficulty increases with complexity. C3/C4 trap current agents in futile trial-and-error loops."

--- SLIDE 21: WHY RULE-BASED FIRST? (Before RL) ---
Title: "Why Rule-Based Recovery Before Reinforcement Learning?"
DIAGRAM: A staircase/progression visual:

Step 1 (current): Rule-Based Recovery
→ Interpretable: we can see exactly why a response was flagged
→ Controllable: decisions can be explicitly tested
→ Debuggable: rule failures are easier to inspect
→ Generates trajectories for RL training

Step 2 (Semester 2): RL Recovery Policy
→ Learns optimal retry/reroute/abort decisions from experience
→ State: task state + failure evidence + tool reliability + remaining budget
→ Actions: retry, verify, reroute, abort
→ Reward: +1 for recovery success, penalties for wasted calls and loops

Arrow: "Rule-based system is the FOUNDATION for RL, not a dead-end prototype."

--- SLIDE 22: EXPERIMENTAL PLAN — Staged Ablation ---
Title: "Experimental Plan: Staged Ablation Study"
TABLE with checkmarks showing incremental additions:

| Configuration | Semantic Validation | Failure Diagnosis | Recovery Controller | DAG-Aware | Dynamic Prompt | Cost Control |
|---------------|:--:|:--:|:--:|:--:|:--:|:--:|
| (1) Original Agent | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| (2) + Failure-Aware Prompt | ✗ | ✗ | ✗ | ✗ | partial | ✗ |
| (3) + Semantic Validation | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| (4) + Recovery Controller | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |
| (5) + DAG-Aware Planning | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| (6) Full CARE System | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

"Each row isolates the contribution of one component. This answers: WHICH components improve PRR and WHICH reduce RC."

--- SLIDE 23: EVALUATION METRICS ---
Title: "Evaluation Metrics"
TWO SECTIONS:

Section 1: Primary Metrics (large, prominent)
PIE CHART or GAUGE for each:
• TSR (Task Success Rate) ↑ — Binary: did the agent reach the correct final answer?
• PRR (Perturbation Recovery Rate) ↑ — Of tasks with injected failures, how many recovered?
• RC (Recovery Cost) ↓ — Additional tool calls beyond the optimal path length

Section 2: Diagnostic Metrics (smaller table)
| Metric | What It Measures |
|--------|-----------------|
| Anomaly Detection Precision | Are flagged failures actually failures? |
| Anomaly Detection Recall | Are real failures being caught? |
| Failure Diagnosis Accuracy | Is the failure type classified correctly? |
| Recovery Action Accuracy | Was the right recovery action chosen? |
| False Positive Rate | Valid outputs incorrectly flagged |
| Recovery Loop Frequency | How often does the agent get stuck? |
| Tool-Call Count | Total API calls used |
| Recovery Latency | Time overhead from recovery |

--- SLIDE 24: RESEARCH QUESTIONS ---
Title: "Research Questions"
Numbered list with colored boxes:

RQ1: Can deterministic semantic validation improve recovery from implicit tool failures (P3/P4)?
RQ2: Which validation signals (schema, entity, cross-tool, temporal) contribute most to detection accuracy?
RQ3: Can DAG-aware recovery improve PRR while simultaneously reducing RC?
RQ4: Does dynamic evidence-based prompting outperform static failure-aware prompting?
RQ5 (Sem 2): Can an RL recovery policy outperform the rule-based policy on unseen failure types?
RQ6 (Future): How well does the approach transfer from simulated tool failures to realistic cloud/AIOps environments?

--- SLIDE 25: TIMELINE (GANTT CHART) ---
Title: "Project Timeline — Semester 1 & 2"
GANTT CHART spanning August 2026 → March 2027:

Phase 1 (Aug–Sep): Literature Review + ToolMaze Baseline Setup ████████
Phase 2 (Oct): Semantic Validation Layer Implementation         ████
Phase 3 (Oct–Nov): Recovery Controller + DAG-Aware Recovery       ████████
Phase 4 (Nov): Ablation Experiments + Evaluation                    ████
Phase 5 (Nov–Dec): Paper Writing + Semester 1 Submission              ████████
Phase 6 (Jan–Feb): RL Recovery Policy Training                           ████████
Phase 7 (Feb–Mar): Final Evaluation + Cloud Extension Study                 ████████

Color-code: Blue = Semester 1, Teal = Semester 2

--- SLIDE 26: INFRASTRUCTURE ---
Title: "Computational Infrastructure"
TABLE:

| Resource | Specification |
|----------|--------------|
| Server | College Server @ 10.18.1.16 (VNIT CSE) |
| GPU | NVIDIA TITAN RTX — 24 GB VRAM |
| CPU | Intel i9-9900K (8 cores, 16 threads, 5.0 GHz) |
| RAM | 128 GB DDR4 |
| Storage | 3.6 TB secondary drive (3.4 TB available) |
| OS | Ubuntu 24.04.3 LTS |
| Models | Qwen-2.5-7B-Instruct, Llama-3.1-8B-Instruct (via vLLM) |
| Framework | ToolMaze benchmark (2,000 tasks, 270 tools) |

Note: "All models are open-source and self-hosted. No proprietary API dependencies."

--- SLIDE 27: EXPECTED CONTRIBUTIONS ---
Title: "Expected Contributions"
Numbered list with academic framing:

1. A hybrid deterministic–LLM recovery architecture (CARE) for tool-using agents.
2. A 10-layer semantic validation hierarchy for detecting implicit tool failures.
3. Structured failure diagnosis with evidence and confidence scores.
4. DAG-aware recovery planning that exploits task graph structure.
5. Cost-weighted PRR metric that penalizes wasteful recovery.
6. Component-level ablation study isolating each contribution.
7. (Sem 2) RL-based recovery policy trained on rule-based trajectories.
8. (Future) Transfer study from simulated to real cloud/AIOps failures.

--- SLIDE 28: RISK ANALYSIS ---
Title: "Risk Analysis & Mitigation"
TABLE:

| Risk | Impact | Mitigation |
|------|--------|------------|
| False Positives (valid outputs flagged) | Increases RC, may reduce TSR | Evidence + confidence scoring; threshold tuning on dev set |
| False Negatives (corruption missed) | Corrupted values propagate | Multi-layer validation; cross-tool checks |
| Recovery Loops | Agent gets stuck retrying | Loop detection + retry budget (max 3) |
| Over-Conservative Recovery | Agent aborts recoverable tasks | Graduated evidence thresholds; VERIFY before REROUTE |
| Validation Overhead | Extra latency and cost | Cheap checks first; LLM only for ambiguous cases |
| Rule Brittleness | Rules may not generalize | Test on unseen corruption types; rules operate on features, not perturbation labels |

--- SLIDE 29: COMPARISON WITH EXISTING APPROACHES ---
Title: "How Our Approach Differs from Existing Methods"
COMPARISON TABLE:

| Feature | Raw LLM Recovery | Failure-Aware Prompt | ReAct + Retry | Our CARE System |
|---------|:-:|:-:|:-:|:-:|
| Detects explicit failures | ✓ | ✓ | ✓ | ✓ |
| Detects implicit failures | ✗ | Partial | ✗ | ✓ |
| Structured diagnosis | ✗ | ✗ | ✗ | ✓ |
| Cost-aware recovery | ✗ | ✗ | ✗ | ✓ |
| DAG-aware path selection | ✗ | ✗ | ✗ | ✓ |
| Loop detection | ✗ | ✗ | ✗ | ✓ |
| Tool failure memory | ✗ | ✗ | ✗ | ✓ |
| Evidence-based prompting | ✗ | ✗ | ✗ | ✓ |

--- SLIDE 30: SEMESTER 1 DELIVERABLES ---
Title: "Semester 1 Deliverables"
Checklist style:

☐ Reproducible ToolMaze baseline with TSR/PRR/RC measurements
☐ Rule-based semantic validation layer (10 check levels)
☐ Structured failure-diagnosis module with evidence/confidence
☐ Recovery controller with retry, verify, reroute, abort actions
☐ Retry limits, tool-failure memory, and loop detection
☐ DAG-aware alternative-path selection
☐ Dynamic recovery prompting for unresolved semantic cases
☐ Staged ablation study isolating each component's contribution
☐ TSR/PRR/RC evaluation across all C1–C4 × P0–P4 configurations

--- SLIDE 31: FUTURE ROADMAP ---
Title: "Future Roadmap"
HORIZONTAL ARROW DIAGRAM (left to right):

[ToolMaze Baseline] → [Rule-Based Recovery (CARE)] → [Evaluation & Ablations] → [RL Recovery Policy] → [Cloud/AIOps Transfer] → [Realistic Telemetry Scenarios]

Label: "Semester 1" under first three boxes. "Semester 2" under next two. "Future Work" under the last.

--- SLIDE 32: REFERENCES ---
Title: "References"
Numbered academic citation format:

[1] D. Zhu et al., "When Tools Fail: Benchmarking Dynamic Replanning and Anomaly Recovery in LLM Agents," arXiv:2606.05806, Jun 2026.
[2] J. Yang et al., "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering," arXiv:2405.15793, May 2024.
[3] S. Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models," ICLR 2023.
[4] N. Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning," NeurIPS 2023.
[5] C. Packer et al., "MemGPT: Towards LLMs as Operating Systems," arXiv:2310.08560, 2023.
[6] LangGraph Framework, github.com/langchain-ai/langgraph, 2024.

--- SLIDE 33: THANK YOU ---
Center-aligned:
"Thank You"
"Questions & Discussion"
Below: team names and email addresses.
VNIT logo centered at bottom.

=== END OF SLIDE CONTENT ===

Generate the complete PowerPoint file following these specifications exactly. Every diagram should be clean, professional, and vector-style. No clipart, no stock photos. White background on every slide. VNIT logo placeholder in top-left of every slide.
```

---

## PART B: Detailed Slide-by-Slide Guide — What to Put, Where to Put, How to Put

Below is an **exhaustive, visual guide** for each slide. Use this alongside NotebookLM output to manually refine the PPT.

---

### SLIDE 1 — Title Slide

| Element | Details |
|---------|---------|
| **Position** | Everything center-aligned |
| **VNIT Logo** | Top-left corner, ~1.2 cm height. Download from VNIT website or use existing one. |
| **Title** | "Enhanced ToolMaze: Reliable and Cost-Aware Recovery from Tool Failures in LLM Agents" — 28pt, bold, navy (#1B2A4A) |
| **Subtitle** | "Final Year Project Proposal — First Evaluation" — 18pt, teal (#0D9488) |
| **Department** | "Computer Science and Engineering Department" — 16pt |
| **Institute** | "Visvesvaraya National Institute of Technology (VNIT), Nagpur" — 16pt |
| **Team Table** | Clean 2-column table, no heavy borders |
| **Guide** | "Under the guidance of Prof. Anshul Agrawal" — 14pt, italic |

**Team Table:**

| Name | Roll No |
|------|---------|
| Anupam Ayush | BT23CSE026 |
| Mrunmayee Limaye | BT23CSE019 |
| Reeti Gupta | BT23CSE013 |
| Samyak Borkar | BT23CSE028 |

> [!TIP]
> First impression matters. Keep this slide clean. No clutter. White space is your friend.

---

### SLIDE 2 — Presentation Outline

Show the flow of the entire PPT as a numbered vertical list. This tells professors "we have a structured, logical story." Use small colored circle icons (not bullet points) for each item.

---

### SLIDE 3 — Background: What Are LLM Agents?

**Why this slide:** Professors may NOT know what an "LLM Agent" is in this specific context. Define it clearly.

**Diagram (RIGHT SIDE):**
```
[User Query] → [LLM Agent] → [Tool 1: Weather API] → [Tool 2: Flight API] → [Tool 3: Hotel API] → [Final Answer]
```
Draw as rounded rectangles connected by arrows. Color each tool a different shade.

**Text (LEFT SIDE):**
- LLM agents = autonomous systems using Large Language Models to plan and execute multi-step tasks
- They call external tools (APIs, databases, search engines) to gather info
- Example: trip-planning agent calls weather → flights → hotels sequentially
- Frameworks: ReAct, AutoGen, LangGraph, CrewAI

---

### SLIDE 4 — What Is Tool Failure? (2×2 Matrix)

**This is the most critical concept slide.** Professors must understand the P1–P4 taxonomy.

**Diagram: 2×2 Matrix (FULL SLIDE)**

```
                    │  Transient               │  Permanent
                    │  (clears on retry)        │  (persists; must reroute)
────────────────────┼──────────────────────────┼──────────────────────────
Explicit            │  P1: HTTP 429, Timeout   │  P2: Tool permanently
(error codes)       │  → retry works           │  removed → must reroute
────────────────────┼──────────────────────────┼──────────────────────────
Implicit            │  P3: Stale data,         │  P4: Consistently
(valid syntax,      │  wrong values            │  corrupted output
 wrong semantics)   │  → retry with validation │  → must detect + reroute
```

Color code: P1=blue, P2=amber, P3=teal, P4=red

**Bottom callout (red box):** "P3 and P4 are the HARDEST — the tool returns NO error, but the output is semantically WRONG."

---

### SLIDE 5 — Core Problem Visual Example

**Full-slide visual story. NO bullet points. Just the example.**

```
┌─────────────────────────────────────────┐
│  Agent Request: "Get weather for Tokyo" │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  Tool Response: {"city":"Osaka","temp":28,"sunny"}  │
│  ✅ Valid JSON    ✅ No error code                   │
│  ❌ WRONG CITY — Osaka instead of Tokyo!            │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  Agent plans outdoor activities in "Tokyo"          │
│  using OSAKA's weather data                         │
│  → FINAL ANSWER IS WRONG                            │
└─────────────────────────────────────────────────────┘
```

**Red warning callout:** "This is an IMPLICIT PERMANENT failure (P4). Current agents CANNOT detect this."

---

### SLIDE 6 — Problem Statement

**Single prominent statement in a light-blue bordered box, center-aligned.**

Keep this slide minimal. One box. One statement. Maximum impact.

---

### SLIDE 7 — Literature Review: ToolMaze

**Left:** Bullet points about ToolMaze paper metadata and key features.
**Right:** 2D evaluation grid diagram (C1–C4 × P0–P4) color-coded by difficulty (green→red).

---

### SLIDE 8 — Key Findings (BAR CHART)

**This is where data speaks. The bar chart is essential.**

**Bar Chart Data (approximate from ToolMaze paper findings):**

| Perturbation Mode | PRR (%) |
|-------------------|---------|
| P1 (Explicit Transient) | ~75% |
| P2 (Explicit Permanent) | ~55% |
| P3 (Implicit Transient) | ~45% |
| P4 (Implicit Permanent) | ~38% |

Color bars: P1=green, P2=yellow, P3=orange, P4=red.

**Annotation arrow on P3/P4:** "~37% drop — agents OVER-TRUST corrupted outputs"

**3 bullets below:**
1. Fault-tolerance scales 3.66× slower than basic task execution with model size
2. Complex topologies (C3, C4) trap agents in futile trial-and-error loops
3. Failure-aware prompting helps but does NOT close the gap

---

### SLIDE 9 — Related Work Table

Full-width table. 4 columns: Work | Year | Key Contribution | Relevance.
Include: ToolMaze, SWE-Agent, AgentDebug, LangGraph, ReAct, Reflexion.

---

### SLIDE 10 — Research Gaps (3-Column Layout)

For each gap, show: **Gap (red) → Impact (amber) → Our Fix (green)**

Show at least 4 gaps. Use colored icon circles.

---

### SLIDE 11 — Our Novelty: CARE Architecture (Layered Diagram)

**7-layer stack diagram** showing each novel component, bottom to top:
1. Deterministic Semantic Validation (foundation)
2. Structured Failure Diagnosis
3. Failure-State Tracking & Tool Memory
4. DAG-Aware Alternative Path Selection
5. Dynamic Recovery Prompts
6. Cost-Aware Control
7. Selective LLM Use (top)

This visual immediately shows professors "we have 7 distinct components — not just one idea."

---

### SLIDE 12 — Full System Architecture Flowchart

**THE MOST IMPORTANT SLIDE.** This is the slide professors will stare at.

Full-page flowchart showing the complete pipeline:
```
User Task → Agent → Tool Call → Tool Response → Semantic Validator
                                                      ↓
                                            PASS → Continue
                                            FAIL → Failure Diagnosis
                                                      ↓
                                            Recovery Controller
                                     ┌────┬────┬────┬────┐
                                  RETRY  VERIFY REROUTE ABORT
                                     └────┴────┴────┘
                                            ↓
                                  Post-Recovery Validation
                                            ↓
                                     Continue / Escalate
```

Use color-coded boxes. Add "Budget Tracker" on the side.

---

### SLIDE 13 — Semantic Validation Pyramid

**10-layer pyramid/funnel** from cheapest checks (top/wide) to most expensive (bottom/narrow).

This shows professors that validation is NOT just "ask ChatGPT if it looks right" — it's a systematic hierarchy.

---

### SLIDE 14 — Worked Example with Check Table

Concrete Tokyo/Osaka example with a table showing each check layer's result.
This makes the abstract concept tangible.

---

### SLIDE 15 — Failure Diagnosis Decision Tree + Memory Table

**Left:** Decision tree diagram for classifying failure type.
**Right:** Tool memory table showing tracked failure history.

---

### SLIDE 16 — Recovery Controller (4 Parallel Lanes)

Four vertical lanes: RETRY | VERIFY | REROUTE | ABORT
Each with: icon, when to use, how it works, budget limit.

---

### SLIDE 17 — DAG-Aware Recovery (Graph Diagram)

Show a sample DAG with one node marked as failed (red X).
Show path elimination and alternative path selection.
This is visually compelling and shows algorithmic thinking.

---

### SLIDE 18 — Dynamic Recovery Prompt Template

Show the actual prompt template the LLM receives.
This demonstrates that the LLM gets structured evidence, not "figure it out."

---

### SLIDE 19 — Cost-Aware Control (Gauge + Formula)

**Left:** Cost meter gauge (green/yellow/red zones).
**Right:** Formula for cost-weighted PRR.
**Bottom:** Three prevention mechanisms (retry budget, loop detection, tool memory).

---

### SLIDE 20 — Complexity Levels (4 DAG Diagrams)

Four DAG structures side by side: C1 (simple) → C4 (complex).
Shows professors the increasing difficulty.

---

### SLIDE 21 — Why Rule-Based First? (Staircase)

Staircase visual: Rule-Based (Sem 1) → RL (Sem 2).
5 reasons for rule-based first. Arrow showing "foundation for RL."

---

### SLIDE 22 — Staged Ablation Table

Checkmark table showing 6 configurations, each adding one component.
This shows rigorous experimental methodology.

---

### SLIDE 23 — Evaluation Metrics

**Primary metrics** (TSR, PRR, RC) with gauge/pie visuals.
**Diagnostic metrics** in a table below.

---

### SLIDE 24 — Research Questions

RQ1–RQ6 in colored boxes. RQ5–RQ6 marked as Sem 2 / Future.

---

### SLIDE 25 — Gantt Chart Timeline

Horizontal Gantt chart: Aug 2026 → Mar 2027.
Color-coded: Blue=Sem 1, Teal=Sem 2.

---

### SLIDE 26 — Infrastructure Table

Server specs table. Shows professors you have real hardware ready.

---

### SLIDE 27 — Expected Contributions (Numbered)

8 contributions, numbered. Last 2 marked as Sem 2 / Future.

---

### SLIDE 28 — Risk Analysis Table

6 risks with impact and mitigation. Shows maturity and forethought.

---

### SLIDE 29 — Comparison Table

Feature comparison: Raw LLM vs Failure-Aware Prompt vs ReAct vs CARE.
Checkmarks show CARE has all features others lack.

---

### SLIDE 30 — Semester 1 Deliverables (Checklist)

Concrete deliverables as checklist items.

---

### SLIDE 31 — Future Roadmap (Arrow Diagram)

Horizontal arrow: ToolMaze Baseline → CARE → Ablations → RL → Cloud → Real-world.

---

### SLIDE 32 — References

Formal academic citations. APA/IEEE format.

---

### SLIDE 33 — Thank You

Clean. Center-aligned. "Questions & Discussion."

---

## PART C: PPT Design Best Practices for Academic Evaluation

> [!IMPORTANT]
> **Golden Rules for First Evaluation PPTs at Indian Engineering Institutes:**

1. **White background ALWAYS.** No dark themes. No gradients. Professors print slides.
2. **VNIT logo on every slide** — shows institutional pride and formality.
3. **One idea per slide.** Never cram two concepts onto one slide.
4. **Diagrams > Text.** For every concept, ask: "Can I show this as a diagram instead of bullets?"
5. **Use the 2×2 matrix, flowchart, bar chart, table** — these are the visual formats professors respect most.
6. **Define every term.** Professors didn't read the ToolMaze paper. Define TSR, PRR, RC, P1–P4, C1–C4.
7. **Show a concrete example.** The Tokyo/Osaka example makes the abstract problem tangible.
8. **Show your methodology is rigorous.** The staged ablation table proves you're not just "trying stuff."
9. **Show you've thought about risks.** The risk analysis slide shows maturity.
10. **Show you have infrastructure.** The server specs table shows you're not just theorizing.
11. **Keep font sizes readable.** Title: 24–28pt. Body: 16–18pt. Never below 14pt.
12. **Consistent color scheme.** Navy + Teal + White. No rainbow slides.
13. **Slide numbers.** Always. Bottom-right.
14. **Rehearse the flow.** Slides should tell a story: Problem → Why it matters → What exists → What's missing → Our solution → How we'll validate → Timeline.

---

## PART D: Diagram Specifications (For Manual Creation or PowerPoint SmartArt)

### Diagram 1: Agent Pipeline (Slide 3)
```
[User Query] ──→ [LLM Agent] ──→ [Tool 1] ──→ [Tool 2] ──→ [Tool 3] ──→ [Final Answer]
   (blue)        (navy)         (teal)       (teal)       (teal)         (green)
```
**Type:** Horizontal process flow. Use SmartArt "Basic Process" or draw rounded rectangles with arrows.

### Diagram 2: Perturbation Matrix (Slide 4)
**Type:** 2×2 table with colored cells. Use PowerPoint table with fills:
- P1: Light blue (#DBEAFE)
- P2: Light amber (#FEF3C7)
- P3: Light teal (#CCFBF1)
- P4: Light red (#FEE2E2)

### Diagram 3: PRR Bar Chart (Slide 8)
**Type:** Clustered bar chart.
**Data:**

| Mode | PRR (%) |
|------|---------|
| P1 | 75 |
| P2 | 55 |
| P3 | 45 |
| P4 | 38 |

**Colors:** P1=green, P2=yellow, P3=orange, P4=red.
**Annotation:** Arrow pointing to P3/P4 with "~37% drop"

### Diagram 4: System Architecture Flowchart (Slide 12)
**Type:** Multi-level flowchart. Use PowerPoint shapes.
**Key:** Color-code each module:
- Agent: Navy
- Semantic Validator: Teal
- Failure Diagnosis: Amber
- Recovery Controller: Blue
- Recovery Actions: Green/Red
- Budget Tracker: Gray sidebar

### Diagram 5: Validation Pyramid (Slide 13)
**Type:** Inverted funnel / pyramid. 10 layers.
**Left label:** "CHEAP" (top) → "EXPENSIVE" (bottom)
**Right label:** "DETERMINISTIC" (top) → "LLM-BASED" (bottom)

### Diagram 6: DAG Recovery (Slide 17)
**Type:** Directed graph with nodes and edges.
- Primary path: solid blue arrows
- Failed node: red X
- Alternative paths: dashed green arrows
- Eliminated paths: grayed out with strikethrough

### Diagram 7: Gantt Chart (Slide 25)
**Type:** Horizontal bar/Gantt chart.
**Tool:** Use PowerPoint stacked bar chart or SmartArt timeline.
- Semester 1 bars: Blue (#2563EB)
- Semester 2 bars: Teal (#0D9488)

### Diagram 8: Future Roadmap (Slide 31)
**Type:** Horizontal arrow / chevron process.
6 stages left-to-right. Use SmartArt "Chevron List."
- Stage 1–3: Blue (Sem 1)
- Stage 4–5: Teal (Sem 2)
- Stage 6: Gray (Future)

---

## PART E: Key Data Points to Include (From Project Documents)

| Data Point | Value | Use On Slide |
|------------|-------|-------------|
| ToolMaze tasks | 2,000 perturbed tasks | Slide 7 |
| Complexity levels | C1–C4 (4 levels) | Slides 7, 20 |
| Perturbation modes | P0–P4 (5 modes) | Slides 4, 7, 8 |
| PRR drop under implicit failures | ~37% | Slide 8 |
| Fault-tolerance scaling gap | 3.66× slower | Slide 8 |
| Total tools in ToolMaze | 270 tools | Slide 7 |
| Tool categories | Action, Source, Processor | Slide 7 |
| DAG templates | 400 (100 per complexity) | Slide 7 |
| Server GPU | NVIDIA TITAN RTX (24 GB VRAM) | Slide 26 |
| Server RAM | 128 GB | Slide 26 |
| Server storage | 3.6 TB (3.4 TB free) | Slide 26 |
| Target models | Qwen-2.5-7B, Llama-3.1-8B | Slide 26 |
| Validation layers | 10 hierarchical checks | Slide 13 |
| Recovery actions | 4 (Retry, Verify, Reroute, Abort) | Slide 16 |
| Research gaps found | 7 gaps in ToolMaze | Slide 10 |
| Research questions | 6 (RQ1–RQ6) | Slide 24 |
| Ablation configurations | 6 staged configs | Slide 22 |
| Project timeline | Aug 2026 → Mar 2027 | Slide 25 |
