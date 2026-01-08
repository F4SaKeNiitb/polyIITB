/**
 * Onboarding Module
 * Shows welcome carousel for first-time visitors
 */

let currentSlide = 0;
const totalSlides = 4;

function showOnboarding() {
    // Check if user has seen onboarding
    if (localStorage.getItem('onboarding_seen')) {
        return;
    }

    document.getElementById('onboarding-modal').classList.add('show');
}

function skipOnboarding() {
    localStorage.setItem('onboarding_seen', 'true');
    document.getElementById('onboarding-modal').classList.remove('show');
}

function nextOnboardingSlide() {
    currentSlide++;

    if (currentSlide >= totalSlides) {
        skipOnboarding();
        return;
    }

    updateOnboardingSlide();
}

function goToSlide(slideIndex) {
    currentSlide = slideIndex;
    updateOnboardingSlide();
}

function updateOnboardingSlide() {
    // Update slides
    document.querySelectorAll('.onboarding-slide').forEach((slide, index) => {
        slide.classList.toggle('active', index === currentSlide);
    });

    // Update dots
    document.querySelectorAll('.onboarding-dots .dot').forEach((dot, index) => {
        dot.classList.toggle('active', index === currentSlide);
    });

    // Update button text
    const nextBtn = document.getElementById('onboarding-next');
    if (currentSlide === totalSlides - 1) {
        nextBtn.textContent = 'Get Started';
    } else {
        nextBtn.textContent = 'Next';
    }
}

// Initialize onboarding
document.addEventListener('DOMContentLoaded', () => {
    // Setup dot click handlers
    document.querySelectorAll('.onboarding-dots .dot').forEach(dot => {
        dot.addEventListener('click', () => {
            goToSlide(parseInt(dot.dataset.slide));
        });
    });

    // Show onboarding after a short delay
    setTimeout(showOnboarding, 500);
});
