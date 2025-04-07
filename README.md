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

## Installation

### Prerequisites

- Python 3.x
- Odoo development environment
- PostgreSQL
- sudo access (for service control and permission fixes)

### One-Line Installation

Install with a single command (requires sudo):

```bash
curl -sSL https://raw.githubusercontent.com/solutionsunity/odoo-server-moon/main/scripts/install-remote.sh | sudo bash
```

With custom options:

```bash
curl -sSL https://raw.githubusercontent.com/solutionsunity/odoo-server-moon/main/scripts/install-remote.sh | sudo bash -s -- --dir /opt/custom-path --port 8080
```

Available options:
- `--dir DIR`: Installation directory (default: /opt/odoo-server-moon)
- `--branch BRANCH`: Git branch to use (default: main)
- `--port PORT`: Port to run the server on (default: 8008)
- `--no-start`: Don't start the service after installation

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/solutionsunity/odoo-server-moon.git
   cd odoo-server-moon
   ```

2. Run the application (choose one method):
   ```bash
   # Using the shell script
   ./run.sh  # Symlink to scripts/run.sh

   # OR using Python directly
   ./odoo-monitor.py
   ```

3. Access the web interface at http://localhost:8008

### Install as a Service

To install the tool as a systemd service that runs automatically:

```bash
sudo ./scripts/install-service.sh
```

This will:
- Install dependencies
- Create a systemd service
- Enable the service to start on boot
- Start the service immediately

## Configuration

Configuration is stored in `config/config.json`. You can modify:

- Server host and port
- Monitoring refresh interval
- Service names
- PostgreSQL instance detection

## Usage

### Web Interface

The web interface provides:
- System metrics (CPU, memory, disk)
- Service status and control buttons
- Module directories with permission status
- Detailed permission information
- One-click permission fixes

### Service Management

If installed as a service:

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
