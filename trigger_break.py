import json
import socket
import base64

class BreakManager:
    """Manages break/fix dispatch for the web UI backend."""
    
    def __init__(self, config_file='BreakLevels.json'):
        self.config_file = config_file
        self.breaks_data = self.load_config()
        self.broken_services = set()
    
    def load_config(self):
        """Load break configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"Error: {self.config_file} not found")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Error parsing {self.config_file}: {e}")
    
    def xor_encode(self, data, key=0x55):
        """XOR encode data with key (for Linux module)"""
        return bytes([b ^ key for b in data])
    
    def is_windows_command(self, command):
        """Detect if command is for Windows based on syntax"""
        windows_indicators = [
            'Stop-Service', 'Start-Service', 'Set-Service', 
            'New-NetFirewall', 'Remove-NetFirewall', 'Set-DnsClient',
            'Set-ItemProperty', 'Remove-DnsServer', 'takeown', 'icacls',
            'netsh', 'PowerShell', 'Remove-Item'
        ]
        return any(indicator in command for indicator in windows_indicators)

    def apply_team_to_target(self, target, team_number=None):
        """Replace any `x` host octet placeholder in target addresses with team number."""
        if team_number is None:
            return target

        host, sep, port = target.partition(':')
        octets = host.split('.')
        resolved_host = '.'.join(
            str(team_number) if octet.lower() == 'x' else octet
            for octet in octets
        )
        return f"{resolved_host}{sep}{port}" if sep else resolved_host
    
    def send_linux_command(self, ip, command):
        """Send command to Linux system via UDP port 5555 (fire-and-forget)."""
        try:
            magic_header = b"INTLUPD:"
            encoded_cmd = self.xor_encode(command.encode())
            payload = magic_header + encoded_cmd
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(payload, (ip, 5555))
            sock.close()
            return True
        except Exception as e:
            print(f"[!] Error sending Linux command to {ip}: {e}")
            return False
    
    def send_windows_command(self, ip, command):
        """Send command to Windows system via TCP port 443 (fire-and-forget)."""
        try:
            magic_header = "INTLUPD:"
            encoded_cmd = base64.b64encode(command.encode()).decode()
            payload = magic_header + encoded_cmd
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((ip, 443))
            sock.send(payload.encode())
            sock.close()
            return True
        except Exception as e:
            print(f"[!] Error sending Windows command to {ip}: {e}\n")
            return False
    
    def trigger_break(self, level, target=None, team_number=None):
        """
        Trigger a break for specific level and optionally specific target
        Args:
            level (str): Break level (e.g., 'lvl1', 'lvl2', 'lvl3', 'lvl4')
            target (str): Optional specific target IP or IP:port (e.g., '10.x.1.60' or '10.x.2.10:22')
                         If None, triggers all breaks for the level
            team_number (int): Optional team number used to replace `.x.` placeholders
        """
        if 'breaks' not in self.breaks_data:
            print("[!] No breaks section found in config\n")
            return False
        
        if level not in self.breaks_data['breaks']:
            print(f"[!] Level '{level}' not found. Available levels: {list(self.breaks_data['breaks'].keys())}\n")
            return False
        
        breaks = self.breaks_data['breaks'][level]
        
        if target:
            # Trigger single target
            if target not in breaks:
                print(f"[!] Target '{target}' not found in level '{level}'\n")
                return False
            
            command = breaks[target]
            if not command:
                print(f"[!] No command defined for {target}\n")
                return False
            
            # Extract IP (remove port if present) after team placeholder replacement.
            resolved_target = self.apply_team_to_target(target, team_number)
            ip = resolved_target.split(':')[0]
            
            print(f"[*] Triggering break for {resolved_target}")
            print(f"[*] Command: {command}")
            
            if self.is_windows_command(command):
                print(f"[*] Detected Windows target, using TCP:443")
                success = self.send_windows_command(ip, command)
            else:
                print(f"[*] Detected Linux target, using UDP:5555")
                success = self.send_linux_command(ip, command)
            
            if success:
                self.broken_services.add(f"{level}:{target}")
                print(f"[+] Successfully triggered break for {resolved_target}")

            print('\n')
            
            return success
        else:
            # Trigger all targets in level
            print(f"[*] Triggering all breaks for level '{level}'")
            success_count = 0
            total_count = 0
            
            for target, command in breaks.items():
                if not command:
                    print(f"[!] Skipping {target} (no command defined)\n")
                    continue
                
                total_count += 1
                resolved_target = self.apply_team_to_target(target, team_number)
                ip = resolved_target.split(':')[0]
                
                print(f"\n[*] Triggering break for {resolved_target}")
                print(f"[*] Command: {command}")
                
                if self.is_windows_command(command):
                    print(f"[*] Detected Windows target, using TCP:443")
                    success = self.send_windows_command(ip, command)
                else:
                    print(f"[*] Detected Linux target, using UDP:5555")
                    success = self.send_linux_command(ip, command)
                
                if success:
                    self.broken_services.add(f"{level}:{target}")
                    success_count += 1
            
            print(f"\n[+] Completed: {success_count}/{total_count} breaks triggered successfully")
            return success_count > 0
    
    def trigger_fix(self, level, target=None, team_number=None):
        """
        Trigger a fix for specific level and optionally specific target
        Args:
            level (str): Break level (e.g., 'lvl1', 'lvl2', 'lvl3', 'lvl4')
            target (str): Optional specific target IP or IP:port
            team_number (int): Optional team number used to replace `.x.` placeholders
        """
        if 'fixs' not in self.breaks_data:
            print("[!] No fixs section found in config\n")
            return False
        
        if level not in self.breaks_data['fixs']:
            print(f"[!] Level '{level}' not found. Available levels: {list(self.breaks_data['fixs'].keys())}\n")
            return False
        
        fixes = self.breaks_data['fixs'][level]
        
        if target:
            # Fix single target
            if target not in fixes:
                print(f"[!] Target '{target}' not found in level '{level}'\n")
                return False
            
            command = fixes[target]
            if not command:
                print(f"[!] No fix command defined for {target}\n")
                return False
            
            resolved_target = self.apply_team_to_target(target, team_number)
            ip = resolved_target.split(':')[0]
            
            print(f"[*] Triggering fix for {resolved_target}")
            print(f"[*] Command: {command}")
            
            if self.is_windows_command(command):
                print(f"[*] Detected Windows target, using TCP:443")
                success = self.send_windows_command(ip, command)
            else:
                print(f"[*] Detected Linux target, using UDP:5555")
                success = self.send_linux_command(ip, command)
            
            if success:
                self.broken_services.discard(f"{level}:{target}")
                print(f"[+] Successfully triggered fix for {resolved_target}\n")
            
            return success
        else:
            # Fix all targets in level
            print(f"[*] Triggering all fixes for level '{level}'\n")
            success_count = 0
            total_count = 0
            
            for target, command in fixes.items():
                if not command:
                    print(f"[!] Skipping {target} (no fix command defined)\n")
                    continue
                
                total_count += 1
                resolved_target = self.apply_team_to_target(target, team_number)
                ip = resolved_target.split(':')[0]
                
                print(f"\n[*] Triggering fix for {resolved_target}")
                print(f"[*] Command: {command}")
                
                if self.is_windows_command(command):
                    print(f"[*] Detected Windows target, using TCP:443")
                    success = self.send_windows_command(ip, command)
                else:
                    print(f"[*] Detected Linux target, using UDP:5555")
                    success = self.send_linux_command(ip, command)
                
                if success:
                    self.broken_services.discard(f"{level}:{target}")
                    success_count += 1
            
            print(f"\n[+] Completed: {success_count}/{total_count} fixes triggered successfully")
            return success_count > 0
    
class break_management:
    """UI-facing API used by main.py."""

    def __init__(self, config_file='BreakLevels.json', default_level='lvl3', service_keys=None, service_target_map=None):
        self.manager = BreakManager(config_file=config_file)
        available_levels = list(self.manager.breaks_data.get('breaks', {}).keys())
        if default_level in available_levels:
            self.level = default_level
        elif available_levels:
            self.level = available_levels[0]
        else:
            self.level = None

        level_breaks = self.manager.breaks_data.get('breaks', {}).get(self.level, {}) if self.level else {}
        self.service_targets = list(level_breaks.keys())
        self.service_keys = list(service_keys) if service_keys else []
        self.service_target_map = dict(service_target_map) if service_target_map else {}

        # Validate explicit mappings early to avoid silent misrouting.
        if self.level and self.service_target_map:
            missing_targets = [
                target for target in self.service_target_map.values()
                if target and target not in level_breaks
            ]
            if missing_targets:
                print(f"[!] Warning: mapped targets missing in level '{self.level}': {sorted(set(missing_targets))}")

    def get_service_names(self):
        if self.service_keys:
            return self.service_keys
        if not self.level:
            return []
        return list(self.manager.breaks_data.get('breaks', {}).get(self.level, {}).keys())

    def _resolve_target(self, service_idx):
        """Resolve selected UI service index to a concrete BreakLevels target."""
        if self.service_keys and self.service_target_map:
            if service_idx < 0 or service_idx >= len(self.service_keys):
                return None
            service_key = self.service_keys[service_idx]
            return self.service_target_map.get(service_key)

        if service_idx < 0 or service_idx >= len(self.service_targets):
            return None
        return self.service_targets[service_idx]

    def trigger_break(self, team_idx, service_idx):
        if self.level is None:
            print("[!] No break levels available")
            return False
        target = self._resolve_target(service_idx)
        if target is None:
            print(f"[!] Invalid service index: {service_idx}")
            return False
        if not target:
            if self.service_keys and service_idx < len(self.service_keys):
                print(f"[!] No target mapping defined for service '{self.service_keys[service_idx]}'")
            else:
                print(f"[!] No target mapping defined for service index {service_idx}")
            return False
        team_number = team_idx + 1
        return self.manager.trigger_break(self.level, target, team_number=team_number)

    def trigger_unbreak(self, team_idx, service_idx):
        if self.level is None:
            print("[!] No break levels available")
            return False
        target = self._resolve_target(service_idx)
        if target is None:
            print(f"[!] Invalid service index: {service_idx}")
            return False
        if not target:
            if self.service_keys and service_idx < len(self.service_keys):
                print(f"[!] No target mapping defined for service '{self.service_keys[service_idx]}'")
            else:
                print(f"[!] No target mapping defined for service index {service_idx}")
            return False
        team_number = team_idx + 1
        return self.manager.trigger_fix(self.level, target, team_number=team_number)
