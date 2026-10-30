
"""
ToolMaze/dag_rerouting/path_selector.py

Layer 4: DAG-Aware Alternative Path Selection.

Selects a complete, executable alternative path after a tool failure.
A candidate is accepted only when:
- Its path contains no blacklisted tools.
- Its tools are allowed by the available tool set, when supplied.
- Its already-executed prefix is consistent with execution order.
- Its next tool has the inputs required by its parameter mappings.
- It does not reuse outputs from failed or invalid executions.

Path selection does not claim that the overall task goal is achieved.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from tools.alternatives_loader import AlternativesLoader
except ImportError:
    from ..tools.alternatives_loader import AlternativesLoader


@dataclass
class RerouteCandidate:
    """Outcome of an alternative-path search."""

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
    """
    Selects executable alternative paths.

    Important:
    - Tool execution history is not the same as data availability.
    - A tool is considered reusable only if its execution was valid.
    - Exact predecessor tool names are not required when the required
      data is already available from an equivalent successful tool.
    """

    def __init__(
        self,
        alternatives_loader: Optional[AlternativesLoader] = None,
        alternatives_file: Optional[str] = None,
    ):
        if alternatives_loader is not None:
            self.loader = alternatives_loader
        else:
            if alternatives_file:
                path = Path(alternatives_file)
            else:
                path = (
                    Path(__file__).resolve().parent.parent
                    / "tools"
                    / "definitions"
                    / "alternatives.yaml"
                )

            self.loader = (
                AlternativesLoader(str(path))
                if path.exists()
                else None
            )

        # Retained for compatibility with existing code/tests.
        self._tool_to_alternatives: Dict[str, Set[str]] = {}
        self._build_alternative_lookup()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_reroute(
        self,
        failed_tool: str,
        task_json: Dict[str, Any],
        blacklisted_tools: Optional[Set[str]] = None,
        executed_tools: Optional[List[str]] = None,
        available_tools: Optional[List[str]] = None,
        available_outputs: Optional[Dict[str, Any]] = None,
        available_data: Optional[Dict[str, Any]] = None,
    ) -> RerouteCandidate:
        """
        Find the best executable alternative path.

        Args:
            failed_tool:
                Tool that failed permanently.

            task_json:
                Task specification containing valid_paths,
                valid_solution_paths, DAG and/or alternative_tools.

            blacklisted_tools:
                Tools that must never be executed again.

            executed_tools:
                Tools that have been attempted in this episode.

            available_tools:
                Allowed tools in the current environment.
                None means no additional allow-list restriction.
                An empty list means no tools are allowed.

            available_outputs:
                Actual outputs from successful tool executions.
                Keys should identify the producing tool or output name.

            available_data:
                Task inputs and other currently available values.

        Returns:
            RerouteCandidate. A viable result contains the selected
            next tool and the complete target path.
        """
        blacklisted = set(blacklisted_tools or set())
        executed = list(executed_tools or [])
        outputs_were_supplied = available_outputs is not None
        outputs = available_outputs if outputs_were_supplied else None
        data = available_data or {}

        if not isinstance(task_json, dict):
            return self._failure(
                failed_tool,
                "Invalid task specification: expected a dictionary.",
            )

        # A caller may pass an empty available_tools list intentionally.
        allowed = (
            set(available_tools)
            if available_tools is not None
            else None
        )

        if failed_tool not in blacklisted:
            # Do not silently treat an arbitrary failed tool as blocked.
            blacklisted.add(failed_tool)

        paths = self._collect_candidate_paths(task_json, failed_tool)

        if not paths:
            return self._failure(
                failed_tool,
                "No explicitly defined alternative path contains the failed tool.",
            )

        evaluated: List[Tuple[Tuple[int, int, int], Dict[str, Any]]] = []

        for path in paths:
            steps = path["steps"]
            names = [step["tool_name"] for step in steps]

            if not names:
                continue

            if any(name in blacklisted for name in names):
                continue

            if allowed is not None and any(name not in allowed for name in names):
                continue

                        # Find the first step that has not already completed.
            # This works for both the original path and sibling
            # alternative paths that do not contain the failed tool.
            next_index = self._first_uncompleted_index(
                names,
                executed,
                outputs,
            )

            # Every step before the next step must have been completed
            # in the declared path order.
            prefix = names[:next_index]

            if not self._prefix_is_satisfied(prefix, executed):
                continue

            if next_index >= len(names):
                continue

            next_step = steps[next_index]

            # Do not select a tool if its required mapped inputs
            # cannot be resolved from task inputs or successful outputs.
            if not self._parameters_are_resolvable(
                next_step.get("params", {}),
                data,
                outputs,
            ):
                continue

            # Rank by:
            # 1. Number of reusable successful steps.
            # 2. Number of already completed steps in order.
            # 3. Shorter remaining path.
            reusable_count = sum(
                1 for name in names[:next_index] if name in executed
            )
            completed_prefix = next_index
            remaining_length = len(names) - next_index

            score = (
                reusable_count,
                completed_prefix,
                -remaining_length,
            )

            evaluated.append((score, path))

        if not evaluated:
            return self._failure(
                failed_tool,
                (
                    "No alternative path is currently executable. "
                    "Candidates were blocked, unavailable, had an "
                    "inconsistent execution prefix, or required "
                    "unavailable input data."
                ),
            )

        # Stable deterministic selection: highest score first,
        # then original candidate order.
        evaluated.sort(key=lambda item: item[0], reverse=True)
        selected_path = evaluated[0][1]

        steps = selected_path["steps"]
        names = [step["tool_name"] for step in steps]

        next_index = self._first_uncompleted_index(
            names,
            executed,
            outputs,
        )

        selected_tool = names[next_index]

        return RerouteCandidate(
            failed_tool=failed_tool,
            candidate_tools=[
                name
                for name in names
                if name != failed_tool
            ],
            selected_tool=selected_tool,
            target_path=names,
            reason=(
                f"Selected executable alternative path "
                f"'{selected_path['path_id']}'. "
                f"Next tool: '{selected_tool}'."
            ),
            is_viable=True,
        )

    # ------------------------------------------------------------------
    # Candidate path discovery
    # ------------------------------------------------------------------

    def _collect_candidate_paths(
        self,
        task_json: Dict[str, Any],
        failed_tool: str,
    ) -> List[Dict[str, Any]]:
        """
        Collect only explicitly declared solution/alternative paths.

        Arbitrary DAG nodes are deliberately not treated as substitutes.
        """
        collected: List[Dict[str, Any]] = []

        raw_paths = (
            task_json.get("valid_paths")
            or task_json.get("valid_solution_paths")
            or []
        )
        normalized_paths = [
            self._normalize_path(raw_path, path_id=f"task_path_{index}")
            for index, raw_path in enumerate(raw_paths)
        ]
        normalized_paths = [path for path in normalized_paths if path]

        # These paths are alternative complete solutions. If at least
        # one contains the failed tool, evaluate all sibling paths.
        if any(
            failed_tool in [step["tool_name"] for step in path["steps"]]
            for path in normalized_paths
        ):
            collected.extend(normalized_paths)


        # Explicit task-level alternative path definitions.
        explicit_alternatives = task_json.get("alternative_paths", [])

        normalized_alternatives = [
            self._normalize_path(
                raw_path,
                path_id=f"explicit_alt_{index}",
            )
            for index, raw_path in enumerate(explicit_alternatives)
        ]

        normalized_alternatives = [
            path for path in normalized_alternatives if path
        ]

        if any(
            failed_tool in [step["tool_name"] for step in path["steps"]]
            for path in normalized_alternatives
        ):
            collected.extend(normalized_alternatives)

        # Alternatives catalog. Keep complete paths, including params.
        if self.loader is not None:
            for alt_id, group in self.loader.alternatives.items():
                normalized_group_paths = []

                for path in group.paths:
                    normalized = self._normalize_path(
                        {
                            "path_id": path.path_id,
                            "tools": path.tools,
                        },
                        path_id=f"{alt_id}:{path.path_id}",
                    )

                    if normalized:
                        normalized_group_paths.append(normalized)

                group_contains_failed_tool = any(
                    failed_tool in [
                        step["tool_name"] for step in path["steps"]
                    ]
                    for path in normalized_group_paths
                )

                if group_contains_failed_tool:
                    collected.extend(normalized_group_paths)

        # Deduplicate identical paths without losing their order.
        unique: Dict[Tuple[str, ...], Dict[str, Any]] = {}

        for path in collected:
            key = tuple(step["tool_name"] for step in path["steps"])
            unique.setdefault(key, path)

        return list(unique.values())

    @staticmethod
    def _normalize_path(
        raw_path: Any,
        path_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Normalize list- and dictionary-based path formats."""
        if isinstance(raw_path, dict):
            raw_steps = (
                raw_path.get("tools")
                or raw_path.get("steps")
                or raw_path.get("execution_trace")
            )
            actual_path_id = str(raw_path.get("path_id", path_id))
        elif isinstance(raw_path, (list, tuple)):
            raw_steps = raw_path
            actual_path_id = path_id
        else:
            return None

        if not isinstance(raw_steps, (list, tuple)):
            return None

        steps: List[Dict[str, Any]] = []

        for item in raw_steps:
            if isinstance(item, str):
                tool_name = item
                params = {}
            elif isinstance(item, dict):
                tool_name = item.get("tool_name")
                params = item.get("params", {})
            else:
                return None

            if not isinstance(tool_name, str) or not tool_name.strip():
                return None

            if not isinstance(params, dict):
                return None

            steps.append({
                "tool_name": tool_name.strip(),
                "params": params,
            })

        if not steps:
            return None

        return {
            "path_id": actual_path_id,
            "steps": steps,
        }

    # ------------------------------------------------------------------
    # Execution-state validation
    # ------------------------------------------------------------------

    @staticmethod
    def _prefix_is_satisfied(
        prefix: List[str],
        executed_tools: List[str],
    ) -> bool:
        """
        Verify that the path prefix is consistent with execution order.

        This does not require exact predecessor identity for data
        dependencies; it only checks whether the declared path's
        earlier steps have already been attempted successfully.
        """
        if not prefix:
            return True

        position = 0

        for name in executed_tools:
            if position < len(prefix) and name == prefix[position]:
                position += 1

        return position == len(prefix)

    @staticmethod
    def _first_uncompleted_index(
        path: List[str],
        executed_tools: List[str],
        available_outputs: Optional[Dict[str, Any]],
    ) -> int:
        """
        Find the first path step not already completed successfully.

        An executed tool is reusable only when an output entry exists.
        CAREAgent will supply the actual successful outputs.
        """
        # Older callers only supplied executed_tools. Preserve that
        # contract when no output dictionary was provided.
        # When outputs are supplied, require explicit success evidence.
        if available_outputs is None:
            successful_tools = set(executed_tools)
        else:
            successful_tools = set(available_outputs.keys())
            successful_tools.update(
                available_outputs.get("_successful_tools", [])
                if isinstance(
                    available_outputs.get("_successful_tools"), list
                )
                else []
            )

        index = 0

        while index < len(path):
            name = path[index]

            if name not in executed_tools or name not in successful_tools:
                break

            index += 1

        return index

    # ------------------------------------------------------------------
    # Parameter/data validation
    # ------------------------------------------------------------------

    @classmethod
    def _parameters_are_resolvable(
        cls,
        params: Dict[str, Any],
        available_data: Dict[str, Any],
        available_outputs: Dict[str, Any],
    ) -> bool:
        """
        Check whether every parameter mapping can be resolved.

        Supported mappings:
        - "city": direct task input reference.
        - "'USD'": literal string constant.
        - "$tool_name.field": reference to a previous tool output.
        - "$.field": reference to task input data.

        Unknown or missing references are rejected instead of being
        silently passed to a replacement tool.
        """
        for value in params.values():
            if not isinstance(value, str):
                continue

            if value.startswith("'") and value.endswith("'"):
                continue

            if value.startswith('"') and value.endswith('"'):
                continue

            if value.startswith("$"):
                if not cls._resolve_reference(
                    value,
                    available_data,
                    available_outputs,
                )[0]:
                    return False
                continue

            # Plain strings in the YAML mapping represent input keys.
            if value not in available_data:
                return False

        return True

    @staticmethod
    def _resolve_reference(
        reference: str,
        available_data: Dict[str, Any],
        available_outputs: Dict[str, Any],
    ) -> Tuple[bool, Any]:
        """Resolve a supported task-data or tool-output reference."""
        ref = reference[1:]

        # "$.field" refers to task input data.
        if ref.startswith("."):
            current: Any = available_data
            parts = ref[1:].split(".")
        else:
            parts = ref.split(".")
            if not parts:
                return False, None

            producer = parts.pop(0)

            if producer not in available_outputs:
                return False, None

            current = available_outputs[producer]

        try:
            for part in parts:
                if isinstance(current, dict):
                    current = current[part]
                elif isinstance(current, (list, tuple)) and part.isdigit():
                    current = current[int(part)]
                else:
                    return False, None
        except (KeyError, IndexError, TypeError):
            return False, None

        return True, current

    # ------------------------------------------------------------------
    # Alternatives catalog compatibility
    # ------------------------------------------------------------------

    def _build_alternative_lookup(self) -> None:
        """
        Build a compatibility index.

        The index is not used to select individual tools. Complete
        paths are evaluated instead.
        """
        self._tool_to_alternatives = {}

        if self.loader is None:
            return

        for group in self.loader.alternatives.values():
            paths = []

            for path in group.paths:
                names = [
                    step.get("tool_name")
                    for step in path.tools
                    if isinstance(step, dict) and step.get("tool_name")
                ]
                paths.append(names)

            for index, path in enumerate(paths):
                for tool in path:
                    alternatives = self._tool_to_alternatives.setdefault(
                        tool, set()
                    )

                    for other_index, other_path in enumerate(paths):
                        if other_index != index:
                            alternatives.update(other_path)

    # ------------------------------------------------------------------
    # Result helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _failure(
        failed_tool: str,
        reason: str,
    ) -> RerouteCandidate:
        return RerouteCandidate(
            failed_tool=failed_tool,
            candidate_tools=[],
            selected_tool=None,
            target_path=None,
            reason=reason,
            is_viable=False,
        )
