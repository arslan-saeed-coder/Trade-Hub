// ===== TRADEHUB PK — ANIMATIONS & UI ENHANCEMENTS =====
(function() {

  // --- Scroll Progress Bar ---
  const progressBar = document.getElementById('scroll-progress');
  const backTop = document.getElementById('back-to-top');
  const navbar = document.getElementById('mainNav');

  function onScroll() {
    const scrolled = window.scrollY;
    const total = document.documentElement.scrollHeight - window.innerHeight;
    if (progressBar) progressBar.style.width = (total > 0 ? (scrolled / total) * 100 : 0) + '%';
    if (backTop) backTop.classList.toggle('show', scrolled > 400);
    if (navbar) navbar.classList.toggle('scrolled', scrolled > 20);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  if (backTop) backTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

  // --- Mobile Nav Hamburger ---
  const hamburger = document.getElementById('navHamburger');
  const mobileMenu = document.getElementById('navMobileMenu');
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('open');
      mobileMenu.classList.toggle('open');
    });
    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!hamburger.contains(e.target) && !mobileMenu.contains(e.target)) {
        hamburger.classList.remove('open');
        mobileMenu.classList.remove('open');
      }
    });
  }

  // --- Scroll Reveal (IntersectionObserver) ---
  const revealEls = document.querySelectorAll('.reveal, .reveal-left');
  if (revealEls.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(el => observer.observe(el));
  }

  // --- Animated Counters ---
  function animateCounter(el, target, suffix) {
    const duration = 1800;
    const start = performance.now();
    const update = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = Math.floor(eased * target);
      el.textContent = value.toLocaleString() + (suffix || '');
      if (progress < 1) requestAnimationFrame(update);
    };
    requestAnimationFrame(update);
  }

  // Hero stat numbers are populated with real data in index.html (loadHome()).

  // --- Lazy Load Product/Supplier cards (staggered) ---
  function staggerCards(gridId) {
    const grid = document.getElementById(gridId);
    if (!grid) return;
    const obs = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        const cards = grid.children;
        Array.from(cards).forEach((card, i) => {
          card.style.opacity = '0';
          card.style.transform = 'translateY(20px)';
          card.style.transition = `opacity .4s ease ${i * 0.07}s, transform .4s ease ${i * 0.07}s`;
          setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
          }, 50 + i * 70);
        });
        obs.unobserve(grid);
      }
    }, { threshold: 0.1 });
    obs.observe(grid);
  }

  // Run after DOM is loaded and cards are rendered
  setTimeout(() => {
    staggerCards('productsGrid');
    staggerCards('categoriesGrid');
  }, 300);

  // --- Active nav link highlight ---
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-links a, .nav-mobile-menu a').forEach(link => {
    if (link.href && currentPath.endsWith(link.getAttribute('href'))) {
      link.classList.add('active-nav');
    }
  });

})();
