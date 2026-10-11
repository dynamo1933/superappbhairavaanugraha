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

  // 6. Touch-Friendly Dropdown Support
  initDropdownTouchSupport();

  // 7. Ashtami Local Timezone & GMT Alignment Engine
  initAshtamiTimezoneEngine();
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
  // If Bhairav Loka app container is present, allow app.js to control audio
  if (document.querySelector('.app-container')) return;

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
    { title: "Sādhana Paddhati · Three Steps to Union", url: "/sadhana-paddhati", tag: "Discourse" },
    { title: "Mandala Sādhana · Sacred Vows & Sankalpa", url: "/mandala-sadhana", tag: "Vow" },
    { title: "Krishna Paksha Ashtami · Sacred Gateways", url: "/ashtami", tag: "Calendar" },
    { title: "Sacred Documents · Mandala Teachings", url: "/documents", tag: "Documents" },
    { title: "Guru Bhairava · Paramaguru Lineage & Sadhana", url: "/guru-bhairava", tag: "Sādhana" },
    { title: "Vishesh Sādhana · Kaal Ashtami & Eclipse Rites", url: "/vishesh-sadhana", tag: "Ritual" },
    { title: "Prāṇa Pratiṣṭhāna · Consecration Codex", url: "/prana-pratisthana", tag: "Consecration" },
    { title: "Daiva Anugraha Videos · YouTube Discourses", url: "/#videos", tag: "Media" },
    { title: "Life Within or Without · Book & Teachings", url: "/#book", tag: "Book" },
    { title: "Join Sacred Telegram Group", url: "https://t.me/+tM8pVCZWG8cxYjc1", tag: "Community", external: true },
    { title: "Instagram (@bhairava_anugraha)", url: "https://www.instagram.com/bhairava_anugraha/", tag: "Community", external: true }
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
  const backdrop = document.getElementById('drawer-backdrop');
  const openBtn = document.getElementById('mobile-menu-btn');
  const closeBtn = document.getElementById('drawer-close-btn');
  if (!drawer || !openBtn) return;

  function openDrawer() {
    drawer.classList.add('is-open');
    if (backdrop) backdrop.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }

  function closeDrawer() {
    drawer.classList.remove('is-open');
    if (backdrop) backdrop.classList.remove('is-open');
    document.body.style.overflow = '';
  }

  openBtn.addEventListener('click', openDrawer);
  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
  if (backdrop) backdrop.addEventListener('click', closeDrawer);

  // Close drawer on link click
  drawer.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', closeDrawer);
  });

  // Close on Escape key
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && drawer.classList.contains('is-open')) {
      closeDrawer();
    }
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

