/* ==========================================================================
   SUPERAPP BHAIRAVA ANUGRAHA - CLIENT SCRIPTS
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Ambient Golden Ember / Dust Canvas
  initAmbientCanvas();

  // 2. Audio Chime Synthesizer (Web Audio API)
  initSacredAudio();

  // 3. Command Palette (⌘K)
  initCommandPalette();

  // 4. Mobile Drawer Navigation
  initMobileDrawer();

  // 5. Active Link Highlight
  highlightCurrentNav();
});

/* --- 1. Ambient Golden Embers --- */
function initAmbientCanvas() {
  const canvas = document.getElementById('ambient-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let width, height;
  let particles = [];
  const PARTICLE_COUNT = 45;

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', resize);
  resize();

  class Particle {
    constructor() {
      this.reset();
    }
    reset() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.size = Math.random() * 2 + 0.8;
      this.speedY = -(Math.random() * 0.4 + 0.15);
      this.speedX = (Math.random() - 0.5) * 0.3;
      this.opacity = Math.random() * 0.5 + 0.2;
      this.fadeSpeed = Math.random() * 0.005 + 0.002;
    }
    update() {
      this.y += this.speedY;
      this.x += this.speedX;
      this.opacity += this.fadeSpeed;
      if (this.opacity > 0.7 || this.opacity < 0.15) {
        this.fadeSpeed = -this.fadeSpeed;
      }
      if (this.y < -10) {
        this.y = height + 10;
        this.x = Math.random() * width;
      }
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(212, 166, 74, ${Math.max(0, this.opacity)})`;
      ctx.shadowBlur = 6;
      ctx.shadowColor = '#f0d48a';
      ctx.fill();
    }
  }

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push(new Particle());
  }

  function animate() {
    ctx.clearRect(0, 0, width, height);
    for (let p of particles) {
      p.update();
      p.draw();
    }
    requestAnimationFrame(animate);
  }
  animate();
}

/* --- 2. Sacred Audio Chime (Web Audio API Bell Synthesizer) --- */
function initSacredAudio() {
  const btn = document.getElementById('audio-toggle-btn');
  if (!btn) return;

  let audioCtx = null;
  let isPlaying = false;
  let intervalId = null;

  function playBellChime() {
    if (!audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioContext();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }

    // Sacred harmonic frequencies: Root C# (138.5 Hz) with fifths and octaves
    const fundamental = 138.59; // C#3
    const harmonics = [1, 2.76, 5.4, 8.93];
    const gains = [0.15, 0.08, 0.04, 0.02];

    const now = audioCtx.currentTime;

    harmonics.forEach((h, i) => {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(fundamental * h, now);

      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(gains[i], now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 4.5);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start(now);
      osc.stop(now + 5.0);
    });
  }

  btn.addEventListener('click', () => {
    isPlaying = !isPlaying;
    if (isPlaying) {
      btn.innerHTML = '<span>🔔 Chime Active</span>';
      btn.style.borderColor = 'var(--gold)';
      btn.style.color = 'var(--gold-3)';
      playBellChime();
      // Chime gently every 45 seconds
      intervalId = setInterval(playBellChime, 45000);
    } else {
      btn.innerHTML = '<span>🔕 Audio Off</span>';
      btn.style.borderColor = '';
      btn.style.color = '';
      if (intervalId) clearInterval(intervalId);
    }
  });
}

/* --- 3. Command Palette (⌘K / Ctrl+K) --- */
function initCommandPalette() {
  const backdrop = document.getElementById('palette-backdrop');
  const openBtn = document.getElementById('chrome-search');
  const input = document.getElementById('palette-input');
  const resultsContainer = document.getElementById('palette-results');
  if (!backdrop || !input || !resultsContainer) return;

  const SEARCH_ITEMS = [
    { title: "Home · Sacred Portal", url: "/", tag: "Super App" },
    { title: "Jnāna Samvāda · Bhairava Codex & Inquiry", url: "/jnana-samvada", tag: "Codex" },
    { title: "Bhairav Loka · Sahasralinga Codex", url: "/bhairav-loka", tag: "App" },
    { title: "Sādhana Paddhati · Three Steps to Union", url: "/sadhana-paddhati", tag: "Discourse" },
    { title: "Ashtami · Krishna Paksha Inner Gateways", url: "/ashtami", tag: "Calendar" },
    { title: "Daiva Anugraha Videos · YouTube Discourses", url: "/#videos", tag: "Media" },
    { title: "Life Within or Without · Book & Teachings", url: "/#book", tag: "Book" },
    { title: "Join Sacred Telegram Group", url: "https://t.me/+tM8pVCZWG8cxYjc1", tag: "Community", external: true },
    { title: "WhatsApp Direct Guidance (+91 62622 12153)", url: "https://wa.me/916262212153", tag: "Contact", external: true }
  ];

  function openPalette() {
    backdrop.classList.add('is-open');
    input.value = '';
    renderResults(SEARCH_ITEMS);
    setTimeout(() => input.focus(), 50);
  }

  function closePalette() {
    backdrop.classList.remove('is-open');
  }

  if (openBtn) {
    openBtn.addEventListener('click', openPalette);
  }

  window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (backdrop.classList.contains('is-open')) closePalette();
      else openPalette();
    }
    if (e.key === 'Escape' && backdrop.classList.contains('is-open')) {
      closePalette();
    }
  });

  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) closePalette();
  });

  function renderResults(items) {
    resultsContainer.innerHTML = '';
    if (items.length === 0) {
      resultsContainer.innerHTML = '<div style="padding:16px; color:var(--ink-dim); text-align:center;">No sacred records found</div>';
      return;
    }
    items.forEach((item, idx) => {
      const div = document.createElement('div');
      div.className = `palette-item ${idx === 0 ? 'is-selected' : ''}`;
      div.innerHTML = `
        <div>
          <span style="margin-right:8px; color:var(--gold-3)">✦</span>
          <span>${item.title}</span>
        </div>
        <span class="palette-item-tag">${item.tag}</span>
      `;
      div.addEventListener('click', () => {
        closePalette();
        if (item.external) {
          window.open(item.url, '_blank');
        } else {
          window.location.href = item.url;
        }
      });
      resultsContainer.appendChild(div);
    });
  }

  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    if (!q) {
      renderResults(SEARCH_ITEMS);
      return;
    }
    const filtered = SEARCH_ITEMS.filter(it => 
      it.title.toLowerCase().includes(q) || it.tag.toLowerCase().includes(q)
    );
    renderResults(filtered);
  });
}

/* --- 4. Mobile Drawer Navigation --- */
function initMobileDrawer() {
  const drawer = document.getElementById('mobile-drawer');
  const openBtn = document.getElementById('mobile-menu-btn');
  const closeBtn = document.getElementById('drawer-close-btn');
  if (!drawer || !openBtn || !closeBtn) return;

  openBtn.addEventListener('click', () => drawer.classList.add('is-open'));
  closeBtn.addEventListener('click', () => drawer.classList.remove('is-open'));

  // Close drawer on link click
  drawer.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => drawer.classList.remove('is-open'));
  });
}

/* --- 5. Navigation Active State --- */
function highlightCurrentNav() {
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.chrome-nav .nav-item');
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath || (currentPath === '/' && href === '/')) {
      link.classList.add('is-active');
    } else {
      link.classList.remove('is-active');
    }
  });
}
