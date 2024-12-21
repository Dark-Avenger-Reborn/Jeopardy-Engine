import ansible_runner

def run_playbook(inventory_path, playbook_path, limit_hosts=None):
    r = ansible_runner.run(
        private_data_dir='./realinv.ini',  # Temporary directory for runner
        inventory=inventory_path,  # Path to dynamic inventory script
        playbook=playbook_path,    # Path to playbook
        limit=limit_hosts          # Limit to specific hosts (as a comma-separated string)
    )
    
    if r.rc == 0:
        print("Playbook completed successfully!")
    else:
        print(f"Playbook failed with exit code {r.rc}")
