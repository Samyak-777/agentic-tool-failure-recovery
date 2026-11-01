import paramiko

def inspect_template():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("10.18.1.16", username="mrunmayee", password="BT23cse019")
    
    code = """
import json
d = json.load(open('/mnt/data/toolmaze_project/agentic-tool-failure-recovery/ToolMaze/data/templates/c1/C1_template_001.json'))
print('KEYS:', list(d.keys()))
print('DAG KEYS:', list(d.get('dag', {}).keys()))
print('DAG NODES:', [n.get('tool_name') for n in d.get('dag', {}).get('nodes', [])])
"""
    sftp = ssh.open_sftp()
    with sftp.file("/tmp/inspect_tmpl.py", "w") as f:
        f.write(code)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("/mnt/data/toolmaze_project/envs/toolmaze/bin/python /tmp/inspect_tmpl.py")
    out = stdout.read().decode('utf-8')
    ssh.close()
    print(out)

if __name__ == "__main__":
    inspect_template()
