/**
 * Pricing App Utility Functions
 * Shared utilities across all pricing pages
 */

class PricingUtils {

    /**
     * Remove all non-numeric characters from string
     * @param {string} str - String to clean
     * @returns {string} Clean numeric string
     */
    static cleanPrice(str) {
        if (!str) return '';
        return str.toString().replace(/[^\d]/g, '');
    }

    /**
     * Validate price input
     * @param {string|number} price - Price to validate
     * @returns {object} Validation result
     */
    static validatePrice(price) {
        const cleanPrice = this.cleanPrice(price);
        const numPrice = parseInt(cleanPrice);
        
        if (!cleanPrice || cleanPrice === '0') {
            return {
                isValid: false,
                message: 'قیمت باید عددی مثبت باشد'
            };
        }
        
        if (numPrice < 1000) {
            return {
                isValid: false,
                message: 'قیمت باید حداقل ۱۰۰۰ تومان باشد'
            };
        }
        
        if (numPrice > 999999999) {
            return {
                isValid: false,
                message: 'قیمت نمی‌تواند بیش از ۹۹۹ میلیون تومان باشد'
            };
        }
        
        return {
            isValid: true,
            value: numPrice
        };
    }

    /**
     * Show notification to user
     * @param {string} message - Message to display
     * @param {string} type - Type of notification (success, error, info, warning)
     * @param {number} duration - Duration in milliseconds
     */
    static showNotification(message, type = 'info', duration = 5000) {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.pricing-notification');
        existingNotifications.forEach(notification => notification.remove());

        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed pricing-notification`;
        notification.style.cssText = `
            top: 20px; 
            right: 20px; 
            z-index: 9999; 
            min-width: 300px;
            max-width: 400px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            border-radius: 10px;
            animation: slideInRight 0.3s ease-out;
        `;
        
        const iconMap = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-triangle',
            warning: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle'
        };
        
        notification.innerHTML = `
            <i class="${iconMap[type]} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        document.body.appendChild(notification);

        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
    }

    /**
     * Animate element entrance
     * @param {HTMLElement} element - Element to animate
     * @param {string} animation - Animation type
     * @param {number} delay - Delay in milliseconds
     */
    static animateElement(element, animation = 'fadeInUp', delay = 0) {
        if (!element) return;
        
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
            element.classList.add('animate-' + animation);
        }, delay);
    }


    /**
     * Initialize tooltips for elements
     * @param {string} selector - CSS selector for tooltip elements
     */
    static initTooltips(selector = '[data-bs-toggle="tooltip"]') {
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll(selector));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    }

    /**
     * Debounce function for performance optimization
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    static debounce(func, wait) {
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
     * Check if user prefers reduced motion
     * @returns {boolean} True if user prefers reduced motion
     */
    static prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    /**
     * Safe animation with reduced motion support
     * @param {HTMLElement} element - Element to animate
     * @param {object} options - Animation options
     */
    static safeAnimate(element, options = {}) {
        if (!element) return;
        
        if (this.prefersReducedMotion()) {
            // Skip animations for users who prefer reduced motion
            element.style.opacity = '1';
            element.style.transform = 'none';
            return;
        }
        
        this.animateElement(element, options.animation, options.delay);
    }
}

// Add CSS for notifications if not already present
if (!document.querySelector('#pricing-utils-styles')) {
    const style = document.createElement('style');
    style.id = 'pricing-utils-styles';
    style.textContent = `
        @keyframes slideInRight {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes slideOutRight {
            from {
                opacity: 1;
                transform: translateX(0);
            }
            to {
                opacity: 0;
                transform: translateX(100%);
            }
        }
        
        .pricing-notification {
            font-family: 'Vazir', 'Tahoma', sans-serif;
            direction: rtl;
            text-align: right;
        }
    `;
    document.head.appendChild(style);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PricingUtils;
}
