// CEITEC HUB - Main JavaScript

// Toggle mobile menu
function toggleMenu() {
    const navMenu = document.getElementById('navMenu');
    navMenu.classList.toggle('active');
}

// Auto-hide alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Update score dynamically
function updateScore() {
    fetch('/api/pontuacao')
        .then(r => r.json())
        .then(data => {
            const scoreElement = document.querySelector('.score-value');
            if (scoreElement) {
                scoreElement.textContent = data.total;
            }
        });
}

// Confirm before logout
document.querySelectorAll('.btn-logout').forEach(btn => {
    btn.addEventListener('click', function (e) {
        if (!confirm('Deseja realmente sair?')) {
            e.preventDefault();
        }
    });
});
