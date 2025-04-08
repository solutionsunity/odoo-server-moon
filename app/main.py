"""
Main application module for the Odoo Dev Server Monitoring Tool.
"""
import os
import time
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import asyncio
import json
from typing import List, Dict, Any

from app.config.config import get_config
from app.api.routes import router as api_router
from app.api.websocket import ConnectionManager

# Initialize FastAPI app
app = FastAPI(
    title="Odoo Dev Server Monitor",
    description="A web-based tool for monitoring and managing Odoo development servers",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="app/templates")

# Initialize WebSocket connection manager
manager = ConnectionManager()

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """
    Render the main dashboard page.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/reference", response_class=HTMLResponse)
async def get_reference(request: Request):
    """
    Render the Odoo developer reference page.
    """
    return templates.TemplateResponse("reference.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    This endpoint allows clients to receive real-time updates and request specific data.

    Args:
        websocket: The WebSocket connection
    """
    await manager.connect(websocket)
    try:
        while True:
            # Wait for any message from the client
            data = await websocket.receive_json()

            # Handle different request types
            if "type" in data:
                if data["type"] == "get_status":
                    # Send current status
                    from app.services.service_monitor import get_all_services_status
                    from app.monitoring.system_monitor import get_system_resources

                    services = get_all_services_status()
                    resources = get_system_resources()

                    await manager.send_personal_json({
                        "type": "status_update",
                        "services": services,
                        "resources": resources
                    }, websocket)

                elif data["type"] == "get_modules":
                    # Send module directories
                    from app.modules.module_manager import get_module_directories, check_directory_permissions

                    try:
                        directories = get_module_directories()

                        modules = []
                        for directory in directories:
                            permissions = check_directory_permissions(directory)
                            modules.append({
                                "path": directory,
                                "status": permissions["status"],
                                "permissions": permissions
                            })

                        await manager.send_personal_json({
                            "type": "modules_update",
                            "modules": modules
                        }, websocket)
                    except Exception as e:
                        await manager.send_personal_json({
                            "type": "error",
                            "message": str(e)
                        }, websocket)

                else:
                    # Unknown request type
                    await manager.send_personal_json({
                        "type": "error",
                        "message": f"Unknown request type: {data['type']}"
                    }, websocket)
            else:
                # No type specified
                await manager.send_personal_json({
                    "type": "error",
                    "message": "Missing request type"
                }, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        # Handle any other exceptions
        try:
            await manager.send_personal_json({
                "type": "error",
                "message": str(e)
            }, websocket)
        except:
            pass
        manager.disconnect(websocket)


async def periodic_status_update():
    """
    Periodically send status updates to all connected clients.

    This function runs in the background and broadcasts system status
    at regular intervals defined in the configuration.
    """
    config = get_config()
    refresh_interval = config["monitoring"]["refresh_interval"]

    while True:
        try:
            # Only gather and send data if there are active connections
            if manager.active_connections:
                # Gather real-time data
                from app.services.service_monitor import get_all_services_status
                from app.monitoring.system_monitor import get_system_resources

                services = get_all_services_status()
                resources = get_system_resources()

                # Broadcast to all connected clients
                await manager.broadcast_json({
                    "type": "status_update",
                    "services": services,
                    "resources": resources,
                    "timestamp": int(time.time())
                })
        except Exception as e:
            # Log the error but don't crash the background task
            print(f"Error in periodic status update: {e}")

        # Wait for the next update interval
        await asyncio.sleep(refresh_interval)


@app.on_event("startup")
async def startup_event():
    """
    Start background tasks when the application starts.
    """
    asyncio.create_task(periodic_status_update())


def start():
    """
    Start the application server.
    """
    config = get_config()
    uvicorn.run(
        "app.main:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        reload=True
    )


if __name__ == "__main__":
    start()
