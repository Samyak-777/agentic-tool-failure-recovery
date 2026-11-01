import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

cmd = """
cd /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze
git checkout feature/track_analysis_unified
export PYTHONPATH=.
PYTHONIOENCODING=utf-8 /mnt/data/toolmaze_project/envs/toolmaze/bin/python evaluation/scripts/run_eval_care.py \
  --config evaluation/configs/gemini_eval_config_c1.yaml \
  --backend gemini \
  --model gemini-3-flash-preview \
  --agent-type care \
  --category c1 \
  --limit 1 \
  --max-workers 1 \
  --no-resume \
  --run-id test_gemini_care_single
"""

stdin, stdout, stderr = ssh.exec_command(cmd)
for line in iter(stdout.readline, ""):
    print(line, end="")
err = stderr.read().decode('utf-8', errors='replace')
if err:
    print("\nSTDERR:\n", err)
ssh.close()

