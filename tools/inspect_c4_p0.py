import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_script = '''
import json
with open("/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/results/qwen3_8b-care/care/c4/evaluations/C4_task_001_P0_eval.json") as f:
    d = json.load(f)
print(json.dumps(d, indent=2))
'''
stdin, stdout, _ = ssh.exec_command(f'python3 -c \'{remote_script}\'')
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()

