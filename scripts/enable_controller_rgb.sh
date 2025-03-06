#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi
# This script adds udev rules to allow non-root users to control the RGB LEDs on a DualShock 4 controller.
# It overwrites the necessary rules to the /etc/udev/rules.d/99-ds4-led.rules file.
# The rules set the permissions for the red, green, and blue LED subsystems to be accessible by all users.
#
# After adding the rules, the script reloads the udev rules and triggers them to apply the changes immediately.

read -p "Write udev rules for DualShock 4 controller LEDs? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 1
fi

cat <<EOF > /etc/udev/rules.d/99-ds4-led.rules
SUBSYSTEM=="leds", KERNEL=="input*:red", RUN+="/bin/chmod a+w /sys/class/leds/%k/brightness"
SUBSYSTEM=="leds", KERNEL=="input*:green", RUN+="/bin/chmod a+w /sys/class/leds/%k/brightness"
SUBSYSTEM=="leds", KERNEL=="input*:blue", RUN+="/bin/chmod a+w /sys/class/leds/%k/brightness"
EOF

# Reload udev rules
udevadm control --reload-rules
udevadm trigger