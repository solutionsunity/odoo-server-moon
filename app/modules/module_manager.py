"""
Module directory management functionality for the Odoo Dev Server Monitoring Tool.
"""
import os
import stat
import logging
import configparser
import subprocess
import pwd
from typing import List, Dict, Any

from app.config.config import get_config


def get_odoo_user():
    """
    Get the username for the Odoo service user.

    Returns:
        str: Username for Odoo service, defaults to 'odoo' if not found in service file
    """
    # Try to get the user from the systemd service file
    try:
        # Check if odoo service exists
        result = subprocess.run(
            ["systemctl", "cat", "odoo.service"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # Extract User= line from service file
            for line in result.stdout.splitlines():
                if line.strip().startswith("User="):
                    return line.strip().split("=")[1]
    except Exception as e:
        logger.warning(f"Error getting odoo user from service file: {e}")

    # Default to 'odoo' if not found
    return 'odoo'


def get_odoo_uid():
    """
    Get the user ID for the odoo user.

    Returns:
        int: User ID for odoo, or -1 if not found
    """
    try:
        odoo_user = get_odoo_user()
        return pwd.getpwnam(odoo_user).pw_uid
    except KeyError:
        # If odoo user doesn't exist, return -1
        return -1


def get_odoo_group():
    """
    Get the group name for the Odoo service group.

    Returns:
        str: Group name for Odoo service, defaults to 'odoo' if not found
    """
    # Try to get the group from the odoo user's primary group
    try:
        import grp
        odoo_user = get_odoo_user()
        user_info = pwd.getpwnam(odoo_user)
        group_info = grp.getgrgid(user_info.pw_gid)
        return group_info.gr_name
    except (KeyError, ImportError) as e:
        logger.warning(f"Error getting odoo group from user: {e}")

    # Default to 'odoo' if not found
    return 'odoo'


def get_odoo_gid():
    """
    Get the group ID for the odoo group.

    Returns:
        int: Group ID for odoo, or -1 if not found
    """
    try:
        import grp
        odoo_group = get_odoo_group()
        return grp.getgrnam(odoo_group).gr_gid
    except (KeyError, ImportError):
        # If odoo group doesn't exist or grp module is not available, return -1
        return -1


def get_odoo_group_members():
    """
    Get the list of users in the odoo group.

    Returns:
        list: List of usernames in the odoo group, or empty list if not found
    """
    try:
        import grp
        odoo_group = get_odoo_group()
        return grp.getgrnam(odoo_group).gr_mem
    except (KeyError, ImportError):
        # If odoo group doesn't exist or grp module is not available, return empty list
        return []


def is_user_in_odoo_group(username):
    """
    Check if a user is in the odoo group.

    Args:
        username: Username to check

    Returns:
        bool: True if user is in odoo group, False otherwise
    """
    try:
        # First check if user exists
        import pwd
        pwd.getpwnam(username)  # Will raise KeyError if user doesn't exist

        # Check if user is in odoo group
        members = get_odoo_group_members()
        if username in members:
            return True

        # Check if odoo is the user's primary group
        odoo_gid = get_odoo_gid()
        user_gid = pwd.getpwnam(username).pw_gid
        return user_gid == odoo_gid
    except (KeyError, ImportError):
        return False

# Set up logging
logger = logging.getLogger(__name__)


def get_module_directories() -> List[str]:
    """
    Get a list of Odoo module directories from the Odoo configuration file.

    Returns:
        List of module directory paths
    """
    logger.info("Getting Odoo module directories")

    config = get_config()
    odoo_config_path = config["services"]["odoo"]["config_file"]

    if not os.path.exists(odoo_config_path):
        logger.error(f"Odoo configuration file not found: {odoo_config_path}")
        raise FileNotFoundError(f"Odoo configuration file not found: {odoo_config_path}")

    try:
        # Parse the Odoo configuration file
        parser = configparser.ConfigParser()
        parser.read(odoo_config_path)

        # Get the addons_path from the options section
        if 'options' in parser and 'addons_path' in parser['options']:
            addons_path = parser['options']['addons_path']

            # Split the comma-separated list of paths
            directories = [path.strip() for path in addons_path.split(',')]

            logger.info(f"Found {len(directories)} module directories")
            return directories
        else:
            logger.warning("No addons_path found in Odoo configuration")
            return []

    except Exception as e:
        logger.error(f"Error parsing Odoo configuration: {e}")
        raise


def check_directory_permissions(directory: str) -> Dict[str, Any]:
    """
    Check the permissions of a directory.

    Args:
        directory: Path to the directory to check

    Returns:
        Dict with permission information
    """
    logger.info(f"Checking permissions for directory: {directory}")

    if not os.path.exists(directory):
        logger.warning(f"Directory does not exist: {directory}")
        return {
            "status": "not_found",
            "error": f"Directory does not exist: {directory}"
        }

    try:
        # Get the directory's stat information
        dir_stat = os.stat(directory)
        dir_mode = dir_stat.st_mode

        # Check if the directory is readable and writable
        readable = os.access(directory, os.R_OK)
        writable = os.access(directory, os.W_OK)
        executable = os.access(directory, os.X_OK)

        # Check group and other permissions
        group_readable = bool(dir_mode & stat.S_IRGRP)
        group_writable = bool(dir_mode & stat.S_IWGRP)
        group_executable = bool(dir_mode & stat.S_IXGRP)

        others_readable = bool(dir_mode & stat.S_IROTH)
        others_writable = bool(dir_mode & stat.S_IWOTH)
        others_executable = bool(dir_mode & stat.S_IXOTH)

        # Get owner and group IDs
        odoo_uid = get_odoo_uid()
        odoo_gid = get_odoo_gid()

        # Check if directory has correct ownership
        is_odoo_owner = (dir_stat.st_uid == odoo_uid)
        is_odoo_group = (dir_stat.st_gid == odoo_gid)

        # Use find command to check for non-compliant files (faster than Python traversal)
        files_consistent = True
        inconsistent_files = []

        # Check for files/dirs with incorrect ownership
        try:
            # Find files not owned by odoo user (limit to 5)
            odoo_user = get_odoo_user()
            odoo_group = get_odoo_group()
            cmd = [
                "find", directory,
                "-type", "f",
                "!", "-user", odoo_user,
                "-o", "!", "-group", odoo_group,
                "-maxdepth", "3",  # Limit depth for performance
                "-print",
                "-quit"  # Stop after first match
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout.strip():
                files_consistent = False
                inconsistent_files = result.stdout.strip().split('\n')[:5]

            # If no ownership issues, check for permission issues
            if files_consistent:
                # Find files with incorrect permissions
                cmd = [
                    "find", directory,
                    "-type", "f",
                    "!", "-perm", "-664",  # Files should be at least 664
                    "-maxdepth", "3",
                    "-print",
                    "-quit"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.stdout.strip():
                    files_consistent = False
                    inconsistent_files = result.stdout.strip().split('\n')[:5]

                # Find directories with incorrect permissions
                cmd = [
                    "find", directory,
                    "-type", "d",
                    "!", "-perm", "-775",  # Directories should be at least 775
                    "-maxdepth", "3",
                    "-print",
                    "-quit"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.stdout.strip() and files_consistent:  # Only add if we don't already have inconsistent files
                    files_consistent = False
                    inconsistent_files = result.stdout.strip().split('\n')[:5]

        except Exception as e:
            logger.warning(f"Error using find command: {e}")
            # Fall back to basic check if find command fails
            files_consistent = is_odoo_owner and is_odoo_group

        # Determine overall status
        # Check if odoo is the owner
        is_odoo_owner = (dir_stat.st_uid == get_odoo_uid())

        # Check if group has proper permissions (for developer access)
        group_has_proper_permissions = group_readable and group_writable and group_executable

        if not readable or not executable:
            status = "error"
        elif not is_odoo_owner:
            status = "error"  # Odoo must be the owner
        elif not writable:
            status = "warning"
        elif not files_consistent:
            status = "warning"
        elif not group_has_proper_permissions:
            status = "warning"  # Group needs full access
        elif not (others_readable and others_executable):
            status = "warning"  # Others need read/execute
        else:
            status = "ok"

        # Get owner and group names
        try:
            owner_name = pwd.getpwuid(dir_stat.st_uid).pw_name
        except KeyError:
            owner_name = str(dir_stat.st_uid)

        try:
            import grp
            group_name = grp.getgrgid(dir_stat.st_gid).gr_name
        except (KeyError, ImportError):
            group_name = str(dir_stat.st_gid)

        # Get odoo group members
        odoo_group_members = get_odoo_group_members()

        # Check if current user is in odoo group
        current_user = os.getlogin()
        current_user_in_odoo_group = is_user_in_odoo_group(current_user)

        # Get the mode in octal format (e.g., 775)
        mode_octal = oct(dir_stat.st_mode)[-3:]

        result = {
            "status": status,
            "readable": readable,
            "writable": writable,
            "executable": executable,
            "group_readable": group_readable,
            "group_writable": group_writable,
            "group_executable": group_executable,
            "others_readable": others_readable,
            "others_writable": others_writable,
            "others_executable": others_executable,
            "files_consistent": files_consistent,
            "owner": owner_name,
            "group": group_name,
            "is_odoo_owner": is_odoo_owner,
            "is_odoo_group": is_odoo_group,
            "odoo_group_members": odoo_group_members,
            "current_user_in_odoo_group": current_user_in_odoo_group,
            "mode": mode_octal
        }

        if not files_consistent:
            result["inconsistent_files"] = inconsistent_files[:5]  # Include up to 5 inconsistent files

        logger.info(f"Directory {directory} permission status: {status}")
        return result

    except Exception as e:
        logger.error(f"Error checking directory permissions: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def fix_directory_permissions(directory: str) -> Dict[str, Any]:
    """
    Fix the permissions of a directory for Odoo.

    Args:
        directory: Path to the directory to fix

    Returns:
        Dict with the result of the operation
    """
    logger.info(f"Fixing permissions for directory: {directory}")

    if not os.path.exists(directory):
        logger.warning(f"Directory does not exist: {directory}")
        return {
            "success": False,
            "error": f"Directory does not exist: {directory}"
        }

    try:
        # Use subprocess to run chmod and chown with sudo
        # This is similar to what gbfixodoo would do

        # First, ensure the directory has the right permissions
        # 775 gives read/write/execute to owner and group, read/execute to others
        dir_cmd = ["sudo", "chmod", "775", directory]
        subprocess.run(dir_cmd, check=True)

        # Then, set ownership to odoo user and group
        # This ensures the Odoo service has full access
        odoo_user = get_odoo_user()
        odoo_group = get_odoo_group()
        own_cmd = ["sudo", "chown", f"{odoo_user}:{odoo_group}", directory]
        subprocess.run(own_cmd, check=True)

        # Add the current user to the odoo group if not already a member
        current_user = os.getlogin()
        try:
            # Check if current user is in odoo group
            check_group_cmd = ["groups", current_user]
            result = subprocess.run(check_group_cmd, capture_output=True, text=True, check=True)

            if "odoo" not in result.stdout:
                logger.info(f"Adding user {current_user} to odoo group")
                # Add current user to odoo group
                add_group_cmd = ["sudo", "usermod", "-a", "-G", "odoo", current_user]
                subprocess.run(add_group_cmd, check=True)
                logger.info(f"User {current_user} added to odoo group. Changes will take effect on next login.")
        except Exception as e:
            logger.warning(f"Could not add user to odoo group: {e}")

        # Use recursive commands to fix permissions efficiently
        fixed_count = 0
        failed_count = 0

        try:
            # First, recursively set ownership to odoo user and group
            odoo_user = get_odoo_user()
            odoo_group = get_odoo_group()
            logger.info(f"Setting ownership recursively for {directory} to {odoo_user}:{odoo_group}")
            chown_cmd = ["sudo", "chown", "-R", f"{odoo_user}:{odoo_group}", directory]
            subprocess.run(chown_cmd, check=True)

            # Count the number of files and directories affected
            count_cmd = ["find", directory, "-type", "f", "-o", "-type", "d", "-print"]
            result = subprocess.run(count_cmd, capture_output=True, text=True, check=True)
            affected_items = len(result.stdout.strip().split('\n'))
            fixed_count += affected_items

            # Set directory permissions recursively
            logger.info(f"Setting directory permissions recursively for {directory}")
            dir_chmod_cmd = ["sudo", "find", directory, "-type", "d", "-exec", "chmod", "775", "{}", ";"]
            subprocess.run(dir_chmod_cmd, check=True)

            # Set file permissions recursively
            logger.info(f"Setting file permissions recursively for {directory}")
            file_chmod_cmd = ["sudo", "find", directory, "-type", "f", "-exec", "chmod", "664", "{}", ";"]
            subprocess.run(file_chmod_cmd, check=True)

        except Exception as e:
            logger.error(f"Error fixing permissions recursively: {e}")
            failed_count += 1

        # Determine the status
        if failed_count == 0:
            status = "fixed"
        elif fixed_count > 0:
            status = "partially_fixed"
        else:
            status = "failed"

        result = {
            "success": fixed_count > 0,
            "status": status,
            "fixed_count": fixed_count,
            "failed_count": failed_count
        }

        logger.info(f"Fixed permissions for {fixed_count} items in {directory}, {failed_count} failures")
        return result

    except Exception as e:
        logger.error(f"Error fixing directory permissions: {e}")
        return {
            "success": False,
            "error": str(e)
        }
