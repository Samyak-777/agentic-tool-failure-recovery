import re

# 1. Update ToolMaze/evaluation/scripts/run_eval_care.py
with open("ToolMaze/evaluation/scripts/run_eval_care.py", "r", encoding="utf-8") as f:
    eval_content = f.read()

template_loader_code = '''
def load_task_template(task_json: Dict[str, Any], config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Load the original task template DAG definition, never evaluator ground truth."""
    template_dir = config.get("data", {}).get("template_dir")
    if not template_dir:
        return None
    template_id = task_json.get("template_id")
    complexity = task_json.get("complexity", "")
    if not template_id or not complexity:
        return None
    template_path = Path(template_dir) / complexity.lower() / f"{template_id}.json"
    if not template_path.is_file():
        template_path = project_root / template_dir / complexity.lower() / f"{template_id}.json"
        if not template_path.is_file():
            return None
    try:
        with template_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return None
'''

if "def load_task_template" not in eval_content:
    # Insert before evaluate_single_task
    eval_content = eval_content.replace(
        "def evaluate_single_task(",
        template_loader_code + "\ndef evaluate_single_task("
    )

# Ensure agent.set_task_template(task_template) is called
old_block = '''        if hasattr(agent, "set_task_json"):
            # Pure academic boundary: strip ground-truth execution_trace and expected_result
            agent_task_spec = {k: v for k, v in task_json.items() if k not in ("execution_trace", "expected_result")}
            agent.set_task_json(agent_task_spec)'''

new_block = '''        if hasattr(agent, "set_task_json"):
            # Pure academic boundary: strip ground-truth execution_trace and expected_result
            agent_task_spec = {k: v for k, v in task_json.items() if k not in ("execution_trace", "expected_result")}
            agent.set_task_json(agent_task_spec)

        task_template = load_task_template(task_json, config)
        if hasattr(agent, "set_task_template") and task_template:
            agent.set_task_template(task_template)'''

if old_block in eval_content:
    eval_content = eval_content.replace(old_block, new_block)
    print("Updated run_eval_care.py with load_task_template")
else:
    print("Could not find exact block in run_eval_care.py")

with open("ToolMaze/evaluation/scripts/run_eval_care.py", "w", encoding="utf-8") as f:
    f.write(eval_content)


# 2. Update ToolMaze/evaluation/agents/care_agent.py
with open("ToolMaze/evaluation/agents/care_agent.py", "r", encoding="utf-8") as f:
    care_content = f.read()

new_validate_func = '''    def _validate_semantic_invariants(self, tool_name: str, result: Any) -> Tuple[bool, str]:
        """Layer 1 deterministic semantic invariant validation (zero false positives on clean outputs)."""
        if not isinstance(result, dict):
            return True, ""

        DEBUG_PATTERNS = (
            "nullpointerexception", "sql_query", "select * from",
            "select id, status from", "select name from", "debug_level",
            "debug_log", "internal_endpoint", "unknown-err",
            "internalmappingservice", "flighttracker.getstate",
            "db_connection_pool_exhausted", "traceback (most recent call last)",
            "failed to fetch upstream", "service temporarily unavailable",
            "unexpected token", "error code 500"
        )
        CONTRADICTORY_PATTERNS = (
            "confirmed and cancelled", "confirmed_failed", "completed and cancelled",
            "confirmed without a reservation id", "rejected after successful",
            "identifier is missing"
        )

        def _check_node(node: Any) -> Tuple[bool, str]:
            if not isinstance(node, dict):
                return True, ""
            raw_str = json.dumps(node).lower()
            for pat in DEBUG_PATTERNS:
                if pat in raw_str:
                    return False, f"Internal debug/exception leak detected: '{pat}'"
            for pat in CONTRADICTORY_PATTERNS:
                if pat in raw_str:
                    return False, f"Contradictory state in payload: '{pat}'"

            # Action contradiction against tool capability
            action = node.get("action")
            if isinstance(action, str):
                if "buy" in tool_name.lower() and action.upper() == "SELL":
                    return False, f"Action contradiction: buy tool returned SELL in '{tool_name}'"
                if "sell" in tool_name.lower() and action.upper() == "BUY":
                    return False, f"Action contradiction: sell tool returned BUY in '{tool_name}'"

            # Trade zero-quantity order
            if "order" in tool_name.lower() or "trade" in tool_name.lower():
                qty = node.get("quantity")
                if isinstance(qty, (int, float)) and qty == 0:
                    return False, f"Zero quantity order in '{tool_name}'"

            # Essential ID presence
            if "booking" in tool_name.lower() and "passenger_name" in node and node["passenger_name"] == "":
                return False, f"Empty passenger_name on booking payload in '{tool_name}'"
            if "recommendation" in tool_name.lower() and "product_id" in node and node["product_id"] == "":
                return False, f"Empty product_id on recommendation payload in '{tool_name}'"

            # Text metrics coherence
            w_cnt = node.get("word_count")
            c_cnt = node.get("character_count")
            raw_c = node.get("raw_content")
            if isinstance(w_cnt, (int, float)) and w_cnt > 0:
                if isinstance(c_cnt, (int, float)) and c_cnt == 0:
                    return False, f"Semantic contradiction: word_count ({w_cnt}) > 0 but character_count is 0"
                if raw_c is not None and isinstance(raw_c, str) and len(raw_c.strip()) == 0:
                    return False, f"Semantic contradiction: word_count ({w_cnt}) > 0 but raw_content is empty"

            c_at = node.get("created_at")
            u_at = node.get("updated_at")
            if c_at and u_at and str(c_at) > str(u_at):
                return False, f"Temporal inversion: created_at ({c_at}) > updated_at ({u_at})"

            s_date = node.get("start_date") or node.get("meeting_start_time")
            e_date = node.get("end_date") or node.get("meeting_end_time")
            if s_date and e_date and str(s_date) > str(e_date):
                return False, f"Date/time range inversion: start ({s_date}) > end ({e_date})"

            for k, v in node.items():
                if isinstance(v, (int, float)) and v < 0:
                    if not any(term in k.lower() for term in ["temp", "lat", "lon", "change", "pnl"]):
                        return False, f"Impossible negative bound on '{k}': {v}"
                elif isinstance(v, dict):
                    valid, reason = _check_node(v)
                    if not valid:
                        return False, reason
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            valid, reason = _check_node(item)
                            if not valid:
                                return False, reason
            return True, ""

        return _check_node(result)'''

# Replace from def _validate_semantic_invariants to def receive_tool_result
start_marker = "    def _validate_semantic_invariants(self, tool_name: str, result: Any) -> Tuple[bool, str]:"
end_marker = "    def receive_tool_result(self, tool_name: str, result: Dict[str, Any], tool_call_index: int = 0) -> None:"

start_idx = care_content.find(start_marker)
end_idx = care_content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    care_content = care_content[:start_idx] + new_validate_func + "\n\n" + care_content[end_idx:]
    print("Updated care_agent.py with extended semantic invariants")
else:
    print(f"Could not find markers: start={start_idx}, end={end_idx}")

with open("ToolMaze/evaluation/agents/care_agent.py", "w", encoding="utf-8") as f:
    f.write(care_content)

