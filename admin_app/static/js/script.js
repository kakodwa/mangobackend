// Admin Dashboard JavaScript Utilities
// ==============================================

/**
 * Mobile Menu Toggle
 */
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.querySelector('.sidebar');

    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            menuToggle.classList.toggle('active');
        });

        // Close menu when a nav link is clicked
        const navLinks = sidebar.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                sidebar.classList.remove('active');
                menuToggle.classList.remove('active');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!sidebar.contains(event.target) && !menuToggle.contains(event.target)) {
                sidebar.classList.remove('active');
                menuToggle.classList.remove('active');
            }
        });
    }
});

/**
 * Open Modal by ID
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

/**
 * Close Modal by ID
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * View User Details
 */
function viewUserDetails(userName) {
    openModal('userModal');
    
    // Generate mock user details
    const userDetails = document.getElementById('userDetails');
    if (userDetails) {
        userDetails.innerHTML = `
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 6px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div>
                        <label style="color: #666; font-size: 12px;">Full Name</label>
                        <p style="margin: 5px 0;">${userName}</p>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">Email</label>
                        <p style="margin: 5px 0;">user@email.com</p>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">Phone</label>
                        <p style="margin: 5px 0;">+265 123 456 789</p>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">User Type</label>
                        <p style="margin: 5px 0;">Customer</p>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">Status</label>
                        <p style="margin: 5px 0;"><span class="badge badge-green">Active</span></p>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">Joined</label>
                        <p style="margin: 5px 0;">2024-01-10</p>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">Verified</label>
                        <p style="margin: 5px 0;"><span class="badge badge-green">✓ Yes</span></p>
                    </div>
                    <div>
                        <label style="color: #666; font-size: 12px;">District</label>
                        <p style="margin: 5px 0;">Lilongwe</p>
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * Open Shop Approval Modal
 */
function openApprovalModal(shopName, ownerName) {
    openModal('approvalModal');
    
    const shopNameDisplay = document.getElementById('shopNameDisplay');
    const ownerDisplay = document.getElementById('ownerDisplay');
    
    if (shopNameDisplay) {
        shopNameDisplay.textContent = shopName;
    }
    if (ownerDisplay) {
        ownerDisplay.textContent = `Owner: ${ownerName}`;
    }
}

/**
 * Open Property Approval Modal
 */
function openPropertyApproval(propertyName) {
    openModal('propertyApprovalModal');
    
    // You can add property-specific logic here
    console.log('Opening approval for property:', propertyName);
}

/**
 * Close modal when clicking outside of it
 */
window.onclick = function(event) {
    // Get all modals
    const modals = document.querySelectorAll('.modal');
    
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.classList.remove('active');
        }
    });
}

/**
 * Search/Filter functionality
 */
function initializeSearch() {
    const searchInputs = document.querySelectorAll('.search-box input');
    const filterSelects = document.querySelectorAll('.filter-select');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            console.log('Search term:', searchTerm);
            // Implement table filtering logic here
        });
    });
    
    filterSelects.forEach(select => {
        select.addEventListener('change', function(e) {
            const filterValue = e.target.value;
            console.log('Filter applied:', filterValue);
            // Implement filtering logic here
        });
    });
}

/**
 * Initialize page on load
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Admin Dashboard loaded');
    initializeSearch();
    
    // Add active nav link highlighting
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navLinks = document.querySelectorAll('.nav-menu a');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === currentPage || 
            (currentPage === '' && link.getAttribute('href') === 'index.html')) {
            link.classList.add('active');
        }
    });
});

/**
 * Table Action Handlers
 */
function handleApproval(itemId, decision) {
    console.log(`Item ${itemId} - Decision: ${decision}`);
    // Implement approval logic
    alert(`${decision} decision submitted for item ${itemId}`);
}

function handleEdit(itemId) {
    console.log('Edit item:', itemId);
    // Implement edit logic
}

function handleDelete(itemId) {
    if (confirm('Are you sure you want to delete this item?')) {
        console.log('Delete item:', itemId);
        // Implement delete logic
    }
}

function handleSuspend(itemId) {
    if (confirm('Are you sure you want to suspend this item?')) {
        console.log('Suspend item:', itemId);
        // Implement suspend logic
    }
}

/**
 * Export data to CSV
 */
function exportToCSV(tableName) {
    const table = document.querySelector('table');
    if (!table) {
        alert('No table found');
        return;
    }
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        let rowData = [];
        const cells = row.querySelectorAll('th, td');
        cells.forEach(cell => {
            rowData.push(cell.textContent.trim());
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${tableName || 'export'}.csv`;
    a.click();
}

/**
 * Print functionality
 */
function printTable() {
    window.print();
}

/**
 * Format date to readable format
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

/**
 * Notification system
 */
function showNotification(message, type = 'success') {
    const notificationId = 'notification-' + Date.now();
    const notification = document.createElement('div');
    notification.id = notificationId;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background-color: ${type === 'success' ? '#2ECC71' : type === 'error' ? '#E74C3C' : '#FF8C00'};
        color: white;
        border-radius: 6px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideInRight 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

/**
 * Pagination handler
 */
function goToPage(pageNumber) {
    console.log('Go to page:', pageNumber);
    // Implement pagination logic
}

/**
 * Sort table by column
 */
function sortTable(columnIndex) {
    const table = document.querySelector('table');
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Try numeric comparison first
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return aNum - bNum;
        }
        
        // Fall back to string comparison
        return aValue.localeCompare(bValue);
    });
    
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Bulk action handler
 */
function bulkAction(action) {
    const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
    if (checkboxes.length === 0) {
        alert('Please select at least one item');
        return;
    }
    
    const selectedIds = Array.from(checkboxes).map(cb => cb.value);
    console.log(`Performing ${action} on:`, selectedIds);
    
    if (confirm(`Are you sure you want to ${action} ${selectedIds.length} item(s)?`)) {
        // Implement bulk action logic
        showNotification(`${action.charAt(0).toUpperCase() + action.slice(1)} completed for ${selectedIds.length} item(s)`, 'success');
    }
}

/**
 * Real-time search with debounce
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function() {
            const tooltip = this.getAttribute('data-tooltip');
            console.log('Tooltip:', tooltip);
        });
    });
}

// Export functions for use
window.openModal = openModal;
window.closeModal = closeModal;
window.viewUserDetails = viewUserDetails;
window.openApprovalModal = openApprovalModal;
window.openPropertyApproval = openPropertyApproval;
window.handleApproval = handleApproval;
window.handleEdit = handleEdit;
window.handleDelete = handleDelete;
window.handleSuspend = handleSuspend;
window.exportToCSV = exportToCSV;
window.printTable = printTable;
window.showNotification = showNotification;
window.goToPage = goToPage;
window.sortTable = sortTable;
window.bulkAction = bulkAction;
