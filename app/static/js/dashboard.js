/**
 * Dashboard JavaScript for the Odoo Dev Server Monitoring Tool
 */

// DOM elements
const cpuMetric = document.getElementById('cpu-metric');
const memoryMetric = document.getElementById('memory-metric');
const diskMetric = document.getElementById('disk-metric');
const systemInfo = document.getElementById('system-info');
const servicesList = document.getElementById('services-list');
const modulesList = document.getElementById('modules-list');
const logsContent = document.getElementById('logs-content');
const toast = document.getElementById('toast');
const connectionStatus = document.getElementById('connection-status');
const connectionIndicator = connectionStatus.querySelector('.status-indicator');
const connectionText = connectionStatus.querySelector('.status-text');
const moduleDetailsModal = document.getElementById('module-details-modal');
const modalTitle = document.getElementById('modal-title');
const modalBody = document.getElementById('modal-body');
const modalActionBtn = document.getElementById('modal-action-btn');
const modalCloseBtn = document.getElementById('modal-close-btn');
const closeModalBtn = document.getElementById('close-modal-btn');
const refreshServicesBtn = document.getElementById('refresh-services-btn');
const refreshModulesBtn = document.getElementById('refresh-modules-btn');
const clearLogsBtn = document.getElementById('clear-logs-btn');

// WebSocket connection
let socket;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;
let currentModulePath = null;

// Initialize the dashboard
function initDashboard() {
    // Update connection status
    updateConnectionStatus('disconnected', 'Disconnected');

    // Fetch initial data
    fetchStatus();
    fetchModules();

    // Set up WebSocket connection
    connectWebSocket();

    // Add event listeners
    document.addEventListener('click', handleButtonClicks);

    // Add specific event listeners
    refreshServicesBtn.addEventListener('click', fetchStatus);
    refreshModulesBtn.addEventListener('click', fetchModules);
    clearLogsBtn.addEventListener('click', clearLogs);

    // Modal event listeners
    closeModalBtn.addEventListener('click', closeModal);
    modalCloseBtn.addEventListener('click', closeModal);
    modalActionBtn.addEventListener('click', handleModalAction);

    // Add log entry for initialization
    addLogEntry('Dashboard initialized', 'info');
}

// Fetch status data from the API
async function fetchStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        updateServicesList(data.services);
        updateSystemMetrics(data.resources);

        addLogEntry('Status updated');
    } catch (error) {
        console.error('Error fetching status:', error);
        addLogEntry(`Error fetching status: ${error.message}`, 'error');
    }
}

// Fetch modules data from the API
async function fetchModules() {
    try {
        const response = await fetch('/api/modules');
        const data = await response.json();

        updateModulesList(data.modules);

        addLogEntry('Modules updated');
    } catch (error) {
        console.error('Error fetching modules:', error);
        addLogEntry(`Error fetching modules: ${error.message}`, 'error');
    }
}

// Update the services list in the UI
function updateServicesList(services) {
    if (!services) return;

    let html = '';
    let postgresInstances = [];

    // First, process main services and collect PostgreSQL instances
    for (const [serviceName, status] of Object.entries(services)) {
        // Check if this is a PostgreSQL instance
        if (serviceName.startsWith('postgres_postgresql_')) {
            postgresInstances.push({ name: serviceName, status: status });
            continue;
        }

        // Regular service
        const statusClass = getStatusClass(status);
        const displayName = serviceName.charAt(0).toUpperCase() + serviceName.slice(1);

        html += `
            <div class="service-item" data-service="${serviceName}">
                <div class="service-name">${displayName}</div>
                <div class="service-status status-${statusClass}">${status}</div>
                <div class="service-controls">
                    <button class="btn btn-start" data-action="start" data-service="${serviceName}" ${status === 'active' ? 'disabled' : ''}>Start</button>
                    <button class="btn btn-stop" data-action="stop" data-service="${serviceName}" ${status === 'inactive' ? 'disabled' : ''}>Stop</button>
                    <button class="btn btn-restart" data-action="restart" data-service="${serviceName}">Restart</button>
                </div>
            </div>
        `;
    }

    // Add PostgreSQL instances if any
    if (postgresInstances.length > 0) {
        html += '<div class="service-group">';
        html += '<div class="service-group-header">PostgreSQL Instances</div>';

        for (const instance of postgresInstances) {
            const statusClass = getStatusClass(instance.status);

            // Extract the instance name for display
            const instanceParts = instance.name.split('_postgresql_');
            const displayName = instanceParts.length > 1 ?
                `PostgreSQL @${instanceParts[1]}` : instance.name;

            html += `
                <div class="service-item postgres-instance" data-service="${instance.name}">
                    <div class="service-name">${displayName}</div>
                    <div class="service-status status-${statusClass}">${instance.status}</div>
                    <div class="service-controls">
                        <button class="btn btn-start" data-action="start" data-service="${instance.name}" ${instance.status === 'active' ? 'disabled' : ''}>Start</button>
                        <button class="btn btn-stop" data-action="stop" data-service="${instance.name}" ${instance.status === 'inactive' ? 'disabled' : ''}>Stop</button>
                        <button class="btn btn-restart" data-action="restart" data-service="${instance.name}">Restart</button>
                    </div>
                </div>
            `;
        }

        html += '</div>';
    }

    if (html === '') {
        html = '<div class="service-item"><div class="service-name">No services found</div></div>';
    }

    servicesList.innerHTML = html;
}

