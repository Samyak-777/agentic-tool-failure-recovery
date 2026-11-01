import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_code = '''
import json, glob

DEBUG_PATTERNS = (
    "exception", "stack trace", "nullpointerexception", "typeerror",
    "internal error", "error code 500", "syntax error", "sql:", "select *",
    "debug_level", "debug_log", "internalmappingservice", "failed to fetch upstream",
    "service temporarily unavailable", "unexpected token", "traceback (most recent call last)",
    "unknown-err"
)
CONTRADICTORY_PATTERNS = (
    "confirmed and cancelled", "confirmed_failed", "completed and cancelled",
    "confirmed without a reservation id", "rejected after successful",
    "identifier is missing"
)

def check_all_invariants(tool_name, node):
    if not isinstance(node, dict):
        return True, ""
    raw_str = json.dumps(node).lower()
    for pat in DEBUG_PATTERNS:
        if pat in raw_str:
            return False, f"Debug leak: {pat}"
    for pat in CONTRADICTORY_PATTERNS:
        if pat in raw_str:
            return False, f"Contradiction: {pat}"

    # Trade action contradiction
    action = node.get("action")
    if isinstance(action, str):
        if "buy" in tool_name.lower() and action.upper() == "SELL":
            return False, f"Action contradiction: buy tool returned SELL"
        if "sell" in tool_name.lower() and action.upper() == "BUY":
            return False, f"Action contradiction: sell tool returned BUY"

    # Trade quantity zero
    if "order" in tool_name.lower() or "trade" in tool_name.lower():
        qty = node.get("quantity")
        if isinstance(qty, (int, float)) and qty == 0:
            return False, f"Zero quantity order"

    # Empty essential IDs on booking / recommendation
    if "booking" in tool_name.lower() and "passenger_name" in node and node["passenger_name"] == "":
        return False, f"Empty passenger_name on booking"
    if "recommendation" in tool_name.lower() and "product_id" in node and node["product_id"] == "":
        return False, f"Empty product_id on recommendation"

    c_at = node.get("created_at")
    u_at = node.get("updated_at")
    if c_at and u_at and str(c_at) > str(u_at):
        return False, f"Temporal inversion: created_at > updated_at"

    s_date = node.get("start_date") or node.get("meeting_start_time")
    e_date = node.get("end_date") or node.get("meeting_end_time")
    if s_date and e_date and str(s_date) > str(e_date):
        return False, f"Date inversion: start > end"

    w_cnt = node.get("word_count")
    c_cnt = node.get("character_count")
    raw_c = node.get("raw_content")
    if isinstance(w_cnt, (int, float)) and w_cnt > 0:
        if isinstance(c_cnt, (int, float)) and c_cnt == 0:
            return False, f"word_count={w_cnt} but character_count=0"
        if raw_c is not None and isinstance(raw_c, str) and len(raw_c.strip()) == 0:
            return False, f"word_count={w_cnt} but raw_content empty"

    for k, v in node.items():
        if isinstance(v, (int, float)) and v < 0:
            if not any(term in k.lower() for term in ["temp", "lat", "lon", "change", "pnl"]):
                return False, f"Negative bound on {k}: {v}"
        elif isinstance(v, dict):
            ok, r = check_all_invariants(tool_name, v)
            if not ok: return ok, r
        elif isinstance(v, list):
            for it in v:
                if isinstance(it, dict):
                    ok, r = check_all_invariants(tool_name, it)
                    if not ok: return ok, r
    return True, ""

def get_perturbed_steps(d):
    steps = []
    for s in d.get("execution_trace", []):
        if s.get("is_perturbed"):
            steps.append(s)
    for vp in d.get("valid_paths", []):
        for s in vp.get("execution_trace", []):
            if s.get("is_perturbed"):
                steps.append(s)
    return steps

def get_all_p0_steps(d):
    steps = []
    for s in d.get("execution_trace", []):
        steps.append(s)
    for vp in d.get("valid_paths", []):
        for s in vp.get("execution_trace", []):
            steps.append(s)
    return steps

# Check FP on clean P0
fp_count = 0
total_p0 = 0
for cat in ["c1", "c2", "c3", "c4"]:
    for f in glob.glob(f"/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/data/perturbed_tasks/{cat}/*_P0.json"):
        total_p0 += 1
        with open(f) as fp:
            d = json.load(fp)
        for step in get_all_p0_steps(d):
            out = step.get("output", {})
            tname = step.get("tool_name", "")
            ok, r = check_all_invariants(tname, out)
            if not ok:
                fp_count += 1
                print(f"FP on {f} ({tname}): {r}")

print(f"Total P0 tasks: {total_p0}, False Positives: {fp_count}")

# Check detection on P3 and P4
for mode in ["P3", "P4"]:
    detected = 0
    total = 0
    for cat in ["c1", "c2", "c3", "c4"]:
        for f in glob.glob(f"/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/data/perturbed_tasks/{cat}/*_{mode}.json"):
            total += 1
            with open(f) as fp:
                d = json.load(fp)
            pert_steps = get_perturbed_steps(d)
            if not pert_steps:
                continue
            is_det = False
            for step in pert_steps:
                ok, r = check_all_invariants(step.get("tool_name", ""), step.get("output", {}))
                if not ok:
                    is_det = True
                    break
            if is_det:
                detected += 1

    print(f"Total {mode} tasks: {total}, Detected: {detected} ({detected/total*100:.1f}%)")
'''

stdin, stdout, stderr = ssh.exec_command(f'python3 -c \'{remote_code}\'')
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
