#!/bin/bash

# Odoo Dev Server Monitoring Tool - Remote Installation Script
# This script downloads and installs the tool from GitHub

# Ensure we're running with bash
if [ -z "$BASH_VERSION" ]; then
  echo "This script must be run with bash. Please use: bash $0"
  exit 1
fi

# Exit on error
set -e

# Default values
INSTALL_DIR="/opt/odoo-server-moon"
BRANCH="main"
PORT="8008"
AUTO_START="yes"
REPO_URL="https://github.com/solutionsunity/odoo-server-moon.git"
UPDATE_EXISTING="yes"

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
    --no-update)
      UPDATE_EXISTING="no"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --dir DIR       Installation directory (default: /opt/odoo-server-moon)"
      echo "  --branch BRANCH Git branch to use (default: main)"
      echo "  --port PORT     Port to run the server on (default: 8008)"
      echo "  --no-start      Don't start the service after installation"
      echo "  --no-update     Don't update if already installed"
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

# Check if the tool is already installed
if [ -d "$INSTALL_DIR/.git" ]; then
  if [ "$UPDATE_EXISTING" = "yes" ]; then
    echo "Tool already installed at $INSTALL_DIR. Updating..."

    # Change to the installation directory
    cd "$INSTALL_DIR"

    # Save the current version for reference
    CURRENT_VERSION=$(git rev-parse HEAD)
    echo "Current version: $CURRENT_VERSION"

    # Stash any local changes
    echo "Stashing any local changes..."
    git stash

    # Fetch the latest changes
    echo "Fetching latest changes..."
    git fetch origin

    # Check if there are updates available
    LATEST_VERSION=$(git rev-parse origin/$BRANCH)
    if [ "$CURRENT_VERSION" == "$LATEST_VERSION" ]; then
      echo "Already up to date. No update needed."
    else
      echo "New version available: $LATEST_VERSION"

      # Update to the latest version
      echo "Updating to the latest version..."
      git checkout $BRANCH
      git pull origin $BRANCH
    fi
  else
    echo "Tool already installed at $INSTALL_DIR."
    echo "Use --no-update to skip this check or run the update script:"
    echo "  sudo $INSTALL_DIR/scripts/update.sh"
    exit 0
  fi
else
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
fi

# Update port in configuration if needed
if [ "$PORT" != "8008" ]; then
  echo "Updating port to $PORT in configuration..."
  sed -i "s/\"port\": 8008/\"port\": $PORT/g" config/config.json
fi

# Source common functions now that we have the repository
echo "Loading common functions..."
source "$INSTALL_DIR/scripts/common.sh"

# Detect Python command and check version
detect_python_command || exit 1
check_python_version || exit 1

# Setup Python environment (detect, check version, create venv, install dependencies)
setup_python_environment "$INSTALL_DIR/venv" "$INSTALL_DIR/requirements.txt" || exit 1

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
# Update the ExecStart path to use the virtual environment
sed -i "s|ExecStart=.*|ExecStart=$INSTALL_DIR/venv/bin/python -m app.main|g" /etc/systemd/system/odoo-dev-monitor.service

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
