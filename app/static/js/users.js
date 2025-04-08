/**
 * User Management JavaScript for the Odoo Dev Server Monitoring Tool
 */

// DOM elements
const usersList = document.getElementById('users-list');
const refreshUsersBtn = document.getElementById('refresh-users-btn');
const odooUserElement = document.getElementById('odoo-user');
const odooGroupElement = document.getElementById('odoo-group');
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
    
    for (const user of users) {
        const inGroup = user.in_odoo_group;
        const statusClass = inGroup ? 'in-group' : 'not-in-group';
        const statusText = inGroup ? 'In Odoo Group' : 'Not in Odoo Group';
        
        html += `
            <div class="user-item" data-username="${user.username}">
                <div class="user-name">${user.username}</div>
                <div class="user-status ${statusClass}">${statusText}</div>
                <div class="user-action">
                    ${!inGroup ? `<button class="btn btn-primary" data-action="add-to-group" data-username="${user.username}">Add to Group</button>` : ''}
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
    odooUserElement.textContent = odooUser || 'Unknown';
    odooGroupElement.textContent = odooGroup || 'Unknown';
}

// Handle user action button clicks
function handleUserAction(event) {
    const target = event.target;
    
    if (target.matches('[data-action="add-to-group"]')) {
        const username = target.dataset.username;
        showAddToGroupModal(username);
    }
}

// Show the add to group modal
function showAddToGroupModal(username) {
    currentUsername = username;
    selectedUsername.textContent = username;
    
    // Show the modal
    userActionModal.classList.add('show');
}

// Close the user modal
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

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', initUserManagement);
