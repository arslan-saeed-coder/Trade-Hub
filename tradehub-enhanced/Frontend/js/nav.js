// ===== TRADEHUB PK — SHARED NAV ENHANCEMENTS =====
(function() {
  // Scroll progress
  const progressBar = document.getElementById('scroll-progress');
  const backTop = document.getElementById('back-to-top');
  const navbar = document.querySelector('.navbar');

  function onScroll() {
    const scrolled = window.scrollY;
    const total = document.documentElement.scrollHeight - window.innerHeight;
    if (progressBar) progressBar.style.width = (total > 0 ? (scrolled / total) * 100 : 0) + '%';
    if (backTop) backTop.classList.toggle('show', scrolled > 400);
    if (navbar) navbar.classList.toggle('scrolled', scrolled > 20);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  if (backTop) backTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

  // Hamburger
  const hamburger = document.getElementById('navHamburger');
  const mobileMenu = document.getElementById('navMobileMenu');
  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('open');
      mobileMenu.classList.toggle('open');
    });
    document.addEventListener('click', (e) => {
      if (!hamburger.contains(e.target) && !mobileMenu.contains(e.target)) {
        hamburger.classList.remove('open');
        mobileMenu.classList.remove('open');
      }
    });
  }

  // Reveal
  document.addEventListener('DOMContentLoaded', () => {
    const revealEls = document.querySelectorAll('.reveal, .reveal-left');
    if (revealEls.length) {
      const obs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) { entry.target.classList.add('visible'); obs.unobserve(entry.target); }
        });
      }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });
      revealEls.forEach(el => obs.observe(el));
    }
  });
})();
