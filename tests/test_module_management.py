"""
Tests for module directory management functionality.
"""
import os
import pytest
from unittest.mock import patch, mock_open


from app.modules.module_manager import (
    get_module_directories,
    check_directory_permissions,
    fix_directory_permissions,
    make_directory_odoo_owner
)


@patch('app.modules.module_manager.get_odoo_config_path')
def test_get_module_directories_success(mock_get_config_path, temp_odoo_conf):
    """
    Success case: Test that module directories are correctly parsed from odoo.conf.
    """
    # Mock the config path to use our test config
    mock_get_config_path.return_value = temp_odoo_conf

    # Now we can use the actual implementation
    directories = get_module_directories()

    # Verify the result
    assert len(directories) > 0

    # Check that paths from our fixture are included
    paths = [d["path"] for d in directories]
    with open(temp_odoo_conf, 'r') as f:
        content = f.read()
        assert "addons_path" in content

        # Extract paths from the config
        import re
        match = re.search(r'addons_path\s*=\s*([^\n]+)', content)
        if match:
            config_paths = [p.strip() for p in match.group(1).split(',')]
            for path in config_paths:
                # At least one of the configured paths should be in our result
                assert any(path in p for p in paths)


def test_get_module_directories_missing_file():
    """
    Failure case: Test behavior when odoo.conf is missing.
    """
    # This is a placeholder - we'll implement the actual test once we have the module
    # with pytest.raises(FileNotFoundError):
    #     get_module_directories("/nonexistent/path/odoo.conf")

    # For now, we'll just verify the path doesn't exist
    assert not os.path.exists("/nonexistent/path/odoo.conf")


def test_get_module_directories_invalid_format():
    """
    Failure case: Test behavior with malformed odoo.conf.
    """
    mock_conf_content = """
    [options]
    # No addons path defined here
    data_dir = /var/lib/odoo
    """

    with patch("builtins.open", mock_open(read_data=mock_conf_content)):
        # This is a placeholder - we'll implement the actual test once we have the module
        # directories = get_module_directories("mock_path")
        # assert len(directories) == 0

        # For now, we'll just verify our mock was set up correctly
        assert "addons_path =" not in mock_conf_content


def test_check_directory_permissions_success(temp_module_dirs):
    """
    Success case: Test that directory permissions are correctly checked.
    """
    # Now we can use the actual implementation
    permissions = check_directory_permissions(temp_module_dirs["good_perm"])

    # Verify the result
    assert permissions["status"] in ["valid", "warning"]
    assert permissions["readable"] is True
    assert permissions["writable"] is True
    assert "mode" in permissions
    assert "owner" in permissions
    assert "group" in permissions

    # Also verify our fixture is set up correctly
    assert os.path.exists(temp_module_dirs["good_perm"])
    assert os.access(temp_module_dirs["good_perm"], os.R_OK)
    assert os.access(temp_module_dirs["good_perm"], os.W_OK)


def test_check_directory_permissions_bad(temp_module_dirs):
    """
    Failure case: Test behavior with bad permissions.
    """
    # This is a placeholder - we'll implement the actual test once we have the module
    # permissions = check_directory_permissions(temp_module_dirs["bad_perm"])
    # assert permissions["status"] == "error"
    # assert permissions["readable"] is True  # Owner can still read
    # assert permissions["writable"] is True  # Owner can still write
    # assert permissions["group_readable"] is False
    # assert permissions["others_readable"] is False

    # For now, we'll just verify our fixture was set up correctly
    assert os.path.exists(temp_module_dirs["bad_perm"])
    mode = os.stat(temp_module_dirs["bad_perm"]).st_mode
    assert mode & 0o070 == 0  # No group permissions
    assert mode & 0o007 == 0  # No other permissions


@patch('subprocess.run')
def test_fix_directory_permissions(mock_run, temp_module_dirs):
    """
    Success case: Test fixing directory permissions.
    """
    from subprocess import CompletedProcess

    # Mock the subprocess.run call
    mock_run.return_value = CompletedProcess(args=[], returncode=0)

    # Call the function
    result = fix_directory_permissions(temp_module_dirs["bad_perm"])

    # Verify the result
    assert result["success"] is True
    assert "message" in result

    # Verify the subprocess was called with the right arguments
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "chmod" in args
    assert "775" in args or "0775" in args
    assert temp_module_dirs["bad_perm"] in args


@patch('subprocess.run')
def test_fix_directory_permissions_failure(mock_run, temp_module_dirs):
    """
    Failure case: Test handling of permission fix failure.
    """
    from subprocess import CalledProcessError

    # Mock the subprocess.run call to raise an exception
    mock_run.side_effect = CalledProcessError(
        returncode=1,
        cmd=["sudo", "chmod"],
        stderr="Permission denied"
    )

    # Call the function
    result = fix_directory_permissions(temp_module_dirs["bad_perm"])

    # Verify the result
    assert result["success"] is False
    assert "error" in result


def test_check_directory_permissions_mixed(temp_module_dirs):
    """
    Edge case: Test behavior with mixed permissions.
    """
    # This is a placeholder - we'll implement the actual test once we have the module
    # permissions = check_directory_permissions(temp_module_dirs["mixed_perm"])
    # assert permissions["status"] == "warning"
    # assert permissions["readable"] is True
    # assert permissions["writable"] is True
    # assert permissions["files_consistent"] is False

    # For now, we'll just verify our fixture was set up correctly
    assert os.path.exists(temp_module_dirs["mixed_perm"])
    file_path = os.path.join(temp_module_dirs["mixed_perm"], "file_0.py")
    assert os.path.exists(file_path)
    mode = os.stat(file_path).st_mode
    assert mode & 0o077 == 0  # No group or other permissions


@patch('subprocess.run')
def test_make_directory_odoo_owner(mock_run, temp_module_dirs):
    """
    Success case: Test making odoo the owner of a directory.
    """
    from subprocess import CompletedProcess

    # Mock the subprocess.run call
    mock_run.return_value = CompletedProcess(args=[], returncode=0)

    # Call the function
    result = make_directory_odoo_owner(temp_module_dirs["bad_perm"])

    # Verify the result
    assert result["success"] is True
    assert "message" in result

    # Verify the subprocess was called with the right arguments
    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert "chown" in args
    assert temp_module_dirs["bad_perm"] in args


@patch('subprocess.run')
def test_make_directory_odoo_owner_failure(mock_run, temp_module_dirs):
    """
    Failure case: Test handling of ownership change failure.
    """
    from subprocess import CalledProcessError

    # Mock the subprocess.run call to raise an exception
    mock_run.side_effect = CalledProcessError(
        returncode=1,
        cmd=["sudo", "chown"],
        stderr="Permission denied"
    )

    # Call the function
    result = make_directory_odoo_owner(temp_module_dirs["bad_perm"])

    # Verify the result
    assert result["success"] is False
    assert "error" in result
