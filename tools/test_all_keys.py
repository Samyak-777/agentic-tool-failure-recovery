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
print(f"Testing {len(all_keys)} keys on gemini-3-flash-preview...")
for i, k in enumerate(all_keys):
    masked = k[:8] + "..." + k[-4:]
    client = OpenAI(api_key=k, base_url=base_url)
    try:
        r = client.chat.completions.create(
            model="gemini-3-flash-preview",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=50
        )
        print(f"Key #{i+1} ({masked}): SUCCESS -> {repr(r.choices[0].message.content)}")
    except Exception as e:
        print(f"Key #{i+1} ({masked}): ERROR -> {type(e).__name__}: {e}")
'''

stdin, stdout, stderr = ssh.exec_command(f'/mnt/data/toolmaze_project/envs/toolmaze/bin/python -c \'{remote_code}\'')
print(stdout.read().decode('utf-8', errors='replace'))
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print("STDERR:", err)
ssh.close()

