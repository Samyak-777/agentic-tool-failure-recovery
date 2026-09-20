# Novel Agentic AI Research Directions (August 2026)

> **Generated:** August 11, 2026 | **Method:** Enhanced Research Prompt v2.0 with systematic prior art verification
> **Constraints:** 4-person team, 6–12 months, ≤$500 compute, public data only

---

## Direction 1: Action-Reversibility-Aware Agent Planning

**Innovation Category:** B (Reliability & Verification) + D (Human-Agent Interaction)

**Core Research Question:**
An agent planner that classifies every candidate tool-call into a 4-tier reversibility taxonomy (read-only → reversible → compensatable → irreversible) *before* execution, and gates irreversible actions behind mandatory checkpoints, will reduce catastrophic side-effects by ≥60% on the AgentDojo and τ²-bench benchmark suites compared to standard ReAct agents with no reversibility awareness, while maintaining ≥90% of baseline task-completion rate.

**Novelty Justification:**
- Concept-level: **Exists partially** — Action-reversibility taxonomies are discussed in 2026 industry best practices and the ACRFence paper. However, these are *policy-level* recommendations, not *integrated planner components*.
- Implementation-level: **Does NOT exist** — No open-source agent framework integrates a learned reversibility classifier into the planning loop as a first-class constraint.
- Evaluation-level: **Does NOT exist** — No benchmark evaluates the *tradeoff* between task-completion and side-effect reduction using reversibility-aware planning.
- **Differentiation:** Existing work treats reversibility as an external policy enforcement layer (OPA, guardrails). This direction makes reversibility awareness *intrinsic to the planning step itself* — the agent reasons about reversibility during plan construction, not after.

**Technical Architecture:**
- Base framework: LangGraph (github.com/langchain-ai/langgraph) for state-machine agent
- Foundation model(s): Llama-3.1-8B-Instruct (Q4_K_M via Ollama) for the planner; a fine-tuned DistilBERT classifier for reversibility scoring
- Agent topology: Single agent with a pre-execution "Reversibility Gate" node in the LangGraph state machine
- Memory strategy: Checkpoint-based state snapshots before every compensatable/irreversible action; rollback capability via LangGraph's built-in persistence
- External tools/APIs: File I/O, web search, code execution sandbox, mock financial API (for irreversible action testing)

**Feasibility Timeline:**
| Phase | Months | Deliverable | Biggest Risk | Mitigation |
|---|---|---|---|---|
| Foundation | 1–3 | Reversibility taxonomy defined; 500 tool-calls manually annotated; baseline ReAct agent on AgentDojo | Annotation agreement on reversibility labels | Use 3 annotators + majority vote; target κ ≥ 0.75 |
| Core Build | 4–6 | Reversibility classifier trained; integrated into LangGraph planner with gate logic | Classifier accuracy insufficient to be useful | Fallback: rule-based classifier using tool metadata (read/write flags) |
| Evaluation | 7–9 | Full benchmark campaign: task-completion vs. side-effect rate across 4 reversibility-gate thresholds | AgentDojo task set too narrow | Supplement with custom scenarios targeting compensatable/irreversible actions |
| Write-up | 10–12 | Paper, open-source repo, annotated dataset release | — | — |

**Evaluation Protocol:**
- Primary metrics: (1) Catastrophic Side-Effect Rate (CSR) = fraction of episodes with irreversible unintended consequences; (2) Task Completion Rate (TCR)
- Baselines: (1) Vanilla ReAct (no reversibility awareness); (2) ReAct + OPA external policy gate (strong baseline)
- Ablations: Classifier on/off; checkpoint-rollback on/off; threshold sweep (gate at compensatable vs. irreversible only)
- Statistical rigor: ≥200 episodes per condition; bootstrap 95% CI; paired permutation test

**Deliverables:**
- Open-source LangGraph plugin for reversibility-aware planning
- Annotated dataset of 500+ tool-calls with reversibility labels
- Benchmark harness (single-command Docker)
- Paper draft targeting AAMAS 2027 or AAAI Safe AI workshop

**Ethical Analysis:**
- Misuse potential: LOW — system is defensive by design
- Bias risk: LOW — reversibility labels are based on tool semantics, not user demographics
- Privacy: NONE — synthetic/simulated environments only

**Interestingness Scores:**
- Build excitement: 5/5 (novel planner architecture, satisfying safety engineering)
- Demo impact: 4/5 (showing an agent refusing to send an irreversible email is visceral)
- Learning value: 5/5 (LangGraph state machines, classifier training, safety engineering)

**Novelty Confidence:** HIGH
**Risk Level:** LOW
**Composite Suitability Score:** 91/100

---

## Direction 2: Cascading Uncertainty Propagation in Multi-Step Agent Pipelines

**Innovation Category:** H (Evaluation & Benchmarking) + B (Reliability)

**Core Research Question:**
A trajectory-level uncertainty propagation framework, which aggregates per-step confidence estimates and flags when cumulative uncertainty exceeds a threshold, will detect ≥70% of eventual task failures *before the final step* on τ²-bench and ALFWorld, compared to ≤30% detection by step-level confidence thresholds alone.

**Novelty Justification:**
- Concept-level: **Exists partially** — AgentUQ (ACL 2026) formalizes agent uncertainty but focuses on *measurement*, not *early termination* or *branching decisions* driven by cumulative uncertainty.
- Implementation-level: **Does NOT exist** — No open-source framework propagates uncertainty across steps and uses it as a *control surface* for plan modification.
- Evaluation-level: **Does NOT exist** — No benchmark measures "how early can the agent predict its own failure?" as a primary metric.
- **Differentiation:** AgentUQ *measures* trajectory uncertainty post-hoc. This direction *uses* propagated uncertainty as a runtime control signal — triggering early abort, human escalation, or plan revision mid-trajectory.

