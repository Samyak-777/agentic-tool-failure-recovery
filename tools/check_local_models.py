import paramiko, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('10.18.1.16', username='mrunmayee', password='BT23cse019')

stdin, stdout, stderr = ssh.exec_command('ollama list')
print("OLLAMA MODELS:")
print(stdout.read().decode('utf-8', errors='replace'))

stdin, stdout, stderr = ssh.exec_command('ls -la /mnt/data/toolmaze_project/models')
print("STORED MODELS:")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()

