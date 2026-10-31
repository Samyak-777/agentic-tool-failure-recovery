"""
ToolMaze/dag_rerouting/path_selector.py
Layer 4: DAG-Aware Alternative Path Selection

Analyzes task DAG, alternative tool groups, and current execution state
to deterministically find unblocked substitute tools and bypass failed nodes.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

try:
    from tools.alternatives_loader import AlternativesLoader, AlternativeGroup
except ImportError:
    from ..tools.alternatives_loader import AlternativesLoader, AlternativeGroup


@dataclass
class RerouteCandidate:
    """Represents the outcome of a DAG rerouting search."""
    failed_tool: str
    candidate_tools: List[str] = field(default_factory=list)
    selected_tool: Optional[str] = None
    target_path: Optional[List[str]] = None
    reason: str = ""
    is_viable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "failed_tool": self.failed_tool,
            "candidate_tools": self.candidate_tools,
            "selected_tool": self.selected_tool,
            "target_path": self.target_path,
            "reason": self.reason,
            "is_viable": self.is_viable,
        }


class DAGPathSelector:
    """Selects valid alternative tools and execution paths when a tool is blocked."""

    def __init__(
        self,
        alternatives_loader: Optional[AlternativesLoader] = None,
        alternatives_file: Optional[str] = None
    ):
        if alternatives_loader:
            self.loader = alternatives_loader
        elif alternatives_file and Path(alternatives_file).exists():
            self.loader = AlternativesLoader(alternatives_file)
        else:
            # Try to resolve default alternatives.yaml location
            default_path = Path(__file__).resolve().parent.parent / "tools" / "definitions" / "alternatives.yaml"
            if default_path.exists():
                self.loader = AlternativesLoader(str(default_path))
            else:
                self.loader = None

        self._tool_to_alternatives: Dict[str, Set[str]] = {}
        self._build_alternative_lookup()

    def _build_alternative_lookup(self):
        """Index all tool alternatives from the loader for fast O(1) queries."""
        if not self.loader:
            return

        for alt_id, group in self.loader.alternatives.items():
            all_path_tools = []
            for path in group.paths:
                tool_names = [t.get("tool_name") for t in path.tools if t.get("tool_name")]
                all_path_tools.append(tool_names)

            # Map each tool to tools from sibling paths in the same group
            for i, p1 in enumerate(all_path_tools):
                for tool in p1:
                    if tool not in self._tool_to_alternatives:
                        self._tool_to_alternatives[tool] = set()
                    for j, p2 in enumerate(all_path_tools):
                        if i != j:
                            self._tool_to_alternatives[tool].update(p2)

    def find_reroute(
        self,
        failed_tool: str,
        task_json: Dict[str, Any],
        blacklisted_tools: Set[str],
        executed_tools: List[str],
        available_tools: Optional[List[str]] = None
    ) -> RerouteCandidate:
        """Find a viable substitute tool that satisfies DAG dependencies.

        Args:
            failed_tool: Name of the tool that encountered a permanent failure.
            task_json: Full task specification (DAG, valid_solution_paths, tools).
            blacklisted_tools: Set of tools that are permanently corrupted/blocked.
            executed_tools: List of tools already executed in this episode.
            available_tools: Optional pool of allowed tools in the environment.
        """
        # 1. Strategy A: Check valid_paths / valid_solution_paths in task_json
        raw_paths = task_json.get("valid_paths") or task_json.get("valid_solution_paths") or []
        if raw_paths:
            candidate = self._reroute_from_solution_paths(
                failed_tool=failed_tool,
                valid_paths=raw_paths,
                blacklisted_tools=blacklisted_tools,
                executed_tools=executed_tools,
                task_json=task_json
            )
            if candidate and candidate.is_viable:
                return candidate
            # If valid solution paths were explicitly supplied, do not invent a
            # replacement from the general alternatives catalogue.
            return RerouteCandidate(
                failed_tool=failed_tool,
                candidate_tools=[],
                selected_tool=None,
                target_path=None,
                reason="No viable permitted alternative solution path exists.",
                is_viable=False,
            )
        # 1b. Strategy A.2: Check explicit task_json["alternative_tools"]
        task_alts = task_json.get("alternative_tools", [])
        if failed_tool in task_alts:
            viable_task_alts = [
                alt for alt in task_alts
                if alt != failed_tool and alt not in blacklisted_tools
            ]

            if available_tools:
                viable_task_alts = [
                    alt for alt in viable_task_alts if alt in available_tools
                ]

            best_tool = self._pick_dependency_satisfied_tool(
                candidates=viable_task_alts,
                task_json=task_json,
                executed_tools=executed_tools
            )

            if best_tool:
                return RerouteCandidate(
                    failed_tool=failed_tool,
                    candidate_tools=viable_task_alts,
                    selected_tool=best_tool,
                    reason=(
                        f"Selected unblocked alternative tool '{best_tool}' "
                        "with satisfied DAG prerequisites."
                    ),
                    is_viable=True
                )

        # 2. Strategy B: Query alternatives.yaml for known functional substitutes
        alt_tools = self._tool_to_alternatives.get(failed_tool, set())
        viable_alts = [
            t for t in sorted(alt_tools)
            if t not in blacklisted_tools and t != failed_tool
        ]

        if available_tools:
            viable_alts = [t for t in viable_alts if t in available_tools]

        if viable_alts:
            # Check DAG dependencies before selecting a substitute.
            best_tool = self._pick_dependency_satisfied_tool(
                candidates=viable_alts,
                task_json=task_json,
                executed_tools=executed_tools
            )
            if best_tool:
                return RerouteCandidate(
                    failed_tool=failed_tool,
                    candidate_tools=viable_alts,
                    selected_tool=best_tool,
                    reason=(
                        "Found substitute from alternatives catalog "
                        f"avoiding {len(blacklisted_tools)} blacklisted tools."
                    ),
                    is_viable=True
                )


        # 3. Strategy C: Do not treat arbitrary DAG nodes as substitutes.
        return RerouteCandidate(
            failed_tool=failed_tool,
            candidate_tools=[],
            selected_tool=None,
            reason="No safe alternative found among validated paths or explicit subsitutes.",
            is_viable=False
        )

    def _reroute_from_solution_paths(
        self,
        failed_tool: str,
        valid_paths: Any,
        blacklisted_tools: Set[str],
        executed_tools: List[str],
        task_json: Optional[Dict[str, Any]] = None
    ) -> Optional[RerouteCandidate]:
        """Find an alternative path whose next tool has satisfied prerequisites."""
        normalized_paths: List[List[str]] = []

        for path in valid_paths:
            if isinstance(path, dict):
                tools = path.get("tools")
                if not tools and "execution_trace" in path:
                    tools = [
                        step.get("tool_name")
                        for step in path.get("execution_trace", [])
                        if step.get("tool_name")
                    ]
                if tools:
                    normalized_paths.append(list(tools))
            elif isinstance(path, (list, tuple)):
                normalized_paths.append(list(path))

        # Exclude paths that contain any permanently blocked tool.
        candidate_paths = [
            path for path in normalized_paths
            if not any(tool in blacklisted_tools for tool in path)
        ]

        if not candidate_paths:
            return None

        # Prefer paths that preserve the longest successfully completed prefix.
        exec_set = set(executed_tools)

        def completed_prefix_length(path):
            count = 0

            for tool in path:
                if tool in exec_set:
                    count += 1
                else:
                    break

            return count

        candidate_paths.sort(
            key=lambda path: (
                -completed_prefix_length(path),
                len(path),
                tuple(path),
            )
        )

        # Select the first unfinished tool on the highest-ranked valid path.
        for chosen_path in candidate_paths:

            next_tool = None

            for tool in chosen_path:
                if tool in blacklisted_tools:
                    next_tool = None
                    break

                if tool not in exec_set:
                    next_tool = tool
                    break

            if next_tool is None:
                continue

            if task_json is not None:
                selected = self._pick_dependency_satisfied_tool(
                    candidates=[next_tool],
                    task_json=task_json,
                    executed_tools=executed_tools
                )

                if selected is None:
                    continue

            return RerouteCandidate(
                failed_tool=failed_tool,
                candidate_tools=[next_tool],
                selected_tool=next_tool,
                target_path=chosen_path,
                reason=(
                    "Selected the first unfinished tool on the highest-ranked "
                    "permitted alternative path."
                ),
                is_viable=True
            )

        return None

    
    def _pick_dependency_satisfied_tool(
        self,
        candidates: List[str],
        task_json: Dict[str, Any],
        executed_tools: List[str]
    ) -> Optional[str]:
        """Select a candidate whose known DAG prerequisites are satisfied.

        Backward-compatible helper: executed_tools is historical tool-name data,
        not proof that a specific node invocation succeeded.
        """
        dag = task_json.get("dag", {})
        nodes = dag.get("nodes", []) if isinstance(dag, dict) else []

        # Preserve the previous behavior for tasks that do not declare a DAG.
        if not nodes:
            for candidate in candidates:
                if candidate:
                    return candidate
            return None

        node_by_id: Dict[str, Dict[str, Any]] = {}
        nodes_by_tool: Dict[str, List[Dict[str, Any]]] = {}

        for node in nodes:
            if not isinstance(node, dict):
                continue

            node_id = node.get("node_id", node.get("id"))
            tool_name = node.get("tool_name", node.get("name"))

            if node_id is not None:
                node_by_id[str(node_id)] = node

            if tool_name:
                nodes_by_tool.setdefault(str(tool_name), []).append(node)

        executed = set(executed_tools)

        for candidate in candidates:
            matching_nodes = nodes_by_tool.get(candidate, [])

            # An explicitly declared DAG must contain the candidate.
            if not matching_nodes:
                continue

            for node in matching_nodes:
                dependencies = node.get(
                    "dependencies",
                    node.get("depends_on", [])
                ) or []

                if not isinstance(dependencies, list):
                    continue

                prerequisites_satisfied = True

                for dependency in dependencies:
                    dependency_key = str(dependency)

                    # Prefer an exact node-ID match.
                    dependency_node = node_by_id.get(dependency_key)

                    if dependency_node is not None:
                        prerequisite_tool = dependency_node.get(
                            "tool_name",
                            dependency_node.get("name")
                        )

                        # This compatibility helper has no node-level success
                        # state. It can only approximate completion by tool name.
                        if not prerequisite_tool or prerequisite_tool not in executed:
                            prerequisites_satisfied = False
                            break

                        continue

                    # Otherwise accept a tool-name dependency only if the DAG
                    # actually declares that tool name.
                    if dependency_key in nodes_by_tool:
                        if dependency_key not in executed:
                            prerequisites_satisfied = False
                            break
                        continue

                    # Unknown dependencies must never be treated as satisfied.
                    prerequisites_satisfied = False
                    break

                if prerequisites_satisfied:
                    return candidate

        return None
