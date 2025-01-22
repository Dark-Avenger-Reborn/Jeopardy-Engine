import ansible_runner

# Define all playbook functions for "breaks" actions
def ADoffDNS(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/ADoffDNS.yml",
        limit=limit_hosts
    )

def ADfixDNS(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/ADfixDNS.yml",
        limit=limit_hosts
    )

def ADoffLDAP(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/ADoffLDAP.yml",
        limit=limit_hosts
    )

def ADfixLDAP(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/ADfixLDAP.yml",
        limit=limit_hosts
    )

def BackupOffHTTP(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/BackupOffHTTP.yml",
        limit=limit_hosts
    )

def BackupFixHTTP(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/BackupFixHTTP.yml",
        limit=limit_hosts
    )

def DevOffPing(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/DevOffPing.yml",
        limit=limit_hosts
    )

def DevFixPing(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/DevFixPing.yml",
        limit=limit_hosts
    )

def DevOffSSH(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/DevOffSSH.yml",
        limit=limit_hosts
    )

def DevFixSSH(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/DevFixSSH.yml",
        limit=limit_hosts
    )

def FTPOffFTP(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/FTPOffFTP.yml",
        limit=limit_hosts
    )

def FTPFixFTP(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/FTPFixFTP.yml",
        limit=limit_hosts
    )

def UbuntuOffPing(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/UbuntuOffPing.yml",
        limit=limit_hosts
    )

def UbuntuFixPing(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/UbuntuFixPing.yml",
        limit=limit_hosts
    )

def UbuntuOffSSH(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/UbuntuOffSSH.yml",
        limit=limit_hosts
    )

def UbuntuFixSSH(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/UbuntuFixSSH.yml",
        limit=limit_hosts
    )

def WebAppOffHTTP(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/WebAppOffHTTP.yml",
        limit=limit_hosts
    )

def WebAppFixHTTP(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/WebAppFixHTTP.yml",
        limit=limit_hosts
    )

def WebAppOffSQL(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/WebAppOffSQL.yml",
        limit=limit_hosts
    )

def WebAppFixSQL(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/WebAppFixSQL.yml",
        limit=limit_hosts
    )

def WinOffPing(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/WinOffPing.yml",
        limit=limit_hosts
    )

def WinFixPing(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/WinFixPing.yml",
        limit=limit_hosts
    )

def WinOffWinRM(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/WinOffWinRM.yml",
        limit=limit_hosts
    )

def WinFixWinRM(inventory_path, playbook_path, limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/WinFixWinRM.yml",
        limit=limit_hosts
    )

# Mapping of actions to playbooks
action_map = {
    "AD_DNS": {"break": ADoffDNS, "fix": ADfixDNS},
    "AD_LDAP": {"break": ADoffLDAP, "fix": ADfixLDAP},
    "Backup_HTTP": {"break": BackupOffHTTP, "fix": BackupFixHTTP},
    "Dev_Ping": {"break": DevOffPing, "fix": DevFixPing},
    "Dev_SSH": {"break": DevOffSSH, "fix": DevFixSSH},
    "FTP": {"break": FTPOffFTP, "fix": FTPFixFTP},
    "Ubuntu_Ping": {"break": UbuntuOffPing, "fix": UbuntuFixPing},
    "Ubuntu_SSH": {"break": UbuntuOffSSH, "fix": UbuntuFixSSH},
    "WebApp_HTTP": {"break": WebAppOffHTTP, "fix": WebAppFixHTTP},
    "WebApp_SQL": {"break": WebAppOffSQL, "fix": WebAppFixSQL},
    "Win_Ping": {"break": WinOffPing, "fix": WinFixPing},
    "Win_WinRM": {"break": WinOffWinRM, "fix": WinFixWinRM},
}

# Function to handle incoming data and route to appropriate playbook
def handle_action(action, state):
    if action in action_map:
        playbook_function = action_map[action]["break"] if state else action_map[action]["fix"]
        result = playbook_function(
            inventory_path="./realinv.ini",
            playbook_path="./ansible_breaks/" if state else "./ansible_fixes/",
            limit_hosts="ip_address" if state else None
        )
        if result.rc == 0:
            print(f"Action '{action}' {'applied' if state else 'reversed'} successfully!")
        else:
            print(f"Action '{action}' {'apply' if state else 'reverse'} failed with exit code {result.rc}")
    else:
        print(f"Unknown action: {action}")