**Technical Architecture:**
- Base framework: LangGraph for agent loop + custom uncertainty propagation module
- Foundation model(s): GPT-4o-mini (API) or Llama-3.1-8B (local); log-probability extraction for confidence
- Agent topology: Single agent with an "Uncertainty Monitor" node that runs in parallel with the main execution loop
- Memory strategy: Each step annotated with (action, observation, confidence, cumulative_uncertainty)
- External tools/APIs: ALFWorld simulator, τ²-bench harness

**Feasibility Timeline:**
| Phase | Months | Deliverable | Biggest Risk | Mitigation |
|---|---|---|---|---|
| Foundation | 1–3 | Reproduce AgentUQ baseline; set up ALFWorld + τ²-bench; implement per-step confidence extraction | Log-prob API access changes | Fallback: use verbalized confidence + calibration |
| Core Build | 4–6 | Cumulative uncertainty propagation module; threshold-based early-termination policy | Propagation formula doesn't improve over per-step | Try multiple aggregation functions (product, harmonic mean, Bayesian update) |
| Evaluation | 7–9 | "Failure prediction lead time" experiments; ablation of propagation vs. step-level | ALFWorld too easy for uncertainty analysis | Add adversarial perturbations to environment |
| Write-up | 10–12 | Paper, open-source module, benchmark extension | — | — |

**Evaluation Protocol:**
- Primary metrics: (1) Failure Prediction Recall@K (fraction of failures detected K steps before final step); (2) False Positive Rate (unnecessary early terminations)
- Baselines: (1) No uncertainty monitoring (always execute to completion); (2) Per-step threshold (AgentUQ-style)
- Ablations: Propagation function (product vs. Bayesian); threshold sensitivity; model size
- Statistical rigor: ≥300 trajectories; McNemar's test for paired comparison

**Deliverables:**
- Uncertainty propagation library (pip-installable)
- Extended τ²-bench with "failure prediction" evaluation mode
- Paper targeting NeurIPS 2027 Agent Reliability workshop

**Ethical Analysis:**
- Misuse potential: LOW — improves safety
- Bias risk: MEDIUM — confidence calibration may vary across demographic contexts in downstream applications
- Privacy: NONE — synthetic environments

**Interestingness Scores:**
- Build excitement: 4/5 (probability propagation + agent loops = elegant)
- Demo impact: 4/5 (live dashboard showing uncertainty accumulating until abort is triggered)
- Learning value: 5/5 (uncertainty quantification, Bayesian methods, agent internals)

**Novelty Confidence:** HIGH
**Risk Level:** MEDIUM
**Composite Suitability Score:** 89/100

---

## Direction 3: Speculative Multi-Path Agent Execution with Cost-Bounded Branching

**Innovation Category:** A (Architectural Innovation)

**Core Research Question:**
A speculative execution strategy that spawns N parallel agent branches at high-uncertainty decision points (selected by the uncertainty monitor from Direction 2 or a simpler entropy heuristic), executes them concurrently, and commits the first branch to pass a verification check, will reduce end-to-end wall-clock time by ≥35% on WebArena and SWE-bench-lite compared to sequential ReAct, while staying within a 2× token-cost budget.

**Novelty Justification:**
- Concept-level: **Exists** — PASTE (Pattern-Aware Speculative Tool Execution) and speculative action frameworks exist (2025–2026).
- Implementation-level: **Exists partially** — PASTE targets *predictable* tool-call sequences. No system handles *branching at uncertainty points* with *cost-bounded* resource management.
- Evaluation-level: **Does NOT exist** — No benchmark measures the *cost-vs-latency Pareto frontier* of speculative agent branching.
- **Differentiation:** PASTE predicts the *most likely* next action and pre-executes it. This direction branches into *multiple* paths at uncertainty points, with an explicit cost budget that prunes branches when the token spend exceeds the threshold — borrowing from CPU branch prediction budgets.

**Technical Architecture:**
- Base framework: LangGraph with async parallel execution
- Foundation model(s): GPT-4o-mini (API) for parallel branches; Llama-3.1-8B for verification
- Agent topology: "Branching Tree" — root agent spawns 2–3 child branches at uncertainty points; first child to pass verification commits
- Memory strategy: Copy-on-write state snapshots; shared read-only context, branch-local write buffers
- External tools/APIs: WebArena browser environment, SWE-bench-lite code environment

**Feasibility Timeline:**
| Phase | Months | Deliverable | Biggest Risk | Mitigation |
|---|---|---|---|---|
| Foundation | 1–3 | Reproduce sequential ReAct baseline on WebArena; implement branching-point detector (entropy-based) | WebArena setup complexity | Use pre-built Docker images from WebArena repo |
| Core Build | 4–6 | Parallel branch spawning in LangGraph; cost-budget pruning; verification-based commit logic | API rate limits on parallel calls | Use async batching; local model fallback |
| Evaluation | 7–9 | Pareto curve: wall-clock time vs. token cost across branching factors (1, 2, 3, 5) | Diminishing returns beyond 2 branches | Report the Pareto frontier honestly; identify the "sweet spot" |
| Write-up | 10–12 | Paper, open-source branching module, cost analysis toolkit | — | — |

**Evaluation Protocol:**
- Primary metrics: (1) Wall-Clock Speedup Ratio vs. sequential; (2) Token Cost Ratio vs. sequential; (3) Task Completion Rate
- Baselines: (1) Sequential ReAct; (2) PASTE (if reproducible)
- Ablations: Branching factor (1–5); branching-point selection strategy (entropy vs. random vs. fixed-interval)
- Statistical rigor: ≥100 episodes per configuration; bootstrap CI for speedup ratio

