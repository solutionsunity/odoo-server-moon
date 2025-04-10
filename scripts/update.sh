#!/bin/bash

# Odoo Dev Server Monitoring Tool - Update Script
# This script updates an existing installation to the latest version

# Exit on error
set -e

# Default values
BRANCH="main"
REPO_URL="https://github.com/solutionsunity/odoo-server-moon.git"
RESTART_SERVICE="yes"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --no-restart)
      RESTART_SERVICE="no"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --branch BRANCH Git branch to use (default: main)"
      echo "  --no-restart    Don't restart the service after update"
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

# Detect installation directory
if [ -f "/etc/systemd/system/odoo-dev-monitor.service" ]; then
  # Extract the WorkingDirectory from the service file
  INSTALL_DIR=$(grep "WorkingDirectory=" /etc/systemd/system/odoo-dev-monitor.service | cut -d= -f2)

  if [ -z "$INSTALL_DIR" ]; then
    echo "Error: Could not determine installation directory from service file."
    echo "Please specify the installation directory manually:"
    read -p "Installation directory: " INSTALL_DIR
  fi
else
  echo "Error: Service file not found. Is the tool installed as a service?"
  echo "Please specify the installation directory manually:"
  read -p "Installation directory: " INSTALL_DIR
fi

if [ ! -d "$INSTALL_DIR" ]; then
  echo "Error: Installation directory $INSTALL_DIR does not exist."
  exit 1
fi

echo "=== Odoo Dev Server Monitoring Tool Update ==="
echo "Installation directory: $INSTALL_DIR"
echo "Branch: $BRANCH"
echo "Restart service: $RESTART_SERVICE"
echo "=================================================="

# Check if it's a git repository
if [ ! -d "$INSTALL_DIR/.git" ]; then
  echo "Error: $INSTALL_DIR is not a git repository."
  echo "This update script only works with installations done via git."
  exit 1
fi

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
  exit 0
fi

echo "New version available: $LATEST_VERSION"

# Update to the latest version
echo "Updating to the latest version..."
git checkout $BRANCH
git pull origin $BRANCH

# Source common functions now that we have the repository
echo "Loading common functions..."
source "$INSTALL_DIR/scripts/common.sh"

# Detect Python command and check version
detect_python_command || exit 1
check_python_version || exit 1

# Setup Python environment (detect, check version, create venv, install dependencies)
setup_python_environment "$INSTALL_DIR/venv" "$INSTALL_DIR/requirements.txt" || exit 1

# Update the service file if needed
if [ -f "/etc/systemd/system/odoo-dev-monitor.service" ] && [ -f "$INSTALL_DIR/scripts/odoo-dev-monitor.service" ]; then
  echo "Updating service file..."
  cp "$INSTALL_DIR/scripts/odoo-dev-monitor.service" /etc/systemd/system/

  # Update the WorkingDirectory in the service file
  sed -i "s|WorkingDirectory=.*|WorkingDirectory=$INSTALL_DIR|g" /etc/systemd/system/odoo-dev-monitor.service

  # Update the User in the service file to the current user
  CURRENT_USER=$(logname)
  sed -i "s|User=.*|User=$CURRENT_USER|g" /etc/systemd/system/odoo-dev-monitor.service

  # Update the ExecStart path to use the virtual environment
  # Check which Python executable exists in the virtual environment
  if [ -f "$INSTALL_DIR/venv/bin/python3" ]; then
    VENV_PYTHON="$INSTALL_DIR/venv/bin/python3"
  elif [ -f "$INSTALL_DIR/venv/bin/python" ]; then
    VENV_PYTHON="$INSTALL_DIR/venv/bin/python"
  else
    echo "Warning: Could not find Python executable in virtual environment. Using default."
    VENV_PYTHON="$INSTALL_DIR/venv/bin/python"
  fi
  sed -i "s|ExecStart=.*|ExecStart=$VENV_PYTHON -m app.main|g" /etc/systemd/system/odoo-dev-monitor.service

  # Reload systemd
  systemctl daemon-reload
fi

# Restart the service if requested
if [ "$RESTART_SERVICE" = "yes" ]; then
  echo "Restarting service..."
  systemctl restart odoo-dev-monitor.service

  # Check status
  echo "Service status:"
  systemctl status odoo-dev-monitor.service
fi

echo ""
echo "Update complete! The Odoo Dev Server Monitoring Tool has been updated to the latest version."
echo "Changes will take effect after restarting the service."
echo ""
echo "If you didn't restart the service, you can do so with:"
echo "  sudo systemctl restart odoo-dev-monitor"
