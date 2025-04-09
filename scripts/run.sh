#!/bin/bash

# Start the Odoo Dev Server Monitoring Tool

# Create logs directory if it doesn't exist
mkdir -p logs

# Get script directory and parent directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

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

# Check if virtual environment exists and use it if available
VENV_DIR="$PARENT_DIR/venv"

if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
    # Activate virtual environment
    activate_virtual_environment "$VENV_DIR" || exit 1

    # Install dependencies if not already installed
    install_dependencies "$PARENT_DIR/requirements.txt" || exit 1

    # Start the application
    echo "Starting Odoo Dev Server Monitoring Tool..."
    python -m app.main
else
    # Try to create virtual environment
    echo "Virtual environment not found. Attempting to create one..."
    if create_virtual_environment "$VENV_DIR" "$USE_SYSTEM_SITE_PACKAGES" && \
       activate_virtual_environment "$VENV_DIR" && \
       install_dependencies "$PARENT_DIR/requirements.txt"; then
        # Start the application with venv
        echo "Starting Odoo Dev Server Monitoring Tool..."
        python -m app.main
    else
        # Fall back to system Python if venv creation fails
        echo "Warning: Could not create or use virtual environment. Using system Python..."
        install_dependencies "$PARENT_DIR/requirements.txt" || exit 1

        # Start the application
        echo "Starting Odoo Dev Server Monitoring Tool..."
        $PYTHON_CMD -m app.main
    fi
fi
