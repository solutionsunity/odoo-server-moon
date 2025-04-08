/**
 * User Management JavaScript for the Odoo Dev Server Monitoring Tool
 */

// DOM elements
const usersList = document.getElementById('users-list');
const odooUserElement = document.getElementById('odoo-user');
const odooGroupElement = document.getElementById('odoo-group');
const modalOdooUserElement = document.getElementById('modal-odoo-user');
const modalOdooGroupElement = document.getElementById('modal-odoo-group');
const refreshUsersBtn = document.getElementById('refresh-users-btn');
const usersModal = document.getElementById('users-modal');
const closeUsersModalBtn = document.getElementById('close-users-modal-btn');
const usersModalCloseBtn = document.getElementById('users-modal-close-btn');
const userActionModal = document.getElementById('user-action-modal');
const userModalTitle = document.getElementById('user-modal-title');
const userModalBody = document.getElementById('user-modal-body');
const selectedUsername = document.getElementById('selected-username');
const userModalActionBtn = document.getElementById('user-modal-action-btn');
const userModalCloseBtn = document.getElementById('user-modal-close-btn');
const closeUserModalBtn = document.getElementById('close-user-modal-btn');

// Current selected user
let currentUsername = null;

// Initialize user management
function initUserManagement() {
    // Fetch initial data
    fetchUsers();

    // Add event listeners
    refreshUsersBtn.addEventListener('click', fetchUsers);
    closeUsersModalBtn.addEventListener('click', closeUsersModal);
    usersModalCloseBtn.addEventListener('click', closeUsersModal);
    userModalActionBtn.addEventListener('click', handleAddUserToGroup);
    userModalCloseBtn.addEventListener('click', closeUserModal);
    closeUserModalBtn.addEventListener('click', closeUserModal);

    // Add event delegation for user actions
    usersList.addEventListener('click', handleUserAction);
}

// Fetch users from the API
async function fetchUsers() {
    try {
        addLogEntry('Fetching users...');

        const response = await fetch('/api/users');
        const data = await response.json();

        updateUsersList(data.users);
        updateOdooInfo(data.odoo_user, data.odoo_group);

        addLogEntry('Users fetched successfully');
    } catch (error) {
        console.error('Error fetching users:', error);
        addLogEntry(`Error fetching users: ${error.message}`, 'error');
        showToast(`Error fetching users: ${error.message}`, 'error');
    }
}

// Update the users list in the UI
function updateUsersList(users) {
    if (!users) return;

    let html = '';

    // Add table header
    html += `
        <div class="user-header">
            <div class="user-name-header">Username</div>
            <div class="user-status-header">Status</div>
            <div class="user-actions-header">Actions</div>
        </div>
    `;

    for (const user of users) {
        const inGroup = user.in_odoo_group;
        const statusClass = inGroup ? 'in-group' : 'not-in-group';
        const statusText = inGroup ? 'In Odoo Group' : 'Not in Odoo Group';

        html += `
            <div class="user-item" data-username="${user.username}">
                <div class="user-name">${user.username}</div>
                <div class="user-status ${statusClass}">${statusText}</div>
                <div class="user-actions">
                    ${!inGroup ? `<button class="btn btn-primary btn-small" data-action="add-to-group" data-username="${user.username}">Add to Group</button>` : ''}
                    <button class="btn btn-secondary btn-small" data-action="take-ownership" data-username="${user.username}">Take Ownership</button>
                </div>
            </div>
        `;
    }

    if (html === '') {
        html = '<div class="user-item"><div class="user-name">No users found</div></div>';
    }

    usersList.innerHTML = html;
}

// Update the Odoo user and group information
function updateOdooInfo(odooUser, odooGroup) {
    // Update in the summary panel
    odooUserElement.textContent = odooUser || 'Unknown';
    odooGroupElement.textContent = odooGroup || 'Unknown';

    // Update in the modal
    if (modalOdooUserElement) {
        modalOdooUserElement.textContent = odooUser || 'Unknown';
    }

    if (modalOdooGroupElement) {
        modalOdooGroupElement.textContent = odooGroup || 'Unknown';
    }
}

// Handle user action button clicks
function handleUserAction(event) {
    const target = event.target;

    if (target.matches('[data-action="add-to-group"]')) {
        const username = target.dataset.username;
        showAddToGroupModal(username);
    } else if (target.matches('[data-action="take-ownership"]')) {
        const username = target.dataset.username;
        takeOwnership(username);
    }
}

// Show the add to group modal
function showAddToGroupModal(username) {
    currentUsername = username;
    selectedUsername.textContent = username;

    // Show the modal
    userActionModal.classList.add('show');
}

// Show the users modal
function showUsersModal() {
    // Fetch fresh data
    fetchUsers();

    // Show the modal
    usersModal.classList.add('show');
}

// Close the users modal
function closeUsersModal() {
    usersModal.classList.remove('show');
}

// Close the user action modal
function closeUserModal() {
    userActionModal.classList.remove('show');
    currentUsername = null;
}

// Handle adding a user to the odoo group
async function handleAddUserToGroup() {
    if (!currentUsername) return;

    try {
        // Disable the button and show loading state
        userModalActionBtn.disabled = true;
        userModalActionBtn.textContent = 'Adding...';

        // Call the API
        const response = await fetch('/api/users/add-to-odoo-group', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: currentUsername })
        });

        const data = await response.json();

        if (data.success) {
            addLogEntry(`User ${currentUsername} added to odoo group successfully`);
            showToast(`User ${currentUsername} added to odoo group`, 'success');

            // Close the modal and refresh the users list
            closeUserModal();
            fetchUsers();
        } else {
            addLogEntry(`Error adding user ${currentUsername} to odoo group: ${data.error || 'Unknown error'}`, 'error');
            showToast(`Error adding user to odoo group: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error adding user to odoo group:', error);
        addLogEntry(`Error adding user ${currentUsername} to odoo group: ${error.message}`, 'error');
        showToast(`Error adding user to odoo group: ${error.message}`, 'error');
    } finally {
        // Reset the button
        userModalActionBtn.disabled = false;
        userModalActionBtn.textContent = 'Add to Odoo Group';
    }
}

// Take ownership of module directories
async function takeOwnership(username) {
    try {
        // Show confirmation dialog
        if (!confirm(`Are you sure you want ${username} to take ownership of module directories?`)) {
            return;
        }

        addLogEntry(`Taking ownership of module directories for ${username}...`);

        // Call the API
        const response = await fetch('/api/users/take-ownership', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username })
        });

        const data = await response.json();

        if (data.success) {
            addLogEntry(`${username} has taken ownership of module directories successfully`);
            showToast(`${username} has taken ownership of module directories`, 'success');

            // Refresh modules list
            if (typeof fetchModules === 'function') {
                fetchModules();
            }
        } else {
            addLogEntry(`Error taking ownership for ${username}: ${data.error || 'Unknown error'}`, 'error');
            showToast(`Error taking ownership: ${data.error || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error taking ownership:', error);
        addLogEntry(`Error taking ownership for ${username}: ${error.message}`, 'error');
        showToast(`Error taking ownership: ${error.message}`, 'error');
    }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', initUserManagement);
