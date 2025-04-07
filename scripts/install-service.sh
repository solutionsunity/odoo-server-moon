#!/bin/bash

# Odoo Dev Server Monitoring Tool Service Installer
# This script installs the tool as a systemd service

# Exit on error
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing from directory: $SCRIPT_DIR"

# Install dependencies
echo "Installing dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

# Set correct permissions
echo "Setting permissions..."
chown -R $(logname):$(logname) "$SCRIPT_DIR"

# Copy service file
echo "Installing systemd service..."
cp "$SCRIPT_DIR/scripts/odoo-dev-monitor.service" /etc/systemd/system/

# Update the WorkingDirectory in the service file
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|g" /etc/systemd/system/odoo-dev-monitor.service

# Update the User in the service file to the current user
sed -i "s|User=gbadmin|User=$(logname)|g" /etc/systemd/system/odoo-dev-monitor.service

# Reload systemd
systemctl daemon-reload

# Enable the service to start on boot
systemctl enable odoo-dev-monitor.service

# Start the service
echo "Starting service..."
systemctl start odoo-dev-monitor.service

# Check status
echo "Service status:"
systemctl status odoo-dev-monitor.service

echo ""
echo "Installation complete! The Odoo Dev Server Monitoring Tool is now running as a service."
echo "You can access it at: http://localhost:8008"
echo ""
echo "Service management commands:"
echo "  - Check status: sudo systemctl status odoo-dev-monitor"
echo "  - Start service: sudo systemctl start odoo-dev-monitor"
echo "  - Stop service: sudo systemctl stop odoo-dev-monitor"
echo "  - Restart service: sudo systemctl restart odoo-dev-monitor"
echo "  - View logs: sudo journalctl -u odoo-dev-monitor -f"
