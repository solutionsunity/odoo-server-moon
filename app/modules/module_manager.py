"""
Module directory management functionality for the Odoo Dev Server Monitoring Tool.
"""
import os
import stat
import logging
import configparser
import subprocess
from typing import List, Dict, Any, Optional

from app.config.config import get_config

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
        if not readable or not executable:
            status = "error"
        elif not writable:
            status = "warning"
        elif not files_consistent:
            status = "warning"
        elif not (group_readable and group_executable and others_readable and others_executable):
            status = "warning"
        else:
            status = "ok"
        
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
            "files_consistent": files_consistent
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
        # Get the current user and group
        current_user = os.getlogin()
        
        # Use subprocess to run chmod and chown with sudo
        # This is similar to what gbfixodoo would do
        
        # First, ensure the directory has the right permissions
        dir_cmd = ["sudo", "chmod", "755", directory]
        subprocess.run(dir_cmd, check=True)
        
        # Then, set ownership to the current user
        own_cmd = ["sudo", "chown", f"{current_user}:odoo", directory]
        subprocess.run(own_cmd, check=True)
        
        # Now, recursively fix permissions for all files and subdirectories
        fixed_count = 0
        failed_count = 0
        
        for root, dirs, files in os.walk(directory):
            # Fix directory permissions
            for d in dirs:
                dir_path = os.path.join(root, d)
                try:
                    # Directories need execute permission
                    subprocess.run(["sudo", "chmod", "755", dir_path], check=True)
                    subprocess.run(["sudo", "chown", f"{current_user}:odoo", dir_path], check=True)
                    fixed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to fix permissions for directory {dir_path}: {e}")
                    failed_count += 1
            
            # Fix file permissions
            for f in files:
                file_path = os.path.join(root, f)
                try:
                    # Files don't need execute permission
                    subprocess.run(["sudo", "chmod", "644", file_path], check=True)
                    subprocess.run(["sudo", "chown", f"{current_user}:odoo", file_path], check=True)
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
