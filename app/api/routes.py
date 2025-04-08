"""
API routes for the Odoo Dev Server Monitoring Tool.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Any, Optional

from app.services.service_monitor import (
    get_all_services_status,
    start_service,
    stop_service,
    restart_service
)
from app.monitoring.system_monitor import get_system_resources
from app.modules.module_manager import (
    get_module_directories,
    check_directory_permissions,
    fix_directory_permissions
)
from app.modules.module_manager import get_odoo_user, get_odoo_group
from app.modules.user_manager import (
    get_human_users,
    add_user_to_odoo_group
)

# Create router with tags for API documentation
router = APIRouter(
    tags=["api"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


# Define request/response models
class ServiceControlRequest(BaseModel):
    """Request model for service control operations."""
    service: str = "odoo"

    class Config:
        schema_extra = {
            "example": {
                "service": "odoo"
            }
        }


class FixPermissionsRequest(BaseModel):
    """Request model for fixing directory permissions."""
    path: str

    class Config:
        schema_extra = {
            "example": {
                "path": "/var/lib/odoo/addons"
            }
        }


class AddUserToGroupRequest(BaseModel):
    """Request model for adding a user to the odoo group."""
    username: str

    class Config:
        schema_extra = {
            "example": {
                "username": "developer1"
            }
        }


class ServiceResponse(BaseModel):
    """Response model for service operations."""
    success: bool
    message: str
    error: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Service odoo started successfully",
                "error": None
            }
        }


class PermissionInfo(BaseModel):
    """Model for directory permission details."""
    status: str
    readable: bool
    writable: bool
    executable: bool
    group_readable: Optional[bool] = None
    group_writable: Optional[bool] = None
    group_executable: Optional[bool] = None
    others_readable: Optional[bool] = None
    others_writable: Optional[bool] = None
    others_executable: Optional[bool] = None
    files_consistent: Optional[bool] = None
    error: Optional[str] = None


class ModuleDirectoryInfo(BaseModel):
    """Model for module directory information."""
    path: str
    status: str
    permissions: Dict[str, Any]


# API routes
@router.get(
    "/status",
    summary="Get system status",
    description="Get the status of all services and system resources",
    response_description="Status of services and system resources"
)
async def get_status():
    """
    Get the status of all services and system resources.

    Returns:
        Dict containing services status and system resource information

    Raises:
        HTTPException: If there's an error getting the status
    """
    try:
        services = get_all_services_status()
        resources = get_system_resources()

        return {
            "services": services,
            "resources": resources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/services/{service}/start",
    summary="Start a service",
    description="Start a systemd service",
    response_model=ServiceResponse,
    responses={
        200: {"description": "Service started successfully"},
        500: {"description": "Failed to start service"}
    }
)
async def start_service_endpoint(service: str):
    """
    Start a service.

    Args:
        service: Name of the service to start

    Returns:
        ServiceResponse: Result of the operation

    Raises:
        HTTPException: If there's an error starting the service
    """
    try:
        result = start_service(service)

        if result:
            return ServiceResponse(
                success=True,
                message=f"Service {service} started successfully"
            )
        else:
            return ServiceResponse(
                success=False,
                message=f"Failed to start service {service}",
                error="See logs for details"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/services/{service}/stop",
    summary="Stop a service",
    description="Stop a systemd service",
    response_model=ServiceResponse,
    responses={
        200: {"description": "Service stopped successfully"},
        500: {"description": "Failed to stop service"}
    }
)
async def stop_service_endpoint(service: str):
    """
    Stop a service.

    Args:
        service: Name of the service to stop

    Returns:
        ServiceResponse: Result of the operation

    Raises:
        HTTPException: If there's an error stopping the service
    """
    try:
        result = stop_service(service)

        if result:
            return ServiceResponse(
                success=True,
                message=f"Service {service} stopped successfully"
            )
        else:
            return ServiceResponse(
                success=False,
                message=f"Failed to stop service {service}",
                error="See logs for details"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/services/{service}/restart",
    summary="Restart a service",
    description="Restart a systemd service",
    response_model=ServiceResponse,
    responses={
        200: {"description": "Service restarted successfully"},
        500: {"description": "Failed to restart service"}
    }
)
async def restart_service_endpoint(service: str):
    """
    Restart a service.

    Args:
        service: Name of the service to restart

    Returns:
        ServiceResponse: Result of the operation

    Raises:
        HTTPException: If there's an error restarting the service
    """
    try:
        result = restart_service(service)

        if result:
            return ServiceResponse(
                success=True,
                message=f"Service {service} restarted successfully"
            )
        else:
            return ServiceResponse(
                success=False,
                message=f"Failed to restart service {service}",
                error="See logs for details"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/modules",
    summary="Get module directories",
    description="Get a list of all Odoo module directories with their permission status",
    response_description="List of module directories with permission status",
    responses={
        200: {"description": "List of module directories"},
        500: {"description": "Failed to get module directories"}
    }
)
async def get_modules():
    """
    Get a list of all Odoo module directories with their permission status.

    Returns:
        Dict containing a list of module directories with permission information

    Raises:
        HTTPException: If there's an error getting the module directories
    """
    try:
        directories = get_module_directories()

        modules = []
        for directory in directories:
            permissions = check_directory_permissions(directory)
            modules.append(ModuleDirectoryInfo(
                path=directory,
                status=permissions["status"],
                permissions=permissions
            ).model_dump())

        return {
            "modules": modules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/modules/fix",
    summary="Fix module permissions",
    description="Fix permissions for a module directory",
    response_model=ServiceResponse,
    responses={
        200: {"description": "Permission fix started"},
        500: {"description": "Failed to start permission fix"}
    }
)
async def fix_module_permissions(request: FixPermissionsRequest, background_tasks: BackgroundTasks):
    """
    Fix permissions for a module directory.

    Args:
        request: Request containing the path to fix
        background_tasks: FastAPI background tasks manager

    Returns:
        ServiceResponse: Result of the operation

    Raises:
        HTTPException: If there's an error starting the permission fix
    """
    try:
        # Run the fix in the background to avoid blocking the API
        background_tasks.add_task(fix_directory_permissions, request.path)

        return ServiceResponse(
            success=True,
            message=f"Permission fix started for {request.path}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/modules/{path:path}/permissions",
    summary="Get module permissions",
    description="Get detailed permission information for a specific module directory",
    response_description="Permission details for the specified directory",
    responses={
        200: {"description": "Permission details"},
        404: {"description": "Directory not found"},
        500: {"description": "Failed to get permissions"}
    }
)
async def get_module_permissions(path: str):
    """
    Get detailed permission information for a specific module directory.

    Args:
        path: Path to the directory to check

    Returns:
        Dict containing permission information for the directory

    Raises:
        HTTPException: If there's an error checking the permissions or the directory doesn't exist
    """
    try:
        permissions = check_directory_permissions(path)

        if permissions.get("status") == "not_found":
            raise HTTPException(status_code=404, detail=f"Directory not found: {path}")

        return {
            "path": path,
            "permissions": permissions
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/users",
    summary="Get human users",
    description="Get a list of all human users on the system with their odoo group membership status",
    response_description="List of human users with odoo group membership status",
    responses={
        200: {"description": "List of human users"},
        500: {"description": "Failed to get human users"}
    }
)
async def get_users():
    """
    Get a list of all human users on the system with their odoo group membership status.

    Returns:
        Dict containing a list of human users with odoo group membership status

    Raises:
        HTTPException: If there's an error getting the human users
    """
    try:
        users = get_human_users()

        return {
            "users": users,
            "odoo_user": get_odoo_user(),
            "odoo_group": get_odoo_group()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/users/add-to-odoo-group",
    summary="Add user to odoo group",
    description="Add a user to the odoo group",
    response_model=ServiceResponse,
    responses={
        200: {"description": "User added to odoo group"},
        500: {"description": "Failed to add user to odoo group"}
    }
)
async def add_user_to_odoo_group_endpoint(request: AddUserToGroupRequest):
    """
    Add a user to the odoo group.

    Args:
        request: Request containing the username to add to the odoo group

    Returns:
        ServiceResponse: Result of the operation

    Raises:
        HTTPException: If there's an error adding the user to the odoo group
    """
    try:
        result = add_user_to_odoo_group(request.username)

        if result["status"] == "success" or result["status"] == "already_in_group":
            return ServiceResponse(
                success=True,
                message=result["message"]
            )
        else:
            return ServiceResponse(
                success=False,
                message=result["message"],
                error="See logs for details"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