/* --- 6. Dropdown Support (Hover, Click, Touch, Keyboard Accessibility) --- */
function initDropdownTouchSupport() {
  const navDropdownWraps = document.querySelectorAll('.nav-dropdown-wrap');
  const userMenuWraps = document.querySelectorAll('.user-menu-wrap');

  function closeAllDropdowns(exceptWrap = null) {
    navDropdownWraps.forEach(w => {
      if (w !== exceptWrap) {
        w.classList.remove('is-open');
        const btn = w.querySelector('.nav-dropdown-btn');
        if (btn) btn.setAttribute('aria-expanded', 'false');
      }
    });
    userMenuWraps.forEach(w => {
      if (w !== exceptWrap) {
        w.classList.remove('is-open');
        const btn = w.querySelector('.user-btn-trigger');
        if (btn) btn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // 1. Navigation dropdowns (e.g. Resources menu)
  navDropdownWraps.forEach(wrap => {
    const btn = wrap.querySelector('.nav-dropdown-btn');
    if (!btn) return;

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = wrap.classList.contains('is-open');
      closeAllDropdowns(isOpen ? null : wrap);
      if (!isOpen) {
        wrap.classList.add('is-open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });

  // 2. User & Admin Control dropdown
  userMenuWraps.forEach(wrap => {
    const btn = wrap.querySelector('.user-btn-trigger');
    const menu = wrap.querySelector('.user-dropdown-menu');
    if (!btn || !menu) return;

    btn.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const isOpen = wrap.classList.contains('is-open');
      closeAllDropdowns(isOpen ? null : wrap);
      if (!isOpen) {
        wrap.classList.add('is-open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });

    // When clicking any link inside the dropdown, allow navigation while resetting open state
    menu.addEventListener('click', (e) => {
      const link = e.target.closest('a');
      if (link) {
        wrap.classList.remove('is-open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  });

  // Tap / click outside to close open dropdowns
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.nav-dropdown-wrap') && !e.target.closest('.user-menu-wrap')) {
      closeAllDropdowns();
    }
  });

  // Escape key closes open dropdowns
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeAllDropdowns();
    }
  });
}

/* ==========================================================================
   7. ASHTAMI LOCAL TIMEZONE & GMT ALIGNMENT ENGINE
   ========================================================================== */
function initAshtamiTimezoneEngine() {
  const banner = document.querySelector('.ashtami-banner');
  const timingVals = document.querySelectorAll('.ashtami-timing-val');

  // If no banner and no timing display on page, exit
  if (!banner && timingVals.length === 0) return;

  // Canonical base timestamps (IST, UTC+05:30)
  let startIso = (banner && banner.getAttribute('data-start-iso')) || '2026-10-03T08:00:00+05:30';
  let endIso = (banner && banner.getAttribute('data-end-iso')) || '2026-10-04T05:52:00+05:30';

  // Comprehensive IANA Timezone to Country & Region Mapping
  const TZ_COUNTRY_MAP = {
    'Asia/Kolkata': { country: 'India', flag: '🇮🇳', name: 'India (IST)' },
    'Asia/Calcutta': { country: 'India', flag: '🇮🇳', name: 'India (IST)' },
    'Asia/Colombo': { country: 'Sri Lanka', flag: '🇱🇰', name: 'Sri Lanka' },
    'Asia/Kathmandu': { country: 'Nepal', flag: '🇳🇵', name: 'Nepal (NPT)' },
    'Asia/Dhaka': { country: 'Bangladesh', flag: '🇧🇩', name: 'Bangladesh' },
    'Asia/Dubai': { country: 'United Arab Emirates', flag: '🇦🇪', name: 'UAE (Dubai / Gulf)' },
    'Asia/Muscat': { country: 'Oman', flag: '🇴🇲', name: 'Oman' },
    'Asia/Riyadh': { country: 'Saudi Arabia', flag: '🇸🇦', name: 'Saudi Arabia' },
    'Asia/Singapore': { country: 'Singapore', flag: '🇸🇬', name: 'Singapore' },
    'Asia/Kuala_Lumpur': { country: 'Malaysia', flag: '🇲🇾', name: 'Malaysia' },
    'Asia/Bangkok': { country: 'Thailand', flag: '🇹🇭', name: 'Thailand' },
    'Asia/Jakarta': { country: 'Indonesia', flag: '🇮🇩', name: 'Indonesia' },
    'Asia/Tokyo': { country: 'Japan', flag: '🇯🇵', name: 'Japan (Tokyo)' },
    'Asia/Seoul': { country: 'South Korea', flag: '🇰🇷', name: 'South Korea' },
    'Asia/Hong_Kong': { country: 'Hong Kong', flag: '🇭🇰', name: 'Hong Kong' },
    'Asia/Shanghai': { country: 'China', flag: '🇨🇳', name: 'China' },
    'America/New_York': { country: 'United States', flag: '🇺🇸', name: 'USA · Eastern (NY/DC)' },
    'America/Detroit': { country: 'United States', flag: '🇺🇸', name: 'USA · Eastern (Detroit)' },
    'America/Chicago': { country: 'United States', flag: '🇺🇸', name: 'USA · Central (Chicago)' },
    'America/Denver': { country: 'United States', flag: '🇺🇸', name: 'USA · Mountain (Denver)' },
    'America/Phoenix': { country: 'United States', flag: '🇺🇸', name: 'USA · Arizona' },
    'America/Los_Angeles': { country: 'United States', flag: '🇺🇸', name: 'USA · Pacific (LA/SF)' },
    'America/Anchorage': { country: 'United States', flag: '🇺🇸', name: 'USA · Alaska' },
    'Pacific/Honolulu': { country: 'United States', flag: '🇺🇸', name: 'USA · Hawaii' },
    'America/Toronto': { country: 'Canada', flag: '🇨🇦', name: 'Canada · Toronto' },
    'America/Vancouver': { country: 'Canada', flag: '🇨🇦', name: 'Canada · Vancouver' },
    'America/Montreal': { country: 'Canada', flag: '🇨🇦', name: 'Canada · Montreal' },
    'Europe/London': { country: 'United Kingdom', flag: '🇬🇧', name: 'United Kingdom (London)' },
    'Europe/Dublin': { country: 'Ireland', flag: '🇮🇪', name: 'Ireland (Dublin)' },
    'Europe/Paris': { country: 'France', flag: '🇫🇷', name: 'France (Paris)' },
    'Europe/Berlin': { country: 'Germany', flag: '🇩🇪', name: 'Europe · Berlin / Paris' },
    'Europe/Rome': { country: 'Italy', flag: '🇮🇹', name: 'Italy (Rome)' },
    'Europe/Madrid': { country: 'Spain', flag: '🇪🇸', name: 'Spain (Madrid)' },
    'Europe/Amsterdam': { country: 'Netherlands', flag: '🇳🇱', name: 'Netherlands' },
    'Europe/Brussels': { country: 'Belgium', flag: '🇧🇪', name: 'Belgium' },
    'Europe/Zurich': { country: 'Switzerland', flag: '🇨🇭', name: 'Switzerland' },
    'Europe/Vienna': { country: 'Austria', flag: '🇦🇹', name: 'Austria' },
    'Europe/Stockholm': { country: 'Sweden', flag: '🇸🇪', name: 'Sweden' },
    'Europe/Oslo': { country: 'Norway', flag: '🇳🇴', name: 'Norway' },
    'Europe/Helsinki': { country: 'Finland', flag: '🇫🇮', name: 'Finland' },
    'Europe/Athens': { country: 'Greece', flag: '🇬🇷', name: 'Greece' },
    'Europe/Moscow': { country: 'Russia', flag: '🇷🇺', name: 'Russia (Moscow)' },
    'Australia/Sydney': { country: 'Australia', flag: '🇦🇺', name: 'Australia · Sydney' },
    'Australia/Melbourne': { country: 'Australia', flag: '🇦🇺', name: 'Australia · Melbourne' },
    'Australia/Brisbane': { country: 'Australia', flag: '🇦🇺', name: 'Australia · Brisbane' },
    'Australia/Adelaide': { country: 'Australia', flag: '🇦🇺', name: 'Australia · Adelaide' },
    'Australia/Perth': { country: 'Australia', flag: '🇦🇺', name: 'Australia · Perth' },
    'Pacific/Auckland': { country: 'New Zealand', flag: '🇳🇿', name: 'New Zealand (Auckland)' },
    'Africa/Johannesburg': { country: 'South Africa', flag: '🇿🇦', name: 'South Africa' },
    'Africa/Cairo': { country: 'Egypt', flag: '🇪🇬', name: 'Egypt (Cairo)' },
    'Africa/Nairobi': { country: 'Kenya', flag: '🇰🇪', name: 'Kenya (Nairobi)' },
    'America/Sao_Paulo': { country: 'Brazil', flag: '🇧🇷', name: 'Brazil (Sao Paulo)' },
    'UTC': { country: 'Universal', flag: '🌐', name: 'Universal Time (UTC)' }
  };

  // Helper: Format timezone offset string e.g. "GMT+05:30", "GMT-04:00"
  function getTzOffsetString(tz, date = new Date()) {
    if (tz && (tz.startsWith('GMT') || tz.startsWith('UTC'))) {
      return tz;
    }
    try {
      const parts = new Intl.DateTimeFormat('en-US', {
        timeZone: tz,
        timeZoneName: 'shortOffset'
      }).formatToParts(date);
      const found = parts.find(p => p.type === 'timeZoneName');
      if (found && found.value) return found.value;
    } catch (e) {}

    // Fallback using Date offset
    const offsetMinutes = -date.getTimezoneOffset();
    const sign = offsetMinutes >= 0 ? '+' : '-';
    const abs = Math.abs(offsetMinutes);
    const h = String(Math.floor(abs / 60)).padStart(2, '0');
    const m = String(abs % 60).padStart(2, '0');
    return `GMT${sign}${h}:${m}`;
  }

  // Detect native browser timezone & country
  let detectedTz = 'Asia/Kolkata';
  try {
    detectedTz = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Kolkata';
  } catch (e) {
    detectedTz = 'Asia/Kolkata';
  }

  let detectedOffset = getTzOffsetString(detectedTz);
  let detectedMeta = TZ_COUNTRY_MAP[detectedTz] || {
    country: detectedTz.includes('/') ? detectedTz.split('/')[0].replace(/_/g, ' ') : 'Local',
    flag: '📍',
    name: detectedTz.includes('/') ? detectedTz.split('/')[1].replace(/_/g, ' ') : detectedTz
  };

  // State: load saved user preference
  let currentSetting = {
    mode: 'auto', // 'auto' or 'manual'
    tz: detectedTz,
    offset: detectedOffset,
    country: detectedMeta.country,
    name: detectedMeta.name
  };

  try {
    const saved = localStorage.getItem('bhairava_ashtami_user_tz');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && (parsed.tz || parsed.offset)) {
        currentSetting = Object.assign(currentSetting, parsed);
      }
    }
  } catch (e) {}

  // Single date formatting function supporting IANA timezones and custom GMT offsets
  function formatSingleDate(dateObj, tzOrOffset) {
    if (!tzOrOffset) tzOrOffset = 'Asia/Kolkata';

    if (tzOrOffset.startsWith('GMT') || tzOrOffset.startsWith('UTC')) {
      const match = tzOrOffset.match(/^(?:GMT|UTC)([+-])(\d{1,2})(?::(\d{2}))?$/i);
      let offsetMins = 0;
      if (match) {
        const sign = match[1] === '-' ? -1 : 1;
        const hours = parseInt(match[2], 10);
        const mins = match[3] ? parseInt(match[3], 10) : 0;
        offsetMins = sign * (hours * 60 + mins);
      }
      const shifted = new Date(dateObj.getTime() + offsetMins * 60 * 1000);
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const m = months[shifted.getUTCMonth()];
      const day = String(shifted.getUTCDate()).padStart(2, '0');
      let hr = shifted.getUTCHours();
      const min = String(shifted.getUTCMinutes()).padStart(2, '0');
      const ampm = hr >= 12 ? 'PM' : 'AM';
      hr = hr % 12;
      hr = hr ? hr : 12;
      return `${m} ${day}, ${hr}:${min} ${ampm}`;
    }

    try {
      const f = new Intl.DateTimeFormat('en-US', {
        timeZone: tzOrOffset,
        month: 'short',
        day: '2-digit',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
      return f.format(dateObj);
    } catch (e) {
      return dateObj.toLocaleDateString('en-US', { month: 'short', day: '2-digit' }) + ' ' +
             dateObj.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
    }
  }

  // Get zone tag suffix (e.g. "IST" or "GMT+5:30" or "EDT")
  function getZoneAbbr(tzOrOffset, dateObj) {
    if (!tzOrOffset) return '';
    if (tzOrOffset === 'Asia/Kolkata' || tzOrOffset === 'Asia/Calcutta') return 'IST';
    if (tzOrOffset.startsWith('GMT') || tzOrOffset.startsWith('UTC')) {
      return tzOrOffset;
    }
    try {
      const parts = new Intl.DateTimeFormat('en-US', {
        timeZone: tzOrOffset,
        timeZoneName: 'short'
      }).formatToParts(dateObj);
      const found = parts.find(p => p.type === 'timeZoneName');
      if (found && found.value) return found.value;
    } catch (e) {}
    return getTzOffsetString(tzOrOffset, dateObj);
  }

  // Format the complete Ashtami range string
  function getFormattedRange(setting) {
    const sDate = new Date(startIso);
    const eDate = new Date(endIso);
    const tzTarget = setting.tz || setting.offset;

    const sStr = formatSingleDate(sDate, tzTarget);
    const eStr = formatSingleDate(eDate, tzTarget);
    const zoneAbbr = getZoneAbbr(tzTarget, sDate);

    return `${sStr} – ${eStr} ${zoneAbbr}`;
  }

  // Update all UI elements on the page
  function updateAllViews(triggerFlash = false) {
    const rangeText = getFormattedRange(currentSetting);
    const activeOffset = currentSetting.offset || getTzOffsetString(currentSetting.tz);
    const activeCountry = currentSetting.country || 'Local';

    // 1. Update text displays
    document.querySelectorAll('.ashtami-timing-val').forEach(el => {
      el.textContent = rangeText;
      if (triggerFlash) {
        el.classList.remove('timing-flash');
        void el.offsetWidth;
        el.classList.add('timing-flash');
      }
    });

    // 2. Update GMT Button displays
    const gmtBtnHtml = `
      <span class="gmt-globe">🌐</span>
      <span class="gmt-val">${activeOffset} (${activeCountry})</span>
      <span class="gmt-change-pill">Change GMT ▾</span>
    `;

    document.querySelectorAll('.ashtami-gmt-btn').forEach(btn => {
      btn.innerHTML = gmtBtnHtml;
      btn.setAttribute('title', `Active: ${activeOffset} (${activeCountry}) · Click to Change GMT`);
    });

    // 3. Update Ashtami page standalone highlight if present
    const pageTimingVal = document.getElementById('ashtami-page-timing-val');
    if (pageTimingVal) {
      pageTimingVal.textContent = rangeText;
      if (triggerFlash) {
        pageTimingVal.classList.remove('timing-flash');
        void pageTimingVal.offsetWidth;
        pageTimingVal.classList.add('timing-flash');
      }
    }
  }

  // Initial render
  updateAllViews(false);

  // Background non-blocking check to /api/next-ashtami for dynamic dates
  fetch('/api/next-ashtami')
    .then(r => r.json())
    .then(data => {
      if (data && data.start_iso && data.end_iso) {
        startIso = data.start_iso;
        endIso = data.end_iso;
        updateAllViews(false);
      }
    })
    .catch(() => {});

  // Background check for client geo if available
  fetch('/api/geo-timezone')
    .then(r => r.json())
    .then(geo => {
      if (geo && geo.country_code) {
        // Can be used to verify country if headers available
      }
    })
    .catch(() => {});

  // Modal Dialog Elements
  const modal = document.getElementById('ashtami-tz-modal');
  if (!modal) return;

  const modalCloseBtn = document.getElementById('ashtami-tz-close');
  const modalCancelBtn = document.getElementById('ashtami-tz-cancel');
  const modalApplyBtn = document.getElementById('ashtami-tz-apply');
  const autoResetBtn = document.getElementById('tz-btn-use-auto');
  const searchInput = document.getElementById('ashtami-tz-search');
  const clearSearchBtn = document.getElementById('ashtami-tz-clear-search');
  const presetsGrid = document.getElementById('tz-presets-grid');
  const offsetSelect = document.getElementById('ashtami-gmt-select');
  const detectedDesc = document.getElementById('tz-modal-detected-desc');
  const modeBadge = document.getElementById('tz-modal-status-badge');
  const previewTiming = document.getElementById('tz-preview-timing');
  const previewZone = document.getElementById('tz-preview-zone');

  // Staging state while modal is open
  let stagingSetting = Object.assign({}, currentSetting);

  function updateModalPreview() {
    if (!previewTiming || !previewZone) return;
    const testRange = getFormattedRange(stagingSetting);
    previewTiming.textContent = testRange;
    const zoneLabel = `${stagingSetting.offset || stagingSetting.tz} (${stagingSetting.country || stagingSetting.name || 'Selected'})`;
    previewZone.textContent = zoneLabel;
  }

  function syncModalUI() {
    // 1. Detected Location box
    if (detectedDesc) {
      detectedDesc.textContent = `${detectedMeta.country} · ${detectedTz} (${detectedOffset})`;
    }
    if (modeBadge) {
      if (currentSetting.mode === 'auto') {
        modeBadge.textContent = 'Auto-Aligned';
        modeBadge.className = 'tz-status-badge';
      } else {
        modeBadge.textContent = 'Custom Selected';
        modeBadge.className = 'tz-status-badge is-custom';
      }
    }

    // 2. Highlight active preset button if match
    if (presetsGrid) {
      presetsGrid.querySelectorAll('.tz-preset-btn').forEach(btn => {
        const btnTz = btn.getAttribute('data-tz');
        const btnOffset = btn.getAttribute('data-offset');
        const isMatch = (stagingSetting.tz && stagingSetting.tz === btnTz) ||
                        (!stagingSetting.tz && stagingSetting.offset === btnOffset);
        btn.classList.toggle('is-active', !!isMatch);
      });
    }

    // 3. Sync select dropdown
    if (offsetSelect && stagingSetting.offset) {
      for (let i = 0; i < offsetSelect.options.length; i++) {
        if (offsetSelect.options[i].value === stagingSetting.offset) {
          offsetSelect.selectedIndex = i;
          break;
        }
      }
    }

    // 4. Update preview
    updateModalPreview();
  }

  function openModal() {
    stagingSetting = Object.assign({}, currentSetting);
    modal.style.display = 'flex';
    void modal.offsetWidth;
    modal.classList.add('is-open');
    if (searchInput) {
      searchInput.value = '';
      filterPresets('');
      setTimeout(() => searchInput.focus(), 100);
    }
    syncModalUI();
  }

  function closeModal() {
    modal.classList.remove('is-open');
    setTimeout(() => {
      modal.style.display = 'none';
    }, 250);
  }

  // Open modal triggers (ribbon buttons and any page trigger)
  document.addEventListener('click', (e) => {
    const trigger = e.target.closest('.ashtami-gmt-btn, #ashtami-page-gmt-btn, .ashtami-page-gmt-trigger');
    if (trigger) {
      e.preventDefault();
      e.stopPropagation();
      openModal();
    }
  });

  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeModal);
  if (modalCancelBtn) modalCancelBtn.addEventListener('click', closeModal);

  // Close on backdrop click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  // Close on ESC
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('is-open')) {
      closeModal();
    }
  });

  // Reset to auto-detect button
  if (autoResetBtn) {
    autoResetBtn.addEventListener('click', () => {
      currentSetting = {
        mode: 'auto',
        tz: detectedTz,
        offset: detectedOffset,
        country: detectedMeta.country,
        name: detectedMeta.name
      };
      try {
        localStorage.removeItem('bhairava_ashtami_user_tz');
      } catch (e) {}
      updateAllViews(true);
      closeModal();
      showSacredToast(`✓ Timezone reset to auto-detected device time: ${detectedOffset} (${detectedMeta.country})`);
    });
  }

  // Preset button clicks
  if (presetsGrid) {
    presetsGrid.addEventListener('click', (e) => {
      const btn = e.target.closest('.tz-preset-btn');
      if (!btn) return;
      const tz = btn.getAttribute('data-tz');
      const offset = btn.getAttribute('data-offset');
      const country = btn.getAttribute('data-country');
      const name = btn.getAttribute('data-name');

      stagingSetting = {
        mode: 'manual',
        tz: tz,
        offset: offset,
        country: country,
        name: name
      };

      syncModalUI();
    });
  }

  // Offset dropdown change
  if (offsetSelect) {
    offsetSelect.addEventListener('change', () => {
      const selVal = offsetSelect.value;
      const selText = offsetSelect.options[offsetSelect.selectedIndex].text;
      const countryMatch = selText.includes('·') ? selText.split('·')[1].trim() : 'Custom';

      stagingSetting = {
        mode: 'manual',
        tz: selVal,
        offset: selVal,
        country: countryMatch,
        name: selText
      };

      syncModalUI();
    });
  }

  // Search filter
  function filterPresets(query) {
    if (!presetsGrid) return;
    const q = query.toLowerCase().trim();
    if (clearSearchBtn) {
      clearSearchBtn.style.display = q ? 'block' : 'none';
    }
    const buttons = presetsGrid.querySelectorAll('.tz-preset-btn');
    buttons.forEach(btn => {
      const text = btn.textContent.toLowerCase();
      const tz = (btn.getAttribute('data-tz') || '').toLowerCase();
      const offset = (btn.getAttribute('data-offset') || '').toLowerCase();
      const match = !q || text.includes(q) || tz.includes(q) || offset.includes(q);
      btn.style.display = match ? 'flex' : 'none';
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      filterPresets(searchInput.value);
    });
  }

  if (clearSearchBtn) {
    clearSearchBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      filterPresets('');
      if (searchInput) searchInput.focus();
    });
  }

  // Apply button
  if (modalApplyBtn) {
    modalApplyBtn.addEventListener('click', () => {
      currentSetting = Object.assign({}, stagingSetting, { mode: 'manual' });
      try {
        localStorage.setItem('bhairava_ashtami_user_tz', JSON.stringify(currentSetting));
      } catch (e) {}

      updateAllViews(true);
      closeModal();
      showSacredToast(`✓ Timezone aligned to ${currentSetting.offset} (${currentSetting.country || currentSetting.name})`);
    });
  }

  // Helper: Sacred Toast notification
  function showSacredToast(msg) {
    let toast = document.getElementById('sacred-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'sacred-toast';
      toast.className = 'sacred-toast';
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.classList.add('show');
    toast.classList.add('is-visible');
    setTimeout(() => {
      toast.classList.remove('show');
      toast.classList.remove('is-visible');
    }, 3800);
  }
}


