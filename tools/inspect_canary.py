import paramiko

def verify_checker_bug():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("10.18.1.16", username="mrunmayee", password="BT23cse019")
    
    code = """
import json, sys
sys.path.insert(0, '/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze')
from dag_rerouting.prerequisite_checker import PrerequisiteChecker

# 1. Load C1_template_001.json
with open('/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/data/templates/c1/C1_template_001.json') as f:
    template = json.load(f)

# Reeti does: self.task_json = self.task_template; PrerequisiteChecker(self.task_json)
checker = PrerequisiteChecker(template)
print("checker.valid_paths on template:", checker.valid_paths)
res = checker.check('book_flight_with_status_check', set())
print("checker.check('book_flight_with_status_check'):", res)
"""
    sftp = ssh.open_sftp()
    with sftp.file("/tmp/verify_bug.py", "w") as f:
        f.write(code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("/mnt/data/toolmaze_project/envs/toolmaze/bin/python /tmp/verify_bug.py")
    out = stdout.read().decode('utf-8')
    ssh.close()
    print("STDOUT:\n", out)

if __name__ == "__main__":
    verify_checker_bug()
