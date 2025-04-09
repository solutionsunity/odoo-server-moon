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

# Check Python version compatibility for venv options
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

# Check if Python version is 3.12 or newer for venv creation options
USE_SYSTEM_SITE_PACKAGES=$($PYTHON_CMD -c "import sys; print('yes' if (sys.version_info.major > 3 or (sys.version_info.major == 3 and sys.version_info.minor >= 12)) else 'no')")

echo "Python version $PYTHON_VERSION_INFO detected. Compatible version."

# Create or update virtual environment
if [ ! -d "$INSTALL_DIR/venv" ]; then
  echo "Creating virtual environment..."
  if [ "$USE_SYSTEM_SITE_PACKAGES" = "yes" ]; then
    echo "Using --system-site-packages flag for Python $PYTHON_VERSION_INFO compatibility"
    $PYTHON_CMD -m venv --system-site-packages "$INSTALL_DIR/venv"
  else
    $PYTHON_CMD -m venv "$INSTALL_DIR/venv"
  fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$INSTALL_DIR/venv/bin/activate"

# Install any new dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Update the service file if needed
if [ -f "/etc/systemd/system/odoo-dev-monitor.service" ] && [ -f "$INSTALL_DIR/scripts/odoo-dev-monitor.service" ]; then
  echo "Updating service file..."
  cp "$INSTALL_DIR/scripts/odoo-dev-monitor.service" /etc/systemd/system/

  # Update the WorkingDirectory in the service file
  sed -i "s|WorkingDirectory=.*|WorkingDirectory=$INSTALL_DIR|g" /etc/systemd/system/odoo-dev-monitor.service

  # Update the User in the service file to the current user
  CURRENT_USER=$(logname)
  sed -i "s|User=.*|User=$CURRENT_USER|g" /etc/systemd/system/odoo-dev-monitor.service

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
