/**
 * Time Tracker Application JavaScript
 * Handles client-side functionality for the time tracking app
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeApp();
});

function initializeApp() {
    // Initialize Feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Initialize date pickers
    initializeDatePickers();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize auto-dismiss alerts
    initializeAlerts();
    
    // Initialize form enhancements
    initializeFormEnhancements();
}

/**
 * Initialize Flatpickr date pickers
 */
function initializeDatePickers() {
    if (typeof flatpickr !== 'undefined') {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            flatpickr(input, {
                theme: 'dark',
                dateFormat: 'Y-m-d',
                allowInput: true,
                defaultDate: input.value || null,
                locale: {
                    firstDayOfWeek: 1 // Monday
                }
            });
        });
    }
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Auto-dismiss alerts after 5 seconds
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

/**
 * Form enhancements and validation
 */
function initializeFormEnhancements() {
    // Hours input formatting
    const hoursInputs = document.querySelectorAll('input[name="hours"]');
    hoursInputs.forEach(input => {
        input.addEventListener('blur', formatHoursInput);
        input.addEventListener('input', validateHoursInput);
    });
    
    // Project selection enhancement
    const projectSelects = document.querySelectorAll('select[name="project_id"]');
    projectSelects.forEach(select => {
        select.addEventListener('change', updateProjectInfo);
    });
}

/**
 * Format hours input on blur
 */
function formatHoursInput(event) {
    const input = event.target;
    const value = input.value.trim();
    
    if (value && validateHours(value)) {
        const decimal = parseHours(value);
        // Keep original format if it's already in time format
        if (value.includes(':')) {
            input.value = value;
        } else {
            // Convert to time format for better readability
            input.value = decimalToTimeFormat(decimal);
        }
    }
}

/**
 * Validate hours input in real-time
 */
function validateHoursInput(event) {
    const input = event.target;
    const value = input.value.trim();
    
    // Remove existing feedback
    const existingFeedback = input.parentNode.querySelector('.invalid-feedback');
    if (existingFeedback) {
        existingFeedback.remove();
    }
    input.classList.remove('is-invalid', 'is-valid');
    
    if (value) {
        if (validateHours(value)) {
            const decimal = parseHours(value);
            if (decimal > 24) {
                showInputError(input, 'Hours cannot exceed 24 per day');
            } else {
                input.classList.add('is-valid');
            }
        } else {
            showInputError(input, 'Please enter valid hours (e.g., 8, 8:30, or 8.5)');
        }
    }
}

/**
 * Show input validation error
 */
function showInputError(input, message) {
    input.classList.add('is-invalid');
    const feedback = document.createElement('div');
    feedback.className = 'invalid-feedback';
    feedback.textContent = message;
    input.parentNode.appendChild(feedback);
}

/**
 * Update project information when selection changes
 */
function updateProjectInfo(event) {
    const select = event.target;
    const selectedOption = select.options[select.selectedIndex];
    
    // You could add project-specific information display here
    // For example, showing project description or default hours
}

/**
 * Validate hours string format
 */
function validateHours(value) {
    if (!value) return false;
    
    // Decimal format (8.5)
    if (/^\d+(\.\d+)?$/.test(value)) {
        return parseFloat(value) > 0;
    }
    
    // Time format (8:30)
    if (/^\d+:[0-5]\d$/.test(value)) {
        const parts = value.split(':');
        const hours = parseInt(parts[0]);
        const minutes = parseInt(parts[1]);
        return hours >= 0 && minutes >= 0 && minutes < 60;
    }
    
    // Simple hours (8)
    if (/^\d+$/.test(value)) {
        return parseInt(value) > 0;
    }
    
    return false;
}

/**
 * Parse hours string to decimal
 */
function parseHours(value) {
    if (!value) return 0;
    
    // Decimal format
    if (/^\d+(\.\d+)?$/.test(value)) {
        return parseFloat(value);
    }
    
    // Time format
    if (/^\d+:[0-5]\d$/.test(value)) {
        const parts = value.split(':');
        const hours = parseInt(parts[0]);
        const minutes = parseInt(parts[1]);
        return hours + (minutes / 60);
    }
    
    // Simple hours
    if (/^\d+$/.test(value)) {
        return parseInt(value);
    }
    
    return 0;
}

/**
 * Convert decimal hours to time format
 */
function decimalToTimeFormat(decimal) {
    if (!decimal) return '0:00';
    
    const totalMinutes = Math.round(decimal * 60);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    return `${hours}:${minutes.toString().padStart(2, '0')}`;
}

/**
 * Utility function to show toast notifications
 */
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to toast container or create one
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    container.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove element after hiding
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

/**
 * Utility function to format dates for display
 */
function formatDateForDisplay(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Utility function to calculate working days between dates
 */
function calculateWorkingDays(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    let workingDays = 0;
    
    for (let date = new Date(start); date <= end; date.setDate(date.getDate() + 1)) {
        const dayOfWeek = date.getDay();
        if (dayOfWeek !== 0 && dayOfWeek !== 6) { // Not Sunday (0) or Saturday (6)
            workingDays++;
        }
    }
    
    return workingDays;
}

/**
 * Export functions for global use
 */
window.TimeTracker = {
    showToast,
    formatDateForDisplay,
    calculateWorkingDays,
    validateHours,
    parseHours,
    decimalToTimeFormat
};
