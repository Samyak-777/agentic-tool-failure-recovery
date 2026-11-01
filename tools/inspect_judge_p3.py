import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_code = '''
import json
with open("/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/results/qwen3_8b-care/care/c1/inferences/C1_task_002_P3_inference.json") as f:
    d = json.load(f)
print("Number of messages:", len(d.get("messages", [])))
for i, m in enumerate(d.get("messages", [])):
    print(f"[{i}] role={m.get('role')} keys={list(m.keys())}")
    if m.get('role') != 'system':
        print("   content snippet:", str(m.get('content'))[:100])
'''

stdin, stdout, stderr = ssh.exec_command(f'python3 -c \'{remote_code}\'')
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
