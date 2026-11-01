import paramiko
import time
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def run_eval():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("10.18.1.16", username="mrunmayee", password="BT23cse019")
    
    # 1. Kill any stale run
    ssh.exec_command("pkill -f run_eval_care.py")
    time.sleep(1)
    
    # 2. Launch with nohup and redirect to eval_50.log
    launch_cmd = """
cd /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze
git checkout feature/track_analysis_unified
rm -f eval_50.log
PYTHONIOENCODING=utf-8 nohup /mnt/data/toolmaze_project/envs/toolmaze/bin/python evaluation/scripts/run_eval_care.py \
  --config evaluation/configs/gemini_eval_config_c1.yaml \
  --backend ollama \
  --model qwen3:8b \
  --agent-type care \
  --category c1 \
  --limit 50 \
  --max-workers 4 \
  --no-resume \
  --run-id unified_best_50_eval > eval_50.log 2>&1 &
echo $!
"""
    stdin, stdout, stderr = ssh.exec_command(launch_cmd)
    pid = stdout.read().decode().strip().splitlines()[-1]
    print(f"Launched benchmark on server PID: {pid}")
    
    # 3. Stream eval_50.log until completion
    time.sleep(2)
    last_pos = 0
    start_time = time.time()
    
    while True:
        # Check if process is still running
        check_cmd = f"ps -p {pid} -o pid="
        _, chk_out, _ = ssh.exec_command(check_cmd)
        is_running = bool(chk_out.read().decode().strip())
        
        # Read new log content
        read_cmd = f"tail -c +{last_pos + 1} /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/eval_50.log"
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
    print(f"\nBenchmark finished in {elapsed:.1f}s ({elapsed/60:.2f} mins).")
    
    # Read the summary
    summary_cmd = "cat /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records/unified_best_50_eval/run_summary.json"
    _, sum_out, _ = ssh.exec_command(summary_cmd)
    raw_sum = sum_out.read().decode('utf-8', errors='replace')
    if raw_sum:
        print("\n=== RUN SUMMARY ===")
        print(raw_sum)
        
    ssh.close()

if __name__ == "__main__":
    run_eval()