**Deliverables:**
- Open-source "SpecBranch" LangGraph extension
- Cost-analysis dashboard (Streamlit)
- Paper targeting ICML 2027 or Systems for ML workshop

**Ethical Analysis:**
- Misuse potential: LOW — efficiency optimization
- Bias risk: LOW — branch selection is entropy-based, not content-based
- Privacy: NONE — benchmark environments only

**Interestingness Scores:**
- Build excitement: 5/5 (async systems programming + agent architecture = deeply fun)
- Demo impact: 5/5 (side-by-side video: sequential agent crawling vs. speculative agent blazing through)
- Learning value: 5/5 (concurrency, distributed systems, cost optimization — directly industry-relevant)

**Novelty Confidence:** MEDIUM (PASTE and speculative actions exist; the cost-bounded branching angle is novel)
**Risk Level:** MEDIUM
**Composite Suitability Score:** 87/100

---

## Direction 4: Automatic Regulatory Compliance Diff for the EU AI Act

**Innovation Category:** G (Domain-Specific Innovation)

**Core Research Question:**
A multi-agent pipeline that ingests (a) the full text of the EU AI Act and (b) an organization's AI governance documentation, then outputs a structured gap analysis with specific article citations and remediation suggestions, will achieve ≥80% precision and ≥70% recall on a manually constructed ground-truth gap dataset (50 policy documents with expert-labeled gaps), compared to ≤40% recall for keyword-based search.

**Novelty Justification:**
- Concept-level: **Exists partially** — Commercial GRC tools (Credo AI, OneTrust) offer AI Act compliance features. Academic work on "Policy-to-Tests" (P2T) converts policy prose to machine-readable logic.
- Implementation-level: **Does NOT exist as open-source** — No open-source academic system provides structured, article-level gap analysis between the AI Act and organizational policies.
- Evaluation-level: **Does NOT exist** — No benchmark dataset pairs AI Act articles with policy documents annotated for compliance gaps.
- **Differentiation:** Commercial tools are black-box and enterprise-priced. P2T converts policy to tests but doesn't perform *gap analysis between two documents*. This direction creates the first open-source, reproducible EU AI Act compliance-diff system with a public evaluation dataset.

**Technical Architecture:**
- Base framework: CrewAI (github.com/crewAIInc/crewAI) for multi-agent orchestration
- Foundation model(s): GPT-4o-mini for extraction + Llama-3.1-8B for verification
- Agent topology: 3-agent pipeline: (1) Obligation Extractor (parses AI Act articles into structured obligations); (2) Policy Mapper (matches obligations to organizational policy sections); (3) Gap Analyst (identifies unmatched obligations and generates remediation suggestions)
- Memory strategy: Obligation knowledge graph (Neo4j or NetworkX) linking articles → obligations → policy sections
- External tools/APIs: EU AI Act full text (EUR-Lex, public), sample governance templates (publicly available)

**Feasibility Timeline:**
| Phase | Months | Deliverable | Biggest Risk | Mitigation |
|---|---|---|---|---|
| Foundation | 1–3 | Parse AI Act into structured obligation list; collect 50 sample policy documents from public sources | Policy document diversity insufficient | Supplement with synthetic policies generated by LLM |
| Core Build | 4–6 | 3-agent pipeline; obligation KG; gap detection logic | LLM hallucinating article citations | RAG over the actual Act text; citation verification step |
| Evaluation | 7–9 | Expert annotation of ground-truth gaps (2 legal/compliance annotators); precision/recall measurement | Expert annotator recruitment | Partner with law faculty; use compliance-certified team members |
| Write-up | 10–12 | Paper, open-source toolkit, annotated dataset | — | — |

**Evaluation Protocol:**
- Primary metrics: (1) Gap Detection Precision (fraction of flagged gaps that are genuine); (2) Gap Detection Recall (fraction of genuine gaps that are flagged)
- Baselines: (1) Keyword/regex search over Act text; (2) Single-agent RAG (no obligation extraction)
- Ablations: Obligation KG on/off; verification agent on/off; model size
- Statistical rigor: 50 policy documents × ~20 obligations each = ~1,000 gap judgments; inter-annotator κ reported

**Deliverables:**
- Open-source EU AI Act compliance-diff toolkit
- Annotated dataset: 50 policy documents with expert-labeled gaps
- Obligation knowledge graph for the EU AI Act (reusable artifact)
- Paper targeting FAccT 2027 or RegML workshop

**Ethical Analysis:**
- Misuse potential: MEDIUM — could be used to identify *minimum* compliance rather than genuine safety
- Bias risk: LOW — regulatory text is deterministic
- Privacy: LOW — policy documents should be anonymized

**Interestingness Scores:**
- Build excitement: 4/5 (legal NLP + knowledge graphs + multi-agent = interesting intersection)
- Demo impact: 5/5 (showing a "compliance report card" for a real-looking policy document is impressive)
- Learning value: 4/5 (regulatory AI is a growing career field)

**Novelty Confidence:** HIGH
**Risk Level:** MEDIUM
**Composite Suitability Score:** 88/100

---

## Direction 5: Agent Energy Profiling & Sustainability-Aware Workflow Routing

**Innovation Category:** C (Resource-Constrained) + H (Evaluation)

**Core Research Question:**
An "Energy-per-Successful-Goal" (EpG) profiling framework that instruments LangGraph agent workflows with per-node energy measurement (via CodeCarbon) and a routing policy that selects the most energy-efficient model/tool combination per task type, will reduce total energy consumption by ≥40% compared to a fixed-model baseline, while maintaining ≥95% task-completion parity, on ALFWorld and a custom multi-tool benchmark.

