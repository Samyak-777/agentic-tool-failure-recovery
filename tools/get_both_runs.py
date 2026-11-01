import paramiko

def get_both_results():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("10.18.1.16", username="mrunmayee", password="BT23cse019")
    
    code = """
import json, glob, os

def get_run_details(run_id):
    path = f'/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records/{run_id}/task_records/*.json'
    files = sorted(glob.glob(path))
    results = {}
    for f in files:
        task_name = os.path.basename(f)
        with open(f) as fp:
            d = json.load(fp)
        passed = d.get('passed')
        reason = d.get('failure_reason')
        tools = [tc.get('tool_name') for tc in d.get('tool_calls', [])]
        results[task_name] = {
            'passed': passed,
            'reason': reason,
            'tools': tools
        }
    return results

r_without = get_run_details('canary_full_fix_10')
r_with = get_run_details('canary_template_unified_10')

print("TASK_NAMES:", list(r_without.keys()))
print("WITHOUT:", json.dumps(r_without, indent=2))
print("WITH:", json.dumps(r_with, indent=2))
"""
    sftp = ssh.open_sftp()
    with sftp.file("/tmp/get_both_runs.py", "w") as f:
        f.write(code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("/mnt/data/toolmaze_project/envs/toolmaze/bin/python /tmp/get_both_runs.py")
    out = stdout.read().decode('utf-8')
    ssh.close()
    return out

if __name__ == "__main__":
    out = get_both_results()
    with open("compare_runs.json", "w", encoding="utf-8") as f:
        f.write(out)
    print("Fetched successfully. Length:", len(out))

