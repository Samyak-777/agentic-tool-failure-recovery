import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_code = '''
with open("/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/core/sandbox.py") as f:
    lines = f.readlines()

print("=== _build_perturbation_map ===")
for line in lines[279:330]:
    print(line, end="")

print("\\n=== _intercept_tool_call ===")
for line in lines[570:630]:
    print(line, end="")
'''

stdin, stdout, stderr = ssh.exec_command(f'python3 -c \'{remote_code}\'')
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
