/**
 * About Page JavaScript
 * Handles animations, smooth scrolling, and interactive elements
 */

document.addEventListener('DOMContentLoaded', () => {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Animation on scroll for feature boxes and team members
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.feature-box, .team-member');
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const screenPosition = window.innerHeight / 1.3;
            
            if (elementPosition < screenPosition) {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }
        });
    };

    // Initial check on page load
    animateOnScroll();
    
    // Check on scroll
    window.addEventListener('scroll', animateOnScroll);

    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.2
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate__animated');
                if (entry.target.classList.contains('team-member')) {
                    entry.target.classList.add('animate__fadeInUp');
                } else if (entry.target.classList.contains('feature-box')) {
                    entry.target.classList.add('animate__zoomIn');
                } else if (entry.target.classList.contains('doctor-card')) {
                    entry.target.classList.add('animate__fadeInUp');
                } else if (entry.target.classList.contains('service-card')) {
                    entry.target.classList.add('animate__zoomIn');
                }
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe elements
    document.querySelectorAll('.team-member, .feature-box, .doctor-card, .service-card').forEach(element => {
        observer.observe(element);
    });

    // Hover effects for cards
    const cards = document.querySelectorAll('.feature-box, .team-member, .doctor-card, .service-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-10px)';
            card.style.transition = 'transform 0.3s ease, box-shadow 0.3s ease';
            card.style.boxShadow = '0 15px 30px rgba(0, 0, 0, 0.1)';
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '0 5px 20px rgba(0, 0, 0, 0.05)';
        });
    });

    // Animate social links
    const socialLinks = document.querySelectorAll('.social-links a');
    socialLinks.forEach((link, index) => {
        link.style.opacity = '0';
        setTimeout(() => {
            link.style.transition = 'opacity 0.5s ease, transform 0.3s ease';
            link.style.opacity = '1';
            link.addEventListener('mouseenter', () => {
                link.style.transform = 'translateY(-3px)';
            });
            link.addEventListener('mouseleave', () => {
                link.style.transform = 'translateY(0)';
            });
        }, index * 200);
    });

    // Add loading animation to buttons
    const buttons = document.querySelectorAll('.btn, .cta-btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>در حال بارگذاری...';
            this.disabled = true;
            
            // Reset button after 3 seconds (for demo purposes)
            setTimeout(() => {
                this.innerHTML = this.getAttribute('data-original-text') || this.textContent;
                this.disabled = false;
            }, 3000);
        });
        
        // Store original button text
        button.setAttribute('data-original-text', button.innerHTML);
    });
});