**Novelty Justification:**
- Concept-level: **Exists partially** — A-LEMS and CEDAR (2026) address agentic energy measurement and carbon-aware routing, respectively.
- Implementation-level: **Does NOT exist as open-source** — No open-source framework combines per-node energy profiling with *dynamic model switching within a single agent workflow*.
- Evaluation-level: **Does NOT exist** — No benchmark reports EpG as a primary metric alongside task completion.
- **Differentiation:** A-LEMS *measures* energy; CEDAR *routes across geo-distributed servers*. This direction performs *intra-workflow model switching* — using a small model for simple tool calls and escalating to a larger model only for complex reasoning steps, all within a single agent session.

**Technical Architecture:**
- Base framework: LangGraph + CodeCarbon (github.com/mlco2/codecarbon)
- Foundation model(s): Phi-3-mini-4k (1.8B, Q4) for simple steps; Llama-3.1-8B (Q4) for medium; GPT-4o-mini (API) for complex — selected dynamically by a lightweight "complexity classifier"
- Agent topology: Single agent with a "Model Router" node that estimates step complexity and selects the appropriate backend
- Memory strategy: Standard LangGraph state; energy metrics logged per node
- External tools/APIs: ALFWorld, CodeCarbon, Ollama (local inference), OpenAI API

**Feasibility Timeline:**
| Phase | Months | Deliverable | Biggest Risk | Mitigation |
|---|---|---|---|---|
| Foundation | 1–3 | Instrument LangGraph with CodeCarbon; establish energy baselines for 3 models on ALFWorld | CodeCarbon measurement noise on consumer hardware | Average over 10 runs per configuration |
| Core Build | 4–6 | Complexity classifier (DistilBERT on step descriptions); Model Router integration | Complexity classifier inaccurate | Fallback: use token-count heuristic (short prompt → small model) |
| Evaluation | 7–9 | EpG comparison: fixed-model vs. routed; Pareto frontier: energy vs. accuracy | Energy savings too small to be meaningful | Report honestly; focus on the profiling framework as the contribution |
| Write-up | 10–12 | Paper, profiling framework, benchmark results | — | — |

**Evaluation Protocol:**
- Primary metrics: (1) Energy per Successful Goal (EpG) in Joules; (2) Task Completion Rate (TCR)
- Baselines: (1) Fixed large model (GPT-4o-mini for all steps); (2) Fixed small model (Phi-3-mini for all steps)
- Ablations: Router on/off; complexity classifier type; number of model tiers (2 vs. 3)
- Statistical rigor: ≥200 episodes; energy measurements averaged over 10 runs per episode

**Deliverables:**
- Open-source LangGraph energy profiling plugin
- Model Router library (pip-installable)
- EpG benchmark results and Pareto curves
- Paper targeting Green AI workshop (ICML/NeurIPS 2027) or ACM e-Energy

**Ethical Analysis:**
- Misuse potential: LOW — promotes sustainability
- Bias risk: LOW — routing based on task complexity, not user identity
- Privacy: NONE — synthetic benchmarks

**Interestingness Scores:**
- Build excitement: 4/5 (hardware profiling + ML routing = systems engineering fun)
- Demo impact: 4/5 (real-time energy dashboard showing savings is visually compelling)
- Learning value: 5/5 (Green AI, model optimization, systems engineering — industry hot topic)

**Novelty Confidence:** MEDIUM (A-LEMS and CEDAR exist; the intra-workflow routing is novel)
**Risk Level:** LOW
**Composite Suitability Score:** 86/100

---

## Direction 6: Bi-Temporal Belief Audit Trail for High-Stakes Agent Decisions

**Innovation Category:** A (Architectural) + B (Reliability)

**Core Research Question:**
An agent that maintains a bi-temporal knowledge graph (event-time + ingestion-time) for every fact used in its reasoning, enabling "time-travel" queries ("What did the agent believe about X when it made decision Y?"), will produce auditable decision traces that achieve ≥90% provenance accuracy (every cited fact traceable to a timestamped source) on a government-benefit eligibility task, compared to ≤50% for standard RAG agents.

**Novelty Justification:**
- Concept-level: **Exists** — Graphiti/Zep (2026) implement bi-temporal knowledge graphs for RAG.
- Implementation-level: **Exists partially** — Graphiti provides temporal storage but is NOT integrated into an *agent decision pipeline* with *provenance auditing*.
- Evaluation-level: **Does NOT exist** — No benchmark measures "provenance accuracy" (can every fact in a decision trace be traced to a timestamped source?) for agent decisions.
- **Differentiation:** Graphiti provides the *storage layer*. This direction builds the *audit layer on top* — instrumenting the agent's reasoning to produce fully traceable decision traces with timestamped fact provenance, and evaluating whether this enables meaningful contestability.

**Technical Architecture:**
- Base framework: LangGraph + Graphiti (github.com/getzep/graphiti) for bi-temporal KG
- Foundation model(s): GPT-4o-mini or Llama-3.1-8B
- Agent topology: Single agent with a "Provenance Tracker" that logs every fact retrieval with (fact, event_time, ingestion_time, source_id)
- Memory strategy: Graphiti bi-temporal KG; each decision node linked to its supporting facts with timestamps
- External tools/APIs: Graphiti, Neo4j (optional), BenefitPulse eligibility rules (existing codebase)

**Feasibility Timeline:**
| Phase | Months | Deliverable | Biggest Risk | Mitigation |
|---|---|---|---|---|
| Foundation | 1–3 | Set up Graphiti; ingest eligibility rules with timestamps; build baseline RAG agent | Graphiti API changes or instability | Fork and pin version; fallback to custom temporal graph |
| Core Build | 4–6 | Provenance Tracker integration; time-travel query interface; decision trace generator | Provenance tracking adds too much latency | Batch fact logging; async writes |
| Evaluation | 7–9 | Provenance accuracy measurement on 100 eligibility decisions; comparison vs. standard RAG | Ground-truth provenance annotation is labor-intensive | Use synthetic scenarios where the "correct" provenance is known by construction |
| Write-up | 10–12 | Paper, open-source audit trail plugin, demo notebook | — | — |

