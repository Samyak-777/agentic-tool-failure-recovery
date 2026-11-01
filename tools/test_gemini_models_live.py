import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_code = '''
from pathlib import Path
from openai import OpenAI

keys = []
with open("/mnt/data/toolmaze_project/secrets/gemini_env") as f:
    for l in f:
        l = l.strip()
        if "=" in l and not l.startswith("#"):
            k = l.split("=", 1)[1].strip().strip("'").strip('"')
            if k: keys.append(k)

print(f"Loaded {len(keys)} keys from secrets/gemini_env.")
test_key = keys[0]
masked = test_key[:6] + "..." + test_key[-4:]
print(f"Testing key #1 ({masked}) against Google Gemini API...")
base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
client = OpenAI(api_key=test_key, base_url=base_url)

models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3.8-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
]

for model in models_to_test:
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "respond with the single word: OK"}],
            max_tokens=20
        )
        print(f"  {model}: SUCCESS! -> {r.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"  {model}: FAILED -> {type(e).__name__}: {str(e)[:80]}")
'''

sftp = ssh.open_sftp()
with sftp.file('/mnt/data/toolmaze_project/test_gemini_live.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/mnt/data/toolmaze_project/envs/toolmaze/bin/python /mnt/data/toolmaze_project/test_gemini_live.py')
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print("STDOUT:", out)
if err:
    print("STDERR:", err)
ssh.close()
