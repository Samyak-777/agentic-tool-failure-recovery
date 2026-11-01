import paramiko

def run_canary():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("10.18.1.16", username="mrunmayee", password="BT23cse019")
    
    cmd = """
cd /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze
git checkout test_reeti_evaluator_fix
PYTHONPATH=. /mnt/data/toolmaze_project/envs/toolmaze/bin/python evaluation/scripts/run_eval_care.py \
  --config evaluation/configs/gemini_eval_config_c1.yaml \
  --backend ollama \
  --model qwen3:8b \
  --agent-type care \
  --category c1 \
  --limit 10 \
  --max-workers 2 \
  --no-resume \
  --run-id canary_reeti_new_e89d623b_10
"""
    print("Launching Reeti's new code canary benchmark on server...")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    
    for line in iter(stdout.readline, ""):
        print(line, end="")
    
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print("\nSTDERR:\n", err)
        
    ssh.close()

if __name__ == "__main__":
    run_canary()
