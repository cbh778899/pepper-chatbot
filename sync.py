import os
import sys
import subprocess

# Constants
DEFAULT_IP = "10.234.7.154"
REMOTE_USER = "nao"
REMOTE_FOLDER = "/home/nao/pepperchat"
LOCAL_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")

def run_command(command):
    """Run a shell command and print it."""
    print(f"Running command: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(result.returncode)
    print(result.stdout)

def sync_files(remote_ip):
    """Sync local files to the remote system."""
    # Remove the existing folder on the remote system
    remove_command = f"ssh {REMOTE_USER}@{remote_ip} 'rm -rf {REMOTE_FOLDER}'"
    run_command(remove_command)

    # Copy the local folder to the remote system
    copy_command = f"scp -r {LOCAL_FOLDER}/. {REMOTE_USER}@{remote_ip}:{REMOTE_FOLDER}"
    run_command(copy_command)

def main():
    """Main function to handle command line arguments and initiate file sync."""
    if len(sys.argv) > 1:
        remote_ip = sys.argv[1]
    else:
        remote_ip = DEFAULT_IP

    print(f"Using remote IP: {remote_ip}")
    sync_files(remote_ip)

if __name__ == "__main__":
    main()