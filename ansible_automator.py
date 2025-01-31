import ansible_runner

# Define all playbook functions for "breaks" actions
def ADoffDNS(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/ADoffDNS.yml",
        limit=limit_hosts
    )

def ADfixDNS(limit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/ADfixDNS.yml",
        limit=limit_hosts
    )

def ADoffLDAP(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/ADoffLDAP.yml",
        limit=limit_hosts
    )

def ADfixLDAP(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/ADfixLDAP.yml",
        limit=limit_hosts
    )

def BackupOffHTTP(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/BackupOffHTTP.yml",
        limit=limit_hosts
    )

def BackupFixHTTP(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/BackupFixHTTP.yml",
        limit=limit_hosts
    )

def DevOffPing(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/DevOffPing.yml",
        limit=limit_hosts
    )

def DevFixPing(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/DevFixPing.yml",
        limit=limit_hosts
    )

def DevOffSSH(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/DevOffSSH.yml",
        limit=limit_hosts
    )

def DevFixSSH(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/DevFixSSH.yml",
        limit=limit_hosts
    )

def FTPOffFTP(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/FTPOffFTP.yml",
        limit=limit_hosts
    )

def FTPFixFTP(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/FTPFixFTP.yml",
        limit=limit_hosts
    )

def UbuntuOffPing(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/UbuntuOffPing.yml",
        limit=limit_hosts
    )

def UbuntuFixPing(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/UbuntuFixPing.yml",
        limit=limit_hosts
    )

def UbuntuOffSSH(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/UbuntuOffSSH.yml",
        limit=limit_hosts
    )

def UbuntuFixSSH(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/UbuntuFixSSH.yml",
        limit=limit_hosts
    )

def WebAppOffHTTP(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/WebAppOffHTTP.yml",
        limit=limit_hosts
    )

def WebAppFixHTTP(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/WebAppFixHTTP.yml",
        limit=limit_hosts
    )

def WebAppOffSQL(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/WebAppOffSQL.yml",
        limit=limit_hosts
    )

def WebAppFixSQL(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/WebAppFixSQL.yml",
        limit=limit_hosts
    )

def WinOffPing(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/WinOffPing.yml",
        limit=limit_hosts
    )

def WinFixPing(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_fixes/WinFixPing.yml",
        limit=limit_hosts
    )

def WinOffWinRM(imit_hosts=None):
    return ansible_runner.run(
        private_data_dir='./realinv.ini',
        inventory="./realinv.ini",
        playbook="./ansible_breaks/WinOffWinRM.yml",
        limit=limit_hosts
    )

def WinFixWinRM(imit_hosts=None):
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