**Evaluation Protocol:**
- Primary metrics: (1) Provenance Accuracy (fraction of cited facts with valid timestamped source); (2) Decision Consistency (does the trace logically support the decision?)
- Baselines: (1) Standard RAG with no temporal tracking; (2) RAG + simple source attribution (no timestamps)
- Ablations: Bi-temporal on/off; provenance tracker on/off; KG vs. flat store
- Statistical rigor: 100 decisions; 2 annotators for decision consistency; Cohen's κ

**Deliverables:**
- Open-source provenance-tracking plugin for LangGraph + Graphiti
- Time-travel query interface (CLI + notebook)
- Paper targeting FAccT 2027 or AAAI Accountable AI workshop

**Ethical Analysis:**
- Misuse potential: LOW — improves accountability
- Bias risk: MEDIUM — temporal KG could perpetuate outdated rules if invalidation is broken
- Privacy: LOW — synthetic eligibility data

**Interestingness Scores:**
- Build excitement: 4/5 (temporal databases + agent reasoning = intellectually rich)
- Demo impact: 5/5 ("show me what the agent believed when it denied this claim" is powerful)
- Learning value: 5/5 (temporal data modeling, knowledge graphs, accountability — directly relevant to AI Act)

**Novelty Confidence:** MEDIUM (Graphiti exists; the audit trail evaluation is novel)
**Risk Level:** MEDIUM
**Composite Suitability Score:** 88/100

---

## Direction 7: MCP Tool-Poisoning Adversarial Benchmark

**Innovation Category:** H (Evaluation) + E (Multi-Agent Coordination)

**Core Research Question:**
A standardized adversarial benchmark that evaluates agent robustness to MCP tool-poisoning attacks (tool description injection, rug pulls, tool shadowing) will reveal that ≥60% of mainstream agent frameworks (LangGraph, CrewAI, AutoGen, smolagents) are vulnerable to at least one attack category with >50% attack success rate, and that proposed defenses (tool hash pinning, metadata sanitization) reduce ASR by ≥80%.

**Novelty Justification:**
- Concept-level: **Exists** — MCP tool poisoning is documented (OWASP, CrowdStrike, 2026). Defense strategies are proposed.
- Implementation-level: **Does NOT exist** — No standardized *benchmark suite* exists for systematically testing agent robustness to MCP tool-poisoning across multiple frameworks.
- Evaluation-level: **Does NOT exist** — No comparative evaluation measures vulnerability rates across mainstream frameworks using a standardized attack taxonomy.
- **Differentiation:** Existing work *describes* attacks and *proposes* defenses. This direction creates the first *reproducible benchmark* for measuring and comparing tool-poisoning vulnerability across frameworks, analogous to what AgentDojo did for prompt injection but specifically for MCP tool metadata attacks.

**Technical Architecture:**
- Base framework: Custom harness wrapping LangGraph, CrewAI, AutoGen, smolagents
- Foundation model(s): GPT-4o-mini, Llama-3.1-8B, Claude 3.5 Haiku (to test across model families)
- Agent topology: Standard single-agent for each framework; attacked via malicious MCP server
- Memory strategy: N/A (stateless per-attack evaluation)
- External tools/APIs: Custom malicious MCP servers (implementing 5 attack categories); legitimate MCP servers as controls

**Feasibility Timeline:**
| Phase | Months | Deliverable | Biggest Risk | Mitigation |
|---|---|---|---|---|
| Foundation | 1–3 | Define attack taxonomy (5 categories); build malicious MCP server toolkit; set up 4 framework baselines | MCP specification changes | Pin MCP protocol version |
| Core Build | 4–6 | Attack execution harness; defense implementations (hash pinning, sanitization, allowlisting) | Attack categories too similar to each other | Consult OWASP taxonomy; ensure orthogonality |
| Evaluation | 7–9 | Cross-framework vulnerability matrix; defense effectiveness measurement | Some frameworks too different to compare fairly | Standardize on identical tool sets and tasks across frameworks |
| Write-up | 10–12 | Paper, benchmark suite, malicious MCP server toolkit (responsible disclosure) | Responsible disclosure concerns | Release defenses alongside attacks; coordinate with framework maintainers |

**Evaluation Protocol:**
- Primary metrics: (1) Attack Success Rate (ASR) per attack category per framework; (2) Defense Effectiveness = 1 − (ASR_defended / ASR_undefended)
- Baselines: (1) Undefended framework (default settings); (2) Framework with basic input validation only
- Ablations: Attack category isolation; defense combination analysis; model family comparison
- Statistical rigor: 50 attack attempts per category per framework = 1,000+ data points; Fisher's exact test for significance

**Deliverables:**
- Open-source MCP tool-poisoning benchmark suite
- Malicious MCP server toolkit (with responsible disclosure protocol)
- Defense reference implementations (hash pinning, sanitization)
- Paper targeting USENIX Security 2027 or NeurIPS Safe AI workshop

**Ethical Analysis:**
- Misuse potential: HIGH — attack toolkit could be misused; mitigated by bundling defenses and coordinated disclosure
- Bias risk: LOW — security evaluation, not content generation
- Privacy: NONE — synthetic scenarios

**Interestingness Scores:**
- Build excitement: 5/5 (building attacks AND defenses = deeply engaging security research)
- Demo impact: 5/5 (live demo of an agent being tricked into exfiltrating data is attention-grabbing)
- Learning value: 5/5 (security engineering, protocol design, responsible disclosure — premium skills)

