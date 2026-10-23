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

  // 2. Interactive Digital Pass Switcher (Google Wallet vs Apple Wallet vs Telegram Mini App)
  const switchBtns = document.querySelectorAll('.card-switch-btn');
  const phoneMockup = document.getElementById('phone-mockup');
  const walletBadgeText = document.getElementById('wallet-badge-text');
  const screenImgs = {
    google: document.getElementById('img-google'),
    apple: document.getElementById('img-apple'),
    tma: document.getElementById('img-tma')
  };

  const badgeLabels = {
    google: '🤖 Google Wallet Pass • Android',
    apple: '🍎 Apple Wallet PassKit • iOS',
    tma: '✈️ Telegram Mini App • Все платформы'
  };

  const modes = ['google', 'apple', 'tma'];
  let currentModeIndex = 0;

  function setMode(mode) {
    // 1. Update buttons
    switchBtns.forEach(btn => {
      const isActive = btn.dataset.mode === mode;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    // 2. Update images
    Object.keys(screenImgs).forEach(key => {
      if (screenImgs[key]) {
        screenImgs[key].classList.toggle('active', key === mode);
      }
    });

    // 3. Update Phone Mockup Glow & Theme Class
    if (phoneMockup) {
      phoneMockup.classList.remove('mode-google', 'mode-apple', 'mode-tma');
      phoneMockup.classList.add(`mode-${mode}`);
    }

    // 4. Update Badge Pill Text
    if (walletBadgeText && badgeLabels[mode]) {
      walletBadgeText.textContent = badgeLabels[mode];
    }

    currentModeIndex = modes.indexOf(mode);
  }

  if (switchBtns.length) {
    switchBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const mode = btn.dataset.mode;
        if (mode) setMode(mode);
      });
    });
  }

  // Click on phone mockup to quickly cycle through cards
  if (phoneMockup) {
    phoneMockup.addEventListener('click', (e) => {
      // Avoid conflict if clicked something else inside
      const nextIndex = (currentModeIndex + 1) % modes.length;
      setMode(modes[nextIndex]);
    });
  }

  // 3. Subtle 3D Phone Tilt Effect on Desktop
  if (phoneMockup && window.innerWidth > 992) {
    phoneMockup.addEventListener('mousemove', (e) => {
      const rect = phoneMockup.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      const rotateX = -(y / 25).toFixed(2);
      const rotateY = (x / 25).toFixed(2);
      phoneMockup.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-6px)`;
    });

    phoneMockup.addEventListener('mouseleave', () => {
      phoneMockup.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
    });
  }
});