def get_service_from_ip(ip):
    # Dictionary of service titles and their respective ports
    service_mapping = {
        1: "AD_DNS",        # DNS
        2: "AD_LDAP",       # LDAP
        3: "Backup_HTTP",   # HTTP
        4: "Dev_Ping",      # DevServer: PING
        5: "Dev_SSH",       # DevServer: SSH
        6: "FTP",           # UbuntuFTP: FTP
        7: "Ubuntu_Ping",   # Ubuntu1: PING
        8: "Ubuntu_SSH",    # Ubuntu1: SSH
        9: "WebApp_HTTP",   # WebApp: HTTP
        10: "WebApp_SQL",   # WebApp: SQL
        11: "Win_Ping",     # Windows1: PING
        12: "Win_WinRM"     # Windows1: WINRM
    }

    # Base IPs for each team (the first part of the IP address without port)
    base_ips = {
        "10.1.1.60": 1, "10.1.1.60:389": 2, "10.1.2.2:80": 3, "10.1.2.10": 4,
        "10.1.2.10:22": 5, "10.1.2.4:21": 6, "10.1.1.10": 7, "10.1.1.10:22": 8,
        "10.1.1.40": 7, "10.1.1.40:22": 8, "10.1.1.30:80": 9, "10.1.1.30:3306": 10,
        "10.1.1.70": 11, "10.1.1.70:5985": 12, "10.1.1.80": 11, "10.1.1.80:5985": 12,

        "10.2.1.60": 1, "10.2.1.60:389": 2, "10.2.2.2:80": 3, "10.2.2.10": 4,
        "10.2.2.10:22": 5, "10.2.2.4:21": 6, "10.2.1.10": 7, "10.2.1.10:22": 8,
        "10.2.1.40": 7, "10.2.1.40:22": 8, "10.2.1.30:80": 9, "10.2.1.30:3306": 10,
        "10.2.1.70": 11, "10.2.1.70:5985": 12, "10.2.1.80": 11, "10.2.1.80:5985": 12,

        "10.3.1.60": 1, "10.3.1.60:389": 2, "10.3.2.2:80": 3, "10.3.2.10": 4,
        "10.3.2.10:22": 5, "10.3.2.4:21": 6, "10.3.1.10": 7, "10.3.1.10:22": 8,
        "10.3.1.40": 7, "10.3.1.40:22": 8, "10.3.1.30:80": 9, "10.3.1.30:3306": 10,
        "10.3.1.70": 11, "10.3.1.70:5985": 12, "10.3.1.80": 11, "10.3.1.80:5985": 12,

        "10.4.1.60": 1, "10.4.1.60:389": 2, "10.4.2.2:80": 3, "10.4.2.10": 4,
        "10.4.2.10:22": 5, "10.4.2.4:21": 6, "10.4.1.10": 7, "10.4.1.10:22": 8,
        "10.4.1.40": 7, "10.4.1.40:22": 8, "10.4.1.30:80": 9, "10.4.1.30:3306": 10,
        "10.4.1.70": 11, "10.4.1.70:5985": 12, "10.4.1.80": 11, "10.4.1.80:5985": 12,

        "10.5.1.60": 1, "10.5.1.60:389": 2, "10.5.2.2:80": 3, "10.5.2.10": 4,
        "10.5.2.10:22": 5, "10.5.2.4:21": 6, "10.5.1.10": 7, "10.5.1.10:22": 8,
        "10.5.1.40": 7, "10.5.1.40:22": 8, "10.5.1.30:80": 9, "10.5.1.30:3306": 10,
        "10.5.1.70": 11, "10.5.1.70:5985": 12, "10.5.1.80": 11, "10.5.1.80:5985": 12,

        "10.6.1.60": 1, "10.6.1.60:389": 2, "10.6.2.2:80": 3, "10.6.2.10": 4,
        "10.6.2.10:22": 5, "10.6.2.4:21": 6, "10.6.1.10": 7, "10.6.1.10:22": 8,
        "10.6.1.40": 7, "10.6.1.40:22": 8, "10.6.1.30:80": 9, "10.6.1.30:3306": 10,
        "10.6.1.70": 11, "10.6.1.70:5985": 12, "10.6.1.80": 11, "10.6.1.80:5985": 12,

        "10.7.1.60": 1, "10.7.1.60:389": 2, "10.7.2.2:80": 3, "10.7.2.10": 4,
        "10.7.2.10:22": 5, "10.7.2.4:21": 6, "10.7.1.10": 7, "10.7.1.10:22": 8,
        "10.7.1.40": 7, "10.7.1.40:22": 8, "10.7.1.30:80": 9, "10.7.1.30:3306": 10,
        "10.7.1.70": 11, "10.7.1.70:5985": 12, "10.7.1.80": 11, "10.7.1.80:5985": 12,

        "10.8.1.60": 1, "10.8.1.60:389": 2, "10.8.2.2:80": 3, "10.8.2.10": 4,
        "10.8.2.10:22": 5, "10.8.2.4:21": 6, "10.8.1.10": 7, "10.8.1.10:22": 8,
        "10.8.1.40": 7, "10.8.1.40:22": 8, "10.8.1.30:80": 9, "10.8.1.30:3306": 10,
        "10.8.1.70": 11, "10.8.1.70:5985": 12, "10.8.1.80": 11, "10.8.1.80:5985": 12,

        "10.9.1.60": 1, "10.9.1.60:389": 2, "10.9.2.2:80": 3, "10.9.2.10": 4,
        "10.9.2.10:22": 5, "10.9.2.4:21": 6, "10.9.1.10": 7, "10.9.1.10:22": 8,
        "10.9.1.40": 7, "10.9.1.40:22": 8, "10.9.1.30:80": 9, "10.9.1.30:3306": 10,
        "10.9.1.70": 11, "10.9.1.70:5985": 12, "10.9.1.80": 11, "10.9.1.80:5985": 12,

        "10.10.1.60": 1, "10.10.1.60:389": 2, "10.10.2.2:80": 3, "10.10.2.10": 4,
        "10.10.2.10:22": 5, "10.10.2.4:21": 6, "10.10.1.10": 7, "10.10.1.10:22": 8,
        "10.10.1.40": 7, "10.10.1.40:22": 8, "10.10.1.30:80": 9, "10.10.1.30:3306": 10,
        "10.10.1.70": 11, "10.10.1.70:5985": 12, "10.10.1.80": 11, "10.10.1.80:5985": 12,

        "10.11.1.60": 1, "10.11.1.60:389": 2, "10.11.2.2:80": 3, "10.11.2.10": 4,
        "10.11.2.10:22": 5, "10.11.2.4:21": 6, "10.11.1.10": 7, "10.11.1.10:22": 8,
        "10.11.1.40": 7, "10.11.1.40:22": 8, "10.11.1.30:80": 9, "10.11.1.30:3306": 10,
        "10.11.1.70": 11, "10.11.1.70:5985": 12, "10.11.1.80": 11, "10.11.1.80:5985": 12,

        "10.12.1.60": 1, "10.12.1.60:389": 2, "10.12.2.2:80": 3, "10.12.2.10": 4,
        "10.12.2.10:22": 5, "10.12.2.4:21": 6, "10.12.1.10": 7, "10.12.1.10:22": 8,
        "10.12.1.40": 7, "10.12.1.40:22": 8, "10.12.1.30:80": 9, "10.12.1.30:3306": 10,
        "10.12.1.70": 11, "10.12.1.70:5985": 12, "10.12.1.80": 11, "10.12.1.80:5985": 12,

        "10.13.1.60": 1, "10.13.1.60:389": 2, "10.13.2.2:80": 3, "10.13.2.10": 4,
        "10.13.2.10:22": 5, "10.13.2.4:21": 6, "10.13.1.10": 7, "10.13.1.10:22": 8,
        "10.13.1.40": 7, "10.13.1.40:22": 8, "10.13.1.30:80": 9, "10.13.1.30:3306": 10,
        "10.13.1.70": 11, "10.13.1.70:5985": 12, "10.13.1.80": 11, "10.13.1.80:5985": 12,

        "10.14.1.60": 1, "10.14.1.60:389": 2, "10.14.2.2:80": 3, "10.14.2.10": 4,
        "10.14.2.10:22": 5, "10.14.2.4:21": 6, "10.14.1.10": 7, "10.14.1.10:22": 8,
        "10.14.1.40": 7, "10.14.1.40:22": 8, "10.14.1.30:80": 9, "10.14.1.30:3306": 10,
        "10.14.1.70": 11, "10.14.1.70:5985": 12, "10.14.1.80": 11, "10.14.1.80:5985": 12,

        "10.15.1.60": 1, "10.15.1.60:389": 2, "10.15.2.2:80": 3, "10.15.2.10": 4,
        "10.15.2.10:22": 5, "10.15.2.4:21": 6, "10.15.1.10": 7, "10.15.1.10:22": 8,
        "10.15.1.40": 7, "10.15.1.40:22": 8, "10.15.1.30:80": 9, "10.15.1.30:3306": 10,
        "10.15.1.70": 11, "10.15.1.70:5985": 12, "10.15.1.80": 11, "10.15.1.80:5985": 12
    }

    # Check if the provided IP is in the mapping and return the corresponding service
    service_id = base_ips.get(ip)
    if service_id:
        return service_mapping.get(service_id, "Service not found")
    else:
        return "IP not found in the system data"

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


def handle_list_of_ips(ip_list):
    for ip_array in ip_list:
        for ip, status in ip_array.items():  # Iterate over the dictionary
            action_type = get_service_from_ip(ip)
            if status == "on":
                print(action_map[action_type]["break"])
                action_map[action_type]["break"](ip)
            else:
                print(action_map[action_type]["fix"])
                action_map[action_type]["fix"](ip)