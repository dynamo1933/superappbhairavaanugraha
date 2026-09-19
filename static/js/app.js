/**
 * BHAIRAVA LOKA · SAHASRALINGA CODEX
 * Kinetic Celestial Spiral Engine & Codex Darshan Inspector
 */

(function () {
  'use strict';

  const TOTAL_POSTS = 150;
  const SPIRAL_TURNS = 6.2; // Number of cosmic spiral coils for 150 nodes
  const CX = 800;
  const CY = 800;
  const R_MIN = 28;
  const R_MAX = 685;

  function getOptimalZoom() {
    const w = window.innerWidth;
    if (w < 480) return 0.42;
    if (w < 768) return 0.55;
    if (w < 1024) return 0.68;
    return 0.85;
  }

  // State
  const state = {
    posts: [],
    filteredPosts: [],
    activePost: null,
    activePostIndex: 0,
    searchQuery: '',
    selectedTag: '',
    sortBy: 'date_desc',
    viewMode: 'mandala', // 'mandala' (spiral), 'grid', 'dense', 'cards'
    isAudioEnabled: false,
    audioCtx: null,
    isSidebarOpen: false,
    hoverDisabledUntil: 0,
    hoverLockTimer: null,

    // Spiral Motion state
    motionOffset: 0.0,
    isMotionPaused: false,
    motionSpeedMultiplier: 1.0, // 1.0 = exactly 1 position per 60 seconds (1 min)
    lastTimestamp: 0,
    animFrameId: null,

    // Canvas Pan & Zoom (Device Agnostic initial scale)
    zoom: getOptimalZoom(),
    panX: 0,
    panY: 0,
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0,
    startPanX: 0,
    startPanY: 0,

    hoveredPost: null
  };

  // DOM Elements Map
  let dom = {};

  function initDom() {
    dom = {
      mandalaContainer: document.getElementById('mandala-container'),
      mandalaViewport: document.getElementById('mandala-viewport'),
      mandalaWorld: document.getElementById('mandala-world'),
      mandalaRingsSvg: document.getElementById('mandala-rings-svg'),
      mandalaNodesContainer: document.getElementById('mandala-nodes-container'),
      mandalaTooltip: document.getElementById('mandala-tooltip'),
      zoomInBtn: document.getElementById('zoom-in-btn'),
      zoomOutBtn: document.getElementById('zoom-out-btn'),
      zoomResetBtn: document.getElementById('zoom-reset-btn'),
      motionToggleBtn: document.getElementById('motion-toggle-btn'),
      speedSelectBtn: document.getElementById('speed-select-btn'),

      lingamGrid: document.getElementById('lingam-grid'),
      gridCount: document.getElementById('grid-count'),
      headerBrandHome: document.getElementById('header-brand-home'),
      mobileReturnBanner: document.getElementById('mobile-return-banner'),
      sidebar: document.getElementById('darshan-sidebar'),
      sidebarBackdrop: document.getElementById('sidebar-backdrop'),
      sidebarBody: document.getElementById('sidebar-scroll-body'),
      closeSidebarBtn: document.getElementById('close-sidebar-btn'),
      prevPostBtn: document.getElementById('prev-post-btn'),
      nextPostBtn: document.getElementById('next-post-btn'),
      searchInput: document.getElementById('filter-search-input'),
      clearSearchBtn: document.getElementById('clear-search-btn'),
      sortSelect: document.getElementById('sort-select'),
      tagPillsContainer: document.getElementById('tag-pills-row'),
      viewButtons: document.querySelectorAll('.view-mode-btn'),
      audioToggleBtn: document.getElementById('audio-toggle-btn'),
      paletteModal: document.getElementById('palette-modal'),
      paletteInput: document.getElementById('palette-input'),
      paletteResults: document.getElementById('palette-results'),
      chromeSearchBtn: document.getElementById('chrome-search-btn'),
      closePaletteBtn: document.getElementById('close-palette-btn'),
      lightboxModal: document.getElementById('lightbox-modal'),
      lightboxImg: document.getElementById('lightbox-img'),
      closeLightboxBtn: document.getElementById('close-lightbox-btn'),
      toast: document.getElementById('sacred-toast'),
      copyCaptionBtn: document.getElementById('copy-caption-btn'),
      instaLinkBtn: document.getElementById('insta-link-btn'),
      appContainer: document.querySelector('.app-container')
    };
  }

  // High-performance Lingam SVG with direct path rendering & shared gradient references
  function getLingamSvg(isCentral = false) {
    const strokeWidth = isCentral ? '1.2' : '0.8';
    return `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120" width="100%" height="100%">
        <circle cx="50" cy="45" r="${isCentral ? 42 : 38}" fill="url(#auraGlowShared)" />
        <path d="M 18 102 L 82 102 L 86 110 L 14 110 Z" fill="url(#peethaGradShared)" stroke="url(#goldRimShared)" stroke-width="${strokeWidth}" />
        <path d="M 22 92 L 78 92 L 82 102 L 18 102 Z" fill="url(#peethaGradShared)" stroke="#d4a64a" stroke-width="0.6" />
        <path d="M 12 78 C 12 72 26 70 50 70 C 74 70 88 72 88 78 C 88 84 74 88 50 88 C 26 88 12 84 12 78 Z" fill="url(#peethaGradShared)" stroke="url(#goldRimShared)" stroke-width="${strokeWidth}" />
        <path d="M 16 77 L 4 75 C 2 75 2 81 4 81 L 18 80 Z" fill="#2a1f18" stroke="url(#goldRimShared)" stroke-width="0.8" />
        <path d="M 33 72 C 33 34 33 22 50 22 C 67 22 67 34 67 72 Z" fill="url(#lingamShadeShared)" stroke="url(#goldRimShared)" stroke-width="${strokeWidth}" />
        <path d="M 40 28 C 48 24 54 24 58 28" stroke="rgba(255,255,255,0.45)" stroke-width="1.2" stroke-linecap="round" fill="none" />
        <g transform="translate(0, 3)">
          <path d="M 41 42 C 45 40 55 40 59 42" stroke="#f0ebe0" stroke-width="1.4" stroke-linecap="round" fill="none" opacity="0.95" />
          <path d="M 39 46 C 45 44 55 44 61 46" stroke="#f0ebe0" stroke-width="1.4" stroke-linecap="round" fill="none" opacity="0.95" />
          <path d="M 41 50 C 45 48 55 48 59 50" stroke="#f0ebe0" stroke-width="1.4" stroke-linecap="round" fill="none" opacity="0.95" />
          <circle cx="50" cy="46" r="2.2" fill="#c41a1a" stroke="#ffe066" stroke-width="0.4" />
        </g>
        <path d="M 32 72 C 42 78 58 78 68 72" stroke="url(#goldRimShared)" stroke-width="1.8" stroke-dasharray="1.5,2" fill="none" />
        <polygon points="50,11 51.5,15 55.5,16 51.5,17 50,21 48.5,17 44.5,16 48.5,15" fill="#f5d061" opacity="0.9" />
      </svg>
    `;
  }

  // Calculate Spiral Coordinate for index `t`
  function getSpiralCoordinates(t, total = TOTAL_POSTS) {
    const u = Math.min(Math.max(t / (total - 1), 0), 1);

    // Smooth continuous spiral radius from center (0) to outer boundary (R_MAX)
    // Starting directly from the center Bindu/Jyoti (0) at u=0, emerging gracefully out to R_MIN at u=0.06
    let radius;
    if (u <= 0.06) {
      const respawnProgress = u / 0.06;
      radius = R_MIN * Math.pow(respawnProgress, 1.3);
    } else {
      const normU = (u - 0.06) / 0.94;
      radius = R_MIN + (R_MAX - R_MIN) * Math.pow(normU, 0.62);
    }

    const angle = (2 * Math.PI * SPIRAL_TURNS * Math.pow(u, 0.76)) - (Math.PI / 2);
    const x = CX + radius * Math.cos(angle);
    const y = CY + radius * Math.sin(angle);
    const rotation = (angle * 180 / Math.PI) + 90; // Radiate outwards along curve

    // Respawn from center & Dissolve at outer edge
    let opacity = 1.0;
    let scale = 1.0;
    let isRespawning = false;
    let isCompleting = false;

    if (u < 0.07) {
      // Emergence from the center sacred jyoti
      isRespawning = true;
      const respawnProg = u / 0.07;
      opacity = Math.max(0.08, respawnProg);
      scale = 0.3 + 0.7 * respawnProg;
    } else if (u > 0.92) {
      // Graceful dissolution into the cosmic void at the end of the spiral
      isCompleting = true;
      const completeProg = (1.0 - u) / 0.08;
      opacity = Math.max(0.0, completeProg);
      scale = 0.35 + 0.65 * Math.max(0.0, completeProg);
    }

    const isCentral = (u < 0.02);

    return { x, y, rotation, opacity, scale, isCentral, isRespawning, isCompleting };
  }

  // Draw SVG Background Spiral Arm Track & Canvas Gradients
  function drawSpiralTrackSvg() {
    if (!dom.mandalaRingsSvg) return;

    let pathD = '';
    const STEPS = 800;
    for (let s = 0; s <= STEPS; s++) {
      const u = s / STEPS;
      let radius;
      if (u <= 0.06) {
        const respawnProgress = u / 0.06;
        radius = R_MIN * Math.pow(respawnProgress, 1.3);
      } else {
        const normU = (u - 0.06) / 0.94;
        radius = R_MIN + (R_MAX - R_MIN) * Math.pow(normU, 0.62);
      }
      const angle = (2 * Math.PI * SPIRAL_TURNS * Math.pow(u, 0.76)) - (Math.PI / 2);
      const x = CX + radius * Math.cos(angle);
      const y = CY + radius * Math.sin(angle);
      if (s === 0) {
        pathD += `M ${x.toFixed(1)} ${y.toFixed(1)}`;
      } else {
        pathD += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
      }
    }

    dom.mandalaRingsSvg.innerHTML = `
      <defs>
        <linearGradient id="spiralGoldTrack" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#ffd700" stop-opacity="0.4" />
          <stop offset="50%" stop-color="#d4a64a" stop-opacity="0.22" />
          <stop offset="100%" stop-color="#8a5e1a" stop-opacity="0.1" />
        </linearGradient>
        <radialGradient id="auraGlowShared" cx="50%" cy="40%" r="50%">
          <stop offset="0%" stop-color="#ffd700" stop-opacity="0.45" />
          <stop offset="60%" stop-color="#d4a64a" stop-opacity="0.15" />
          <stop offset="100%" stop-color="#d4a64a" stop-opacity="0" />
        </radialGradient>
        <linearGradient id="lingamShadeShared" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#141012" />
          <stop offset="25%" stop-color="#2a2220" />
          <stop offset="50%" stop-color="#42342b" />
          <stop offset="75%" stop-color="#221a16" />
          <stop offset="100%" stop-color="#0a0809" />
        </linearGradient>
        <linearGradient id="goldRimShared" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#fff0b3" />
          <stop offset="40%" stop-color="#d4a64a" />
          <stop offset="80%" stop-color="#8a5e1a" />
          <stop offset="100%" stop-color="#f0d48a" />
        </linearGradient>
        <linearGradient id="peethaGradShared" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#34271e" />
          <stop offset="35%" stop-color="#1e1612" />
          <stop offset="70%" stop-color="#2d2118" />
          <stop offset="100%" stop-color="#120c09" />
        </linearGradient>
      </defs>
      <!-- Glowing Spiral Core Path -->
      <path d="${pathD}" stroke="url(#spiralGoldTrack)" stroke-width="1.6" stroke-dasharray="3, 5" fill="none" />
      <path d="${pathD}" stroke="rgba(212, 166, 74, 0.12)" stroke-width="6" fill="none" />
    `;
  }

  // Web Audio Bell Chime
  function playSacredChime() {
    if (!state.isAudioEnabled) return;
    try {
      if (!state.audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        state.audioCtx = new AudioContext();
      }
      if (state.audioCtx.state === 'suspended') {
        state.audioCtx.resume();
      }

      const now = state.audioCtx.currentTime;
      const fundamental = 528; // Sacred Solfeggio frequency

      const osc1 = state.audioCtx.createOscillator();
      const osc2 = state.audioCtx.createOscillator();
      const gainNode = state.audioCtx.createGain();

      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(fundamental, now);

      osc2.type = 'triangle';
      osc2.frequency.setValueAtTime(fundamental * 2.02, now);

      gainNode.gain.setValueAtTime(0, now);
      gainNode.gain.linearRampToValueAtTime(0.2, now + 0.04);
      gainNode.gain.exponentialRampToValueAtTime(0.0001, now + 2.4);

      osc1.connect(gainNode);
      osc2.connect(gainNode);
      gainNode.connect(state.audioCtx.destination);

      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + 2.5);
      osc2.stop(now + 2.5);
    } catch (e) {
      console.warn('Audio chime warning:', e);
    }
  }

  function showToast(message) {
    if (!dom.toast) return;
    dom.toast.textContent = message;
    dom.toast.classList.add('show');
    clearTimeout(dom.toast._timer);
    dom.toast._timer = setTimeout(() => {
      dom.toast.classList.remove('show');
    }, 2800);
  }

  // Instant inlined dataset loader with API fallback
  function getInlinedPosts() {
    const el = document.getElementById('initial-posts-data');
    if (el && el.textContent && el.textContent.trim().length > 0) {
      try {
        const parsed = JSON.parse(el.textContent.trim());
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      } catch (err) {
        console.warn('Inlined posts parse warning:', err);
      }
    }
    return null;
  }

  // Fetch or retrieve initial posts data instantly
  async function fetchPosts() {
    const inlined = getInlinedPosts();
    if (inlined) {
      state.posts = inlined;
      applyFiltersAndRender();
      if (state.posts.length > 0) {
        selectPost(state.posts[0], false);
      }
      return;
    }

    try {
      const res = await fetch('/api/posts');
      const data = await res.json();
      if (data.status === 'success') {
        state.posts = data.posts;
        applyFiltersAndRender();
        if (state.posts.length > 0) {
          selectPost(state.posts[0], false);
        }
      }
    } catch (err) {
      console.error('Error fetching posts:', err);
    }
  }

  // Apply filters and sort
  function applyFiltersAndRender() {
    let list = [...state.posts];

    if (state.searchQuery) {
      const q = state.searchQuery.toLowerCase();
      list = list.filter(p =>
        p.caption.toLowerCase().includes(q) ||
        p.title.toLowerCase().includes(q) ||
        String(p.index).includes(q) ||
        p.post_id.toLowerCase().includes(q)
      );
    }

    if (state.selectedTag) {
      const tagLower = state.selectedTag.toLowerCase().replace('#', '');
      list = list.filter(p =>
        p.hashtags.some(t => t.toLowerCase() === tagLower)
      );
    }

    if (state.sortBy === 'index_asc') {
      list.sort((a, b) => a.index - b.index);
    } else if (state.sortBy === 'index_desc') {
      list.sort((a, b) => b.index - a.index);
    } else if (state.sortBy === 'likes_desc') {
      list.sort((a, b) => b.likes - a.likes || a.index - b.index);
    } else if (state.sortBy === 'date_desc') {
      list.sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
    } else if (state.sortBy === 'date_asc') {
      list.sort((a, b) => (a.timestamp || '').localeCompare(b.timestamp || ''));
    } else if (state.sortBy === 'length_desc') {
      list.sort((a, b) => b.caption_length - a.caption_length);
    }

    state.filteredPosts = list;

    if (state.viewMode === 'mandala') {
      setupSpiralNodes();
    } else {
      renderGridView();
    }
    updateCount();
  }

  function updateCount() {
    if (dom.gridCount) {
      dom.gridCount.textContent = `${state.filteredPosts.length} Lingams`;
    }
  }

  // ==========================================================================
  // KINETIC CELESTIAL SPIRAL ENGINE
  // ==========================================================================
  function setupSpiralNodes() {
    if (!dom.mandalaContainer || !dom.mandalaNodesContainer) return;

    dom.mandalaContainer.style.display = 'block';
    if (dom.lingamGrid) dom.lingamGrid.style.display = 'none';

    drawSpiralTrackSvg();

    const filteredPostIds = new Set(state.filteredPosts.map(p => p.post_id));
    let nodesHtml = '';

    state.posts.forEach((post, i) => {
      const isMatch = filteredPostIds.has(post.post_id);
      const isCentral = (i === 0);
      const svgContent = getLingamSvg(isCentral);

      nodesHtml += `
        <div class="mandala-lingam-node ${isCentral ? 'is-central' : ''} ${!isMatch ? 'is-dimmed' : ''}"
             data-id="${post.post_id}"
             data-index="${post.index}"
             data-slot="${i}"
             id="mandala-node-${post.post_id}">
          ${svgContent}
        </div>
      `;
    });

    dom.mandalaNodesContainer.innerHTML = nodesHtml;
    attachSpiralEvents();
    updateSpiralPositions();
    updateMandalaTransform();
    startSpiralAnimation();
  }

  function attachSpiralEvents() {
    if (!dom.mandalaNodesContainer) return;
    const nodes = dom.mandalaNodesContainer.querySelectorAll('.mandala-lingam-node');

    nodes.forEach(node => {
      const postId = node.getAttribute('data-id');
      const post = state.posts.find(p => p.post_id === postId);

      node.addEventListener('click', (e) => {
        e.stopPropagation();
        if (post) {
          selectPost(post, true);
          openSidebar();
          playSacredChime();
          hideSpiralTooltip();
        }
      });

      node.addEventListener('mouseenter', () => {
        // Stop hover action if within 3 seconds of click or if sidebar is open
        if (Date.now() < state.hoverDisabledUntil || state.isSidebarOpen) return;

        if (post) {
          state.hoveredPost = post;
          showSpiralTooltip(node, post);
        }
      });

      node.addEventListener('mouseleave', () => {
        state.hoveredPost = null;
        hideSpiralTooltip();
      });
    });
  }

  // Continuous animation loop advancing 1 position per 60 seconds (1 minute)
  function startSpiralAnimation() {
    if (state.animFrameId) cancelAnimationFrame(state.animFrameId);
    state.lastTimestamp = performance.now();

    function loop(now) {
      if (state.viewMode !== 'mandala') return;

      const dt = now - state.lastTimestamp;
      state.lastTimestamp = now;

      if (!state.isMotionPaused && dt > 0) {
        // Speed: 1 position delta per 60,000 milliseconds (60 seconds)
        const speed = (1.0 / 60000.0) * state.motionSpeedMultiplier;
        state.motionOffset = (state.motionOffset + (speed * dt)) % TOTAL_POSTS;
        updateSpiralPositions();

        // Update tooltip position if hovered (only when hover is enabled)
        if (state.hoveredPost && Date.now() >= state.hoverDisabledUntil) {
          const hoveredNode = document.getElementById(`mandala-node-${state.hoveredPost.post_id}`);
          if (hoveredNode) showSpiralTooltip(hoveredNode, state.hoveredPost);
        } else if (Date.now() < state.hoverDisabledUntil) {
          hideSpiralTooltip();
        }
      }

      state.animFrameId = requestAnimationFrame(loop);
    }

    state.animFrameId = requestAnimationFrame(loop);
  }

  function updateSpiralPositions() {
    if (!dom.mandalaNodesContainer) return;
    const nodes = dom.mandalaNodesContainer.querySelectorAll('.mandala-lingam-node');
    const total = state.posts.length || TOTAL_POSTS;

    nodes.forEach((node, i) => {
      // Shift continuous slot along the spiral curve
      const continuousSlot = (i + state.motionOffset) % total;
      const { x, y, rotation, opacity, scale, isCentral, isRespawning, isCompleting } = getSpiralCoordinates(continuousSlot, total);

      node.style.left = `${x.toFixed(1)}px`;
      node.style.top = `${y.toFixed(1)}px`;

      const isActive = node.classList.contains('is-active');
      const finalScale = isActive ? 1.85 : scale;
      const finalOpacity = isActive ? 1 : opacity;

      node.style.transform = `rotate(${rotation.toFixed(1)}deg) scale(${finalScale.toFixed(2)})`;
      node.style.opacity = finalOpacity.toFixed(2);

      if (isCentral) {
        node.classList.add('is-central');
      } else {
        node.classList.remove('is-central');
      }

      if (isRespawning) {
        node.classList.add('is-respawning');
      } else {
        node.classList.remove('is-respawning');
      }

      if (isCompleting) {
        node.classList.add('is-completing');
      } else {
        node.classList.remove('is-completing');
      }
    });
  }

  function showSpiralTooltip(node, post) {
    if (!dom.mandalaTooltip) return;
    const rect = node.getBoundingClientRect();
    const containerRect = dom.mandalaContainer.getBoundingClientRect();

    const tipX = rect.left - containerRect.left + (rect.width / 2);
    const tipY = rect.top - containerRect.top;

    dom.mandalaTooltip.style.left = `${tipX}px`;
    dom.mandalaTooltip.style.top = `${tipY}px`;
    dom.mandalaTooltip.innerHTML = `
      <div class="tip-index">№ ${String(post.index).padStart(3, '0')} · ${post.formatted_date || ''}</div>
      <div class="tip-title">${escapeHtml(post.title)}</div>
      <div style="font-family: var(--mono); font-size: 9px; color: var(--gold); margin-top: 4px;">♥ ${post.likes.toLocaleString()} Reverence</div>
    `;
    dom.mandalaTooltip.classList.add('is-visible');
  }

  function hideSpiralTooltip() {
    if (dom.mandalaTooltip) {
      dom.mandalaTooltip.classList.remove('is-visible');
    }
  }

  function updateMandalaTransform() {
    if (!dom.mandalaWorld) return;
    dom.mandalaWorld.style.transform = `translate(${state.panX}px, ${state.panY}px) scale(${state.zoom})`;
  }

  // ==========================================================================
  // GRID / DENSE / CARDS VIEW RENDERER
  // ==========================================================================
  function renderGridView() {
    if (!dom.lingamGrid) return;

    dom.lingamGrid.style.display = 'grid';
    if (dom.mandalaContainer) dom.mandalaContainer.style.display = 'none';

    if (state.filteredPosts.length === 0) {
      dom.lingamGrid.innerHTML = `
        <div class="no-results-state" style="grid-column: 1 / -1;">
          <div class="skt-symbol">॥ ॐ ॥</div>
          <h3>No Sacred Inscriptions Found</h3>
          <p>No Shiva Lingams match your search or filter parameters.</p>
          <button type="button" id="reset-filters-btn">Reset All Filters</button>
        </div>
      `;
      const resetBtn = document.getElementById('reset-filters-btn');
      if (resetBtn) {
        resetBtn.addEventListener('click', () => {
          state.searchQuery = '';
          state.selectedTag = '';
          if (dom.searchInput) dom.searchInput.value = '';
          document.querySelectorAll('.tag-filter-pill').forEach(el => el.classList.remove('active'));
          applyFiltersAndRender();
        });
      }
      return;
    }

    const svgHtml = getLingamSvg(false);
    const htmlParts = state.filteredPosts.map((post, idx) => {
      const pid = post.post_id || post.id || `p-${idx}`;
      const isActive = state.activePost && (state.activePost.post_id === pid || state.activePost.id === pid);
      const postIndex = (post.index !== undefined && post.index !== null) ? post.index : (idx + 1);
      const formattedIndex = String(postIndex).padStart(3, '0');
      const likesCount = post.likes ? post.likes.toLocaleString() : '0';

      return `
        <div class="lingam-card ${isActive ? 'is-active' : ''}" data-id="${pid}" data-index="${postIndex}" id="lingam-card-${pid}">
          <div class="card-index-badge">№ ${formattedIndex}</div>
          <div class="lingam-visual-wrap">
            <div class="lingam-halo"></div>
            ${svgHtml}
          </div>
          <div class="card-title">${escapeHtml(post.title)}</div>
          <div class="card-meta-row">
            <span>${(post.formatted_date || post.date || '').split(',')[0]}</span>
            <span class="likes-tag">♥ ${likesCount}</span>
          </div>
        </div>
      `;
    });

    dom.lingamGrid.innerHTML = htmlParts.join('');

    const cards = dom.lingamGrid.querySelectorAll('.lingam-card');
    cards.forEach(card => {
      const postId = card.getAttribute('data-id');
      const post = state.posts.find(p => p.post_id === postId);

      card.addEventListener('click', () => {
        if (post) {
          selectPost(post, true);
          openSidebar();
          playSacredChime();
        }
      });
    });
  }

  // ==========================================================================
  // SIDEBAR DARSHAN INSPECTOR & DATA SYNC
  // ==========================================================================
  function selectPost(post, updateActiveState = true) {
    if (!post) return;
    state.activePost = post;
    state.activePostIndex = state.filteredPosts.findIndex(p => p.post_id === post.post_id);

    // Disable hover action for the next 3 seconds so viewer can read peacefully
    state.hoveredPost = null;
    hideSpiralTooltip();
    state.hoverDisabledUntil = Date.now() + 3000;
    document.body.classList.add('hover-locked');
    if (state.hoverLockTimer) clearTimeout(state.hoverLockTimer);
    state.hoverLockTimer = setTimeout(() => {
      document.body.classList.remove('hover-locked');
    }, 3000);

    // Update grid active state
    document.querySelectorAll('.lingam-card').forEach(c => c.classList.remove('is-active'));
    const activeCard = document.getElementById(`lingam-card-${post.post_id}`);
    if (activeCard) activeCard.classList.add('is-active');

    // Update spiral active state
    document.querySelectorAll('.mandala-lingam-node').forEach(n => n.classList.remove('is-active'));
    const activeNode = document.getElementById(`mandala-node-${post.post_id}`);
    if (activeNode) activeNode.classList.add('is-active');

    renderSidebarContent(post, true);
  }

  function renderSidebarContent(post, isCommitted = true) {
    if (!dom.sidebar || !post) return;

    const formattedIndex = String(post.index).padStart(3, '0');
    const totalCount = String(state.posts.length).padStart(3, '0');

    const indexInd = dom.sidebar.querySelector('.index-indicator');
    if (indexInd) {
      indexInd.innerHTML = `№ ${formattedIndex} <span class="bullet">/</span> ${totalCount} DARSHAN`;
    }

    const mediaFrame = dom.sidebar.querySelector('.sidebar-media-frame');
    if (mediaFrame) {
      if (post.image_url) {
        mediaFrame.style.display = 'block';
        mediaFrame.innerHTML = `
          <img src="${post.image_url}" alt="${escapeHtml(post.title)}" loading="lazy" id="sidebar-image-elem" />
          <span class="zoom-hint-badge">🔍 Expand</span>
        `;
        const imgElem = mediaFrame.querySelector('#sidebar-image-elem');
        imgElem.addEventListener('click', () => {
          openLightbox(post.image_url);
        });
      } else {
        mediaFrame.style.display = 'none';
      }
    }

    const titleElem = dom.sidebar.querySelector('.sidebar-title-block h2');
    if (titleElem) {
      titleElem.textContent = post.title;
    }

    const statsRow = dom.sidebar.querySelector('.sidebar-stats-row');
    if (statsRow) {
      statsRow.innerHTML = `
        <span class="sidebar-badge gold">♥ ${post.likes.toLocaleString()} Reverence</span>
        <span class="sidebar-badge">💬 ${post.comments} Comments</span>
        <span class="sidebar-badge">🗓 ${post.formatted_date || ''}</span>
        <span class="sidebar-badge">📜 ${post.word_count} words</span>
      `;
    }

    const discourseBody = dom.sidebar.querySelector('.sidebar-discourse-body');
    if (discourseBody) {
      discourseBody.innerHTML = formatCaptionHtml(post.caption);
    }

    const tagsContainer = dom.sidebar.querySelector('.sidebar-tags-container');
    if (tagsContainer) {
      if (post.hashtags && post.hashtags.length > 0) {
        tagsContainer.style.display = 'flex';
        tagsContainer.innerHTML = post.hashtags.map(t =>
          `<span class="sidebar-tag-link" data-tag="${escapeHtml(t)}">#${escapeHtml(t)}</span>`
        ).join('');

        tagsContainer.querySelectorAll('.sidebar-tag-link').forEach(pill => {
          pill.addEventListener('click', () => {
            const tag = pill.getAttribute('data-tag');
            setTagFilter(tag);
          });
        });
      } else {
        tagsContainer.style.display = 'none';
      }
    }

    if (dom.instaLinkBtn) {
      if (post.instagram_url) {
        dom.instaLinkBtn.href = post.instagram_url;
        dom.instaLinkBtn.style.display = 'flex';
      } else {
        dom.instaLinkBtn.style.display = 'none';
      }
    }

    updateNavButtons();
  }

  function formatCaptionHtml(rawText) {
    if (!rawText) return '';
    const paragraphs = rawText.split(/\n\s*\n/);
    return paragraphs.map(para => {
      let clean = escapeHtml(para).replace(/\n/g, '<br/>');
      clean = clean.replace(/(ॐ\s*[^<]+|Jai\s+Bhairava|Kaal\s+Bhairava|Bhairavāya\s+Namaḥ|Martanda\s+Bhairava|Kilkāra\s+Bhairava)/gi,
        '<span class="gold" style="font-weight:600;">$1</span>'
      );
      return `<p>${clean}</p>`;
    }).join('');
  }

  function openSidebar() {
    if (dom.sidebar) {
      state.isSidebarOpen = true;
      hideSpiralTooltip();
      dom.sidebar.classList.add('is-open');
      if (window.innerWidth <= 900) {
        if (dom.sidebarBackdrop) dom.sidebarBackdrop.classList.add('is-visible');
        document.body.classList.add('modal-open');
      } else {
        if (dom.sidebarBackdrop) dom.sidebarBackdrop.classList.remove('is-visible');
        document.body.classList.remove('modal-open');
        if (dom.appContainer) {
          dom.appContainer.style.paddingRight = 'var(--sidebar-w)';
        }
      }
    }
  }

  function closeSidebar() {
    if (dom.sidebar) {
      state.isSidebarOpen = false;
      dom.sidebar.classList.remove('is-open');
      if (dom.sidebarBackdrop) {
        dom.sidebarBackdrop.classList.remove('is-visible');
      }
      document.body.classList.remove('modal-open');
      if (dom.appContainer) {
        dom.appContainer.style.paddingRight = '0';
      }
    }
  }

  function returnToLandingPage() {
    closeSidebar();
    closePalette();
    closeLightbox();

    // Reset search query
    state.searchQuery = '';
    if (dom.searchInput) dom.searchInput.value = '';
    if (dom.clearSearchBtn) dom.clearSearchBtn.style.display = 'none';

    // Reset tag filter
    state.selectedTag = '';
    document.querySelectorAll('.tag-filter-pill').forEach(el => el.classList.remove('active'));

    // Reset sorting order to default (newest first)
    state.sortBy = 'date_desc';
    if (dom.sortSelect) dom.sortSelect.value = 'date_desc';

    // Switch view mode back to Celestial Spiral
    state.viewMode = 'mandala';
    if (dom.viewButtons) {
      dom.viewButtons.forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-view') === 'mandala');
      });
    }

    // Reset pan and zoom to centered optimal viewport
    state.panX = 0;
    state.panY = 0;
    state.zoom = getOptimalZoom();
    updateMandalaTransform();

    // Resume perpetual spiral motion
    state.isMotionPaused = false;
    if (dom.motionToggleBtn) {
      dom.motionToggleBtn.classList.add('active');
      dom.motionToggleBtn.innerHTML = '<span>⏸ Pause</span>';
    }

    // Apply filters and re-render
    applyFiltersAndRender();

    // Smooth scroll to top of window
    window.scrollTo({ top: 0, behavior: 'smooth' });
    showToast('Returned to Bhairava Loka · Celestial Spiral');
  }

  function navigatePost(direction) {
    if (state.filteredPosts.length === 0) return;
    let newIndex = state.activePostIndex + direction;
    if (newIndex < 0) newIndex = state.filteredPosts.length - 1;
    if (newIndex >= state.filteredPosts.length) newIndex = 0;

    const nextPost = state.filteredPosts[newIndex];
    if (nextPost) {
      selectPost(nextPost, true);
      openSidebar();
      playSacredChime();

      if (state.viewMode === 'mandala') {
        const node = document.getElementById(`mandala-node-${nextPost.post_id}`);
        if (node) showSpiralTooltip(node, nextPost);
      } else {
        const card = document.getElementById(`lingam-card-${nextPost.post_id}`);
        if (card) card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }

  function updateNavButtons() {
    if (dom.prevPostBtn) dom.prevPostBtn.disabled = state.filteredPosts.length <= 1;
    if (dom.nextPostBtn) dom.nextPostBtn.disabled = state.filteredPosts.length <= 1;
  }

  function setTagFilter(tag) {
    state.selectedTag = (state.selectedTag === tag) ? '' : tag;
    document.querySelectorAll('.tag-filter-pill').forEach(el => {
      const elTag = el.getAttribute('data-tag');
      if (elTag === state.selectedTag) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });
    applyFiltersAndRender();
    showToast(`Filter: #${tag}`);
  }

  function openLightbox(imgUrl) {
    if (!dom.lightboxModal || !dom.lightboxImg) return;
    dom.lightboxImg.src = imgUrl;
    dom.lightboxModal.classList.add('is-visible');
  }

  function closeLightbox() {
    if (dom.lightboxModal) dom.lightboxModal.classList.remove('is-visible');
  }

  function openPalette() {
    if (!dom.paletteModal) return;
    dom.paletteModal.classList.add('is-visible');
    if (dom.paletteInput) {
      dom.paletteInput.value = '';
      dom.paletteInput.focus();
      renderPaletteResults('');
    }
  }

  function closePalette() {
    if (dom.paletteModal) dom.paletteModal.classList.remove('is-visible');
  }

  function renderPaletteResults(query) {
    if (!dom.paletteResults) return;
    const q = (query || '').toLowerCase().trim();
    let matches = state.posts;
    if (q) {
      matches = matches.filter(p =>
        p.title.toLowerCase().includes(q) ||
        p.caption.toLowerCase().includes(q) ||
        p.post_id.toLowerCase().includes(q) ||
        String(p.index).includes(q)
      );
    }
    matches = matches.slice(0, 10);

    if (matches.length === 0) {
      dom.paletteResults.innerHTML = `
        <div style="padding: 20px; text-align: center; color: var(--ink-dim); font-style: italic;">
          No matching codex entries found.
        </div>
      `;
      return;
    }

    dom.paletteResults.innerHTML = matches.map(p => `
      <div class="palette-item" data-id="${p.post_id}">
        <div>
          <div class="item-title">${escapeHtml(p.title)}</div>
          <div style="font-size: 11px; color: var(--ink-dim); margin-top: 2px;">
            ${p.formatted_date || ''} · ${p.word_count} words
          </div>
        </div>
        <div class="item-meta">№ ${String(p.index).padStart(3, '0')}</div>
      </div>
    `).join('');

    dom.paletteResults.querySelectorAll('.palette-item').forEach(item => {
      item.addEventListener('click', () => {
        const postId = item.getAttribute('data-id');
        const p = state.posts.find(x => x.post_id === postId);
        if (p) {
          closePalette();
          selectPost(p, true);
          openSidebar();
          playSacredChime();
        }
      });
    });
  }

  function copyActiveCaption() {
    if (!state.activePost) return;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(state.activePost.caption).then(() => {
        showToast('Discourse copied to clipboard');
      }).catch(() => fallbackCopyText(state.activePost.caption));
    } else {
      fallbackCopyText(state.activePost.caption);
    }
  }

  function fallbackCopyText(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showToast('Discourse copied to clipboard');
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Setup Event Listeners
  function setupEventListeners() {
    // Spiral Viewport Mouse Dragging (Pan)
    if (dom.mandalaViewport) {
      dom.mandalaViewport.addEventListener('mousedown', (e) => {
        if (e.target.closest('.mandala-lingam-node') || e.target.closest('.mandala-overlay-controls')) return;
        state.isDragging = true;
        state.dragStartX = e.clientX;
        state.dragStartY = e.clientY;
        state.startPanX = state.panX;
        state.startPanY = state.panY;
      });

      window.addEventListener('mousemove', (e) => {
        if (!state.isDragging) return;
        const dx = e.clientX - state.dragStartX;
        const dy = e.clientY - state.dragStartY;
        state.panX = state.startPanX + dx;
        state.panY = state.startPanY + dy;
        updateMandalaTransform();
        hideSpiralTooltip();
      });

      window.addEventListener('mouseup', () => {
        state.isDragging = false;
      });

      // Mouse Wheel Zoom
      dom.mandalaViewport.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.08 : 0.08;
        state.zoom = Math.min(Math.max(state.zoom + delta, 0.35), 2.4);
        updateMandalaTransform();
        hideSpiralTooltip();
      }, { passive: false });

      // Touch Gestures: 1-Finger Pan & 2-Finger Pinch-to-Zoom
      let touchStartX = 0;
      let touchStartY = 0;
      let startTouchPanX = 0;
      let startTouchPanY = 0;
      let initialPinchDist = 0;
      let initialPinchZoom = 0.85;
      let isTouchPanning = false;

      dom.mandalaViewport.addEventListener('touchstart', (e) => {
        if (e.target.closest('.mandala-overlay-controls')) return;

        if (e.touches.length === 1) {
          isTouchPanning = true;
          touchStartX = e.touches[0].clientX;
          touchStartY = e.touches[0].clientY;
          startTouchPanX = state.panX;
          startTouchPanY = state.panY;
        } else if (e.touches.length === 2) {
          isTouchPanning = false;
          initialPinchDist = Math.hypot(
            e.touches[0].clientX - e.touches[1].clientX,
            e.touches[0].clientY - e.touches[1].clientY
          );
          initialPinchZoom = state.zoom;
        }
      }, { passive: true });

      dom.mandalaViewport.addEventListener('touchmove', (e) => {
        if (e.touches.length === 1 && isTouchPanning) {
          const dx = e.touches[0].clientX - touchStartX;
          const dy = e.touches[0].clientY - touchStartY;
          state.panX = startTouchPanX + dx;
          state.panY = startTouchPanY + dy;
          updateMandalaTransform();
          hideSpiralTooltip();
        } else if (e.touches.length === 2 && initialPinchDist > 0) {
          const dist = Math.hypot(
            e.touches[0].clientX - e.touches[1].clientX,
            e.touches[0].clientY - e.touches[1].clientY
          );
          const scaleFactor = dist / initialPinchDist;
          state.zoom = Math.min(Math.max(initialPinchZoom * scaleFactor, 0.32), 2.5);
          updateMandalaTransform();
          hideSpiralTooltip();
        }
      }, { passive: true });

      dom.mandalaViewport.addEventListener('touchend', (e) => {
        if (e.touches.length === 0) {
          isTouchPanning = false;
          initialPinchDist = 0;
        } else if (e.touches.length === 1) {
          isTouchPanning = true;
          touchStartX = e.touches[0].clientX;
          touchStartY = e.touches[0].clientY;
          startTouchPanX = state.panX;
          startTouchPanY = state.panY;
        }
      }, { passive: true });
    }

    // Motion Play / Pause Button
    if (dom.motionToggleBtn) {
      dom.motionToggleBtn.addEventListener('click', () => {
        state.isMotionPaused = !state.isMotionPaused;
        if (state.isMotionPaused) {
          dom.motionToggleBtn.innerHTML = '<span>▶ Resume</span>';
          dom.motionToggleBtn.classList.remove('active');
          showToast('Spiral Motion Paused');
        } else {
          dom.motionToggleBtn.innerHTML = '<span>⏸ Pause</span>';
          dom.motionToggleBtn.classList.add('active');
          showToast('Spiral Motion Active (1 pos / min)');
        }
      });
    }

    // Motion Speed Selector Button
    if (dom.speedSelectBtn) {
      dom.speedSelectBtn.addEventListener('click', () => {
        if (state.motionSpeedMultiplier === 1.0) {
          state.motionSpeedMultiplier = 2.0;
          dom.speedSelectBtn.textContent = '2x Flow';
          showToast('Speed: 2x Flow');
        } else if (state.motionSpeedMultiplier === 2.0) {
          state.motionSpeedMultiplier = 0.5;
          dom.speedSelectBtn.textContent = '0.5x Meditative';
          showToast('Speed: 0.5x Meditative');
        } else {
          state.motionSpeedMultiplier = 1.0;
          dom.speedSelectBtn.textContent = '1x (1 min/pos)';
          showToast('Speed: 1x (1 position / 1 minute)');
        }
      });
    }

    // Spiral Zoom Controls
    if (dom.zoomInBtn) {
      dom.zoomInBtn.addEventListener('click', () => {
        state.zoom = Math.min(state.zoom + 0.15, 2.4);
        updateMandalaTransform();
      });
    }
    if (dom.zoomOutBtn) {
      dom.zoomOutBtn.addEventListener('click', () => {
        state.zoom = Math.max(state.zoom - 0.15, 0.35);
        updateMandalaTransform();
      });
    }
    if (dom.zoomResetBtn) {
      dom.zoomResetBtn.addEventListener('click', () => {
        state.zoom = getOptimalZoom();
        state.panX = 0;
        state.panY = 0;
        updateMandalaTransform();
        showToast('View Centered');
      });
    }

    // Responsive window resize / orientation handler
    window.addEventListener('resize', () => {
      if (window.innerWidth <= 900 && dom.appContainer) {
        dom.appContainer.style.paddingRight = '0';
      } else if (state.isSidebarOpen && window.innerWidth > 1200 && dom.appContainer) {
        dom.appContainer.style.paddingRight = 'var(--sidebar-w)';
      }
    });

    // Search Input
    if (dom.searchInput) {
      dom.searchInput.addEventListener('input', (e) => {
        state.searchQuery = e.target.value.trim();
        if (dom.clearSearchBtn) dom.clearSearchBtn.style.display = state.searchQuery ? 'block' : 'none';
        applyFiltersAndRender();
      });
    }

    if (dom.clearSearchBtn) {
      dom.clearSearchBtn.addEventListener('click', () => {
        state.searchQuery = '';
        if (dom.searchInput) dom.searchInput.value = '';
        dom.clearSearchBtn.style.display = 'none';
        applyFiltersAndRender();
      });
    }

    // Sort Select
    if (dom.sortSelect) {
      dom.sortSelect.addEventListener('change', (e) => {
        state.sortBy = e.target.value;
        applyFiltersAndRender();
      });
    }

    // View Mode Buttons
    dom.viewButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        dom.viewButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const mode = btn.getAttribute('data-view');
        state.viewMode = mode;

        if (mode === 'mandala') {
          setupSpiralNodes();
        } else {
          if (dom.lingamGrid) dom.lingamGrid.className = `lingam-grid view-${mode}`;
          renderGridView();
        }
      });
    });

    // Tag pills
    document.querySelectorAll('.tag-filter-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const tag = pill.getAttribute('data-tag');
        setTagFilter(tag);
      });
    });

    // Header Brand / Logo click -> Return to main landing page
    if (dom.headerBrandHome) {
      dom.headerBrandHome.addEventListener('click', returnToLandingPage);
      dom.headerBrandHome.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          returnToLandingPage();
        }
      });
    }

    // Sidebar Close / Navigation
    if (dom.closeSidebarBtn) dom.closeSidebarBtn.addEventListener('click', closeSidebar);
    if (dom.mobileReturnBanner) {
      dom.mobileReturnBanner.addEventListener('click', closeSidebar);
      dom.mobileReturnBanner.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          closeSidebar();
        }
      });
    }
    if (dom.sidebarBackdrop) dom.sidebarBackdrop.addEventListener('click', closeSidebar);
    if (dom.prevPostBtn) dom.prevPostBtn.addEventListener('click', () => navigatePost(-1));
    if (dom.nextPostBtn) dom.nextPostBtn.addEventListener('click', () => navigatePost(1));
    if (dom.copyCaptionBtn) dom.copyCaptionBtn.addEventListener('click', copyActiveCaption);

    // Audio Toggle
    if (dom.audioToggleBtn) {
      dom.audioToggleBtn.addEventListener('click', () => {
        state.isAudioEnabled = !state.isAudioEnabled;
        if (state.isAudioEnabled) {
          dom.audioToggleBtn.classList.add('active');
          dom.audioToggleBtn.innerHTML = '<span>🔔 Audio On</span>';
          playSacredChime();
          showToast('Sacred Chime Enabled');
        } else {
          dom.audioToggleBtn.classList.remove('active');
          dom.audioToggleBtn.innerHTML = '<span>🔕 Audio Off</span>';
          showToast('Audio Muted');
        }
      });
    }

    // Palette Modal
    if (dom.chromeSearchBtn) dom.chromeSearchBtn.addEventListener('click', openPalette);
    if (dom.closePaletteBtn) dom.closePaletteBtn.addEventListener('click', closePalette);
    if (dom.paletteModal) {
      dom.paletteModal.addEventListener('click', (e) => {
        if (e.target === dom.paletteModal) closePalette();
      });
    }
    if (dom.paletteInput) {
      dom.paletteInput.addEventListener('input', (e) => {
        renderPaletteResults(e.target.value);
      });
    }

    // Lightbox Modal
    if (dom.closeLightboxBtn) dom.closeLightboxBtn.addEventListener('click', closeLightbox);
    if (dom.lightboxModal) {
      dom.lightboxModal.addEventListener('click', (e) => {
        if (e.target === dom.lightboxModal) closeLightbox();
      });
    }

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openPalette();
        return;
      }
      if (e.key === 'Escape') {
        closePalette();
        closeLightbox();
        closeSidebar();
        return;
      }
      if (document.activeElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
        return;
      }
      if (e.key === 'ArrowLeft' || e.key === 'h') navigatePost(-1);
      if (e.key === 'ArrowRight' || e.key === 'l') navigatePost(1);
      if (e.key === '/' && dom.searchInput) {
        e.preventDefault();
        dom.searchInput.focus();
      }
      // Space -> Pause/Resume Motion
      if (e.key === ' ' && state.viewMode === 'mandala') {
        e.preventDefault();
        if (dom.motionToggleBtn) dom.motionToggleBtn.click();
      }
    });
  }

  // Initialize immediately or on DOM ready
  function init() {
    initDom();
    setupEventListeners();
    fetchPosts();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