// Update the modules list in the UI
function updateModulesList(modules) {
    if (!modules) return;

    let html = '';

    for (const module of modules) {
        const statusClass = getStatusClass(module.status);

        html += `
            <div class="module-item" data-path="${module.path}" data-status="${module.status}">
                <div class="module-path">${module.path}</div>
                <div class="module-status status-${statusClass}">${module.status}</div>
                <button class="btn btn-fix" data-action="fix" data-path="${module.path}" ${module.status === 'ok' ? 'disabled' : ''}>Fix</button>
            </div>
        `;
    }

    if (html === '') {
        html = '<div class="module-item"><div class="module-path">No modules found</div></div>';
    }

    modulesList.innerHTML = html;

    // Add click event listeners to module items
    const moduleItems = modulesList.querySelectorAll('.module-item');
    moduleItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Don't show modal if the fix button was clicked
            if (e.target.tagName === 'BUTTON') return;

            const path = this.dataset.path;
            const moduleData = modules.find(m => m.path === path);

            if (moduleData) {
                showModuleDetails(path, moduleData.permissions);
            }
        });
    });
}

// Update the system metrics in the UI
function updateSystemMetrics(resources) {
    if (!resources) return;

    // Update CPU
    if (resources.cpu !== null) {
        const cpuValue = resources.cpu;
        const cpuValueElement = cpuMetric.querySelector('.metric-value');
        const cpuProgressElement = cpuMetric.querySelector('.progress');

        cpuValueElement.textContent = `${cpuValue.toFixed(1)}%`;
        cpuProgressElement.style.width = `${cpuValue}%`;

        // Change color based on usage
        if (cpuValue > 80) {
            cpuProgressElement.style.backgroundColor = 'var(--danger-color)';
        } else if (cpuValue > 60) {
            cpuProgressElement.style.backgroundColor = 'var(--warning-color)';
        } else {
            cpuProgressElement.style.backgroundColor = 'var(--secondary-color)';
        }
    }

    // Update Memory
    if (resources.memory !== null) {
        const memoryValue = resources.memory.percent;
        const memoryValueElement = memoryMetric.querySelector('.metric-value');
        const memoryProgressElement = memoryMetric.querySelector('.progress');

        memoryValueElement.textContent = `${memoryValue.toFixed(1)}%`;
        memoryProgressElement.style.width = `${memoryValue}%`;

        // Change color based on usage
        if (memoryValue > 80) {
            memoryProgressElement.style.backgroundColor = 'var(--danger-color)';
        } else if (memoryValue > 60) {
            memoryProgressElement.style.backgroundColor = 'var(--warning-color)';
        } else {
            memoryProgressElement.style.backgroundColor = 'var(--secondary-color)';
        }
    }

    // Update Disk
    if (resources.disk !== null) {
        const diskValue = resources.disk.percent;
        const diskValueElement = diskMetric.querySelector('.metric-value');
        const diskProgressElement = diskMetric.querySelector('.progress');

        diskValueElement.textContent = `${diskValue.toFixed(1)}%`;
        diskProgressElement.style.width = `${diskValue}%`;

        // Change color based on usage
        if (diskValue > 80) {
            diskProgressElement.style.backgroundColor = 'var(--danger-color)';
        } else if (diskValue > 60) {
            diskProgressElement.style.backgroundColor = 'var(--warning-color)';
        } else {
            diskProgressElement.style.backgroundColor = 'var(--secondary-color)';
        }
    }

    // Update System Info
    const infoContent = systemInfo.querySelector('.info-content');
    const date = new Date();
    infoContent.textContent = `Last updated: ${date.toLocaleTimeString()}`;
}

