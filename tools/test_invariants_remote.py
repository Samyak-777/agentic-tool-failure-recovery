import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_code = '''
import json, glob

def check_text_invariant(node):
    if not isinstance(node, dict):
        return True, ""
    w_cnt = node.get("word_count")
    c_cnt = node.get("character_count")
    raw_c = node.get("raw_content")
    if isinstance(w_cnt, (int, float)) and w_cnt > 0:
        if isinstance(c_cnt, (int, float)) and c_cnt == 0:
            return False, f"word_count={w_cnt} but character_count=0"
        if raw_c is not None and isinstance(raw_c, str) and len(raw_c.strip()) == 0:
            return False, f"word_count={w_cnt} but raw_content empty"
    for k, v in node.items():
        if isinstance(v, dict):
            ok, r = check_text_invariant(v)
            if not ok: return ok, r
        elif isinstance(v, list):
            for it in v:
                if isinstance(it, dict):
                    ok, r = check_text_invariant(it)
                    if not ok: return ok, r
    return True, ""

fp_count = 0
total_p0 = 0
for cat in ["c1", "c2", "c3", "c4"]:
    for f in glob.glob(f"/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/data/perturbed_tasks/{cat}/*_P0.json"):
        total_p0 += 1
        with open(f) as fp:
            d = json.load(fp)
        for step in d.get("execution_trace", []):
            out = step.get("output", {})
            ok, r = check_text_invariant(out)
            if not ok:
                fp_count += 1
                print(f"FP on {f}: {r}")

print(f"Total P0 tasks: {total_p0}, False Positives: {fp_count}")

# Check on P3 and P4 for detection:
detected_p3 = 0
total_p3 = 0
for cat in ["c1", "c2", "c3", "c4"]:
    for f in glob.glob(f"/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/data/perturbed_tasks/{cat}/*_P3.json"):
        total_p3 += 1
        with open(f) as fp:
            d = json.load(fp)
        for step in d.get("execution_trace", []):
            if step.get("is_perturbed"):
                ok, r = check_text_invariant(step.get("output", {}))
                if not ok:
                    detected_p3 += 1
                    break

print(f"Total P3 tasks: {total_p3}, Detected by text invariant: {detected_p3}")
'''

stdin, stdout, stderr = ssh.exec_command(f'python3 -c \'{remote_code}\'')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)
ssh.close()

