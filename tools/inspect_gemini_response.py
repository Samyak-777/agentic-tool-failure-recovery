import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_code = '''
from openai import OpenAI
import json

keys = []
with open("/mnt/data/toolmaze_project/secrets/gemini_env") as f:
    for l in f:
        l = l.strip()
        if "=" in l and not l.startswith("#"):
            k = l.split("=", 1)[1].strip().strip("'").strip('"')
            if k: keys.append(k)

client = OpenAI(api_key=keys[0], base_url="https://generativelanguage.googleapis.com/v1beta/openai")

r = client.chat.completions.create(
    model="gemini-3-flash-preview",
    messages=[{"role": "user", "content": "Say hello"}],
    max_tokens=500
)
print("gemini-3-flash-preview:", r.model_dump_json(indent=2))
'''

sftp = ssh.open_sftp()
with sftp.file('/mnt/data/toolmaze_project/dump_response.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/mnt/data/toolmaze_project/envs/toolmaze/bin/python /mnt/data/toolmaze_project/dump_response.py')
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print("STDOUT:", out)
if err:
    print("STDERR:", err)
ssh.close()
