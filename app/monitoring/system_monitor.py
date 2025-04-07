"""
System resource monitoring functionality for the Odoo Dev Server Monitoring Tool.
"""
import psutil
import logging
from typing import Dict, Any, Optional

# Set up logging
logger = logging.getLogger(__name__)


def get_cpu_usage() -> Optional[float]:
    """
    Get the current CPU usage percentage.
    
    Returns:
        CPU usage as a percentage, or None if an error occurred
    """
    try:
        # Get CPU usage as a percentage (0-100)
        cpu_percent = psutil.cpu_percent(interval=0.5)
        logger.debug(f"CPU usage: {cpu_percent}%")
        return cpu_percent
    
    except Exception as e:
        logger.error(f"Error getting CPU usage: {e}")
        return None


def get_memory_usage() -> Optional[Dict[str, Any]]:
    """
    Get the current memory usage.
    
    Returns:
        Dict with memory usage information, or None if an error occurred
    """
    try:
        # Get virtual memory information
        memory = psutil.virtual_memory()
        
        # Create a dict with relevant information
        memory_info = {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percent": memory.percent
        }
        
        logger.debug(f"Memory usage: {memory_info['percent']}%")
        return memory_info
    
    except Exception as e:
        logger.error(f"Error getting memory usage: {e}")
        return None


def get_disk_usage() -> Optional[Dict[str, Any]]:
    """
    Get the current disk usage.
    
    Returns:
        Dict with disk usage information, or None if an error occurred
    """
    try:
        # Get disk usage for the root partition
        disk = psutil.disk_usage('/')
        
        # Create a dict with relevant information
        disk_info = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
        
        logger.debug(f"Disk usage: {disk_info['percent']}%")
        return disk_info
    
    except Exception as e:
        logger.error(f"Error getting disk usage: {e}")
        return None


def get_system_resources() -> Dict[str, Any]:
    """
    Get comprehensive system resource information.
    
    Returns:
        Dict with CPU, memory, and disk usage information
    """
    logger.info("Getting system resource information")
    
    resources = {
        "cpu": get_cpu_usage(),
        "memory": get_memory_usage(),
        "disk": get_disk_usage()
    }
    
    return resources
