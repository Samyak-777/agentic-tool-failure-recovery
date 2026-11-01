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

messages = [{"role": "user", "content": "Look up flight info for flight CA1234"}]

for m in ["gemini-3.5-flash", "gemini-flash-latest", "gemma-4-31b-it"]:
    try:
        r = client.chat.completions.create(
            model=m,
            messages=messages,
            tools=tools,
            max_tokens=1024
        )
        msg = r.choices[0].message
        print(f"Model: {m}")
        print("  finish_reason:", r.choices[0].finish_reason)
        print("  tool_calls:", len(msg.tool_calls) if msg.tool_calls else 0)
        if msg.tool_calls:
            print("  first call:", msg.tool_calls[0].function.name, msg.tool_calls[0].function.arguments)
        else:
            print("  content snippet:", repr(msg.content)[:80])
    except Exception as e:
        print(f"Model: {m} ERROR -> {type(e).__name__}: {str(e)[:80]}")
'''

stdin, stdout, stderr = ssh.exec_command(f'/mnt/data/toolmaze_project/envs/toolmaze/bin/python -c \'{remote_code}\'')
print(stdout.read().decode('utf-8', errors='replace'))
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print("STDERR:", err)
ssh.close()

