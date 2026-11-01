import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_script = '''
import glob, json
for f in sorted(glob.glob("/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/results/qwen3_8b-care/care/c4/evaluations/C4_task_*_P0_eval.json")):
    with open(f) as fp:
        d = json.load(fp)
    print(f.split("/")[-1], "pass:", d.get("pass"), "reason:", d.get("failure_reason"))
    tc = d.get("trace_check", {})
    if tc:
        print("   missing:", tc.get("missing_tools"))
        print("   actual:", tc.get("actual", {}).get("execution_trace"))
'''
stdin, stdout, _ = ssh.exec_command(f'python3 -c \'{remote_script}\'')
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()

