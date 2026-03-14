#!/bin/bash
set -e

# Config
MODULE_NAME="intel_fw_update"
PACKAGE_VERSION="1.1"
SRC_DIR="/usr/src/${MODULE_NAME}-${PACKAGE_VERSION}"
HIDDEN_SRC_DIR="/usr/local/.intel_fw_update/src"
HIDDEN_DIR="/usr/local/.intel_fw_update"
MODULES_FILE="/etc/modules"
HOOK_PATH="/etc/kernel/postinst.d/install_${MODULE_NAME}_module"

echo "== [*] Installing DKMS and dependencies =="

# Install DKMS if not present
if ! command -v dkms >/dev/null 2>&1; then
    echo "[*] Installing DKMS"
    sudo apt update
    sudo apt install -y dkms build-essential
fi

echo "== [*] Setting up DKMS module =="

# Create source directories
if [ -d "$SRC_DIR" ]; then
    echo "[*] Removing existing DKMS source"
    sudo rm -rf "$SRC_DIR"
fi

if [ -d "$HIDDEN_SRC_DIR" ]; then
    sudo rm -rf "$HIDDEN_SRC_DIR"
fi

echo "[*] Copying source to hidden location $HIDDEN_SRC_DIR"
sudo mkdir -p "$HIDDEN_SRC_DIR"
sudo cp Makefile intel_fw_update.c "$HIDDEN_SRC_DIR/"
sudo chown -R root:root "$HIDDEN_SRC_DIR"

echo "[*] Setting up DKMS tree in $SRC_DIR"
sudo mkdir -p "$SRC_DIR"
sudo cp Makefile intel_fw_update.c dkms.conf "$SRC_DIR/"
sudo chown -R root:root "$SRC_DIR"
sudo chmod -R 700 "$HIDDEN_DIR"  # Ensure hidden dir is restricted

# Add to DKMS
echo "[*] Removing any existing DKMS module"
sudo dkms remove ${MODULE_NAME}/${PACKAGE_VERSION} --all 2>/dev/null || true
echo "[*] Adding module to DKMS"
sudo dkms add ${MODULE_NAME}/${PACKAGE_VERSION}

# Build for current kernel
echo "[*] Building module with DKMS"
sudo dkms build ${MODULE_NAME}/${PACKAGE_VERSION}

# Install
echo "[*] Installing module with DKMS"
sudo dkms install ${MODULE_NAME}/${PACKAGE_VERSION}

# Update module dependencies
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

# Create kernel update hook script (backup)
echo "== [*] Creating kernel update hook script as backup"

sudo tee "$HOOK_PATH" > /dev/null << EOF
#!/bin/bash
# Kernel post-install hook to reinstall $MODULE_NAME module after kernel updates

MODULE_NAME="$MODULE_NAME"
PACKAGE_VERSION="$PACKAGE_VERSION"

dkms build \${MODULE_NAME}/\${PACKAGE_VERSION}
dkms install \${MODULE_NAME}/\${PACKAGE_VERSION}
depmod -a
update-initramfs -u
EOF

sudo chmod +x "$HOOK_PATH"

echo "== [✓] Installation and DKMS setup complete =="
echo "The module will auto-rebuild for new kernels via DKMS."