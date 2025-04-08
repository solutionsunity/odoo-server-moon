# Odoo Dev Server Monitoring Tool

A web-based tool for monitoring and managing Odoo development servers locally. This tool provides a simple interface for common maintenance tasks without requiring server command-line expertise.

## Features

- **Service Monitoring & Control**
  - Real-time status of services (Odoo and PostgreSQL)
  - Service stop/start/restart buttons
  - Monitor system resources (CPU, memory, disk usage)
  - Support for PostgreSQL instances (e.g., postgresql@14-main)

- **Module Management**
  - List all Odoo module directories from odoo.conf
  - Display permissions for each directory
  - Provide one-click fix for directory permissions

## Quick Start Guide

### Prerequisites

- Python 3.x
- Odoo development environment
- PostgreSQL
- sudo access (for service control and permission fixes)

### Installation

#### One-Line Installation (Recommended)

Install with a single command (requires sudo):

```bash
curl -sSL https://raw.githubusercontent.com/solutionsunity/odoo-server-moon/main/scripts/install-remote.sh | sudo bash
```

This will:
- Download and install the tool to `/opt/odoo-server-moon`
- Set up a systemd service that starts automatically
- Start the service immediately

After installation, access the web interface at http://localhost:8008

#### Custom Installation Options

You can customize the installation with additional options:

```bash
curl -sSL https://raw.githubusercontent.com/solutionsunity/odoo-server-moon/main/scripts/install-remote.sh | sudo bash -s -- --dir /opt/custom-path --port 8080
```

Available options:
- `--dir DIR`: Installation directory (default: /opt/odoo-server-moon)
- `--branch BRANCH`: Git branch to use (default: main)
- `--port PORT`: Port to run the server on (default: 8008)
- `--no-start`: Don't start the service after installation
- `--no-update`: Don't update if already installed

### Updating

When a new version is available, update your installation with:

```bash
sudo /opt/odoo-server-moon/scripts/update.sh
```

Or use the installation script which automatically updates existing installations:

```bash
curl -sSL https://raw.githubusercontent.com/solutionsunity/odoo-server-moon/main/scripts/install-remote.sh | sudo bash
```

### Uninstalling

To completely remove the tool from your system:

```bash
sudo /opt/odoo-server-moon/scripts/uninstall.sh
```

This will:
- Stop and remove the systemd service
- Ask if you want to remove all application files

Options:
- `--remove-files`: Remove all application files without asking
- `--keep-files`: Keep application files, only remove the service

### Manual Installation (Alternative)

1. Clone the repository:
   ```bash
   git clone https://github.com/solutionsunity/odoo-server-moon.git
   cd odoo-server-moon
   ```

2. Run the application (choose one method):
   ```bash
   # Using the shell script
   ./run.sh

   # OR using Python directly
   ./odoo-monitor.py
   ```

3. Access the web interface at http://localhost:8008

4. To install as a service:
   ```bash
   sudo ./scripts/install-service.sh
   ```

## Configuration

Configuration is stored in `config/config.json`. You can modify:

- Server host and port
- Monitoring refresh interval
- Service names
- PostgreSQL instance detection

## Usage Guide

### Web Interface

After installation, access the web interface at http://localhost:8008 (or your custom port).

The dashboard provides:

1. **System Metrics** - Monitor CPU, memory, and disk usage
2. **Service Control** - Start, stop, and restart Odoo and PostgreSQL services
3. **Module Management** - View and fix permissions for Odoo module directories

### Common Tasks

#### Fixing Module Permissions

1. In the Modules section, look for directories with a warning or error status
2. Click on the directory to see detailed permission information
3. Click the "Fix Permissions" button to automatically correct permissions

#### Managing Services

- Use the Start/Stop/Restart buttons next to each service
- The service status updates in real-time
- PostgreSQL instances (e.g., postgresql@14-main) are shown separately

### Service Management from Terminal

If you need to manage the monitoring tool itself:

- **Check status**: `sudo systemctl status odoo-dev-monitor`
- **Start service**: `sudo systemctl start odoo-dev-monitor`
- **Stop service**: `sudo systemctl stop odoo-dev-monitor`
- **Restart service**: `sudo systemctl restart odoo-dev-monitor`
- **View logs**: `sudo journalctl -u odoo-dev-monitor -f`

## Development

### Project Structure

```
odoo-server-moon/
├── app/                  # Application code
│   ├── api/              # API endpoints
│   ├── config/           # Configuration handling
│   ├── modules/          # Module management
│   ├── monitoring/       # System monitoring
│   ├── services/         # Service control
│   ├── static/           # Static assets
│   └── templates/        # HTML templates
├── config/               # Configuration files
├── docs/                 # Documentation
├── scripts/              # Scripts for installation and running
│   ├── install-remote.sh # One-line installation script
│   ├── install-service.sh # Local service installation
│   ├── odoo-dev-monitor.service # Systemd service file
│   ├── run.sh            # Script to run the application
│   └── uninstall-service.sh # Service uninstallation
├── tests/                # Test cases
├── odoo-monitor.py       # Main Python entry point
└── run.sh                # Symlink to scripts/run.sh
```

### Running Tests

```bash
python -m pytest tests/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
