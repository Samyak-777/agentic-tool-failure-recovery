from typing import Any, Dict, List, Optional


class ExecutionController:
    """Selects the next tool from paths exposed in the runtime task payload."""

    def __init__(self, task_json: Dict[str, Any]):
        self.task_json = task_json or {}

        task_definition = self.task_json.get("task_definition") or {}

        raw_paths = (
            self.task_json.get("valid_paths")
            or task_definition.get("valid_paths")
            or []
        )

        self.valid_paths: List[List[str]] = []

        for path in raw_paths:
            if isinstance(path, dict):
                tools = path.get("tools", [])
            elif isinstance(path, list):
                tools = path
            else:
                continue

            if tools and all(isinstance(t, str) for t in tools):
                self.valid_paths.append(tools)

        self.execution_trace = (
            self.task_json.get("execution_trace")
            or task_definition.get("execution_trace")
            or []
        )

        if not self.valid_paths and self.execution_trace:
            trace_tools = []

            for step in self.execution_trace:
                if isinstance(step, dict):
                    name = step.get("tool_name")
                elif isinstance(step, str):
                    name = step
                else:
                    name = None

                if name:
                    trace_tools.append(name)

            if trace_tools:
                self.valid_paths.append(trace_tools)

        if not self.valid_paths:
            dag = self.task_json.get("dag") or task_definition.get("dag") or {}
            nodes = dag.get("nodes", []) if isinstance(dag, dict) else []
            dag_tools = [n.get("tool_name") for n in nodes if isinstance(n, dict) and n.get("tool_name")]
            if dag_tools:
                self.valid_paths.append(dag_tools)

    def get_next_tool(
        self,
        executed_tools: List[str],
        active_path: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Return the next tool on a path consistent with execution history."""

        executed = list(executed_tools)
        paths = [active_path] if active_path else self.valid_paths

        for path in paths:
            if not path:
                continue

            # Executed tools must appear in the same relative order in this path.
            positions = []
            last_position = -1
            consistent = True

            for tool in executed:
                try:
                    position = path.index(tool, last_position + 1)
                except ValueError:
                    consistent = False
                    break

                positions.append(position)
                last_position = position

            if not consistent:
                continue

            # Find the first tool after the last executed tool.
            start = last_position + 1 if positions else 0

            for tool in path[start:]:
                if tool not in executed:
                    return tool

        return None
