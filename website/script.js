/**
 * MadiTech Landing Page - Interactive Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const mobileToggle = document.getElementById('mobile-toggle');
  const navLinks = document.getElementById('nav-links');

  if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', () => {
      const isVisible = navLinks.style.display === 'flex';
      navLinks.style.display = isVisible ? 'none' : 'flex';
      if (!isVisible) {
        navLinks.style.flexDirection = 'column';
        navLinks.style.position = 'absolute';
        navLinks.style.top = '76px';
        navLinks.style.left = '0';
        navLinks.style.right = '0';
        navLinks.style.background = 'rgba(8, 9, 14, 0.98)';
        navLinks.style.padding = '2rem';
        navLinks.style.borderBottom = '1px solid rgba(255, 255, 255, 0.1)';
        navLinks.style.backdropFilter = 'blur(20px)';
      }
    });

    // Close menu when clicking link
    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
          navLinks.style.display = 'none';
        }
      });
    });
  }

  // 2. Interactive Digital Pass Switcher (Google Wallet vs Apple Wallet)
  const switchBtns = document.querySelectorAll('.card-switch-btn');
  const digitalCard = document.getElementById('digital-card');
  const walletBadgeText = document.getElementById('wallet-badge-text');
  const heroBanner = document.getElementById('card-hero-banner');

  if (switchBtns.length && digitalCard) {
    switchBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        switchBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const mode = btn.dataset.mode;
        if (mode === 'google') {
          digitalCard.style.background = 'linear-gradient(145deg, #18192E 0%, #0F101E 100%)';
          digitalCard.style.borderColor = 'rgba(99, 102, 241, 0.3)';
          if (walletBadgeText) walletBadgeText.textContent = 'Google Wallet Pass';
          if (heroBanner) heroBanner.style.display = 'flex';
        } else if (mode === 'apple') {
          digitalCard.style.background = 'linear-gradient(145deg, #111116 0%, #0A0A0E 100%)';
          digitalCard.style.borderColor = 'rgba(255, 255, 255, 0.2)';
          if (walletBadgeText) walletBadgeText.textContent = 'Apple Wallet PassKit';
          if (heroBanner) heroBanner.style.display = 'flex';
        }
      });
    });
  }

  // 3. Dynamic Points Counting Effect on Hover
  const pointsEl = document.getElementById('card-points-val');
  if (pointsEl) {
    let hovered = false;
    digitalCard?.addEventListener('mouseenter', () => {
      if (!hovered) {
        hovered = true;
        let count = 0;
        const target = 1450;
        const step = () => {
          count += 50;
          if (count <= target) {
            pointsEl.textContent = count.toLocaleString('ru-RU');
            requestAnimationFrame(step);
          } else {
            pointsEl.textContent = '1 450';
          }
        };
        step();
      }
    });
  }

  // 4. Subtle 3D Card Tilt Effect
  if (digitalCard && window.innerWidth > 992) {
    digitalCard.addEventListener('mousemove', (e) => {
      const rect = digitalCard.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      const rotateX = -(y / 20).toFixed(2);
      const rotateY = (x / 20).toFixed(2);
      digitalCard.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
    });

    digitalCard.addEventListener('mouseleave', () => {
      digitalCard.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
    });
  }
});
