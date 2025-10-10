/**
 * Pricing List Page JavaScript
 * Handles functionality specific to the pricing list page
 */

class PricingListManager {
    constructor() {
        this.init();
    }

    init() {
        this.formatPrices();
        this.initAnimations();
        this.initTooltips();
        this.initModals();
    }

    /**
     * Format all price amounts with comma separators
     */
    formatPrices() {
        // Function to add comma separators to numbers
        function addCommas(num) {
            return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
        }
        
        // Format all price amounts
        const priceElements = document.querySelectorAll('.price-amount');
        priceElements.forEach(function(element) {
            const price = element.getAttribute('data-price') || element.textContent.replace(/[^\d]/g, '');
            if (price) {
                element.textContent = addCommas(price);
            }
        });
    }

    /**
     * Initialize animations for pricing cards
     */
    initAnimations() {
        // Add staggered animation to pricing cards
        const cards = document.querySelectorAll('.pricing-card');
        cards.forEach(function(card, index) {
            card.style.animationDelay = (index * 0.1) + 's';
        });
        
        // Add smooth scroll effect for management actions
        const managementBtn = document.querySelector('.management-actions .btn');
        if (managementBtn) {
            managementBtn.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-3px) scale(1.02)';
            });
            managementBtn.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0) scale(1)';
            });
        }

        // Animate contact info section
        const contactSection = document.querySelector('.contact-info-section');
        if (contactSection) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            });
            
            contactSection.style.opacity = '0';
            contactSection.style.transform = 'translateY(30px)';
            contactSection.style.transition = 'all 0.6s ease';
            observer.observe(contactSection);
        }
    }

    /**
     * Initialize Bootstrap tooltips
     */
    initTooltips() {
        // Check if Bootstrap is available
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
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
    new PricingListManager();
});