// Handle button clicks
function handleButtonClicks(event) {
    const target = event.target;

    // Service control buttons
    if (target.matches('.btn[data-action]')) {
        const action = target.dataset.action;

        if (action === 'start' || action === 'stop' || action === 'restart') {
            const service = target.dataset.service;
            controlService(service, action);
        } else if (action === 'fix') {
            const path = target.dataset.path;
            fixPermissions(path);
        }
    }
}

// Control a service (start, stop, restart)
async function controlService(service, action) {
    try {
        // Disable all buttons for this service
        const buttons = document.querySelectorAll(`.btn[data-service="${service}"]`);
        buttons.forEach(button => button.disabled = true);

        // Show loading state
        const serviceItem = document.querySelector(`.service-item[data-service="${service}"]`);
        serviceItem.classList.add('loading');

        // Call the API
        const response = await fetch(`/api/services/${service}/${action}`, {
            method: 'POST'
        });

        const data = await response.json();

        // Show toast notification
        showToast(data.message);

        // Add log entry
        addLogEntry(data.message, data.success ? 'info' : 'error');

        // Refresh status after a short delay
        setTimeout(fetchStatus, 1000);
    } catch (error) {
        console.error(`Error ${action}ing service ${service}:`, error);
        showToast(`Error ${action}ing service ${service}`);
        addLogEntry(`Error ${action}ing service ${service}: ${error.message}`, 'error');

        // Refresh status to reset UI
        fetchStatus();
    }
}

// Fix permissions for a module directory
async function fixPermissions(path) {
    try {
        // Disable the fix button
        const button = document.querySelector(`.btn[data-path="${path}"]`);
        button.disabled = true;

        // Show loading state
        const moduleItem = document.querySelector(`.module-item[data-path="${path}"]`);
        moduleItem.classList.add('loading');

        // Call the API
        const response = await fetch('/api/modules/fix', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ path })
        });

        const data = await response.json();

        // Show toast notification
        showToast(data.message);

        // Add log entry
        addLogEntry(data.message, data.success ? 'info' : 'error');

        // Refresh modules after a short delay
        setTimeout(fetchModules, 2000);
    } catch (error) {
        console.error(`Error fixing permissions for ${path}:`, error);
        showToast(`Error fixing permissions for ${path}`);
        addLogEntry(`Error fixing permissions for ${path}: ${error.message}`, 'error');

        // Refresh modules to reset UI
        fetchModules();
    }
}

// Connect to the WebSocket server
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    updateConnectionStatus('connecting', 'Connecting...');

    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log('WebSocket connected');
        addLogEntry('Real-time updates connected', 'success');
        updateConnectionStatus('connected', 'Connected');
        reconnectAttempts = 0;

        // Request initial status
        requestStatusUpdate();

        // Send a ping to keep the connection alive
        setInterval(() => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    };

    socket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            // Handle different message types
            if (data.type === 'status_update') {
                updateServicesList(data.services);
                updateSystemMetrics(data.resources);
                addLogEntry('Status updated', 'info');
            } else if (data.type === 'modules_update') {
                updateModulesList(data.modules);
                addLogEntry('Modules updated', 'info');
            } else if (data.type === 'error') {
                addLogEntry(`Error: ${data.message}`, 'error');
                showToast(`Error: ${data.message}`);
            }
        } catch (error) {
            console.error('Error processing WebSocket message:', error);
        }
    };

    socket.onclose = () => {
        console.log('WebSocket disconnected');
        updateConnectionStatus('disconnected', 'Disconnected');

        // Attempt to reconnect
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            const delay = Math.min(1000 * reconnectAttempts, 5000);

            addLogEntry(`Connection lost. Reconnecting in ${delay/1000} seconds...`, 'warning');

            setTimeout(connectWebSocket, delay);
        } else {
            addLogEntry('Connection lost. Please refresh the page.', 'error');
            showToast('Connection lost. Please refresh the page.');
        }
    };

    socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        addLogEntry('Connection error', 'error');
        updateConnectionStatus('disconnected', 'Connection Error');
    };
}

// Request status update via WebSocket
function requestStatusUpdate() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'get_status' }));
    }
}

// Request modules update via WebSocket
function requestModulesUpdate() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'get_modules' }));
    }
}

// Update connection status indicator
function updateConnectionStatus(status, text) {
    connectionIndicator.className = 'status-indicator ' + status;
    connectionText.textContent = text;
}

