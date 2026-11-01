import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_code = '''
import json
with open("/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/data/perturbed_tasks/c3/C3_task_001_P3.json") as f:
    d = json.load(f)
print("keys:", list(d.keys()))
for k in ["perturbation", "perturbed_tool", "victim_tool", "injected_perturbation", "dag"]:
    if k in d:
        print(f"{k}:", str(d[k])[:300])
'''

stdin, stdout, stderr = ssh.exec_command(f'python3 -c \'{remote_code}\'')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()

