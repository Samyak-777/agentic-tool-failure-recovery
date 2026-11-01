import paramiko
import os
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

sftp = ssh.open_sftp()

local_records_dir = os.path.abspath('ToolMaze/evaluation/experiment_records')
os.makedirs(local_records_dir, exist_ok=True)

# 1. Download master comparison
remote_master = '/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records/master_50_c3_c4_comparison.json'
local_master = os.path.join(local_records_dir, 'master_50_c3_c4_comparison.json')
sftp.get(remote_master, local_master)
print(f"Downloaded {local_master}")

# 2. Download run summaries for all 4 runs
runs = [
    'qwen14b_care_c3_50',
    'qwen14b_care_c4_50',
    'qwen32b_care_c3_50',
    'qwen32b_care_c4_50'
]

for r in runs:
    local_run_dir = os.path.join(local_records_dir, r)
    os.makedirs(local_run_dir, exist_ok=True)
    remote_run_dir = f'/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records/{r}'
    for fname in ['run_summary.json', 'failure_summary.json', 'run_manifest.json']:
        rem_f = f'{remote_run_dir}/{fname}'
        loc_f = os.path.join(local_run_dir, fname)
        try:
            sftp.get(rem_f, loc_f)
            print(f"Downloaded {r}/{fname}")
        except Exception as e:
            print(f"Error downloading {rem_f}: {e}")

sftp.close()
ssh.close()
print("All files synchronized successfully!")
