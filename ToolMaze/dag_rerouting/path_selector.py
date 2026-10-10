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
        # 1. Strategy A: Check valid_solution_paths in task_json (Ground Truth DAG paths)
        valid_paths = task_json.get("valid_solution_paths", [])
        if valid_paths:
            candidate = self._reroute_from_solution_paths(
                failed_tool=failed_tool,
                valid_paths=valid_paths,
                blacklisted_tools=blacklisted_tools,
                executed_tools=executed_tools
            )
            if candidate and candidate.is_viable:
                return candidate

        # 2. Strategy B: Query alternatives.yaml for known functional substitutes
        alt_tools = self._tool_to_alternatives.get(failed_tool, set())
        viable_alts = [
            t for t in sorted(alt_tools)
            if t not in blacklisted_tools and t != failed_tool
        ]

        if available_tools:
            viable_alts = [t for t in viable_alts if t in available_tools]

        if viable_alts:
            # Check DAG dependencies if DAG nodes exist in task_json
            best_tool = self._pick_dependency_satisfied_tool(
                candidates=viable_alts,
                task_json=task_json,
                executed_tools=executed_tools
            )
            return RerouteCandidate(
                failed_tool=failed_tool,
                candidate_tools=viable_alts,
                selected_tool=best_tool or viable_alts[0],
                reason=f"Found substitute from alternatives catalog avoiding {len(blacklisted_tools)} blacklisted tools.",
                is_viable=True
            )

        # 3. Strategy C: Check DAG node alternatives from task_json["dag"]
        dag = task_json.get("dag", {})
        nodes = dag.get("nodes", [])
        alt_nodes = [
            n.get("tool_name") for n in nodes
            if n.get("tool_name") and n.get("tool_name") != failed_tool
            and n.get("tool_name") not in blacklisted_tools
            and n.get("tool_name") not in executed_tools
        ]
        if alt_nodes:
            best_tool = self._pick_dependency_satisfied_tool(
                candidates=alt_nodes,
                task_json=task_json,
                executed_tools=executed_tools
            )
            if best_tool:
                return RerouteCandidate(
                    failed_tool=failed_tool,
                    candidate_tools=alt_nodes,
                    selected_tool=best_tool,
                    reason=f"Selected unexecuted DAG node '{best_tool}' with satisfied prerequisites.",
                    is_viable=True
                )

        return RerouteCandidate(
            failed_tool=failed_tool,
            candidate_tools=[],
            selected_tool=None,
            reason=f"No viable alternative tools available in DAG. All candidates are blacklisted or missing.",
            is_viable=False
        )

    def _reroute_from_solution_paths(
        self,
        failed_tool: str,
        valid_paths: List[List[str]],
        blacklisted_tools: Set[str],
        executed_tools: List[str]
    ) -> Optional[RerouteCandidate]:
        """Find an alternative pre-computed solution path that avoids all blacklisted tools."""
        candidate_paths = []
        for path in valid_paths:
            # Check if this path contains ANY blacklisted tool
            if any(tool in blacklisted_tools for tool in path):
                continue
            candidate_paths.append(path)

        if not candidate_paths:
            return None

        # Sort candidate paths by similarity to current execution progress
        # Prefer paths that share the most tools already executed
        exec_set = set(executed_tools)
        candidate_paths.sort(
            key=lambda p: len(set(p).intersection(exec_set)),
            reverse=True
        )

        chosen_path = candidate_paths[0]
        # Find next tool in the chosen path that has not been executed yet
        for tool in chosen_path:
            if tool not in executed_tools and tool not in blacklisted_tools:
                return RerouteCandidate(
                    failed_tool=failed_tool,
                    candidate_tools=[tool],
                    selected_tool=tool,
                    target_path=chosen_path,
                    reason=f"Switched to alternative valid solution path avoiding blacklisted tool '{failed_tool}'.",
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
        for n in nodes:
            name = n.get("tool_name")
            deps = n.get("dependencies", [])
            if name:
                dep_map[name] = deps

        exec_set = set(executed_tools)
        for cand in candidates:
            prereqs = dep_map.get(cand, [])
            if all(p in exec_set for p in prereqs):
                return cand

        # If none have 100% satisfied prerequisites or no deps declared, return first candidate
        return candidates[0] if candidates else None
