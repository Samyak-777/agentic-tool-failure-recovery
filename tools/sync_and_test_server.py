import paramiko

def run_remote(cmd):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("10.18.1.16", username="mrunmayee", password="BT23cse019")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    ssh.close()
    return out, err

if __name__ == "__main__":
    commands = [
        "cd /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze && git fetch origin && git checkout feature/track_analysis_unified && git pull origin feature/track_analysis_unified",
        "cd /mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze && PYTHONPATH=. /mnt/data/toolmaze_project/envs/toolmaze/bin/python -m pytest tests/test_prerequisite_checker.py tests/test_full_care_pipeline.py tests/test_c3_p2_victim_recovery.py -v"
    ]
    for c in commands:
        print(">>> RUNNING:", c)
        out, err = run_remote(c)
        print("STDOUT:\n", out)
        if err:
            print("STDERR:\n", err)