**Novelty Confidence:** HIGH
**Risk Level:** LOW
**Composite Suitability Score:** 90/100

---

## Direction 8: Cross-Lingual Agent Behavior Transfer for Low-Resource Indian Languages

**Innovation Category:** C (Resource-Constrained) + G (Domain-Specific)

**Core Research Question:**
Agent tool-use behaviors (planning strategies, tool-selection patterns) learned in English can transfer to Hindi, Marathi, and Tamil with ≤15% task-completion degradation using a lightweight LoRA adapter (≤100M parameters) on a 3B SLM, compared to ≥40% degradation for a non-adapted baseline, on a civic advisory task (government scheme eligibility).

**Novelty Justification:**
- Concept-level: **Exists partially** — Cross-lingual NLP transfer is well-studied. Agent behavior transfer across languages is NOT.
- Implementation-level: **Does NOT exist** — No system has demonstrated that *agentic behaviors* (not just text understanding) transfer across languages with lightweight adaptation.
- Evaluation-level: **Does NOT exist** — No benchmark measures agent *tool-use accuracy* across languages on the same task.
- **Differentiation:** Existing cross-lingual work focuses on text classification, NER, and QA. This is the first study examining whether *agentic planning and tool-use patterns* transfer across language boundaries, which is a fundamentally different capability (procedural vs. declarative knowledge transfer).

**Technical Architecture:**
- Base framework: smolagents (github.com/huggingface/smolagents) for lightweight agent loop
- Foundation model(s): Llama-3.2-3B-Instruct + LoRA adapter trained on Hindi/Marathi/Tamil agentic traces
- Agent topology: Single agent with tool-use in civic advisory domain
- Memory strategy: Conversation memory with language-tagged entries
- External tools/APIs: Bhashini API (existing team experience), IndicTrans2, government scheme database (from BenefitPulse)

**Feasibility Timeline:**
| Phase | Months | Deliverable | Biggest Risk | Mitigation |
|---|---|---|---|---|
| Foundation | 1–3 | English agent baseline on civic advisory task; collect/generate 1,000 agentic traces in English | Trace quality insufficient for training | Use GPT-4o to generate high-quality traces; human-validate 10% |
| Core Build | 4–6 | Translate traces to Hindi/Marathi/Tamil (Bhashini + human review); train LoRA adapters | Translation quality degrades tool-call syntax | Use structured tool-call format (JSON) that survives translation |
| Evaluation | 7–9 | Cross-lingual task-completion comparison; ablation of adapter vs. no-adapter vs. full fine-tune | Too few native speakers for evaluation | Recruit from classmates; target 3 evaluators per language |
| Write-up | 10–12 | Paper, LoRA adapters, multilingual trace dataset | — | — |

**Evaluation Protocol:**
- Primary metrics: (1) Task Completion Rate per language; (2) Tool-Selection Accuracy (correct tool chosen per step)
- Baselines: (1) English-only agent (no adaptation); (2) Machine-translated prompts (no LoRA)
- Ablations: LoRA on/off; language-specific vs. shared adapter; adapter size
- Statistical rigor: 100 tasks per language; bootstrap CI; Wilcoxon signed-rank test

**Deliverables:**
- Multilingual agentic trace dataset (English + 3 Indian languages)
- LoRA adapters for civic advisory domain
- Paper targeting LoResLM (EACL 2027) or REALM workshop

**Ethical Analysis:**
- Misuse potential: LOW — civic advisory is beneficial
- Bias risk: MEDIUM — scheme eligibility rules may reflect systemic biases; document explicitly
- Privacy: LOW — synthetic citizen profiles

**Interestingness Scores:**
- Build excitement: 4/5 (multilingual NLP + agent systems + real-world impact)
- Demo impact: 5/5 (live demo of agent helping a Marathi speaker navigate government schemes)
- Learning value: 4/5 (LoRA fine-tuning, multilingual AI, civic tech — growing field)

**Novelty Confidence:** HIGH
**Risk Level:** MEDIUM
**Composite Suitability Score:** 87/100

---

## Direction 9: Agent Workflow Replay & Differential Debugging

**Innovation Category:** B (Reliability) + H (Evaluation)

**Core Research Question:**
A deterministic replay system that captures and replays agent execution traces (including tool calls, API responses, and LLM outputs) with bit-exact reproducibility, and a "diff debugger" that highlights divergence points when replaying a modified agent against the original trace, will reduce agent debugging time by ≥50% (measured via a controlled developer study with 12 participants) compared to log-reading alone.

**Novelty Justification:**
- Concept-level: **Exists partially** — LangSmith and Langfuse provide trace visualization. Deterministic replay is standard in distributed systems (e.g., Deterministic Simulation Testing).
- Implementation-level: **Does NOT exist** — No agent debugging tool provides *deterministic replay with differential comparison* against a modified agent version.
- Evaluation-level: **Does NOT exist** — No study measures developer debugging efficiency with agent replay tools.
- **Differentiation:** LangSmith shows *what happened*. This direction enables *replaying what happened with a modified agent to see what changes* — analogous to `git diff` but for agent behavior.

**Technical Architecture:**
- Base framework: LangGraph with custom trace capture middleware
- Foundation model(s): Any (responses are cached during recording for deterministic replay)
- Agent topology: Any (framework-agnostic recording layer)
- Memory strategy: Full trace capture: (step_id, prompt, response, tool_call, tool_response, timestamp, random_seed)
- External tools/APIs: Custom mock servers that replay recorded API responses

