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

# Check if Python version is 3.12 or newer for venv creation options
USE_SYSTEM_SITE_PACKAGES=$($PYTHON_CMD -c "import sys; print('yes' if (sys.version_info.major > 3 or (sys.version_info.major == 3 and sys.version_info.minor >= 12)) else 'no')")

echo "Python version $PYTHON_VERSION_INFO detected. Compatible version."

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

# Create virtual environment if it doesn't exist
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

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

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
