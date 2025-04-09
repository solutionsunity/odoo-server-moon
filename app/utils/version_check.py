"""
Python version compatibility utilities for the Odoo Dev Server Monitoring Tool.

This module provides functions to check Python version compatibility and handle
version-specific behaviors.
"""
import sys
import platform
import subprocess
import os
from typing import Tuple, Dict, Any, Optional


def get_python_version() -> Tuple[int, int, int]:
    """
    Get the current Python version as a tuple of (major, minor, micro).

    Returns:
        Tuple containing the major, minor, and micro version numbers
    """
    version_info = sys.version_info
    return (version_info.major, version_info.minor, version_info.micro)


def check_python_version() -> Dict[str, Any]:
    """
    Check if the current Python version is compatible with the application.

    Returns:
        Dict containing:
            - compatible (bool): Whether the version is compatible
            - message (str): A message describing the compatibility status
            - version (tuple): The current Python version tuple
            - version_str (str): The current Python version string
            - use_system_site_packages (bool): Whether to use --system-site-packages for venv
    """
    version = get_python_version()
    version_str = f"{version[0]}.{version[1]}.{version[2]}"
    python_implementation = platform.python_implementation()

    result = {
        "compatible": False,
        "message": "",
        "version": version,
        "version_str": version_str,
        "python_implementation": python_implementation,
        "use_system_site_packages": False
    }

    # Check for Python < 3.7
    if version[0] < 3 or (version[0] == 3 and version[1] < 7):
        result["compatible"] = False
        result["message"] = (
            f"Python {version_str} is not supported. "
            f"This application requires Python 3.7 or newer. "
            f"Please upgrade your Python installation."
        )
        return result

    # Check for Python 3.12+
    if version[0] > 3 or (version[0] == 3 and version[1] >= 12):
        result["compatible"] = True
        result["use_system_site_packages"] = True
        result["message"] = (
            f"Python {version_str} detected. "
            f"Using venv with --system-site-packages flag for compatibility."
        )
        return result

    # Python 3.7-3.11
    result["compatible"] = True
    result["use_system_site_packages"] = False
    result["message"] = f"Python {version_str} detected. Compatible version."

    return result


def get_venv_create_command(python_path: Optional[str] = None) -> str:
    """
    Get the appropriate venv creation command based on the Python version.

    Args:
        python_path: Optional path to the Python executable

    Returns:
        The command string to create a virtual environment
    """
    if not python_path:
        python_path = sys.executable

    version_info = check_python_version()

    if version_info["use_system_site_packages"]:
        return f"{python_path} -m venv --system-site-packages"
    else:
        return f"{python_path} -m venv"


def detect_python_command() -> Dict[str, Any]:
    """
    Detect which Python command to use (python or python3) for Python 3.x.

    Returns:
        Dict containing:
            - command (str): The command to use for Python 3.x ('python' or 'python3')
            - pip_command (str): The command to use for pip ('pip' or 'pip3')
            - has_python3 (bool): Whether the python3 command exists
            - has_python (bool): Whether the python command exists
            - python_is_v3 (bool): Whether the 'python' command points to Python 3.x
    """
    result = {
        "command": "python3",  # Default to python3
        "pip_command": "pip3",  # Default to pip3
        "has_python3": False,
        "has_python": False,
        "python_is_v3": False
    }

    # Check if python3 command exists
    try:
        output = subprocess.check_output(["which", "python3"], stderr=subprocess.STDOUT, universal_newlines=True)
        if output.strip():
            result["has_python3"] = True
    except subprocess.CalledProcessError:
        result["has_python3"] = False

    # Check if python command exists and which version it is
    try:
        output = subprocess.check_output(["which", "python"], stderr=subprocess.STDOUT, universal_newlines=True)
        if output.strip():
            result["has_python"] = True

            # Check if python is Python 3.x
            try:
                version_output = subprocess.check_output(["python", "-c", "import sys; print(sys.version_info.major)"],
                                                       stderr=subprocess.STDOUT, universal_newlines=True)
                if version_output.strip() == "3":
                    result["python_is_v3"] = True
            except subprocess.CalledProcessError:
                result["python_is_v3"] = False
    except subprocess.CalledProcessError:
        result["has_python"] = False

    # Determine which command to use
    if result["python_is_v3"]:
        # If 'python' points to Python 3.x, use it
        result["command"] = "python"
        result["pip_command"] = "pip"
    elif result["has_python3"]:
        # Otherwise, if python3 exists, use it
        result["command"] = "python3"
        result["pip_command"] = "pip3"
    else:
        # If neither is available, keep the default (python3)
        # This will likely fail later, but we'll handle that in the scripts
        pass

    return result


def get_python_command_for_shell() -> str:
    """
    Get a shell script snippet that detects and exports the appropriate Python command.

    Returns:
        A shell script snippet that sets PYTHON_CMD and PIP_CMD variables
    """
    return '''
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
'''


def print_version_info() -> None:
    """
    Print information about the current Python version and compatibility.
    """
    version_info = check_python_version()
    python_cmd = detect_python_command()

    print(f"Python version: {version_info['version_str']} ({version_info['python_implementation']})")
    print(f"Compatibility: {'Compatible' if version_info['compatible'] else 'Not compatible'}")
    print(f"Message: {version_info['message']}")
    print(f"Python command: {python_cmd['command']}")
    print(f"Pip command: {python_cmd['pip_command']}")


if __name__ == "__main__":
    # When run directly, print version information
    print_version_info()

    # Exit with appropriate status code
    version_info = check_python_version()
    sys.exit(0 if version_info["compatible"] else 1)
