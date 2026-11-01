import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_code = '''
from pathlib import Path
p = Path("/mnt/data/toolmaze_project/secrets/gemini_env")
print("Exists:", p.exists())
if p.exists():
    with open(p) as f:
        keys = [l.strip() for l in f if "=" in l and not l.strip().startswith("#")]
        print(f"Loaded {len(keys)} keys from {p}")
'''

stdin, stdout, _ = ssh.exec_command(f'python3 -c \'{remote_code}\'')
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()

