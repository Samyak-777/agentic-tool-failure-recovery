import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_code = '''
import glob, re
all_keys = set()
for f in glob.glob("/mnt/data/toolmaze_project/**", recursive=True):
    if "env" in f.lower() and not "/." in f:
        try:
            with open(f) as fp:
                for line in fp:
                    for m in re.finditer(r"AIzaSy[A-Za-z0-9_-]{33}", line):
                        all_keys.add(m.group(0))
        except Exception:
            pass

print(f"Total unique Gemini keys found across server: {len(all_keys)}")
for i, k in enumerate(all_keys):
    print(f"Key #{i+1}: {k[:8]}...{k[-4:]}")
'''

stdin, stdout, _ = ssh.exec_command(f'python3 -c \'{remote_code}\'')
print(stdout.read().decode('utf-8', errors='replace'))
ssh.close()

