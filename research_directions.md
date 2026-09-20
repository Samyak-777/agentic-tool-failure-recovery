# Agentic AI Research Directions for a Final-Year Project

Selection criteria used below: each direction must be buildable by one person (maybe two) in 6-12 months on a single GPU or API budget, must produce a number you can put in a results table, and must not be "RAG pipeline #4,001" or "chatbot with a system prompt." Two of the four connect directly to work already in progress (BenefitPulse, VarishthaMitra/Bhashini), which cuts ramp-up time and gives a head start on domain knowledge.

---

## 1. Hierarchical Episodic-Semantic Memory with Decay-Driven Consolidation for Long-Horizon Agents

**Core hypothesis (falsifiable):** An agent memory architecture that splits storage into (a) a raw episodic log scored by a spaced-repetition-style decay function and (b) a consolidated semantic store built by periodic LLM-driven summarization, will beat flat vector-store retrieval on multi-session task success rate and will use fewer context tokens per turn, with the gap widening as session count grows past roughly 20-30 sessions.

**Novelty vs. existing work:** MemGPT/Letta (paging between "working" and "archival" memory, arXiv:2310.08560) has no decay function — every archived memory is equally retrievable regardless of age or reinforcement, so retrieval noise grows with history length. Generative Agents (Park et al., arXiv:2304.03442) scores memories on recency, importance, and relevance, but the weights are fixed heuristics, not a tested forgetting curve, and there's no consolidation step that merges related episodic memories into semantic facts. The gap: nobody has combined a principled decay/reinforcement model (à la SM-2 spaced repetition) with a consolidation trigger that converts episodic clutter into compact semantic memory, then measured the token-cost and accuracy tradeoff directly against flat RAG.

**Feasibility, 12 months:**
- Months 1-3: read MemGPT/Letta, Generative Agents, MemoryBank (AAAI 2024); set up LangGraph + Chroma/FAISS + a local model via Ollama (Llama 3 8B or Phi-3, to keep API costs down); implement the flat-RAG baseline agent; pick a benchmark — LoCoMo (long-context multi-session dialogue) or a custom multi-day task simulation if LoCoMo's license is restrictive.
- Months 4-6: build the episodic store with decay scoring, the consolidation trigger (summarize/cluster episodic entries once a buffer threshold is hit), and blended retrieval (decay-weighted episodic + semantic).
- Months 7-9: run experiments across horizon lengths (5, 15, 30, 50+ sessions); ablate decay on/off and consolidation on/off; sweep decay hyperparameters; log token cost per turn.
- Months 10-12: human evaluation of recall coherence, write-up, repo cleanup, thesis.

**Tools/repos to build on:** Letta (github.com/letta-ai/letta), LangGraph (github.com/langchain-ai/langgraph), Chroma (github.com/chroma-core/chroma), Generative Agents reference implementation (github.com/joonspk-research/generative_agents), LoCoMo benchmark (github.com/snap-research/locomo).

**Deliverables:** repo with pinned deps (uv or poetry lockfile) and a Dockerfile, benchmark harness, experiment logs (Weights & Biases), a demo video of the agent recalling facts across a simulated 30-session scenario.

