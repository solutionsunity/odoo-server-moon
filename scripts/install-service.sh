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

# Source common functions
if [ -f "$SCRIPT_DIR/common.sh" ]; then
    source "$SCRIPT_DIR/common.sh"
else
    echo "Error: common.sh not found. Please run this script from the repository directory."
    exit 1
fi

# Detect Python command and check version
detect_python_command || exit 1
check_python_version || exit 1

# Setup Python environment (detect, check version, create venv, install dependencies)
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
setup_python_environment "$PARENT_DIR/venv" "$SCRIPT_DIR/requirements.txt" || exit 1

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

# Update the ExecStart path to use the virtual environment
sed -i "s|ExecStart=.*|ExecStart=$SCRIPT_DIR/venv/bin/python -m app.main|g" /etc/systemd/system/odoo-dev-monitor.service

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