**Feasibility Timeline:**
| Phase | Months | Deliverable | Biggest Risk | Mitigation |
|---|---|---|---|---|
| Foundation | 1–3 | Trace capture middleware for LangGraph; recording format specification (JSONL) | Non-deterministic API responses make replay impossible | Cache and replay all external responses; seed all random sources |
| Core Build | 4–6 | Replay engine; diff viewer (terminal + web UI); divergence-point detection | UI complexity exceeds team's frontend skills | Use Streamlit for web UI; terminal diff as fallback |
| Evaluation | 7–9 | Developer study: 12 participants debug 3 agent bugs with/without replay tool | Participant recruitment | Recruit from CS department; 12 is sufficient for within-subjects design |
| Write-up | 10–12 | Paper, open-source replay framework, study data | — | — |

**Evaluation Protocol:**
- Primary metrics: (1) Time-to-diagnosis (seconds from bug report to correct root cause identification); (2) Diagnosis accuracy (correct root cause identified?)
- Baselines: (1) Log-reading only (standard LangSmith-style trace viewer); (2) Log + breakpoint debugging
- Ablations: Replay only vs. replay + diff; UI modality (terminal vs. web)
- Statistical rigor: 12 participants × 3 bugs × 2 conditions = within-subjects design; paired t-test; effect size (Cohen's d)

**Deliverables:**
- Open-source agent replay & diff debugging framework
- Trace recording format specification (potential community standard)
- Developer study results
- Paper targeting CHI 2027 or ICSE 2027 (SE + AI track)

**Ethical Analysis:**
- Misuse potential: LOW — developer tool
- Bias risk: NONE
- Privacy: LOW — developer study requires informed consent (but exempt-level, not full IRB)

**Interestingness Scores:**
- Build excitement: 5/5 (building a debugging tool is deeply satisfying systems engineering)
- Demo impact: 4/5 (side-by-side replay showing exactly where the agent diverged is compelling)
- Learning value: 5/5 (deterministic replay, distributed systems debugging, developer tooling — premium industry skills)

**Novelty Confidence:** HIGH
**Risk Level:** LOW
**Composite Suitability Score:** 89/100

---

## Direction 10: Adaptive Autonomy Levels via Trust Calibration

**Innovation Category:** D (Human-Agent Interaction)

**Core Research Question:**
An agent that dynamically adjusts its autonomy level (from "suggest only" → "act with confirmation" → "act autonomously") based on a running trust score derived from the human's acceptance/rejection patterns will converge to the human's preferred autonomy level within 20 interactions, achieving ≥85% acceptance rate on the autonomy level selected, compared to ≤60% for a fixed autonomy baseline, in a simulated task-management scenario.

**Novelty Justification:**
- Concept-level: **Exists partially** — "Adjustable autonomy" is studied in HRI/robotics. LLM agents with *learned* trust calibration from interaction patterns is NOT published.
- Implementation-level: **Does NOT exist** — No agent system dynamically adjusts its autonomy level based on a Bayesian trust model learned from user feedback.
- Evaluation-level: **Does NOT exist** — No benchmark measures "autonomy calibration convergence speed."
- **Differentiation:** Existing HITL systems have fixed autonomy (always ask, or always act). This direction introduces a *learned* autonomy curve that adapts to each user's risk tolerance, using a multi-armed bandit or Bayesian approach.

**Technical Architecture:**
- Base framework: LangGraph with custom "Trust Manager" node
- Foundation model(s): GPT-4o-mini or Llama-3.1-8B
- Agent topology: Single agent with 3 operating modes (suggest / confirm / autonomous); Trust Manager selects mode per action
- Memory strategy: User interaction history with (action, autonomy_level, user_response) triples; Thompson Sampling or UCB for trust exploration
- External tools/APIs: Simulated task-management environment (email drafting, calendar scheduling, file organization)

**Feasibility Timeline:**
| Phase | Months | Deliverable | Biggest Risk | Mitigation |
|---|---|---|---|---|
| Foundation | 1–3 | Define 3 autonomy levels; build simulated task environment; implement fixed-autonomy baselines | Task environment too simple | Add 3 risk levels to tasks (low/medium/high stakes) |
| Core Build | 4–6 | Trust Manager with Thompson Sampling; autonomy selection logic; feedback loop | Trust model doesn't converge | Try multiple algorithms (UCB, EXP3, Bayesian); report best |
| Evaluation | 7–9 | Simulation with 20 synthetic user personas (varying risk tolerance); convergence analysis | Synthetic personas too uniform | Define personas with explicit risk profiles (risk-averse, risk-neutral, risk-seeking) |
| Write-up | 10–12 | Paper, open-source Trust Manager plugin, persona simulation suite | — | — |

**Evaluation Protocol:**
- Primary metrics: (1) Convergence Speed (interactions to reach ≥85% acceptance rate); (2) Steady-State Acceptance Rate
- Baselines: (1) Always-ask (minimum autonomy); (2) Always-act (maximum autonomy); (3) Fixed medium autonomy
- Ablations: Trust algorithm (Thompson vs. UCB vs. fixed); number of autonomy levels (2 vs. 3 vs. 5); persona diversity
- Statistical rigor: 20 personas × 50 interactions each = 1,000 data points; convergence curves with CI

**Deliverables:**
- Open-source Trust Manager plugin for LangGraph
- Synthetic persona simulation suite
- Paper targeting CHI 2027 or AAMAS 2027

**Ethical Analysis:**
- Misuse potential: MEDIUM — could be used to slowly escalate autonomy without user awareness; mitigated by transparency of current autonomy level
- Bias risk: MEDIUM — trust model may not generalize across cultural contexts
- Privacy: LOW — synthetic personas only

**Interestingness Scores:**
- Build excitement: 4/5 (bandits + agent autonomy = elegant)
- Demo impact: 4/5 (watching the agent learn to "know when to ask" is intuitive and compelling)
- Learning value: 5/5 (multi-armed bandits, HCI, trust modeling — interdisciplinary skills)

**Novelty Confidence:** HIGH
**Risk Level:** LOW
**Composite Suitability Score:** 88/100

---

## Cross-Validation Self-Audit

### 1. Overlap Check
- Directions 1 (Reversibility) and 2 (Uncertainty Propagation) are *complementary, not overlapping* — one classifies action risk, the other propagates confidence. They could compose but address different problems.
- Direction 6 (Bi-Temporal Audit) and the existing C3 (Faithfulness Traces) are *adjacent* — C3 checks if reasoning is faithful, D6 checks if facts are temporally provenant. Different contributions.

### 2. Category Coverage
| Category | Directions |
|---|---|
| A. Architectural | 3, 6 |
| B. Reliability & Verification | 1, 2, 9 |
| C. Resource-Constrained | 5, 8 |
| D. Human-Agent Interaction | 1, 10 |
| E. Multi-Agent Coordination | 7 |
| F. Scientific Discovery | — (not covered; existing C3/B6 from prior analysis already address this) |
| G. Domain-Specific | 4, 8 |
| H. Evaluation & Benchmarking | 2, 5, 7, 9 |

**7 of 8 categories covered.** Category F (Scientific Discovery) is intentionally omitted — our prior analysis already has strong candidates (C3, B6, B1) in this space.

### 3. Risk Distribution
| Risk Level | Count | Directions |
|---|---|---|
| LOW | 4 | 1, 5, 7, 9, 10 |
| MEDIUM | 5 | 2, 3, 4, 6, 8 |
| HIGH | 0 | — |

> [!NOTE]
> No HIGH-risk directions were proposed. This is intentional given the constraint of a 4-person undergraduate team with 12 months. The MEDIUM-risk directions (3, 4, 6, 8) provide sufficient "reach" opportunities.

### 4. Anti-Pattern Scan
All 10 directions pass. None match the 8 anti-patterns. Direction 4 (Regulatory Compliance) is closest to "Apply Framework X to Domain Y" but is differentiated by the obligation KG and the first-of-its-kind evaluation dataset.

### 5. Feasibility Gut Check
All directions are feasible for a motivated 4-person team in 12 months, with the following caveats:
- **Direction 3** (Speculative Branching): Requires strong async programming skills. If the team lacks this, substitute Direction 5.
- **Direction 8** (Cross-Lingual Transfer): Requires LoRA fine-tuning experience. If new to this, add 1 month to Foundation phase.

### 6. Novelty Confidence Summary
| Direction | Novelty Confidence |
|---|---|
| 1. Reversibility-Aware Planning | HIGH |
| 2. Cascading Uncertainty | HIGH |
| 3. Speculative Branching | MEDIUM |
| 4. Regulatory Compliance Diff | HIGH |
| 5. Energy Profiling | MEDIUM |
| 6. Bi-Temporal Audit Trail | MEDIUM |
| 7. MCP Tool-Poisoning Benchmark | HIGH |
| 8. Cross-Lingual Agent Transfer | HIGH |
| 9. Replay & Diff Debugging | HIGH |
| 10. Adaptive Autonomy | HIGH |

---

## Summary Ranking Table

| Rank | Dir# | Title | Category | Composite Score | Risk | Novelty Confidence |
|---|---|---|---|---|---|---|
| **🥇 1** | **1** | **Action-Reversibility-Aware Planning** | B+D | **91/100** | LOW | HIGH |
| **🥈 2** | **7** | **MCP Tool-Poisoning Benchmark** | H+E | **90/100** | LOW | HIGH |
| **🥉 3** | **2** | **Cascading Uncertainty Propagation** | H+B | **89/100** | MEDIUM | HIGH |
| 3 (tie) | **9** | **Replay & Diff Debugging** | B+H | **89/100** | LOW | HIGH |
| 5 | **4** | **Regulatory Compliance Diff** | G | **88/100** | MEDIUM | HIGH |
| 5 (tie) | **6** | **Bi-Temporal Belief Audit Trail** | A+B | **88/100** | MEDIUM | MEDIUM |
| 5 (tie) | **10** | **Adaptive Autonomy via Trust** | D | **88/100** | LOW | HIGH |
| 8 | **3** | **Speculative Multi-Path Execution** | A | **87/100** | MEDIUM | MEDIUM |
| 8 (tie) | **8** | **Cross-Lingual Agent Transfer** | C+G | **87/100** | MEDIUM | HIGH |
| 10 | **5** | **Energy Profiling & Green Routing** | C+H | **86/100** | LOW | MEDIUM |

---

## Final Recommendation

### 🥇 Top Pick: Direction 1 — Action-Reversibility-Aware Agent Planning
The cleanest research contribution: a novel planner component (not just a policy layer) that reasons about action consequences *before* execution. Low technical risk, high publication potential (AAMAS/AAAI), produces a reusable annotated dataset, and the safety angle is timely for EU AI Act compliance. The team learns LangGraph state machines, classifier training, and safety engineering — all premium skills.

### 🥈 Runner-Up: Direction 7 — MCP Tool-Poisoning Adversarial Benchmark
The most *exciting* direction to build. Creating attacks AND defenses is deeply engaging, the demo is visceral (watching an agent get tricked live), and the artifact (standardized benchmark suite) would be immediately adopted by the community. Security engineering skills are among the most transferable. Risk: responsible disclosure requires coordination with framework maintainers.

### 🥉 Strong Alternative: Direction 9 — Agent Workflow Replay & Differential Debugging
The most *practically useful* direction. A deterministic replay tool for agent debugging would be used by every agent developer — the "git diff for agent behavior" framing is immediately compelling. Low technical risk, strong CHI/ICSE publication target, and the developer study (12 participants) is feasible without full IRB. The team learns distributed systems debugging, developer tooling, and HCI evaluation methods.
