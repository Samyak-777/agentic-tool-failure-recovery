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

        # Prefer paths that share the most tools already executed.
        exec_set = set(executed_tools)
        candidate_paths.sort(
            key=lambda path: len(set(path).intersection(exec_set)),
            reverse=True
        )

        # Check each path for a next tool whose prerequisites are satisfied.
        for chosen_path in candidate_paths:
            for tool in chosen_path:
                if tool in exec_set or tool in blacklisted_tools:
                    continue

                if task_json is not None:
                    selected = self._pick_dependency_satisfied_tool(
                        candidates=[tool],
                        task_json=task_json,
                        executed_tools=executed_tools
                    )
                    if selected is None:
                        break

                return RerouteCandidate(
                    failed_tool=failed_tool,
                    candidate_tools=[tool],
                    selected_tool=tool,
                    target_path=chosen_path,
                    reason=(
                        "Switched to an alternative valid solution path; "
                        f"selected '{tool}' after checking its prerequisites."
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
        """Select a candidate whose upstream DAG prerequisites are satisfied."""
        dag = task_json.get("dag", {})
        nodes = dag.get("nodes", [])
        dep_map: Dict[str, List[str]] = {}

        for node in nodes:
            name = node.get("tool_name")
            deps = node.get("dependencies", [])
            if name:
                dep_map[name] = deps

        exec_set = set(executed_tools)
        dag_declared = bool(nodes)

        for candidate in candidates:
            # With an explicit DAG, don't assume an unlisted tool is ready.
            # Without a DAG, preserve legacy behavior.
            if dag_declared and candidate not in dep_map:
                continue

            prerequisites = dep_map.get(candidate, [])
            if all(prerequisite in exec_set for prerequisite in prerequisites):
                return candidate

        return None
