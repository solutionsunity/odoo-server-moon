import os
import pwd
import grp
import logging
import subprocess
from typing import List, Dict, Any

from app.modules.module_manager import get_odoo_group, get_odoo_user, is_user_in_odoo_group

# Set up logging
logger = logging.getLogger(__name__)

def get_human_users() -> List[Dict[str, Any]]:
    """
    Get a list of human users on the system.
    
    Returns:
        List of dictionaries with user information
    """
    human_users = []
    
    try:
        # Get the minimum UID for human users (typically 1000)
        min_uid = 1000
        try:
            with open('/etc/login.defs', 'r') as f:
                for line in f:
                    if line.strip().startswith('UID_MIN'):
                        min_uid = int(line.strip().split()[1])
                        break
        except Exception as e:
            logger.warning(f"Could not read /etc/login.defs, using default UID_MIN=1000: {e}")
        
        # Get all users
        for user in pwd.getpwall():
            # Skip system users
            if user.pw_uid < min_uid:
                continue
                
            # Skip users with nologin or false shell
            if user.pw_shell.endswith('nologin') or user.pw_shell.endswith('false'):
                continue
                
            # Get user's groups
            groups = []
            try:
                # Get primary group
                group_name = grp.getgrgid(user.pw_gid).gr_name
                groups.append(group_name)
                
                # Get supplementary groups
                for group in grp.getgrall():
                    if user.pw_name in group.gr_mem and group.gr_name not in groups:
                        groups.append(group.gr_name)
            except Exception as e:
                logger.warning(f"Error getting groups for user {user.pw_name}: {e}")
            
            # Check if user is in odoo group
            odoo_group = get_odoo_group()
            in_odoo_group = is_user_in_odoo_group(user.pw_name)
            
            # Add user to list
            human_users.append({
                'username': user.pw_name,
                'uid': user.pw_uid,
                'gid': user.pw_gid,
                'home': user.pw_dir,
                'shell': user.pw_shell,
                'groups': groups,
                'in_odoo_group': in_odoo_group
            })
    
    except Exception as e:
        logger.error(f"Error getting human users: {e}")
    
    return human_users

def add_user_to_odoo_group(username: str) -> Dict[str, Any]:
    """
    Add a user to the odoo group.
    
    Args:
        username: Username to add to the odoo group
        
    Returns:
        Dict with status information
    """
    logger.info(f"Adding user {username} to odoo group")
    
    try:
        # Check if user exists
        pwd.getpwnam(username)
        
        # Check if user is already in odoo group
        if is_user_in_odoo_group(username):
            return {
                'status': 'already_in_group',
                'message': f"User {username} is already in the odoo group"
            }
        
        # Add user to odoo group
        odoo_group = get_odoo_group()
        result = subprocess.run(
            ["sudo", "usermod", "-a", "-G", odoo_group, username],
            capture_output=True,
            text=True,
            check=True
        )
        
        return {
            'status': 'success',
            'message': f"User {username} added to the odoo group"
        }
    
    except KeyError:
        return {
            'status': 'error',
            'message': f"User {username} does not exist"
        }
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error adding user {username} to odoo group: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return {
            'status': 'error',
            'message': f"Error adding user {username} to odoo group: {e.stderr}"
        }
    
    except Exception as e:
        logger.error(f"Unexpected error adding user {username} to odoo group: {e}")
        return {
            'status': 'error',
            'message': f"Unexpected error adding user {username} to odoo group: {str(e)}"
        }
