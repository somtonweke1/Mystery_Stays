document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });

    // Observe all elements with animation classes
    document.querySelectorAll('.animate-fade-in, .animate-slide-up').forEach((el) => {
        observer.observe(el);
    });
});
