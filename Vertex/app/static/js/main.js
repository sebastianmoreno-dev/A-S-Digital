// AS Vertex — main.js

// ── Navbar mobile toggle ─────────────────────────────────────────
const navToggle = document.getElementById('navToggle');
const navLinks  = document.getElementById('navLinks');

if (navToggle && navLinks) {
  // La clase va en AMBOS: en el <ul> lo despliega, en el botón anima la X.
  const setNav = (open) => {
    navLinks.classList.toggle('open', open);
    navToggle.classList.toggle('open', open);
    navToggle.setAttribute('aria-expanded', String(open));
  };
  const isOpen = () => navLinks.classList.contains('open');

  navToggle.addEventListener('click', (e) => {
    e.stopPropagation();          // que no lo cierre el listener de "click afuera"
    setNav(!isOpen());
  });

  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => setNav(false));
  });

  document.addEventListener('click', (e) => {
    if (isOpen() && !navLinks.contains(e.target)) setNav(false);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isOpen()) {
      setNav(false);
      navToggle.focus();
    }
  });

  // Al pasar a desktop el <ul> vuelve a ser flex horizontal: limpiar el estado.
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768 && isOpen()) setNav(false);
  });
}

// ── Navbar scroll border ─────────────────────────────────────────
window.addEventListener('scroll', () => {
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    navbar.style.borderBottomColor = window.scrollY > 10
      ? 'rgba(255,255,255,0.13)'
      : 'rgba(255,255,255,0.07)';
  }
}, { passive: true });

// ── Flash messages: auto-dismiss ─────────────────────────────────
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    alert.style.transition = 'opacity 0.5s, transform 0.5s';
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-6px)';
    setTimeout(() => alert.remove(), 500);
  }, 4500);
});

// ── Scroll reveal con IntersectionObserver ───────────────────────
if ('IntersectionObserver' in window) {
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        // Stagger delay para grids
        const siblings = entry.target.parentElement?.querySelectorAll('.reveal');
        let delay = 0;
        if (siblings) {
          siblings.forEach((el, idx) => { if (el === entry.target) delay = idx * 70; });
        }
        setTimeout(() => entry.target.classList.add('visible'), delay);
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  // Aplicar clase reveal a cards y secciones clave
  document.querySelectorAll('.card, .process-item, .page-header h1, .page-header p').forEach(el => {
    el.classList.add('reveal');
    revealObserver.observe(el);
  });
}

// ── Card mouse glow (efecto spotlight) ──────────────────────────
document.querySelectorAll('.card').forEach(card => {
  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width)  * 100;
    const y = ((e.clientY - rect.top)  / rect.height) * 100;
    card.style.setProperty('--mouse-x', `${x}%`);
    card.style.setProperty('--mouse-y', `${y}%`);
  });
});

// ── Filas de tabla clicables (panel admin) ────────────────────────
document.querySelectorAll('tr.row-link[data-href]').forEach(row => {
  row.addEventListener('click', () => {
    window.location.href = row.dataset.href;
  });
});

// ── Smooth anchor scroll ─────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', (e) => {
    const target = document.querySelector(anchor.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// ── Contador animado en stats ────────────────────────────────────
function animateCounter(el) {
  const raw    = el.textContent.trim();
  const isPlus = raw.startsWith('+');
  const num    = parseInt(raw.replace(/\D/g, ''), 10);
  if (isNaN(num)) return;

  let start = 0; const duration = 1200;
  const step = (timestamp) => {
    if (!start) start = timestamp;
    const progress = Math.min((timestamp - start) / duration, 1);
    const eased    = 1 - Math.pow(1 - progress, 3);
    el.textContent = (isPlus ? '+' : '') + Math.floor(eased * num) + (raw.includes('%') ? '%' : '');
    if (progress < 1) requestAnimationFrame(step);
    else el.textContent = raw;
  };
  requestAnimationFrame(step);
}

if ('IntersectionObserver' in window) {
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.stat-num').forEach(el => counterObserver.observe(el));
}
