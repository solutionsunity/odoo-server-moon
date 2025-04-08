# Testing Strategy

This document outlines the testing approach for the Odoo Dev Server Monitoring Tool, focusing on comprehensive test coverage with minimal overhead.

## Testing Principles

Each functionality will be tested with three types of test cases:
1. **Success Case**: Verifies expected behavior under normal conditions
2. **Failure Case**: Ensures proper error handling when operations fail
3. **Edge Case**: Tests boundary conditions and unusual scenarios (where applicable)

## Test Environment Setup

Before running tests, ensure:
1. A test Odoo environment is available
2. Test directories with various permission states exist
3. The test user has sudo privileges for service control operations
4. PostgreSQL is installed and configured

## Test Categories

### 1. Service Monitoring Tests

| Test Type | Description | Example |
|-----------|-------------|---------|
| Success | Verify service status is correctly reported | Test that running Odoo service reports as "active" |
| Success | Verify PostgreSQL service detection | Test that PostgreSQL and its version-specific service are detected |
| Failure | Handle unavailable service gracefully | Test behavior when service doesn't exist |
| Edge | Handle service in transitional states | Test behavior during service startup/shutdown |

### 2. Service Control Tests

| Test Type | Description | Example |
|-----------|-------------|---------|
| Success | Verify service start/stop/restart works | Test that stop command properly stops the service |
| Success | Verify service status updates in UI | Test that UI updates when service state changes |
| Failure | Handle failed control operations | Test behavior when permission denied |
| Edge | Handle rapid sequential operations | Test behavior when starting an already starting service |

### 3. System Resource Monitoring Tests

| Test Type | Description | Example |
|-----------|-------------|---------|
| Success | Verify resource metrics are collected | Test CPU, memory, disk usage reporting |
| Success | Verify OS information display | Test that OS name, version, and kernel are displayed |
| Failure | Handle resource collection errors | Test behavior when metrics are unavailable |
| Edge | Handle extreme resource values | Test with very high/low resource usage |

### 4. Module Directory Management Tests

| Test Type | Description | Example |
|-----------|-------------|---------|
| Success | Verify module directories are listed | Test parsing of odoo.conf for addon paths |
| Success | Verify ownership and permissions display | Test that ownership and permissions are correctly shown |
| Success | Verify action buttons functionality | Test that "Fix Permissions" and "Make Odoo Owner" buttons work |
| Failure | Handle missing directories gracefully | Test behavior with non-existent directories |
| Failure | Handle permission denied errors | Test behavior when directories can't be accessed |
| Edge | Handle unusual permission scenarios | Test with mixed permission states |
| Edge | Handle directories with special characters | Test paths with spaces, quotes, and other special characters |

### 5. Permission Fix Tests

| Test Type | Description | Example |
|-----------|-------------|---------|
| Success | Verify permissions are fixed correctly | Test that fix resolves permission issues |
| Success | Verify ownership change functionality | Test that "Make Odoo Owner" changes ownership correctly |
| Failure | Handle permission fix failures | Test behavior when fix operation fails |
| Failure | Handle ownership change failures | Test behavior when ownership change fails |
| Edge | Handle partial permission fixes | Test with directories that can't be fully fixed |

### 6. User Management Tests

| Test Type | Description | Example |
|-----------|-------------|---------|
| Success | Verify users are correctly listed | Test that system users are displayed |
| Success | Verify odoo group membership detection | Test that users in odoo group are correctly identified |
| Failure | Handle user listing errors | Test behavior when user information can't be accessed |
| Edge | Handle users with special permissions | Test with users having different permission levels |

### 7. API Endpoint Tests

| Test Type | Description | Example |
|-----------|-------------|---------|
| Success | Verify API endpoints return correct data | Test that /status returns valid service status |
| Success | Verify module management endpoints | Test that module directory endpoints work correctly |
| Failure | Handle API errors gracefully | Test behavior with invalid parameters |
| Edge | Handle concurrent API requests | Test multiple simultaneous requests |

### 8. Configuration Tests

| Test Type | Description | Example |
|-----------|-------------|---------|
| Success | Verify config is loaded correctly | Test that server starts with specified port |
| Success | Verify dynamic configuration | Test that changes to config are applied correctly |
| Failure | Handle invalid configuration | Test behavior with malformed config.json |
| Edge | Handle missing optional config | Test with minimal configuration |

### 9. UI Tests

| Test Type | Description | Example |
|-----------|-------------|---------|
| Success | Verify UI components render correctly | Test that all panels display properly |
| Success | Verify UI interactions work | Test that buttons and controls function as expected |
| Failure | Handle UI rendering errors | Test behavior when data is missing or invalid |
| Edge | Handle responsive layout | Test UI on different screen sizes |

## Test Implementation

Tests will be implemented using Python's `pytest` framework, with the following structure:

```
tests/
  ├── test_service_monitoring.py
  ├── test_service_control.py
  ├── test_resource_monitoring.py
  ├── test_module_management.py
  ├── test_permission_fix.py
  ├── test_user_management.py
  ├── test_api.py
  ├── test_config.py
  └── test_ui.py
```

Each test file will contain test functions for success, failure, and edge cases for the respective functionality.

## Test Fixtures

Common test fixtures will be used to:
- Set up mock services
- Create test directories with various permissions
- Configure test environments
- Simulate system resource states
- Create test users with different permissions

## Continuous Integration

Tests should be designed to run in CI environments for potential future public repository use.

## Running Tests

To run the tests:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=app

# Run specific test category
pytest tests/test_module_management.py
```

## Test Documentation

Each test should include:
- Clear description of what is being tested
- Setup requirements
- Expected outcomes
- Cleanup procedures if needed
