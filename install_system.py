import subprocess, hashlib, base64, os


class Installer:
    def __init__(self, app, root: str, settings: dict):
        self.app = app
        self.root = root
        self.sett = settings

    def mount_part(self, dev: str, path: str):
        self.app.logger.log(f"  Mounting {dev} at {path}.")
        subprocess.run(["mkdir", "-p", path])
        subprocess.run(["mount", dev, path])

    def install_base(self):
        subprocess.run(["pacstrap", self.root, "base linux linux-firmware nano networkmanager grub efibootmgr sudo"])

    def gen_fstab(self):
        with open(f"{self.root}/etc/fstab", "a") as f:
            subprocess.run(["genfstab", "-U", self.root], stdout=f)

    def sys_config(self):
        self.app.logger.log(f"  Setting timezone...")
        self.crexe(f"ln -sf /usr/share/zoneinfo/{self.sett['location']['timezone']} /etc/localtime")
        self.app.logger.log(f"  Setting language...")
        self.crexe(f"echo \"LANG={self.sett['location']['language']}\" > /etc/locale.conf")
        self.crexe(f"sed -i 's/^#\\({self.sett['location']['language']} UTF-8\\)/\\1/' /etc/locale.gen")
        self.app.logger.log(f"  Setting hostname...")
        self.crexe(f"echo \"{self.sett['hostname']}\" > /etc/hostname")
        self.app.logger.log(f"  Enabling multilib...")
        self.crexe("sed -i '/\\[multilib\\]/,/Include/s/^#//' /etc/pacman.conf")

        self.app.logger.log(f"  Regenerating language config...")
        self.crexe("locale-gen")
        self.app.logger.log(f"  Synchronizing hardware clock...")
        self.crexe("hwclock --systohc")

    def bootloader(self):
        self.app.logger.log(f"  Installing grub...")
        self.crexe("grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=CosmicOS")
        self.app.logger.log(f"  Creating grub config...")
        self.crexe("grub-mkconfig -o /boot/grub/grub.cfg")

    def enable_stuff(self):
        self.app.logger.log(f"  Enabling Network Manager...")
        self.crexe("systemctl enable NetworkManager")
        self.app.logger.log(f"  Enabling SSH")
        self.crexe("systemctl enable sshd")

    def add_users(self):
        # Hash password
        self.app.logger.log(f"  Hashing password...")
        salt = base64.b64encode(os.urandom(6)).decode('utf-8')
        hashed_pw = f"$6${salt}${hashlib.sha512((self.sett['users']['pass'] + salt).encode()).hexdigest()}"
        
        # Add user
        self.app.logger.log(f"  Creating user...")
        self.crexe(f"useradd -m -p {hashed_pw} -s /bin/bash {self.sett['users']['name']}")

        # Enable wheel group
        self.app.logger.log(f"  Enabling wheel group...")
        self.crexe("sed -i 's/^# %wheel ALL=(ALL) ALL/%wheel ALL=(ALL) ALL/' /etc/sudoers")
        
        # If user is sudo, add him to the wheel group
        if self.sett['users']['sudo']:
            self.app.logger.log(f"    Adding user to wheel...")
            self.crexe(f"usermod -aG wheel {self.sett['users']['name']}")

        # Set root password
        self.app.logger.log(f"  Setting root password...")
        try:
            proc = subprocess.Popen(
                ["arch-chroot", self.root, "bash", "-c", "passwd root"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            proc.communicate(f"{self.sett['users']['root_pass']}\n{self.sett['users']['root_pass']}\n")
        except Exception as e:
            print(f"Error: {e}")

    def install_desktop(self):
        desktops = {
            'gnome': [
                "gnome-app-list", "gnome-backgrounds", "gnome-calculator", "gnome-characters", "gnome-connections", "gnome-control-center",
                "gnome-desktop",  "gnome-desktop-4", "gnome-desktop-common", "gnome-disk-utility", "gdm", "gnome-font-viewer", "gnome-keybindings",
                "gnome-keyring", "gnome-logs", "gnome-session", "gnome-settings-daemon", "gnome-shell", "gnome-shell-extensions",
                "gnome-shell-extension-pop-shell", "gnome-software", "gnome-system-monitor", "gnome-terminal", "gnome-themes-extra", "gnome-tweaks",
                "xdg-desktop-portal-gnome", "nautilus"
            ],
            'plasma': [
                "aurorae", "bluedevil", "breeze", "breeze-gtk", "breeze-plymouth", "discover", "drkonqi", "flatpak-kcm", "kactivitymanagerd",
                "kde-cli-tools", "kde-gtk-config", "kdecoration", "kdeplasma-addons", "kgamma", "kglobalacceld", "kinfocenter", "kmenuedit",
                "kpipewire", "krdp", "kscreen", "kscreenlocker", "ksshaskpass", "ksystemstats", "kwayland", "kwin", "kwin-x11", "kwrited",
                "layer-shell-qt", "libkscreen", "libksysguard", "libplasma", "milou", "ocean-sound-theme", "oxygen", "oxygen-sounds",
                "plasma-activities", "plasma-activities-stats", "plasma-browser-integration", "plasma-desktop", "plasma-disks", "plasma-firewall",
                "plasma-integration", "plasma-nm", "plasma-pa", "plasma-sdk", "plasma-systemmonitor", "plasma-thunderbolt", "plasma-vault",
                "plasma-workspace", "plasma-workspace-wallpapers", "plasma5support", "plymouth-kcm", "polkit-kde-agent", "powerdevil",
                "print-manager", "qqc2-breeze-style", "sddm", "sddm-kcm", "spectacle", "systemsettings", "xdg-desktop-portal-kde"
            ],
            'mate': [
                "caja", "marco", "mate-backgrounds", "mate-control-center", "mate-desktop", "mate-icon-theme", "mate-menus", "mate-panel",
                "mate-notification-daemon", "mate-polkit", "mate-session-manager", "mate-settings-daemon", "mate-themes", "mate-user-guide"
            ],
            'hypr': [
                "hyprland", "waybar", "rofi", "hyprpaper", "sddm", "hyprcursor", "hyprgraphics", "hypridle", "hyprland-qt-support", "hyprland-qtutils",
                "hyprlang", "hyprlock", "hyprshot", "hyprutils"
            ]
        }
        others = [
            "firefox", "git", "htop", "btop", "7zip", "adwaita-cursors", "adwaita-fonts", "adwaita-icon-theme", "adwaita-icon-theme-legacy", "amd-ucode", "amdvlk",
            "ark", "audacity", "base-devel", "blender", "bzip2", "clang", "cmake", "cmatrix", "curl", "dav1d", "dconf", "ddrescue", "discord", "dosbox", "exfatprogs",
            "ffmpeg", "filezilla", "firefox", "flatpak", "fluidsynth", "gcc",  "gimp", "git", "glad", "glew", "glfw", "glibc", "glm", "go", "gparted", "gradle", "grep",
            "gtk2", "gtk3", "gtk4", "gzip", "heimdall", "hexedit", "hwinfo", "imagemagick", "imath", "inkscape", "jdk-openjdk", "kdenlive", "kitty", "less", "lm_sensors",
            "lua", "mousepad", "nano", "nasm", "ninja", "openal", "openssh", "parted", "pavucontrol", "pipewire", "pipewire-audio", "python", "python-numpy",
            "python-opengl", "python-pillow", "python-pip", "python-pyqt6", "qt5", "qt5ct", "qt6", "qt6ct", "sdl2_image", "sdl2_mixer", "sdl2_ttf", "sdl3", "steam",
            "thunar", "ttf-fira-code", "ttf-firacode-nerd", "unzip", "vlc", "wacomtablet", "wget", "wine", "wl-clipboard", "woff2", "zsh", "zsh-autosuggestions",
            "zsh-completions", "zsh-syntax-highlighting"
        ]
        if self.sett['de'] not in desktops.keys():
            raise ValueError("Wrong desktop environment. Choose from 'gnome', 'plasma', 'mate' and 'hypr'.")

        self.app.logger.log(f"  Installing desktop environment...")
        self.crexe(f"pacman -Syu --noconfirm {' '.join(desktops[self.sett['de']])}")
        self.app.logger.log(f"  Installing other packages...")
        self.crexe(f"pacman -Syu --noconfirm {' '.join(others)}")

    def config_paru(self):
        self.app.logger.log(f"  Downloading paru...")
        self.crexe("mkdir -p /tmp/paru")
        self.crexe("git clone https://aur.archlinux.org/paru.git /tmp/paru")
        self.crexe("cd /tmp/paru")

        # Create temporary user for the build
        self.app.logger.log(f"  Creating temporary user (for safety)...")
        subprocess.run(["useradd", "-M", "-N", "-R", self.root, "-s", "/usr/bin/bash", "builder"])
        self.app.logger.log(f"  Installing paru...")
        self.crexe("runuser -l builder -c 'cd /tmp/paru && makepkg -si --noconfirm --needed'")
        self.crexe("cd /")
        self.crexe("rm -rf /tmp/paru")

        self.app.logger.log(f"  Installing AUR apps...")
        paru_apps = [
            "minecraft-launcher", "f3", "freeimage", "heroic-games-launcher", "minecraft-launcher",
            "multimc-bin", "nbtexplorer-bin", "neofetch", "visual-studio-code-bin", "wl-screenrec"
        ]
        self.crexe(f"runuser -l builder -c 'paru -S --noconfirm --needed {"".join(paru_apps)}'")

        # Delete temporary user
        self.app.logger.log(f"  Removing temporary user...")
        subprocess.run(["userdel", "-f", "-r", "-R", self.root])

    def crexe(self, cmd: str):
        subprocess.run(["arch-chroot", self.root, "bash", "-c", cmd], check=True)

    def install(self):
        # Mount partitions
        self.app.logger.log(f"[1/10] Mounting partitions...")
        self.mount_part(self.sett['parts'][0]['part'], f"{self.root}{self.sett['parts'][0]['path']}")
        self.mount_part(self.sett['parts'][1]['part'], f"{self.root}{self.sett['parts'][1]['path']}")
        self.mount_part(self.sett['parts'][2]['part'], f"{self.root}{self.sett['parts'][2]['path']}")

        # Install system
        self.app.logger.log(f"[2/10] Installing base system...")
        self.install_base()

        self.app.logger.log(f"[3/10] Generating F-stab...")
        self.gen_fstab()

        # Configure system
        self.app.logger.log(f"[4/10] Configuring system settings...")
        self.sys_config()

        # Bootloader setup
        self.app.logger.log(f"[5/10] Installing bootloader...")
        self.bootloader()

        # Enable network and ssh
        self.app.logger.log(f"[6/10] Enabling daemons...")
        self.enable_stuff()

        # Add user
        self.app.logger.log(f"[7/10] Creating users...")
        self.add_users()

        # Delete any user credentials before handling packages (especially AUR)
        self.sett['users'] = {}

        # Install desktop
        self.app.logger.log(f"[8/10] Installing packages... (this might take a while)")
        self.install_desktop()

        # Install AUR helper
        self.app.logger.log(f"[9/10] Installing AUR helper...")
        self.config_paru()

        # Unmount partitions
        self.app.logger.log(f"[10/10] Unmounting partitions...")
        subprocess.run(["sync"])
        subprocess.run(["umount", "-R", self.root], check=False)

        self.app.logger.log(f"Installation complete!")