// AS Vertex — main.js

// Navbar mobile toggle
const navToggle = document.getElementById('navToggle');
const navLinks  = document.getElementById('navLinks');
const navCTA    = document.querySelector('.nav-cta');

if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    navLinks.classList.toggle('open');
    if (navCTA) navCTA.classList.toggle('open');
  });
}

// Cerrar nav al hacer click en un link (mobile)
document.querySelectorAll('.nav-links a').forEach(link => {
  link.addEventListener('click', () => {
    if (navLinks) navLinks.classList.remove('open');
    if (navCTA) navCTA.classList.remove('open');
  });
});

// Scroll activo en navbar
window.addEventListener('scroll', () => {
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    navbar.style.borderBottomColor = window.scrollY > 10
      ? 'rgba(255,255,255,0.12)'
      : 'rgba(255,255,255,0.08)';
  }
});

// Flash messages: desaparecen automáticamente
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.transition = 'opacity 0.5s';
    alert.style.opacity = '0';
    setTimeout(() => alert.remove(), 500);
  }, 4000);
});

// Animación dinámica de entrada para cards (Scroll continuo)
if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // Al entrar en pantalla: se hace visible y sube
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      } else {
        // Al salir de pantalla: vuelve a ocultarse para repetir la animación
        entry.target.style.opacity = '0';
        entry.target.style.transform = 'translateY(16px)';
      }
    });
  }, { threshold: 0.1 });

  // Estado inicial de las tarjetas antes de ser observadas
  document.querySelectorAll('.card').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(16px)';
    card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    observer.observe(card);
  });
}
