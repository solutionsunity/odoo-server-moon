#!/bin/bash

# Odoo Dev Server Monitoring Tool Service Uninstaller
# This script removes the systemd service

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

echo "Stopping service..."
systemctl stop odoo-dev-monitor.service || true

echo "Disabling service..."
systemctl disable odoo-dev-monitor.service || true

echo "Removing service file..."
rm -f /etc/systemd/system/odoo-dev-monitor.service

echo "Reloading systemd..."
systemctl daemon-reload

echo ""
echo "Uninstallation complete! The Odoo Dev Server Monitoring Tool service has been removed."
echo "The application files remain intact and can be run manually using ./run.sh"
