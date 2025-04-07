# Odoo Dev Server Monitoring Tool Requirements

## Overview
A standalone web-based tool for developers to monitor and manage an Odoo development server locally. The tool provides a simple interface for common maintenance tasks without requiring server command-line expertise, enabling developers to focus on their work rather than environment management.

## Functional Requirements

### Service Monitoring & Control
- Real-time status monitoring of services (Odoo and PostgreSQL)
- Service control with stop/start/restart buttons
- System resource monitoring (CPU, memory, disk usage)

### Module Management
- List all Odoo module directories from odoo.conf
- Display permissions status for each directory (visual indicator showing status)
- Provide one-click fix for directory permissions issues

## Technical Requirements

### Backend
- FastAPI framework
- Python 3.x
- Subprocess module for system commands
- File system operations for permission management
- Standalone implementation (no external tool dependencies)

### Frontend
- Simple, responsive web interface
- Real-time status updates via websockets
- Minimalist UI focused on functionality

#### UI Layout
```
-----------------------------------
| CPU | RAM | Disk | System Info  |
-----------------------------------
| Services         | Module Dirs  |
|                  |              |
|                  |              |
-----------------------------------
| Logs                            |
-----------------------------------
```

### Deployment
- Run locally on developer machine
- No authentication/security layer needed (local use only)
- Installation script for easy setup as a service

## Implementation Details
- Parse `/etc/odoo/odoo.conf` for addon paths
- Implement custom directory permission fixes (reference `/gbtools/gbfixodoo` for functionality, but implement independently)
- Use systemd commands to control Odoo and PostgreSQL services
- Implement websockets for real-time updates
- Use `sudo -u postgres` for PostgreSQL commands, if needed

## Testing Requirements
- Implement tests for each functionality:
  - Success case: Test expected normal operation
  - Failure case: Test proper handling of errors
  - Edge case: Test boundary conditions where applicable
- Organize tests by functional area (service monitoring, control, module management)
- Ensure tests are maintainable for potential future public repository
