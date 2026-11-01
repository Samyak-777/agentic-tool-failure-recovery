import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_code = '''
import os
for k, v in os.environ.items():
    if any(term in k.upper() for term in ["KEY", "GEMINI", "OPENAI", "API"]):
        print(f"{k} = ***{v[-4:] if len(v)>4 else '***'}")

with open("/home/mrunmayee/.bashrc") as f:
    for line in f:
        if any(term in line.upper() for term in ["KEY", "GEMINI", "API", "EXPORT"]):
            print("bashrc:", line.strip()[:35], "...")
'''

stdin, stdout, _ = ssh.exec_command(f'python3 -c \'{remote_code}\'')
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()
