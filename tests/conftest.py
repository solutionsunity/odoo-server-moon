"""
Shared test fixtures for the Odoo Dev Server Monitoring Tool.
"""
import json
import os
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_config():
    """Fixture providing a test configuration."""
    return {
        "server": {
            "host": "127.0.0.1",
            "port": 8008
        },
        "monitoring": {
            "refresh_interval": 5,
            "max_log_entries": 100
        },
        "services": {
            "odoo": {
                "service_name": "odoo",
                "config_file": "/etc/odoo/odoo.conf"
            },
            "postgres": {
                "service_name": "postgresql"
            }
        },
        "logging": {
            "level": "info",
            "file": "logs/monitor.log"
        }
    }


@pytest.fixture
def temp_config_file(mock_config):
    """Fixture providing a temporary config file."""
    temp_dir = tempfile.mkdtemp()
    config_path = os.path.join(temp_dir, "config.json")
    
    with open(config_path, 'w') as f:
        json.dump(mock_config, f)
    
    yield config_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_odoo_conf():
    """Fixture providing mock Odoo configuration content."""
    return """
[options]
addons_path = /var/lib/odoo/addons,/usr/lib/python3/dist-packages/odoo/addons,/opt/custom_modules
data_dir = /var/lib/odoo
admin_passwd = admin
db_host = False
db_port = False
db_user = odoo
db_password = False
"""


@pytest.fixture
def temp_odoo_conf(mock_odoo_conf):
    """Fixture providing a temporary odoo.conf file."""
    temp_dir = tempfile.mkdtemp()
    conf_path = os.path.join(temp_dir, "odoo.conf")
    
    with open(conf_path, 'w') as f:
        f.write(mock_odoo_conf)
    
    yield conf_path
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_service_active():
    """Fixture for mocking an active service."""
    with patch('subprocess.run') as mock_run:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "active"
        mock_run.return_value = mock_process
        yield mock_run


@pytest.fixture
def mock_service_inactive():
    """Fixture for mocking an inactive service."""
    with patch('subprocess.run') as mock_run:
        mock_process = MagicMock()
        mock_process.returncode = 3
        mock_process.stdout = "inactive"
        mock_run.return_value = mock_process
        yield mock_run


@pytest.fixture
def mock_system_resources():
    """Fixture for mocking system resource data."""
    with patch('psutil.cpu_percent') as mock_cpu, \
         patch('psutil.virtual_memory') as mock_memory, \
         patch('psutil.disk_usage') as mock_disk:
        
        mock_cpu.return_value = 25.5
        
        mock_memory_obj = MagicMock()
        mock_memory_obj.percent = 40.2
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = MagicMock()
        mock_disk_obj.percent = 65.8
        mock_disk.return_value = mock_disk_obj
        
        yield {
            "cpu": mock_cpu,
            "memory": mock_memory,
            "disk": mock_disk
        }


@pytest.fixture
def temp_module_dirs():
    """Fixture providing temporary module directories with different permissions."""
    base_dir = tempfile.mkdtemp()
    
    # Create directories with different permissions
    dirs = {
        "good_perm": os.path.join(base_dir, "good_perm"),
        "bad_perm": os.path.join(base_dir, "bad_perm"),
        "mixed_perm": os.path.join(base_dir, "mixed_perm")
    }
    
    for dir_path in dirs.values():
        os.makedirs(dir_path)
    
    # Create some files in each directory
    for dir_path in dirs.values():
        for i in range(3):
            with open(os.path.join(dir_path, f"file_{i}.py"), 'w') as f:
                f.write(f"# Test file {i}")
    
    # Set permissions
    os.chmod(dirs["good_perm"], 0o755)
    os.chmod(dirs["bad_perm"], 0o700)  # Owner only
    
    # Mixed permissions for files
    for i in range(3):
        os.chmod(os.path.join(dirs["mixed_perm"], f"file_{i}.py"), 0o600)  # Owner only
    
    yield dirs
    
    # Cleanup
    shutil.rmtree(base_dir)
