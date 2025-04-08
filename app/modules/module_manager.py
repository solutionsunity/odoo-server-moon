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


def get_odoo_uid():
    """
    Get the user ID for the odoo user.

    Returns:
        int: User ID for odoo, or -1 if not found
    """
    try:
        return pwd.getpwnam('odoo').pw_uid
    except KeyError:
        # If odoo user doesn't exist, return -1
        return -1


def get_odoo_gid():
    """
    Get the group ID for the odoo group.

    Returns:
        int: Group ID for odoo, or -1 if not found
    """
    try:
        import grp
        return grp.getgrnam('odoo').gr_gid
    except (KeyError, ImportError):
        # If odoo group doesn't exist or grp module is not available, return -1
        return -1

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

        # Check file permissions consistency
        files_consistent = True
        inconsistent_files = []

        # Check a sample of files in the directory
        for root, dirs, files in os.walk(directory, topdown=True, followlinks=False):
            for file in files[:10]:  # Check up to 10 files per directory
                file_path = os.path.join(root, file)
                try:
                    file_stat = os.stat(file_path)
                    file_mode = file_stat.st_mode

                    # Check if file permissions match directory permissions
                    if (bool(file_mode & stat.S_IRGRP) != group_readable or
                        bool(file_mode & stat.S_IWGRP) != group_writable or
                        bool(file_mode & stat.S_IROTH) != others_readable or
                        bool(file_mode & stat.S_IWOTH) != others_writable):
                        files_consistent = False
                        inconsistent_files.append(file_path)
                        if len(inconsistent_files) >= 5:  # Limit the number of inconsistent files to report
                            break
                except Exception as e:
                    logger.warning(f"Error checking file permissions for {file_path}: {e}")

            if not files_consistent and len(inconsistent_files) >= 5:
                break

            # Don't recurse too deep
            if root != directory:
                dirs[:] = []  # Don't go into subdirectories

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
            "is_odoo_owner": is_odoo_owner
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

        # Then, set ownership to odoo:odoo
        # This ensures the Odoo service has full access
        own_cmd = ["sudo", "chown", "odoo:odoo", directory]
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

        # Now, recursively fix permissions for all files and subdirectories
        fixed_count = 0
        failed_count = 0

        for root, dirs, files in os.walk(directory):
            # Fix directory permissions
            for d in dirs:
                dir_path = os.path.join(root, d)
                try:
                    # Directories need execute permission
                    # 775 gives read/write/execute to owner and group, read/execute to others
                    subprocess.run(["sudo", "chmod", "775", dir_path], check=True)
                    subprocess.run(["sudo", "chown", "odoo:odoo", dir_path], check=True)
                    fixed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to fix permissions for directory {dir_path}: {e}")
                    failed_count += 1

            # Fix file permissions
            for f in files:
                file_path = os.path.join(root, f)
                try:
                    # Files don't need execute permission
                    # 664 gives read/write to owner and group, read to others
                    subprocess.run(["sudo", "chmod", "664", file_path], check=True)
                    subprocess.run(["sudo", "chown", "odoo:odoo", file_path], check=True)
                    fixed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to fix permissions for file {file_path}: {e}")
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
