#!/bin/bash

# Odoo Dev Server Monitoring Tool - Complete Uninstaller
# This script removes the tool completely from the system

# Exit on error
set -e

# Default values
REMOVE_FILES="ask"  # Options: yes, no, ask

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --remove-files)
      REMOVE_FILES="yes"
      shift
      ;;
    --keep-files)
      REMOVE_FILES="no"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --remove-files  Remove all application files (default: ask)"
      echo "  --keep-files    Keep application files, only remove service"
      echo "  --help          Show this help message"
      exit 0
      ;;
    *)
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
  echo "Service file not found. Is the tool installed as a service?"
  echo "Please specify the installation directory manually:"
  read -p "Installation directory (default: /opt/odoo-server-moon): " INSTALL_DIR
  INSTALL_DIR=${INSTALL_DIR:-/opt/odoo-server-moon}
fi

echo "=== Odoo Dev Server Monitoring Tool Uninstallation ==="
echo "Installation directory: $INSTALL_DIR"
echo "=================================================="

# Stop and disable the service
echo "Stopping service..."
systemctl stop odoo-dev-monitor.service 2>/dev/null || true

echo "Disabling service..."
systemctl disable odoo-dev-monitor.service 2>/dev/null || true

echo "Removing service file..."
rm -f /etc/systemd/system/odoo-dev-monitor.service

echo "Reloading systemd..."
systemctl daemon-reload

# Ask about removing files if not specified
if [ "$REMOVE_FILES" = "ask" ]; then
  read -p "Do you want to remove all application files? (y/N): " RESPONSE
  if [[ "$RESPONSE" =~ ^[Yy]$ ]]; then
    REMOVE_FILES="yes"
  else
    REMOVE_FILES="no"
  fi
fi

# Remove application files if requested
if [ "$REMOVE_FILES" = "yes" ]; then
  if [ -d "$INSTALL_DIR" ]; then
    echo "Removing application files from $INSTALL_DIR..."
    rm -rf "$INSTALL_DIR"
    echo "Application files removed."
  else
    echo "Installation directory $INSTALL_DIR not found. Nothing to remove."
  fi
else
  echo "Application files have been kept at $INSTALL_DIR."
  echo "You can still run the application manually using $INSTALL_DIR/run.sh"
fi

echo ""
echo "Uninstallation complete! The Odoo Dev Server Monitoring Tool has been removed from your system."
if [ "$REMOVE_FILES" = "no" ]; then
  echo "To completely remove the application, delete the directory: $INSTALL_DIR"
fi