// Add a log entry to the logs panel
function addLogEntry(message, level = 'info') {
    const date = new Date();
    const timestamp = date.toLocaleTimeString();
    const logEntry = document.createElement('div');

    logEntry.className = `log-entry log-${level}`;
    logEntry.textContent = `[${timestamp}] ${message}`;

    logsContent.appendChild(logEntry);
    logsContent.scrollTop = logsContent.scrollHeight;

    // Limit the number of log entries
    const maxEntries = 100;
    const entries = logsContent.querySelectorAll('.log-entry');

    if (entries.length > maxEntries) {
        for (let i = 0; i < entries.length - maxEntries; i++) {
            logsContent.removeChild(entries[i]);
        }
    }
}

// Clear all log entries
function clearLogs() {
    logsContent.innerHTML = '';
    addLogEntry('Logs cleared', 'info');
}

// Show module details in modal
function showModuleDetails(path, permissions) {
    currentModulePath = path;
    modalTitle.textContent = 'Module Directory Details';

    // Create content for modal body
    let content = `<h4>${path}</h4>`;
    content += '<div class="permission-details">';

    // Add permission details
    const permissionItems = [
        { key: 'status', label: 'Status' },
        { key: 'owner', label: 'Owner' },
        { key: 'group', label: 'Group' },
        { key: 'is_odoo_owner', label: 'Odoo is Owner' },
        { key: 'is_odoo_group', label: 'Odoo is Group' },
        { key: 'current_user_in_odoo_group', label: 'Current User in Odoo Group' },
        { key: 'readable', label: 'Readable' },
        { key: 'writable', label: 'Writable' },
        { key: 'executable', label: 'Executable' },
        { key: 'group_readable', label: 'Group Readable' },
        { key: 'group_writable', label: 'Group Writable' },
        { key: 'group_executable', label: 'Group Executable' },
        { key: 'others_readable', label: 'Others Readable' },
        { key: 'others_writable', label: 'Others Writable' },
        { key: 'others_executable', label: 'Others Executable' },
        { key: 'files_consistent', label: 'Files Consistent' }
    ];

    permissionItems.forEach(item => {
        if (permissions[item.key] !== undefined) {
            const value = permissions[item.key];
            let valueClass = '';

            if (typeof value === 'boolean') {
                valueClass = value ? 'true' : 'false';
            }

            content += `
                <div class="permission-item">
                    <div class="permission-label">${item.label}</div>
                    <div class="permission-value ${valueClass}">${value}</div>
                </div>
            `;
        }
    });

    content += '</div>';

    // Add error message if any
    if (permissions.error) {
        content += `<div class="error-message">${permissions.error}</div>`;
    }

    // Add inconsistent files if any
    if (permissions.inconsistent_files && permissions.inconsistent_files.length > 0) {
        content += '<div class="inconsistent-files"><h4>Inconsistent Files</h4><ul>';
        permissions.inconsistent_files.forEach(file => {
            content += `<li>${file}</li>`;
        });
        content += '</ul></div>';
    }

    // Add odoo group members if any
    if (permissions.odoo_group_members && permissions.odoo_group_members.length > 0) {
        content += '<div class="odoo-group-members"><h4>Odoo Group Members</h4><ul>';
        permissions.odoo_group_members.forEach(user => {
            content += `<li>${user}</li>`;
        });
        content += '</ul></div>';
    } else {
        content += '<div class="odoo-group-members"><h4>Odoo Group Members</h4><p>No users found in odoo group</p></div>';
    }

    // Set modal content
    modalBody.innerHTML = content;

    // Configure action button based on status
    if (permissions.status === 'ok') {
        modalActionBtn.textContent = 'Permissions OK';
        modalActionBtn.disabled = true;
    } else {
        modalActionBtn.textContent = 'Fix Permissions';
        modalActionBtn.disabled = false;
    }

    // Show modal
    moduleDetailsModal.classList.add('show');
}

// Close the modal
function closeModal() {
    moduleDetailsModal.classList.remove('show');
    currentModulePath = null;
}

// Handle modal action button click
function handleModalAction() {
    if (currentModulePath) {
        fixPermissions(currentModulePath);
        closeModal();
    }
}

// Show a toast notification
function showToast(message, duration = 3000) {
    const toastContent = toast.querySelector('.toast-content');
    toastContent.textContent = message;

    toast.classList.add('show');

    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

// Helper function to get CSS class for status
function getStatusClass(status) {
    switch (status) {
        case 'active':
            return 'active';
        case 'inactive':
        case 'failed':
        case 'error':
            return 'failed';
        case 'warning':
        case 'partially_fixed':
            return 'warning';
        case 'ok':
            return 'ok';
        default:
            return 'warning';
    }
}

// Initialize the dashboard when the DOM is loaded
document.addEventListener('DOMContentLoaded', initDashboard);
