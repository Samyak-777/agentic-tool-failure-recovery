import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

print("=== OLD C3 RUN SUMMARY (unified_c3_25_eval) ===")
stdin, stdout, _ = ssh.exec_command("cat /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records/unified_c3_25_eval/run_summary.json")
print(stdout.read().decode('utf-8', errors='replace'))

print("=== NEW C3 RUN SUMMARY (unified_c3_sov_25) ===")
stdin, stdout, _ = ssh.exec_command("cat /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records/unified_c3_sov_25/run_summary.json")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()

