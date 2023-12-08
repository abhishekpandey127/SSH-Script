import paramiko
import json
import os
import time

json_file_path = 'creds.json'


# Function to connect to an SSH server
def ssh_connect(ssh_client, hostname, username, password):
    known_hosts_file = os.path.expanduser('~/.ssh/known_hosts')
    host_key_known = False

    try:
        with open(known_hosts_file, 'r') as file:
            for line in file:
                if hostname in line:
                    host_key_known = True
                    break
    except FileNotFoundError:
        print(f"Known hosts file '{known_hosts_file}' not found. It will be created.")

    if host_key_known:
        ssh_client.set_missing_host_key_policy(paramiko.RejectPolicy())
    else:
        print(f"Host key for {hostname} not known. Adding automatically.")
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(hostname, username=username, password=password)


json_file_path = 'creds.json'

# Create an SSH client instance
ssh = paramiko.SSHClient()
ssh.load_system_host_keys()

try:
    with open(json_file_path, 'r') as file:
        creds = json.load(file)

    # First SSH into the gateway server
    print("Connecting to gateway server...")
    ssh_connect(ssh, 'gw.hpc.nyu.edu', creds['username'], creds['password'])

    # Use the gateway server's session to connect to the target server
    print("Connecting to target server...")
    target_ssh = ssh.invoke_shell()
    target_ssh.send(f'ssh {creds["username"]}@greene.hpc.nyu.edu\n')
    time.sleep(5)
    # Wait for the password prompt and send the password
    # while not target_ssh.recv_ready():  # Wait for the server to be ready
    target_ssh.send(creds['password'] + '\n')
    print("Connection to target server successful")

    sbatch_command = f'sbatch /scratch/{creds["username"]}/test/hello-python.sbatch'
    time.sleep(5)
    # sbatch_command = 'cd /scratch/'+creds['username']+'/mro_env/jobs && sbatch job.slurm'

    target_ssh.send(sbatch_command + '\n')
    # while not target_ssh.recv_ready():  # Wait for the server to be ready
    time.sleep(2)
    output = target_ssh.recv(1024)
    print("Output:")
    print(output.decode('utf-8'))

except FileNotFoundError:
    print(f"Credentials file '{json_file_path}' not found.")
except json.JSONDecodeError:
    print(f"Error decoding JSON from the file '{json_file_path}'.")
except KeyError:
    print(f"Missing required credential fields in '{json_file_path}'.")
except paramiko.AuthenticationException:
    print("Authentication failed, please verify your credentials")
except paramiko.BadHostKeyException as badHostKeyException:
    print("Unable to verify server's host key: %s" % badHostKeyException)
except paramiko.SSHException as e:
    print("SSH error: ", e)
except Exception as e:
    print("Operation error: %s" % e)
finally:
    ssh.close()