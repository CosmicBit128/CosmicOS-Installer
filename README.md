# CosmicOS Installer

A graphical installer for **CosmicOS**, built with Python and PyQt6.
It provides a clean step-by-step interface for configuring location, partitions, users, and desktop environments before installing the system.

---

## Overview

The installer guides you through several stages:

1. **Welcome** – basic introduction and logo
2. **License** – shows the project’s MIT (modified) license
3. **Location** – select language, keyboard layout, and timezone
4. **Partitioning** – choose partitions and optionally launch GParted
5. **Account setup** – create a user account and set passwords
6. **General setup** – pick desktop environment, hostname, and UEFI options
7. **Summary** – review your configuration
8. **Installation** – runs the actual system installation
9. **Finish** – confirms that the process completed successfully

---

## Features

* Modern **PyQt6** interface
* Built-in **license viewer**
* **Threaded installation** support for a responsive UI
* **Live log output** during installation
* Desktop environment choices: GNOME, KDE Plasma, MATE, and Hyprland
* Integration with Arch Linux tools (`pacstrap`, `genfstab`, `grub-install`, etc.)

---

## Requirements

* Python 3.10 or newer
* PyQt6 installed (`pip install PyQt6`)
* Running environment with Arch-based live system utilities:

  * `pacstrap`, `genfstab`, `arch-chroot`, `grub-install`, `systemctl`, etc.

---

## Usage

```bash
python3 main.py
```

### Note:
> If you only want to test the interface, it’s strongly recommended to run inside a **virtual machine** to avoid writing to real disks.
