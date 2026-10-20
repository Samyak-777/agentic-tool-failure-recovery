# ToolMaze Offline Failure Analysis & Diagnostic Report

- **Generated At**: 2026-10-20T15:07:48.546522+00:00
- **Runs Analyzed**: `c3_care_telemetry_500, c4_care_telemetry_500, run_20261019_194036_9fe824, run_20261019_201805_8931c7, run_20261020_021004_3c50a9, run_20261020_054844_005104`
- **Total Tasks Analyzed**: 2002
- **Schema Version**: `1.0.0`

## 1. Task Success Rate (TSR) by Perturbation Mode
| Mode | Total | Passed | Failed | TSR | Mean Tokens | Mean Duration (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| P0 | 402 | 135 | 267 | **33.6%** | 31981 | 79.30 |
| P1 | 400 | 63 | 337 | **15.8%** | 27739 | 68.13 |
| P2 | 400 | 8 | 392 | **2.0%** | 18900 | 51.90 |
| P3 | 400 | 10 | 390 | **2.5%** | 25617 | 69.22 |
| P4 | 400 | 3 | 397 | **0.8%** | 23224 | 63.70 |

## 2. Causal Attribution of Failures
| Causal Category | Count | Sample Size | Proportion |
| :--- | :---: | :---: | :---: |
| `perturbation_not_activated` | 558 | 2002 | 27.9% |
| `perturbation_changed_execution_no_failure` | 84 | 2002 | 4.2% |
| `failure_supported_by_evidence_as_perturbation_related` | 965 | 2002 | 48.2% |
| `perturbation_changed_failure_attribution_uncertain` | 303 | 2002 | 15.1% |
| `failure_unrelated_to_observed_perturbation` | 92 | 2002 | 4.6% |

- **Total Configured Perturbations**: 14064
- **Total Actually Activated Perturbations**: 1804
- **Tasks Recovered After Activation**: 84

## 3. Agent Performance Comparison (Baseline vs CARE)
| Agent | Total | Passed | TSR | Mean Tokens |
| :--- | :---: | :---: | :---: | :---: |
| `care` | 1002 | 123 | **12.3%** | 24453 |
| `baseline` | 1000 | 96 | **9.6%** | 26536 |

### Matched Task Comparison
- **matched_tasks_count**: 1000
- **care_matched_tsr**: 12.30%
- **baseline_matched_tsr**: 9.60%
- **delta_tsr**: -2.70%

## 4. Recovery and DAG Rerouting Summary
- **Total Recovery Directives Issued**: 1000
- **Tasks Attempting Recovery**: 552
- **Tasks Successfully Recovered**: 60 (10.9%)
- **Budget Exhaustions**: 14
- **Loop / Cyclic Deadlocks Prevented**: 260
- **Alternative DAG Paths Selected**: 719 (Pruned: 0)

## 5. Diagnostic Metrics (Section 12)
- **Perturbation Activation Rate**: 90.2% (1444/1600)
- **Perturbation Recovery Rate (PRR)**: 5.8% (84/1444)
- **Rate of Failures with Uncertain Attribution**: 15.1% (303/2002)
- **Semantic Invalid Output Rate**: 11.6% (1438/12348)
- **Telemetry Completeness Rate**: 100.0% (2002/2002)
