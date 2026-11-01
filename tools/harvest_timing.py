import paramiko
import json
import sys
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_script = """
import os, json
from datetime import datetime

base_dir = '/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records'

runs = [
    'qwen14b_care_c3_50',
    'qwen14b_care_c4_50',
    'qwen32b_care_c3_50',
    'qwen32b_care_c4_50'
]

timings = {}
for r in runs:
    p = os.path.join(base_dir, r, 'run_summary.json')
    if os.path.exists(p):
        with open(p) as f:
            d = json.load(f)
        t_start = datetime.fromisoformat(d['start_time'])
        t_end = datetime.fromisoformat(d['end_time'])
        duration_s = (t_end - t_start).total_seconds()
        timings[r] = {
            'duration_s': duration_s,
            'duration_m': round(duration_s / 60, 2),
            'avg_sec_per_task': round(duration_s / d['total_tasks'], 2),
            'total_events': d.get('total_events')
        }

print(json.dumps(timings, indent=2))
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/timing_stats.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/mnt/data/toolmaze_project/envs/toolmaze/bin/python /tmp/timing_stats.py')
out = stdout.read().decode('utf-8')
print(out)
ssh.close()
