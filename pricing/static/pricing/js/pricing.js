/**
 * Pricing App JavaScript
 * Handles all interactive functionality for the pricing module
 */

class PricingManager {
    constructor() {
        this.init();
    }

    init() {
        this.initTooltips();
        this.initModals();
        this.initFormValidation();
        this.initPriceFormatting();
        this.initTableInteractions();
        this.initAnimations();
    }

    /**
     * Initialize Bootstrap tooltips
     */
    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    /**
     * Initialize modal functionality
     */
    initModals() {
        // Handle delete confirmation modals
        const deleteButtons = document.querySelectorAll('[data-bs-target^="#deleteModal"]');
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const modalId = button.getAttribute('data-bs-target');
                const modal = document.querySelector(modalId);
                if (modal) {
                    // Add animation class
                    modal.classList.add('fade-in');
                }
            });
        });

        // Handle modal close events
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('hidden.bs.modal', () => {
                modal.classList.remove('fade-in');
            });
        });
    }

    /**
     * Initialize form validation
     */
    initFormValidation() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });

            // Real-time validation
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });
            });
        });
    }

    /**
     * Validate individual form field
     */
    validateField(field) {
        const value = field.value.trim();
        let isValid = true;

        // Remove previous validation classes
        field.classList.remove('is-valid', 'is-invalid');

        // Title validation
        if (field.name === 'title') {
            if (!value || value.length < 3) {
                isValid = false;
                this.showFieldError(field, 'عنوان خدمت باید حداقل ۳ کاراکتر باشد');
            }
        }

        // Price validation
        if (field.name === 'price') {
            const numValue = parseFloat(value);
            if (!value || isNaN(numValue) || numValue <= 0) {
                isValid = false;
                this.showFieldError(field, 'قیمت باید عددی مثبت باشد');
            }
        }

        // Add validation class
        field.classList.add(isValid ? 'is-valid' : 'is-invalid');
        return isValid;
    }

    /**
     * Show field error message
     */
    showFieldError(field, message) {
        let errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            field.parentNode.appendChild(errorDiv);
        }
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i>${message}`;
    }

    /**
     * Validate entire form
     */
    validateForm(form) {
        const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    /**
     * Initialize price formatting
     */
    initPriceFormatting() {
        const priceInputs = document.querySelectorAll('input[name="price"]');
        priceInputs.forEach(input => {
            // Format on input
            input.addEventListener('input', (e) => {
                this.formatPriceInput(e.target);
            });

            // Format on focus out
            input.addEventListener('blur', (e) => {
                this.formatPriceInput(e.target);
            });
        });
    }

    /**
     * Format price input field
     */
    formatPriceInput(input) {
        let value = input.value.replace(/[^\d]/g, '');
        
        if (value) {
            // Store raw value for form submission
            input.setAttribute('data-raw-value', value);
            
            // Format for display
            const formatted = parseInt(value).toLocaleString('fa-IR');
            
            // Show formatted value in a display element if exists
            const displayElement = document.getElementById('price-formatted');
            if (displayElement) {
                displayElement.textContent = formatted + ' تومان';
            }
        }
    }

    /**
     * Initialize table interactions
     */
    initTableInteractions() {
        const tableRows = document.querySelectorAll('.pricing-row');
        
        tableRows.forEach((row, index) => {
            // Add hover effects
            row.addEventListener('mouseenter', () => {
                row.classList.add('table-row-hover');
            });

            row.addEventListener('mouseleave', () => {
                row.classList.remove('table-row-hover');
            });

            // Add click to highlight
            row.addEventListener('click', (e) => {
                // Don't trigger if clicking on buttons
                if (!e.target.closest('.btn')) {
                    this.highlightRow(row);
                }
            });
        });

        // Initialize action buttons
        this.initActionButtons();
    }

    /**
     * Highlight selected table row
     */
    highlightRow(row) {
        // Remove highlight from other rows
        document.querySelectorAll('.pricing-row').forEach(r => {
            r.classList.remove('table-row-selected');
        });

        // Add highlight to selected row
        row.classList.add('table-row-selected');
        
        // Remove highlight after 2 seconds
        setTimeout(() => {
            row.classList.remove('table-row-selected');
        }, 2000);
    }

    /**
     * Initialize action buttons (edit/delete)
     */
    initActionButtons() {
        // Edit buttons
        const editButtons = document.querySelectorAll('.btn-edit');
        editButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleEdit(button);
            });
        });

        // Delete buttons
        const deleteButtons = document.querySelectorAll('.btn-delete');
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                this.handleDelete(button);
            });
        });
    }

    /**
     * Handle edit button click
     */
    handleEdit(button) {
        // Add loading state
        const originalHtml = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;

        // Simulate loading (remove this in production)
        setTimeout(() => {
            button.innerHTML = originalHtml;
            button.disabled = false;
        }, 500);
    }

    /**
     * Handle delete button click
     */
    handleDelete(button) {
        const row = button.closest('.pricing-row');
        if (row) {
            row.classList.add('table-row-deleting');
        }
    }

    /**
     * Initialize animations
     */
    initAnimations() {
        // Animate elements on page load
        this.animateOnLoad();
        
        // Animate elements on scroll
        this.initScrollAnimations();
    }

    /**
     * Animate elements when page loads
     */
    animateOnLoad() {
        const animatedElements = document.querySelectorAll('.pricing-table-container, .stat-card, .card');
        
        animatedElements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                element.style.transition = 'all 0.6s ease';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    /**
     * Initialize scroll-based animations
     */
    initScrollAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, {
            threshold: 0.1
        });

        const animateElements = document.querySelectorAll('.pricing-row, .empty-state');
        animateElements.forEach(element => {
            observer.observe(element);
        });
    }

    /**
     * Utility method to show notifications
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Format numbers with Persian digits
     */
    toPersianDigits(str) {
        const persianDigits = '۰۱۲۳۴۵۶۷۸۹';
        const englishDigits = '0123456789';
        
        return str.toString().replace(/[0-9]/g, (digit) => {
            return persianDigits[englishDigits.indexOf(digit)];
        });
    }

    /**
     * Copy pricing data to clipboard
     */
    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showNotification('اطلاعات کپی شد', 'success');
        }).catch(() => {
            this.showNotification('خطا در کپی کردن', 'danger');
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new PricingManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PricingManager;
}