**Metrics:** automated — task success rate on multi-session QA, retrieval precision@k against a gold fact set, token cost/turn, latency. Human — 3 raters score recall accuracy and coherence on a 1-5 scale, report inter-rater agreement (Cohen's kappa).

**Ethics/reproducibility:** persistent memory of user data is a genuine privacy concern if this ever leaves the lab, so all evaluation runs on synthetic personas, and the design includes a memory-deletion endpoint as a first-class feature, not an afterthought.

**Data fallback:** if LoCoMo access or licensing is a problem, generate synthetic multi-session dialogues with an LLM and validate a sample by hand.

---

## 2. Bandwidth-Constrained Agentic Advisory System for Low-Connectivity Deployment

**Core hypothesis:** A quantized small model (under 3B parameters) using a "plan-once, execute-offline, sync-later" protocol — one planning round instead of per-step ReAct round trips — can match a cloud GPT-4-class ReAct agent's task-completion rate on a domain advisory task (e.g., crop-disease diagnosis plus government scheme eligibility, or civic grievance routing) while running on under 100 kbps effective bandwidth and edge hardware such as a Raspberry Pi 4 or Jetson Nano.

**Novelty vs. existing work:** most "AI for underserved regions" projects are WhatsApp chatbots wired to a cloud LLM API — not agentic, and they assume the connection is always up. Academic agent frameworks (AutoGen, CrewAI, LangGraph) assume near-zero-latency tool calls. This direction targets the actual failure mode of rural deployment — intermittent, low-bandwidth connectivity — with an architecture that front-loads planning into a single low-bandwidth exchange, then executes tool calls locally against cached/offline data, syncing results when connectivity returns.

**Feasibility, 12 months:** the on-device inference stack is mature (llama.cpp, Ollama) so the main research work is the plan-once protocol and the offline/online sync layer, both scoped correctly for two semesters.
- Months 1-3: benchmark candidate small models (Phi-3-mini, Gemma 2B, an Indic-tuned model) for tool-use accuracy on the target domain; set up a bandwidth-throttled test harness (tc/netem on Linux to simulate 100 kbps with packet loss); build the cloud ReAct baseline.
- Months 4-6: implement plan-once protocol, offline execution engine, and sync/reconciliation logic.
- Months 7-9: run head-to-head trials against the baseline at multiple bandwidth/latency profiles; measure task completion and round-trip count.
- Months 10-12: field-style test with a handful of real users if feasible (even a controlled hostel/campus trial), write-up.

**Tools/repos to build on:** llama.cpp (github.com/ggml-org/llama.cpp), Ollama, smolagents (github.com/huggingface/smolagents) for a lightweight agent loop, AI4Bharat's IndicTrans2 for regional-language support, Bhashini API for speech/translation (already used in the VarishthaMitra work, so the integration pattern is familiar).

**Deliverables:** repo with a reproducible bandwidth-throttled test harness, a demo video showing the same task completed over a throttled connection, comparison table against the cloud baseline.

**Metrics:** automated — task completion rate, round-trip count, total bytes transferred, end-to-end latency under each bandwidth profile. Human — usability rating from test users, especially around trust when the system operates offline for a stretch.

**Ethics/reproducibility:** offline advisory systems (crop disease, scheme eligibility) carry real consequences if wrong, so the design needs an explicit confidence threshold below which the agent defers to a human/helpline rather than answering; document this as a guardrail, not a footnote. Pin exact model checkpoints and quantization settings for reproducibility, since accuracy is quantization-sensitive.

**Data fallback:** if a real government-scheme dataset isn't available, build a smaller curated set of scheme rules (these are public documents) and synthesize test queries against it.

---

## 3. Faithfulness-Audited Reasoning Traces for High-Stakes Eligibility Decisions

**Core hypothesis:** Requiring an agent to emit a structured, machine-checkable reasoning trace (claim → evidence → rule citation, rather than free-text chain-of-thought) and then running an automated counterfactual consistency check — perturb one input feature and verify the trace updates consistently with the decision — will catch a measurable fraction of unfaithful explanations (cases where the stated reasoning doesn't match what actually drove the decision) on a benefit/credit eligibility task.

**Novelty vs. existing work:** "add explanations to the agent" is common; actually testing whether those explanations are faithful is not. Lanham et al.'s faithfulness work (Anthropic, 2023) measures this for free-text chain-of-thought on reasoning benchmarks, not for structured agentic decision systems with rule citations. The novel piece here is the structured trace format (so it's checkable at all) plus the counterfactual perturbation test applied to a decision-system setting, where faithfulness actually matters for accountability.

**This direction connects directly to the Amex BenefitPulse work** — the benefit-underutilization/Empirical Bayes shrinkage system already produces per-benefit decisions; extending it with a structured, auditable reasoning layer turns an existing hackathon prototype into a research contribution rather than starting from zero.

**Feasibility, 12 months:**
- Months 1-3: literature review (faithfulness/CoT auditing, DSPy's typed signatures for structured output), define the trace schema (claim/evidence/rule-ID), build or extend a rule-based eligibility dataset from BenefitPulse's domain or a public credit/benefit dataset.
- Months 4-6: implement the structured-trace agent (DSPy or Outlines/Guidance for constrained generation) and the free-text CoT baseline for comparison.
- Months 7-9: build the counterfactual perturbation harness, run it across both agents, measure faithfulness violation rate.
- Months 10-12: human expert review of a sample of flagged violations to validate the automated check isn't producing false positives, write-up.

**Tools/repos to build on:** DSPy (github.com/stanfordnlp/dspy) for typed structured prompting, Outlines (github.com/dottxt-ai/outlines) or Guidance (github.com/guidance-ai/guidance) for constrained output, and the existing BenefitPulse Entitlement Ledger/scoring logic as the decision engine to instrument.

**Deliverables:** repo with the trace schema, the perturbation-testing harness, side-by-side faithfulness numbers for structured vs. free-text CoT, a short demo showing a caught unfaithful trace.

**Metrics:** automated — faithfulness violation rate (fraction of decisions where a perturbed feature changes the outcome but not the cited reasoning, or vice versa), trace completeness (fraction of decisions with a fully resolved evidence chain). Human — domain-expert agreement rate with flagged violations, rated on a 3-point scale (genuine issue / ambiguous / false positive).

**Ethics/reproducibility:** this is explicitly a high-stakes domain (eligibility for benefits/credit), so the write-up needs a limitations section on what "faithful but wrong" still means for the person affected, and the dataset should avoid any real personally identifiable financial data — synthetic or public anonymized data only. Log every experiment run with fixed seeds.

**Data fallback:** public credit-scoring datasets (e.g., German Credit, LendingClub's public data) work as a substitute domain if the benefit-eligibility framing needs a larger dataset than what's available from the BenefitPulse work.

---

## 4. Formal Human-Veto Protocol for Multi-Agent Resource Negotiation

**Core hypothesis:** A multi-agent negotiation protocol with an explicit veto/audit checkpoint, implemented as a formal state machine with logged reason codes rather than ad hoc "ask the human" prompting, achieves higher Pareto efficiency and higher human trust ratings than the default human-in-the-loop hooks in AutoGen or CrewAI, on a simulated resource-allocation task.

**Novelty vs. existing work:** AutoGen's and CrewAI's human-in-the-loop support is turn-based intervention — the human can interrupt, but there's no formal semantics for a veto, no required justification, and no audit trail that can be replayed later. This direction formalizes the negotiation as a state machine (or Petri net) where every veto is a typed event with a reason code, producing a replayable audit log — something regulators or reviewers could actually inspect after the fact, which ad hoc prompting doesn't give you.

**Feasibility, 12 months:** LangGraph is already a graph/state-machine framework, so the state-machine formalization is a natural fit rather than a from-scratch build.
- Months 1-3: literature review (multi-agent negotiation protocols, AutoGen's human-in-loop design, mechanism design basics for Pareto efficiency), pick a toy domain (hospital bed allocation under surge, or something lower-stakes like lab-slot/resource allocation), build the baseline using AutoGen or CrewAI's default hooks.
- Months 4-6: design and implement the state machine (states, veto transitions, reason-code taxonomy) in LangGraph.
- Months 7-9: run simulated negotiations across both systems, compute Pareto efficiency of outcomes, run a small user study having participants play the human-in-loop role and rate trust/transparency.
- Months 10-12: write-up, repo cleanup.

**Tools/repos to build on:** LangGraph (github.com/langchain-ai/langgraph) for the state machine, Microsoft AutoGen (github.com/microsoft/autogen) and CAMEL (github.com/camel-ai/camel) as baseline comparisons.

**Deliverables:** repo with the state-machine implementation, a replayable audit-log format (JSON schema), simulation results, a short video of a negotiation run with a veto triggered mid-negotiation and traced back through the log.

**Metrics:** automated — Pareto efficiency of final allocations vs. a theoretical optimum, number of negotiation rounds to convergence, veto rate. Human — trust and transparency ratings (Likert scale) from participants who played the human-in-loop role, compared across the two systems.

**Ethics/reproducibility:** even a toy resource-allocation domain should be framed carefully if it echoes real high-stakes decisions (hospital allocation especially) — state clearly in the write-up that this is a simulated testbed, not a deployment-ready system, and that real deployment would need domain-expert review of the reason-code taxonomy. Fix random seeds for all simulated negotiation runs.

**Data fallback:** none needed — the task is a simulation, so there's no dataset-availability risk, which is itself one advantage of this direction (see comparison below).

---

## 5. Retrospective Literature-Based Discovery Agent

**Core hypothesis:** A multi-agent pipeline that mines a time-sliced scientific literature corpus (papers published before cutoff year Y) and generates candidate cross-domain hypotheses through co-occurrence-graph reasoning plus an LLM critique/red-team loop will "rediscover" a statistically significant share of relationships that were only published after year Y, at a higher rate than a co-occurrence-only baseline with no agentic reasoning.

**Novelty vs. existing work:** Swanson's classic ABC literature-based-discovery model (the fish-oil/Raynaud's-syndrome connection) used pure co-occurrence statistics with no reasoning step. Recent LLM hypothesis-generation demos — Sakana AI's "AI Scientist," ResearchAgent — produce novel-sounding hypotheses but are evaluated qualitatively or by review cost, not against an objective ground truth. The gap this fills: use time-sliced corpora as automatic ground truth (can the agent "discover," from earlier literature only, what got published later?), which removes the need for expensive expert evaluation as the *primary* metric while still keeping a human plausibility check as a secondary validation step.

**Feasibility, 12 months:**
- Months 1-3: pick a narrow domain with a known historical discovery pair to validate the method against (biomedical subfields work well here — migraine/magnesium is one example besides Swanson's original), download a time-sliced corpus via the PubMed or arXiv API, build the co-occurrence-graph baseline.
- Months 4-6: build the multi-agent pipeline — retrieval agent, hypothesis-generation agent, a critique/red-team agent that checks plausibility and searches for contradicting evidence, then a ranking step.
- Months 7-9: run the pipeline across multiple time cutoffs, measure rediscovery rate against the baseline, tune the number of critique rounds.
- Months 10-12: get a domain expert to rate plausibility of the top-ranked *not-yet-published* candidates (the genuinely novel output), write-up.

**Tools/repos to build on:** PubMed E-utilities API, arXiv API, NetworkX for the co-occurrence graph, AutoGen or CrewAI for the critique loop, PubTator/LitSense for entity extraction, Sakana AI's AI Scientist repo (github.com/SakanaAI/AI-Scientist) as an architectural reference point to differentiate against, not to copy.

**Deliverables:** repo with the corpus pipeline and agent pipeline, rediscovery-rate results across several cutoff years, a ranked list of candidate hypotheses not yet found in the literature with expert plausibility scores attached.

**Metrics:** automated — rediscovery rate (recall of post-cutoff relationships within the top-N generated hypotheses) vs. the co-occurrence baseline, precision@N. Human — blind plausibility rating (1-5) from a domain expert on a sample of top novel candidates, blind to whether each came from the agent or the baseline.

**Ethics/reproducibility:** hypothesis-generation tools risk dressing up spurious correlations as discoveries if used uncritically — frame every output explicitly as a candidate for expert review, not a conclusion, and report the false-discovery rate alongside the rediscovery rate.

**Data:** fully public (PubMed, arXiv), no access constraints. If the first domain doesn't have a clean historical discovery pair to validate against, swapping domains is cheap since the pipeline is domain-agnostic.

---

## 6. Knowledge-Tracing-Driven Socratic Tutoring Agent

**Core hypothesis:** An agent that picks its next question using a live Bayesian Knowledge Tracing (or IRT) estimate of per-skill mastery, and answers with guiding questions rather than direct answers, produces a larger learning-gain (pre/post test delta) on a bounded technical topic than a static-curriculum agent or a direct-answer agent, controlling for time spent.

**Novelty vs. existing work:** most LLM tutoring products get "Socratic" from a persona instruction in the system prompt, with no underlying mastery model actually driving what gets asked next. Pairing a real knowledge-tracing model — from the classic intelligent-tutoring-systems literature, not a new invention — with LLM-generated Socratic dialogue, and evaluating with an actual controlled pre/post study instead of a satisfaction survey, is the differentiator.

**Feasibility, 12 months:**
- Months 1-3: pick a bounded, skill-decomposable topic (a specific DSA subtopic, or a proof technique), build or hand-author a skill-tagged item bank (40-60 items is enough), implement the BKT model.
- Months 4-6: build the Socratic agent, constrained by a structured prompt/DSPy signature to only ask guiding questions and never state the answer, wired to the live BKT estimate for question selection.
- Months 7-9: recruit a small participant pool (classmates or juniors work fine), run controlled sessions across three conditions — Socratic+BKT, static curriculum, direct-answer — with pre/post tests.
- Months 10-12: statistical analysis (learning-gain effect sizes), write-up.

**Tools/repos to build on:** pyBKT (github.com/CAHLR/pyBKT) for the knowledge-tracing model, DSPy for constrained Socratic question generation.

**Deliverables:** repo with all three tutoring conditions as runnable agents, a small controlled-study write-up with effect sizes.

**Metrics:** automated — per-skill mastery convergence speed, question efficiency (mastery gained per question asked). Human — pre/post test score delta as the primary outcome, plus a short engagement survey.

**Ethics/reproducibility:** running a study with real participants needs informed consent and — if a formal publication is the goal — VNIT's ethics/IRB-equivalent review. Keep the topic ungraded to avoid any coercion concern, and anonymize participant data.

**Data:** self-authored item bank plus data from a small in-person study — no external dataset dependency, which removes licensing risk but shifts the main feasibility risk onto actually recruiting participants; worth flagging up front.

---

## 7. Partition-Tolerant Agent Swarm for Distributed Sensing/Coordination

**Core hypothesis:** A swarm of lightweight local agents, each running a small on-device model, that reach consensus through a gossip protocol tolerant of network partitions will hold higher consensus accuracy under simulated connectivity loss than a centralized-coordinator baseline on a distributed sensing task (simulated campus environmental monitoring, or a multi-node anomaly-detection task), while using substantially less total bandwidth.

**Novelty vs. existing work:** this is distinct from the bandwidth-constrained single-agent direction above — here the coordination *protocol itself* is the object of study, not one agent's efficiency. AutoGen, CrewAI, and MetaGPT all assume always-on, low-latency messaging between agents. This direction studies what breaks when that assumption fails, under simulated network partitions, comparing a gossip/epidemic-protocol consensus mechanism against the naive centralized-coordinator pattern these frameworks default to.

**Feasibility, 12 months:**
- Months 1-3: review gossip protocols, epidemic algorithms, and CRDTs for eventual consistency; set up a partition-simulation harness (Mininet, or a custom asyncio-based simulator); build the centralized-coordinator baseline with AutoGen.
- Months 4-6: implement the gossip-based swarm — each node running a small local model plus a CRDT-backed shared state — and design partition-injection test scenarios.
- Months 7-9: run experiments across partition severity and duration, measure consensus accuracy and bandwidth used.
- Months 10-12: write-up, ablate swarm size and gossip fanout.

**Tools/repos to build on:** AutoGen (github.com/microsoft/autogen) or a custom asyncio agent loop, Mininet for network simulation, a CRDT library for shared-state consistency, small local models via Ollama.

**Deliverables:** repo with the simulation harness, consensus-accuracy-vs-bandwidth curves across partition conditions, a demo of the swarm recovering consensus after a simulated partition heals.

**Metrics:** automated only — consensus accuracy against simulated ground truth, time-to-consensus after a partition heals, total bytes exchanged, per-node message overhead. No human-eval component needed, since correctness is objectively checkable against the simulation — a genuine advantage for a solo project, since it removes study-recruitment overhead entirely.

**Ethics/reproducibility:** minimal ethical surface area since this is a pure systems/simulation study; the main obligation is being upfront in the write-up about the gap between simulated partitions and real network behavior, without overclaiming deployment-readiness.

**Data:** none needed beyond the simulation environment itself — lowest external-dependency risk of any direction listed here.

---

## Why these over the obvious alternatives

| Direction | vs. conventional alternative | Main risk |
|---|---|---|
| 1. Memory architecture | Beats "fine-tune a RAG pipeline" because the contribution is architectural (a testable mechanism) rather than a hyperparameter sweep — reviewers can evaluate the idea independent of any one dataset | Benchmark availability/licensing for long-horizon eval |
| 2. Bandwidth-constrained agent | Beats "build another WhatsApp LLM bot" because it targets a real infra constraint with a measurable protocol change, not just a UI wrapper around an API | Access to real low-connectivity test conditions; mitigated by netem-based simulation |
| 3. Faithfulness auditing | Beats "add explainability to my hackathon project" because it produces a number (violation rate) instead of a qualitative claim, and reuses existing BenefitPulse work instead of starting cold | Automated faithfulness check needs careful validation against human judgment to avoid false positives |
| 4. Human-veto negotiation protocol | Beats "wire up AutoGen with a human-in-loop callback" because the state-machine formalization is itself the contribution and produces an auditable artifact | No dataset dependency at all — lowest data risk among the first four |
| 5. Literature-based discovery agent | Beats "ask an LLM to brainstorm research ideas" because retrospective validation against real publication history gives an objective, automatic ground truth instead of relying on expert opinion alone | Needs a domain with a clean historical discovery pair to validate the method against |
| 6. Knowledge-tracing Socratic tutor | Beats "prompt an LLM to be a Socratic tutor" because the question-selection policy is grounded in a measurable mastery model, and the eval is a real controlled study, not a satisfaction score | Needs actual participant recruitment — the main feasibility risk of the whole set |
| 7. Partition-tolerant agent swarm | Beats "add more agents to my CrewAI pipeline" because it tests the one assumption every popular framework quietly makes — reliable messaging — and does it with zero dataset or study dependency | Purely simulated; real-world network behavior may diverge from the simulation |

All seven avoid the saturated categories explicitly (basic chatbot polish, RAG hyperparameter tuning, standard codegen benchmarks) and each produces at least one clean automated metric plus a human-evaluation component, which is what a thesis committee will actually want to see in the results chapter.

If you want, I can turn any one of these into a fuller proposal document (motivation, related-work table, detailed budget/compute estimate) or start scaffolding the repo structure for whichever direction looks most promising to you.
