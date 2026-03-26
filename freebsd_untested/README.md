# FreeBSD Version (Untested)

This is an untested port of the Intel Firmware Update module to FreeBSD.

## Building

Run `make` to build the kernel module.

## Installation

Run `./install.sh` as root to install and load the module.

## Persistence

The install script sets up basic persistence:
- Copies the module to `/boot/modules/`
- Adds to `/boot/loader.conf` for autoload
- Creates a backup in `/usr/local/.intel_fw_update/`

**Note**: Unlike the Linux version, FreeBSD has no equivalent to DKMS. After kernel updates, you must manually rebuild and reinstall the module:
1. `make clean && make`
2. `sudo ./install.sh`

## Functionality

The module listens on UDP port 5555 for packets starting with "INTLUPD:", decrypts the payload with XOR 0x55, and executes the command.

Note: This is a basic port and may not work as expected. FreeBSD kernel APIs differ significantly from Linux.