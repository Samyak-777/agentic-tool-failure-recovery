import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_code = '''
from openai import OpenAI
import re

all_keys = []
with open("/mnt/data/toolmaze_project/secrets/gemini_env") as fp:
    for line in fp:
        for m in re.finditer(r"AIzaSy[A-Za-z0-9_-]{33}", line):
            if m.group(0) not in all_keys:
                all_keys.append(m.group(0))

base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
client = OpenAI(api_key=all_keys[0], base_url=base_url)

try:
    models = client.models.list()
    print("Available models:")
    for m in models.data:
        print(" ", m.id)
except Exception as e:
    print("Error listing models:", e)
'''

stdin, stdout, stderr = ssh.exec_command(f'/mnt/data/toolmaze_project/envs/toolmaze/bin/python -c \'{remote_code}\'')
print(stdout.read().decode('utf-8', errors='replace'))
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print("STDERR:", err)
ssh.close()

