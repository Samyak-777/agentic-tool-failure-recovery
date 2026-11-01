import paramiko
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

remote_script = """
import os, json, glob
from collections import defaultdict

base_dir = '/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records'

runs = [
    'qwen14b_care_c3_50',
    'qwen14b_care_c4_50',
    'qwen32b_care_c3_50',
    'qwen32b_care_c4_50'
]

run_stats = {}

for r in runs:
    task_files = sorted(glob.glob(os.path.join(base_dir, r, 'task_records', '*.json')))
    total = len(task_files)
    passed = 0
    mode_stats = defaultdict(lambda: {'total': 0, 'passed': 0, 'calls': [], 'reasons': defaultdict(int)})
    all_calls = []
    
    for f in task_files:
        with open(f) as fp:
            d = json.load(fp)
        mode = d.get('mode', 'P0')
        p = d.get('passed', False)
        t_calls = len(d.get('tool_calls', []))
        reason = d.get('failure_reason', 'none')
        
        mode_stats[mode]['total'] += 1
        mode_stats[mode]['calls'].append(t_calls)
        all_calls.append(t_calls)
        if p:
            passed += 1
            mode_stats[mode]['passed'] += 1
        else:
            short_r = str(reason).split(';')[0].strip()[:70]
            mode_stats[mode]['reasons'][short_r] += 1
            
    summary_modes = {}
    for m, data in sorted(mode_stats.items()):
        summary_modes[m] = {
            'total': data['total'],
            'passed': data['passed'],
            'tsr': round(data['passed'] / max(1, data['total']), 3),
            'avg_calls': round(sum(data['calls']) / max(1, len(data['calls'])), 2),
            'failure_reasons': dict(data['reasons'])
        }
        
    # Check execution time
    summary_p = os.path.join(base_dir, r, 'run_summary.json')
    duration_s = None
    if os.path.exists(summary_p):
        with open(summary_p) as fp:
            sdata = json.load(fp)
            # compute duration from start_time and end_time if present
            # or from duration
            pass
            
    run_stats[r] = {
        'total_tasks': total,
        'passed_tasks': passed,
        'pass_rate': round(passed / max(1, total), 3),
        'avg_calls_overall': round(sum(all_calls) / max(1, len(all_calls)), 2),
        'modes': summary_modes
    }

print(json.dumps(run_stats, indent=2))
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/detailed_stats_fixed.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command('/mnt/data/toolmaze_project/envs/toolmaze/bin/python /tmp/detailed_stats_fixed.py')
out = stdout.read().decode('utf-8')
print(out)
ssh.close()
