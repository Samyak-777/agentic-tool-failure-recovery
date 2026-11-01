import paramiko
import time
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def run_canary():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("10.18.1.16", username="mrunmayee", password="BT23cse019")
    
    print("\n" + "=" * 70)
    print("Launching Canary Evaluation (10 tasks: P0-P4) with Semantic Invariants...")
    print("=" * 70)
    
    ssh.exec_command("pkill -f run_eval_care.py")
    time.sleep(1)
    
    launch_cmd = """
cd /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze
git checkout feature/track_analysis_unified
export PYTHONPATH=.
rm -f canary_sov.log
PYTHONIOENCODING=utf-8 nohup /mnt/data/toolmaze_project/envs/toolmaze/bin/python evaluation/scripts/run_eval_care.py \
  --config evaluation/configs/gemini_eval_config_c1.yaml \
  --backend ollama \
  --model qwen3:8b \
  --agent-type care \
  --category c1 \
  --limit 10 \
  --max-workers 4 \
  --no-resume \
  --run-id canary_sov_v2_10 > canary_sov.log 2>&1 &
echo $!
"""
    stdin, stdout, stderr = ssh.exec_command(launch_cmd)
    pid = stdout.read().decode().strip().splitlines()[-1]
    print(f"Server PID: {pid}")
    
    time.sleep(2)
    last_pos = 0
    start_time = time.time()
    
    while True:
        check_cmd = f"ps -p {pid} -o pid="
        _, chk_out, _ = ssh.exec_command(check_cmd)
        is_running = bool(chk_out.read().decode().strip())
        
        read_cmd = f"tail -c +{last_pos + 1} /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/canary_sov.log"
        _, log_out, _ = ssh.exec_command(read_cmd)
        new_bytes = log_out.read()
        
        if new_bytes:
            text = new_bytes.decode('utf-8', errors='replace')
            print(text, end="")
            sys.stdout.flush()
            last_pos += len(new_bytes)
            
        if not is_running:
            print("\n[Server Process Exited]")
            break
            
        time.sleep(3)
        
    elapsed = time.time() - start_time
    print(f"\nCanary completed in {elapsed:.1f}s ({elapsed/60:.2f} mins).")
    
    summary_cmd = "cat /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records/canary_sov_v2_10/run_summary.json"
    _, sum_out, _ = ssh.exec_command(summary_cmd)
    raw_sum = sum_out.read().decode('utf-8', errors='replace')
    if raw_sum:
        print("\n=== RUN SUMMARY ===")
        print(raw_sum)
        
    ssh.close()

if __name__ == "__main__":
    run_canary()
