import paramiko
import time
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def run_gemini_c4():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("10.18.1.16", username="mrunmayee", password="BT23cse019")
    
    print("\n" + "=" * 70)
    print("Launching C4 Evaluation (10 tasks: P0-P4) with CARE + gemini-3-flash-preview...")
    print("=" * 70)
    
    # Kill any stale run
    ssh.exec_command("pkill -f run_eval_care.py")
    time.sleep(1)
    
    log_file = "gemini_c4_sov.log"
    run_id = "gemini_care_c4_sov_10"
    
    launch_cmd = f"""
cd /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze
git checkout feature/track_analysis_unified
export PYTHONPATH=.
rm -f {log_file}
PYTHONIOENCODING=utf-8 nohup /mnt/data/toolmaze_project/envs/toolmaze/bin/python evaluation/scripts/run_eval_care.py \
  --config evaluation/configs/gemini_eval_config_c4.yaml \
  --backend gemini \
  --model gemini-3-flash-preview \
  --agent-type care \
  --category c4 \
  --limit 10 \
  --max-workers 2 \
  --no-resume \
  --run-id {run_id} > {log_file} 2>&1 &
echo $!
"""
    stdin, stdout, stderr = ssh.exec_command(launch_cmd)
    pid = stdout.read().decode().strip().splitlines()[-1]
    print(f"[C4 Gemini] Server Process PID: {pid}")
    
    time.sleep(2)
    last_pos = 0
    start_time = time.time()
    
    while True:
        # Check if process is still running
        check_cmd = f"ps -p {pid} -o pid="
        _, chk_out, _ = ssh.exec_command(check_cmd)
        is_running = bool(chk_out.read().decode().strip())
        
        # Read new log content
        read_cmd = f"tail -c +{last_pos + 1} /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/{log_file}"
        _, log_out, _ = ssh.exec_command(read_cmd)
        new_bytes = log_out.read()
        
        if new_bytes:
            text = new_bytes.decode('utf-8', errors='replace')
            print(text, end="")
            sys.stdout.flush()
            last_pos += len(new_bytes)
            
        if not is_running:
            print("\n[C4 Gemini Process Exited]")
            break
            
        time.sleep(3)
        
    elapsed = time.time() - start_time
    print(f"\n[C4 Gemini] Finished in {elapsed:.1f}s ({elapsed/60:.2f} mins).")
    
    summary_cmd = f"cat /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records/{run_id}/run_summary.json"
    _, sum_out, _ = ssh.exec_command(summary_cmd)
    raw_sum = sum_out.read().decode('utf-8', errors='replace')
    if raw_sum:
        print(f"\n=== C4 GEMINI RUN SUMMARY ===")
        print(raw_sum)
        
    ssh.close()

if __name__ == "__main__":
    run_gemini_c4()

