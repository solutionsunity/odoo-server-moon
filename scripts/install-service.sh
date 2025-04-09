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

# Detect Python command (python or python3)
PYTHON_CMD="python3"
PIP_CMD="pip3"

# Check if python command exists and is Python 3.x
if command -v python &> /dev/null; then
  if python -c "import sys; sys.exit(0 if sys.version_info.major == 3 else 1)" &> /dev/null; then
    PYTHON_CMD="python"
    PIP_CMD="pip"
  fi
fi

# Verify the selected Python command exists
if ! command -v $PYTHON_CMD &> /dev/null; then
  echo "Error: $PYTHON_CMD command not found. Please install Python 3.7 or newer."
  exit 1
fi

# Check if pip command exists
if ! command -v $PIP_CMD &> /dev/null; then
  echo "Error: $PIP_CMD command not found. Please install pip for Python 3."
  exit 1
fi

# Check Python version compatibility
echo "Checking Python version compatibility..."
PYTHON_VERSION_INFO=$($PYTHON_CMD -c "import sys; major=sys.version_info.major; minor=sys.version_info.minor; print(f'{major}.{minor}')")
PYTHON_VERSION_CHECK=$($PYTHON_CMD -c "import sys; exit(1 if (sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 7)) else 0)")
PYTHON_VERSION_CHECK_EXIT=$?

if [ $PYTHON_VERSION_CHECK_EXIT -ne 0 ]; then
  echo "Error: Python version $PYTHON_VERSION_INFO is not supported."
  echo "This application requires Python 3.7 or newer."
  echo "Please upgrade your Python installation."
  exit 1
fi

echo "Python version $PYTHON_VERSION_INFO detected. Compatible version."

# Install dependencies
echo "Installing dependencies..."
$PIP_CMD install -r "$SCRIPT_DIR/requirements.txt"

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
