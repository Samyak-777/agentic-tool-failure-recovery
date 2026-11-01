import paramiko
import time
import sys

def run_50():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("10.18.1.16", username="mrunmayee", password="BT23cse019")
    
    cmd = """
cd /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze
git checkout feature/track_analysis_unified
PYTHONPATH=. /mnt/data/toolmaze_project/envs/toolmaze/bin/python evaluation/scripts/run_eval_care.py \
  --config evaluation/configs/gemini_eval_config_c1.yaml \
  --backend ollama \
  --model qwen3:8b \
  --agent-type care \
  --category c1 \
  --limit 50 \
  --max-workers 4 \
  --no-resume \
  --run-id unified_best_50_eval
"""
    print("=" * 70)
    print("Launching 50-Task Unified Evaluation on Server (10.18.1.16, qwen3:8b)...")
    print("=" * 70)
    
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True)
    
    start_time = time.time()
    for line in iter(stdout.readline, ""):
        print(line, end="")
        sys.stdout.flush()
        
    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.1f} seconds ({elapsed/60:.2f} minutes).")
    
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print("\nSTDERR:\n", err)
        
    ssh.close()

if __name__ == "__main__":
    run_50()

