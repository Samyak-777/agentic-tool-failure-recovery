from typing import Any, Dict, List, Optional, Set


class PrerequisiteChecker:
    """
    Checks whether a requested tool is eligible for execution
    according to the task's declared valid execution paths.
    Supports C2-C4 valid_paths, valid_solution_paths, and C1 execution_trace.
    """

    def __init__(self, task_json: Dict[str, Any]):
        self.task_json = task_json if isinstance(task_json, dict) else {}
        task_def = self.task_json.get("task_definition", {})
        if not isinstance(task_def, dict):
            task_def = {}

        raw_paths = self.task_json.get("valid_paths") or task_def.get("valid_paths")

        if not raw_paths:
            sol_paths = self.task_json.get("valid_solution_paths") or task_def.get("valid_solution_paths")
            if isinstance(sol_paths, list):
                raw_paths = []
                for idx, p in enumerate(sol_paths):
                    if isinstance(p, list) and all(isinstance(t, str) and t for t in p):
                        raw_paths.append({"path_id": f"path_{idx}", "tools": p})
                    elif isinstance(p, dict) and "tools" in p:
                        raw_paths.append(p)

        if not raw_paths:
            trace = self.task_json.get("execution_trace") or task_def.get("execution_trace")
            if isinstance(trace, list):
                tools = []
                for step in trace:
                    if isinstance(step, dict) and step.get("tool_name"):
                        tools.append(str(step["tool_name"]))
                    elif isinstance(step, str) and step:
                        tools.append(step)
                if tools:
                    raw_paths = [{"path_id": "path_0", "tools": tools}]

        # Ignore malformed path entries.
        self.valid_paths = [
            path
            for path in raw_paths
            if isinstance(path, dict)
            and isinstance(path.get("tools"), list)
            and all(isinstance(tool, str) and tool for tool in path["tools"])
        ] if isinstance(raw_paths, list) else []

    def check(
        self,
        requested_tool: str,
        executed_tools: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:

        executed = set(executed_tools or set())

        if not self.valid_paths:
            return {
                "allowed": True,
                "missing_prerequisites": [],
                "reason": "No valid declared paths",
            }

        eligible_paths = []

        for path in self.valid_paths:
            tools = path["tools"]

            if requested_tool not in tools:
                continue

            index = tools.index(requested_tool)
            prerequisites = tools[:index]

            if all(tool in executed for tool in prerequisites):
                eligible_paths.append(path)

        if eligible_paths:
            return {
                "allowed": True,
                "missing_prerequisites": [],
                "reason": "A declared path permits this tool",
            }

        candidate_paths = [
            path for path in self.valid_paths
            if requested_tool in path["tools"]
        ]

        if not candidate_paths:
            return {
                "allowed": False,
                "missing_prerequisites": [],
                "reason": "Requested tool is not present in any declared path",
            }

        best_missing = None

        for path in candidate_paths:
            tools = path["tools"]
            index = tools.index(requested_tool)

            missing = [
                tool for tool in tools[:index]
                if tool not in executed
            ]

            if best_missing is None or len(missing) < len(best_missing):
                best_missing = missing

        return {
            "allowed": False,
            "missing_prerequisites": best_missing or [],
            "reason": "Mandatory preceding tools have not executed",
        }
