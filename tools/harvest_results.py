import paramiko
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_script = """
import json, os, glob

runs = [
    'qwen3_baseline_c3_full',
    'qwen3_care_c3_full',
    'qwen3_baseline_c4_full',
    'qwen3_care_c4_full',
    'qwen14b_care_c3_50',
    'qwen14b_care_c4_50',
    'qwen32b_care_c3_50',
    'qwen32b_care_c4_50',
    'gemini_baseline_c3_full',
    'gemini_care_c3_full',
    'gemini_baseline_c4_full',
    'gemini_care_c4_full'
]

results = {}
base_dir = '/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records'

for r in runs:
    p = os.path.join(base_dir, r, 'run_summary.json')
    if os.path.exists(p):
        try:
            with open(p) as f:
                d = json.load(f)
            results[r] = d
        except Exception as e:
            results[r] = {'error': str(e)}
    else:
        results[r] = 'NOT_FOUND'

print(json.dumps(results, indent=2))
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/harvest_summaries.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/mnt/data/toolmaze_project/envs/toolmaze/bin/python /tmp/harvest_summaries.py')
out = stdout.read().decode('utf-8')
print(out)
ssh.close()
