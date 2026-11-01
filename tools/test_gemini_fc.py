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

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_flight_info",
            "description": "Look up flight information",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_number": {"type": "string", "description": "Flight number, e.g. CA1234"}
                },
                "required": ["flight_number"]
            }
        }
    }
]

messages = [
    {"role": "user", "content": "Please look up flight info for flight CA1234"}
]

r = client.chat.completions.create(
    model="gemini-3-flash-preview",
    messages=messages,
    tools=tools,
    max_tokens=1024
)

msg = r.choices[0].message
print("Finish reason:", r.choices[0].finish_reason)
print("Content:", repr(msg.content))
print("Tool calls count:", len(msg.tool_calls) if msg.tool_calls else 0)
if msg.tool_calls:
    for tc in msg.tool_calls:
        print("  Tool call:", tc.function.name, tc.function.arguments)
'''

sftp = ssh.open_sftp()
with sftp.file('/mnt/data/toolmaze_project/test_gemini_tools.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/mnt/data/toolmaze_project/envs/toolmaze/bin/python /mnt/data/toolmaze_project/test_gemini_tools.py')
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print("STDOUT:", out)
if err:
    print("STDERR:", err)
ssh.close()

