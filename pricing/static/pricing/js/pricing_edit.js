/**
 * Edit Pricing Item Page JavaScript
 * Handles functionality specific to the edit pricing page
 */

class PricingEditManager {
    constructor() {
        this.init();
    }

    init() {
        this.initPriceInput();
        this.initFormValidation();
        this.initAnimations();
        this.initPriceComparison();
    }

    /**
     * Initialize price input with basic validation
     */
    initPriceInput() {
        const priceInput = document.querySelector('input[name="price"]');
        
        if (priceInput) {
            // Remove any input restrictions
            priceInput.removeAttribute('maxlength');
            priceInput.setAttribute('inputmode', 'numeric');
            
            // Update price comparison on input
            priceInput.addEventListener('input', (e) => {
                const value = e.target.value.replace(/[^\d]/g, '');
                if (value) {
                    this.updatePriceComparison(parseInt(value));
                } else {
                    this.updatePriceComparison(0);
                }
            });

            // Add real-time validation
            priceInput.addEventListener('blur', () => {
                this.validatePriceField(priceInput);
            });
        }
    }

    /**
     * Initialize price comparison functionality
     */
    initPriceComparison() {
        const oldPriceElement = document.getElementById('old-price');
        const newPriceDisplay = document.getElementById('new-price');
        const priceDifferenceDisplay = document.getElementById('price-difference');
        
        // Get old price from global variable or element
        let oldPrice = 0;
        if (window.pricingData && window.pricingData.oldPrice) {
            oldPrice = window.pricingData.oldPrice;
        } else if (oldPriceElement) {
            const oldPriceText = oldPriceElement.textContent.replace(/[^\d]/g, '');
            oldPrice = parseInt(oldPriceText) || 0;
        }
        
        // Display old price without formatting
        if (oldPriceElement) {
            oldPriceElement.textContent = oldPrice;
        }

        // Store old price for comparison
        this.oldPrice = oldPrice;

        // Initialize with current form value
        const priceInput = document.querySelector('input[name="price"]');
        if (priceInput && priceInput.value) {
            const currentValue = priceInput.value.replace(/[^\d]/g, '');
            if (currentValue) {
                this.updatePriceComparison(parseInt(currentValue));
            }
        }
    }

    /**
     * Update price comparison display
     */
    updatePriceComparison(newPrice) {
        const newPriceDisplay = document.getElementById('new-price');
        const priceDifferenceDisplay = document.getElementById('price-difference');
        
        // Display new price without formatting
        if (newPriceDisplay) {
            newPriceDisplay.textContent = newPrice;
        }
        
        // Calculate and display difference
        if (priceDifferenceDisplay && newPrice > 0) {
            const difference = newPrice - this.oldPrice;
            const percentChange = this.oldPrice > 0 ? ((difference / this.oldPrice) * 100).toFixed(1) : 0;
            
            if (difference > 0) {
                priceDifferenceDisplay.innerHTML = `
                    <i class="fas fa-arrow-up text-success me-1"></i>
                    افزایش ${difference} تومان (${percentChange}%)
                `;
                priceDifferenceDisplay.className = 'badge bg-success fs-6 px-3 py-2';
            } else if (difference < 0) {
                priceDifferenceDisplay.innerHTML = `
                    <i class="fas fa-arrow-down text-danger me-1"></i>
                    کاهش ${Math.abs(difference)} تومان (${Math.abs(percentChange)}%)
                `;
                priceDifferenceDisplay.className = 'badge bg-danger fs-6 px-3 py-2';
            } else {
                priceDifferenceDisplay.innerHTML = `
                    <i class="fas fa-equals text-muted me-1"></i>
                    بدون تغییر
                `;
                priceDifferenceDisplay.className = 'badge bg-light text-dark fs-6 px-3 py-2';
            }
        }
    }


    /**
     * Validate price field
     */
    validatePriceField(field) {
        const value = field.value.replace(/[^\d]/g, '');
        let isValid = true;
        let message = '';

        // Remove previous validation classes
        field.classList.remove('is-valid', 'is-invalid');

        if (!value || value === '0') {
            isValid = false;
            message = 'قیمت باید عددی مثبت باشد';
        } else if (parseInt(value) < 1000) {
            isValid = false;
            message = 'قیمت باید حداقل ۱۰۰۰ تومان باشد';
        }

        // Add validation class
        field.classList.add(isValid ? 'is-valid' : 'is-invalid');
        
        if (!isValid) {
            this.showFieldError(field, message);
        } else {
            this.removeFieldError(field);
        }

        return isValid;
    }

    /**
     * Show field error message
     */
    showFieldError(field, message) {
        let errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback animate-shake';
            field.parentNode.appendChild(errorDiv);
        }
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i>${message}`;
    }

    /**
     * Remove field error message
     */
    removeFieldError(field) {
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    /**
     * Initialize form validation
     */
    initFormValidation() {
        const form = document.querySelector('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.showNotification('لطفاً خطاهای فرم را برطرف کنید', 'danger');
                }
                form.classList.add('was-validated');
            });

            // Real-time validation for all inputs
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });
            });
        }
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
            } else {
                this.removeFieldError(field);
            }
        }

        // Price validation
        if (field.name === 'price') {
            return this.validatePriceField(field);
        }

        // Add validation class
        field.classList.add(isValid ? 'is-valid' : 'is-invalid');
        return isValid;
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
     * Initialize animations
     */
    initAnimations() {
        // Animate form elements on load
        const formElements = document.querySelectorAll('.modern-form-card, .modern-info-card, .navigation-section, .current-info-section, .card');
        
        formElements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                element.style.transition = 'all 0.6s ease';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * 100);
        });

        // Add hover effects to buttons
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px) scale(1.02)';
            });
            button.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
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
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new PricingEditManager();
});
