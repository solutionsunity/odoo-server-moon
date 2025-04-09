#!/bin/bash

# Start the Odoo Dev Server Monitoring Tool

# Create logs directory if it doesn't exist
mkdir -p logs

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
PYTHON_VERSION_CHECK=$($PYTHON_CMD -c "import sys; major=sys.version_info.major; minor=sys.version_info.minor; print(f'{major}.{minor}'); exit(1 if (major < 3 or (major == 3 and minor < 7)) else 0)")
PYTHON_VERSION_CHECK_EXIT=$?

if [ $PYTHON_VERSION_CHECK_EXIT -ne 0 ]; then
    echo "Error: Python version $PYTHON_VERSION_CHECK is not supported."
    echo "This application requires Python 3.7 or newer."
    echo "Please upgrade your Python installation."
    exit 1
fi

echo "Python version $PYTHON_VERSION_CHECK detected. Compatible version."

# Check if virtual environment exists and use it if available
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PARENT_DIR/venv"

if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
    echo "Using virtual environment..."
    source "$VENV_DIR/bin/activate"

    # Install dependencies if not already installed
    echo "Checking dependencies..."
    pip install -r "$PARENT_DIR/requirements.txt"

    # Start the application
    echo "Starting Odoo Dev Server Monitoring Tool..."
    python -m app.main
else
    # Install dependencies if not already installed
    echo "Checking dependencies..."
    $PIP_CMD install -r "$PARENT_DIR/requirements.txt"

    # Start the application
    echo "Starting Odoo Dev Server Monitoring Tool..."
    $PYTHON_CMD -m app.main
fi
