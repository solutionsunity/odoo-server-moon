"""
Service monitoring functionality for the Odoo Dev Server Monitoring Tool.
"""
import subprocess
import logging
from typing import Dict, List

from app.config.config import get_config

# Set up logging
logger = logging.getLogger(__name__)


def get_service_status(service_name: str) -> str:
    """
    Get the status of a systemd service.

    Args:
        service_name: Name of the service to check

    Returns:
        Status of the service (active, inactive, failed, etc.)
    """
    logger.info(f"Checking status of service: {service_name}")

    try:
        # Run systemctl is-active to check if the service is active
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            check=False
        )

        status = result.stdout.strip()

        # If is-active didn't return 'active', check the actual status
        if status != "active":
            status_result = subprocess.run(
                ["systemctl", "status", service_name],
                capture_output=True,
                text=True,
                check=False
            )

            # Parse the status output to get more detailed status
            for line in status_result.stdout.split('\n'):
                if "Active:" in line:
                    # Extract status from the Active line
                    parts = line.split(':', 1)[1].strip().split(' ', 1)
                    if len(parts) > 0:
                        status = parts[0].strip('()')
                    break

        logger.info(f"Service {service_name} status: {status}")
        return status

    except Exception as e:
        logger.error(f"Error checking service status: {e}")
        return "error"


def detect_postgresql_instances() -> List[str]:
    """
    Detect PostgreSQL instances using systemctl.

    Returns:
        List of PostgreSQL instance service names
    """
    logger.info("Detecting PostgreSQL instances")

    try:
        # Run systemctl to list all PostgreSQL instances
        result = subprocess.run(
            ["systemctl", "list-units", "postgresql@*", "--no-legend"],
            capture_output=True,
            text=True,
            check=False
        )

        instances = []

        # Parse the output to extract service names
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 1 and parts[0].startswith("postgresql@"):
                # Extract the service name (e.g., postgresql@14-main.service)
                service_name = parts[0].replace(".service", "")
                instances.append(service_name)

        logger.info(f"Detected PostgreSQL instances: {instances}")
        return instances

    except Exception as e:
        logger.error(f"Error detecting PostgreSQL instances: {e}")
        return []


def get_all_services_status() -> Dict[str, str]:
    """
    Get the status of all configured services.

    Returns:
        Dict mapping service names to their statuses
    """
    logger.info("Checking status of all services")

    config = get_config()
    services = config["services"]

    result = {}
    for service_key, service_config in services.items():
        service_name = service_config["service_name"]
        result[service_key] = get_service_status(service_name)

        # Handle PostgreSQL instances
        if service_key == "postgres":
            # Get configured instances
            instances = service_config.get("instances", [])

            # Auto-detect instances if enabled
            if service_config.get("auto_detect", False):
                detected_instances = detect_postgresql_instances()
                # Add any detected instances that aren't already in the list
                for instance in detected_instances:
                    if instance not in instances:
                        instances.append(instance)

            # Add status for each instance
            for instance in instances:
                instance_key = f"{service_key}_{instance.replace('@', '_')}"
                result[instance_key] = get_service_status(instance)

    return result


def get_service_name_from_key(service_key: str) -> str:
    """
    Get the actual service name from a service key.

    Args:
        service_key: Key of the service (e.g., 'postgres_postgresql_14-main')

    Returns:
        The actual service name (e.g., 'postgresql@14-main')
    """
    config = get_config()

    # Check if this is a PostgreSQL instance
    if "_postgresql_" in service_key:
        # Extract the instance name from the key
        instance_parts = service_key.split("_postgresql_")
        if len(instance_parts) == 2:
            return f"postgresql@{instance_parts[1]}"

    # Regular service
    service_parts = service_key.split("_")
    base_service_key = service_parts[0]

    if base_service_key in config["services"]:
        return config["services"][base_service_key]["service_name"]

    # Fallback to the key itself
    return service_key


def start_service(service_key: str) -> bool:
    """
    Start a systemd service.

    Args:
        service_key: Key of the service in the configuration

    Returns:
        True if the service was started successfully, False otherwise
    """
    logger.info(f"Starting service: {service_key}")

    service_name = get_service_name_from_key(service_key)

    try:
        subprocess.run(
            ["sudo", "systemctl", "start", service_name],
            capture_output=True,
            text=True,
            check=True
        )

        logger.info(f"Service {service_key} ({service_name}) started successfully")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error starting service {service_key} ({service_name}): {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error starting service {service_key} ({service_name}): {e}")
        return False


def stop_service(service_key: str) -> bool:
    """
    Stop a systemd service.

    Args:
        service_key: Key of the service in the configuration

    Returns:
        True if the service was stopped successfully, False otherwise
    """
    logger.info(f"Stopping service: {service_key}")

    service_name = get_service_name_from_key(service_key)

    try:
        subprocess.run(
            ["sudo", "systemctl", "stop", service_name],
            capture_output=True,
            text=True,
            check=True
        )

        logger.info(f"Service {service_key} ({service_name}) stopped successfully")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error stopping service {service_key} ({service_name}): {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error stopping service {service_key} ({service_name}): {e}")
        return False


def restart_service(service_key: str) -> bool:
    """
    Restart a systemd service.

    Args:
        service_key: Key of the service in the configuration

    Returns:
        True if the service was restarted successfully, False otherwise
    """
    logger.info(f"Restarting service: {service_key}")

    service_name = get_service_name_from_key(service_key)

    try:
        subprocess.run(
            ["sudo", "systemctl", "restart", service_name],
            capture_output=True,
            text=True,
            check=True
        )

        logger.info(f"Service {service_key} ({service_name}) restarted successfully")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Error restarting service {service_key} ({service_name}): {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error restarting service {service_key} ({service_name}): {e}")
        return False
