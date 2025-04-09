#!/bin/bash

# Common functions for Odoo Dev Server Monitoring Tool scripts
# This file should be sourced by other scripts

# Detect Python command (python or python3)
detect_python_command() {
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
    return 1
  fi

  # Check if pip command exists
  if ! command -v $PIP_CMD &> /dev/null; then
    echo "Error: $PIP_CMD command not found. Please install pip for Python 3."
    return 1
  fi

  return 0
}

# Check Python version compatibility
check_python_version() {
  echo "Checking Python version compatibility..."
  PYTHON_VERSION_INFO=$($PYTHON_CMD -c "import sys; major=sys.version_info.major; minor=sys.version_info.minor; print(f'{major}.{minor}')")
  PYTHON_VERSION_CHECK=$($PYTHON_CMD -c "import sys; exit(1 if (sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 7)) else 0)")
  PYTHON_VERSION_CHECK_EXIT=$?

  if [ $PYTHON_VERSION_CHECK_EXIT -ne 0 ]; then
    echo "Error: Python version $PYTHON_VERSION_INFO is not supported."
    echo "This application requires Python 3.7 or newer."
    echo "Please upgrade your Python installation."
    return 1
  fi

  # Check if Python version is 3.12 or newer for venv creation options
  USE_SYSTEM_SITE_PACKAGES=$($PYTHON_CMD -c "import sys; print('yes' if (sys.version_info.major > 3 or (sys.version_info.major == 3 and sys.version_info.minor >= 12)) else 'no')")

  echo "Python version $PYTHON_VERSION_INFO detected. Compatible version."
  return 0
}

# Check if virtual environment tools are available
check_venv_tools() {
  # Check if python's built-in venv module is available
  if $PYTHON_CMD -c "import venv" &> /dev/null; then
    VENV_METHOD="builtin"
    return 0
  fi
  
  # Check if system venv package is installed
  PYTHON_VERSION_SHORT=$(echo $PYTHON_VERSION_INFO | cut -d. -f1-2)
  VENV_PACKAGE="python${PYTHON_VERSION_SHORT}-venv"
  
  if command -v dpkg &> /dev/null && dpkg -l | grep -q $VENV_PACKAGE; then
    VENV_METHOD="system"
    return 0
  fi
  
  # Check if virtualenv is installed via pip
  if $PIP_CMD list 2>/dev/null | grep -q virtualenv; then
    VENV_METHOD="pip"
    return 0
  fi
  
  # If we get here, no virtual environment tools are available
  VENV_METHOD="none"
  return 1
}

# Create virtual environment using the best available method
create_virtual_environment() {
  local venv_dir="$1"
  local use_system_site_packages="$2"
  
  # Check for available virtual environment tools
  check_venv_tools
  
  case $VENV_METHOD in
    "builtin")
      echo "Using built-in venv module to create virtual environment..."
      if [ "$use_system_site_packages" = "yes" ]; then
        $PYTHON_CMD -m venv --system-site-packages "$venv_dir"
      else
        $PYTHON_CMD -m venv "$venv_dir"
      fi
      ;;
    "system")
      echo "Using system venv package to create virtual environment..."
      if [ "$use_system_site_packages" = "yes" ]; then
        $PYTHON_CMD -m venv --system-site-packages "$venv_dir"
      else
        $PYTHON_CMD -m venv "$venv_dir"
      fi
      ;;
    "pip")
      echo "Using pip-installed virtualenv to create virtual environment..."
      if ! command -v virtualenv &> /dev/null; then
        echo "Installing virtualenv..."
        $PIP_CMD install virtualenv
      fi
      
      if [ "$use_system_site_packages" = "yes" ]; then
        virtualenv --system-site-packages "$venv_dir"
      else
        virtualenv "$venv_dir"
      fi
      ;;
    *)
      echo "Error: Virtual environment tools not found."
      echo "Please install one of the following:"
      echo "  - System package: sudo apt install $VENV_PACKAGE"
      echo "  - Pip package: $PIP_CMD install virtualenv"
      return 1
      ;;
  esac
  
  # Check if virtual environment was created successfully
  if [ ! -d "$venv_dir" ] || [ ! -f "$venv_dir/bin/activate" ]; then
    echo "Error: Failed to create virtual environment."
    return 1
  fi
  
  return 0
}

# Activate virtual environment
activate_virtual_environment() {
  local venv_dir="$1"
  
  if [ -d "$venv_dir" ] && [ -f "$venv_dir/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$venv_dir/bin/activate"
    return 0
  else
    echo "Error: Virtual environment not found at $venv_dir"
    return 1
  fi
}

# Install dependencies in the current environment
install_dependencies() {
  local requirements_file="$1"
  
  echo "Installing dependencies..."
  $PIP_CMD install -r "$requirements_file"
  return $?
}

# Setup Python environment (detect, check version, create venv if needed)
setup_python_environment() {
  local venv_dir="$1"
  local requirements_file="$2"
  
  # Detect Python command
  if ! detect_python_command; then
    return 1
  fi
  
  # Check Python version
  if ! check_python_version; then
    return 1
  fi
  
  # Create virtual environment if it doesn't exist
  if [ ! -d "$venv_dir" ] || [ ! -f "$venv_dir/bin/activate" ]; then
    echo "Creating virtual environment..."
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "yes" ]; then
      echo "Using --system-site-packages flag for Python $PYTHON_VERSION_INFO compatibility"
    fi
    
    if ! create_virtual_environment "$venv_dir" "$USE_SYSTEM_SITE_PACKAGES"; then
      return 1
    fi
  fi
  
  # Activate virtual environment
  if ! activate_virtual_environment "$venv_dir"; then
    return 1
  fi
  
  # Install dependencies
  if ! install_dependencies "$requirements_file"; then
    return 1
  fi
  
  return 0
}
