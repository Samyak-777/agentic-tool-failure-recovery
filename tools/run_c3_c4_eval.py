import paramiko
import time
import sys
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def run_suite(category, limit, run_id):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("10.18.1.16", username="mrunmayee", password="BT23cse019")
    
    print("\n" + "=" * 70)
    print(f"Launching {category.upper()} Evaluation ({limit} tasks) with CARE on Server (10.18.1.16, qwen3:8b)...")
    print("=" * 70)
    
    # Kill any stale run
    ssh.exec_command("pkill -f run_eval_care.py")
    time.sleep(1)
    
    log_file = f"eval_{category}.log"
    config_file = f"evaluation/configs/gemini_eval_config_{category}.yaml"
    
    launch_cmd = f"""
cd /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze
git checkout feature/track_analysis_unified
export PYTHONPATH=.
rm -f {log_file}
PYTHONIOENCODING=utf-8 nohup /mnt/data/toolmaze_project/envs/toolmaze/bin/python evaluation/scripts/run_eval_care.py \
  --config {config_file} \
  --backend ollama \
  --model qwen3:8b \
  --agent-type care \
  --category {category} \
  --limit {limit} \
  --max-workers 4 \
  --no-resume \
  --run-id {run_id} > {log_file} 2>&1 &
echo $!
"""
    stdin, stdout, stderr = ssh.exec_command(launch_cmd)
    pid = stdout.read().decode().strip().splitlines()[-1]
    print(f"[{category.upper()}] Server Process PID: {pid}")
    
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
            print(f"\n[{category.upper()} Process Exited]")
            break
            
        time.sleep(3)
        
    elapsed = time.time() - start_time
    print(f"\n[{category.upper()}] Finished in {elapsed:.1f}s ({elapsed/60:.2f} mins).")
    
    # Read summary
    summary_cmd = f"cat /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/evaluation/experiment_records/{run_id}/run_summary.json"
    _, sum_out, _ = ssh.exec_command(summary_cmd)
    raw_sum = sum_out.read().decode('utf-8', errors='replace')
    
    summary_data = None
    if raw_sum:
        try:
            summary_data = json.loads(raw_sum)
            print(f"\n=== {category.upper()} RUN SUMMARY ===")
            print(json.dumps(summary_data, indent=2))
        except Exception as e:
            print(f"Error parsing summary: {e}")
            print(raw_sum)
            
    ssh.close()
    return summary_data

def main():
    print("Starting Automated C3 & C4 Benchmark Pipeline with CARE...")
    
    # Run C3 (25 tasks = 5 tasks x 5 modes)
    c3_summary = run_suite(category="c3", limit=25, run_id="unified_c3_sov_25")
    
    # Run C4 (25 tasks = 5 tasks x 5 modes)
    c4_summary = run_suite(category="c4", limit=25, run_id="unified_c4_sov_25")
    
    print("\n" + "#" * 70)
    print("ALL BENCHMARKS FINISHED: C3 and C4 COMPLETE")
    print("#" * 70)

if __name__ == "__main__":
    main()

