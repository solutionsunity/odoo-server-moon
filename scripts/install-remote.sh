#!/bin/bash

# Odoo Dev Server Monitoring Tool - Remote Installation Script
# This script downloads and installs the tool from GitHub

# Exit on error
set -e

# Default values
INSTALL_DIR="/opt/odoo-server-moon"
BRANCH="main"
PORT="8008"
AUTO_START="yes"
REPO_URL="https://github.com/solutionsunity/odoo-server-moon.git"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --no-start)
      AUTO_START="no"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --dir DIR       Installation directory (default: /opt/odoo-server-moon)"
      echo "  --branch BRANCH Git branch to use (default: main)"
      echo "  --port PORT     Port to run the server on (default: 8008)"
      echo "  --no-start      Don't start the service after installation"
      echo "  --help          Show this help message"
      exit 0
      ;;
    *)
      # If no flag is specified, assume it's the branch
      if [[ "$1" != -* ]]; then
        BRANCH="$1"
      fi
      shift
      ;;
  esac
done

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Print installation details
echo "=== Odoo Dev Server Monitoring Tool Installation ==="
echo "Installation directory: $INSTALL_DIR"
echo "Branch: $BRANCH"
echo "Port: $PORT"
echo "Auto-start service: $AUTO_START"
echo "=================================================="

# Check for required tools
command -v git >/dev/null 2>&1 || { echo "Error: git is required but not installed. Please install git and try again."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required but not installed. Please install python3 and try again."; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "Error: pip3 is required but not installed. Please install pip3 and try again."; exit 1; }

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
  echo "Creating installation directory: $INSTALL_DIR"
  mkdir -p "$INSTALL_DIR"
fi

# Clone the repository
echo "Cloning repository from $REPO_URL (branch: $BRANCH)..."
git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"

# Change to the installation directory
cd "$INSTALL_DIR"

# Update port in configuration if needed
if [ "$PORT" != "8008" ]; then
  echo "Updating port to $PORT in configuration..."
  sed -i "s/\"port\": 8008/\"port\": $PORT/g" config/config.json
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Create logs directory if it doesn't exist
mkdir -p logs

# Set correct permissions
echo "Setting permissions..."
chown -R $(logname):$(logname) "$INSTALL_DIR"

# Install as a service
echo "Installing systemd service..."
cp scripts/odoo-dev-monitor.service /etc/systemd/system/

# Update the service file
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$INSTALL_DIR|g" /etc/systemd/system/odoo-dev-monitor.service
sed -i "s|User=gbadmin|User=$(logname)|g" /etc/systemd/system/odoo-dev-monitor.service

# Reload systemd
systemctl daemon-reload

# Enable the service to start on boot
systemctl enable odoo-dev-monitor.service

# Start the service if auto-start is enabled
if [ "$AUTO_START" = "yes" ]; then
  echo "Starting service..."
  systemctl start odoo-dev-monitor.service

  # Check status
  echo "Service status:"
  systemctl status odoo-dev-monitor.service
fi

echo ""
echo "Installation complete! The Odoo Dev Server Monitoring Tool is now installed."
echo "You can access it at: http://localhost:$PORT"
echo ""
echo "Service management commands:"
echo "  - Check status: sudo systemctl status odoo-dev-monitor"
echo "  - Start service: sudo systemctl start odoo-dev-monitor"
echo "  - Stop service: sudo systemctl stop odoo-dev-monitor"
echo "  - Restart service: sudo systemctl restart odoo-dev-monitor"
echo "  - View logs: sudo journalctl -u odoo-dev-monitor -f"
