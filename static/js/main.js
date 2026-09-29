/**
 * Main Client Application Script for Our Little World (Raj & Ashmita)
 * Advanced Love Animations, GSAP Integrations, Audio Synthesizer & Micro-Interactions
 */

document.addEventListener('DOMContentLoaded', function () {

  const appBackButton = document.getElementById('appBackButton');
  if (appBackButton) {
    appBackButton.addEventListener('click', function () {
      const previousPage = document.referrer;
      if (previousPage && new URL(previousPage).origin === window.location.origin) {
        window.history.back();
      } else {
        window.location.assign(appBackButton.dataset.fallback);
      }
    });
  }

  const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
  const sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const sidebarPreferencesToggle = document.getElementById('sidebarPreferencesToggle');

  function setSidebarOpen(isOpen) {
    document.body.classList.toggle('sidebar-open', isOpen);
    if (sidebarToggleBtn) {
      sidebarToggleBtn.setAttribute('aria-expanded', String(isOpen));
      sidebarToggleBtn.setAttribute('aria-label', isOpen ? 'Close navigation' : 'Open navigation');
    }
  }

  if (sidebarToggleBtn) {
    sidebarToggleBtn.addEventListener('click', function () {
      setSidebarOpen(!document.body.classList.contains('sidebar-open'));
    });
  }

  if (sidebarCloseBtn) sidebarCloseBtn.addEventListener('click', function () { setSidebarOpen(false); });
  if (sidebarBackdrop) sidebarBackdrop.addEventListener('click', function () { setSidebarOpen(false); });

  document.querySelectorAll('a.sidebar-link').forEach(function (link) {
    link.addEventListener('click', function () { setSidebarOpen(false); });
  });

  if (sidebarPreferencesToggle) {
    sidebarPreferencesToggle.addEventListener('click', function () {
      const isExpanded = sidebarPreferencesToggle.getAttribute('aria-expanded') === 'true';
      sidebarPreferencesToggle.setAttribute('aria-expanded', String(!isExpanded));
    });
  }

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') setSidebarOpen(false);
  });

  window.addEventListener('resize', function () {
    if (window.innerWidth > 991) setSidebarOpen(false);
  });

  const liveLocationUrl = document.body.dataset.liveLocationUrl;
  const liveLocationCsrfToken = document.body.dataset.csrfToken;
  const liveLocationUserId = Number(document.body.dataset.currentUserId);
  let liveLocationWatchId = null;
  let liveLocationUpdatePending = false;

  function stopLiveLocationWatch() {
    if (liveLocationWatchId !== null && navigator.geolocation) {
      navigator.geolocation.clearWatch(liveLocationWatchId);
      liveLocationWatchId = null;
    }
  }

  function sendLiveLocationUpdate(position) {
    if (liveLocationUpdatePending) return;
    liveLocationUpdatePending = true;

    fetch(liveLocationUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': liveLocationCsrfToken
      },
      body: JSON.stringify({
        action: 'update',
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        _csrf_token: liveLocationCsrfToken
      })
    }).then(function (response) {
      if (response.status === 409) stopLiveLocationWatch();
      if (!response.ok) throw new Error('Could not update your live location.');
      document.dispatchEvent(new Event('live-location-updated'));
    }).catch(function (error) {
      document.dispatchEvent(new CustomEvent('live-location-update-error', { detail: error.message }));
    }).finally(function () {
      liveLocationUpdatePending = false;
    });
  }

  function startLiveLocationWatch() {
    if (!navigator.geolocation || liveLocationWatchId !== null) return;
    liveLocationWatchId = navigator.geolocation.watchPosition(
      sendLiveLocationUpdate,
      function (error) {
        document.dispatchEvent(new CustomEvent('live-location-update-error', { detail: error.message }));
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 20000 }
    );
  }

  async function syncLiveLocationWatch() {
    if (!liveLocationUrl || !navigator.geolocation) return;
    try {
      const response = await fetch(liveLocationUrl, { headers: { 'Accept': 'application/json' } });
      if (!response.ok) return;
      const result = await response.json();
      const isSharing = (result.locations || []).some(function (location) {
        return Number(location.user_id) === liveLocationUserId;
      });
      if (isSharing) startLiveLocationWatch();
      else stopLiveLocationWatch();
    } catch (error) {
      document.dispatchEvent(new CustomEvent('live-location-update-error', { detail: error.message }));
    }
  }

  if (liveLocationUrl) {
    document.addEventListener('live-location-sharing-changed', syncLiveLocationWatch);
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) syncLiveLocationWatch();
    });
    window.setInterval(syncLiveLocationWatch, 15000);
    syncLiveLocationWatch();
  }

  // -------------------------------------------------------------
  // 1. Web Audio API Harmonic Chimes Synthesizer (Zero Dependencies)
  // -------------------------------------------------------------
  let audioCtx = null;
  let isSoundEnabled = localStorage.getItem('love_sound_enabled') !== 'false'; // Enabled by default

  const loveAudioToggleBtn = document.getElementById('loveAudioToggleBtn');
  const loveAudioIcon = document.getElementById('loveAudioIcon');

  function updateSoundIcon() {
    if (!loveAudioIcon) return;
    if (isSoundEnabled) {
      loveAudioIcon.className = 'bi bi-volume-up-fill text-rose';
      loveAudioToggleBtn.title = 'Sound Chimes: ON (Click to Mute)';
    } else {
      loveAudioIcon.className = 'bi bi-volume-mute-fill text-muted';
      loveAudioToggleBtn.title = 'Sound Chimes: OFF (Click to Unmute)';
    }
  }

  if (loveAudioToggleBtn) {
    updateSoundIcon();
    loveAudioToggleBtn.addEventListener('click', function () {
      isSoundEnabled = !isSoundEnabled;
      localStorage.setItem('love_sound_enabled', isSoundEnabled);
      updateSoundIcon();
      if (isSoundEnabled) playLoveChime([523.25, 659.25, 783.99]); // C5, E5, G5
    });
  }

  function getAudioContext() {
    if (!audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        audioCtx = new AudioContextClass();
      }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    return audioCtx;
  }

  function playLoveChime(freqs = [659.25, 830.61, 987.77, 1318.51]) {
    if (!isSoundEnabled) return;
    try {
      const ctx = getAudioContext();
      if (!ctx) return;

      freqs.forEach((freq, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, ctx.currentTime + idx * 0.08);

        gain.gain.setValueAtTime(0, ctx.currentTime + idx * 0.08);
        gain.gain.linearRampToValueAtTime(0.12, ctx.currentTime + idx * 0.08 + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + idx * 0.08 + 0.6);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(ctx.currentTime + idx * 0.08);
        osc.stop(ctx.currentTime + idx * 0.08 + 0.65);
      });
    } catch (e) {
      // Audio autoplay policy catch
    }
  }

  // -------------------------------------------------------------
  // 2. Optional Falling Rose Petals
  // -------------------------------------------------------------
  let petalsCanvas = document.getElementById('fallingPetalsCanvas');
  let isPetalsEnabled = localStorage.getItem('love_petals_enabled') === 'true';
  const petalsToggleBtn = document.getElementById('petalsToggleBtn');

  if (!petalsCanvas) {
    petalsCanvas = document.createElement('canvas');
    petalsCanvas.id = 'fallingPetalsCanvas';
    petalsCanvas.className = 'falling-petals-canvas';
    document.body.appendChild(petalsCanvas);
  }

  const pCtx = petalsCanvas.getContext('2d');
  let pWidth, pHeight;
  let petals = [];
  let petalAnimationFrame = null;

  function resizePetals() {
    pWidth = petalsCanvas.width = window.innerWidth;
    pHeight = petalsCanvas.height = window.innerHeight;
  }

  window.addEventListener('resize', resizePetals);
  resizePetals();

  class Petal {
    constructor() {
      this.reset(true);
    }

    reset(initial = false) {
      this.x = Math.random() * pWidth;
      this.y = initial ? Math.random() * pHeight : -20;
      this.size = Math.random() * 8 + 10;
      this.speedY = Math.random() * 0.9 + 0.6;
      this.speedX = Math.random() * 0.8 - 0.4;
      this.rotation = Math.random() * Math.PI * 2;
      this.rotSpeed = (Math.random() - 0.5) * 0.03;
      this.opacity = Math.random() * 0.5 + 0.35;
      this.oscillation = Math.random() * 100;
      this.color = Math.random() > 0.4 ? '#ff9dc5' : '#f43f5e';
    }

    update() {
      this.y += this.speedY;
      this.oscillation += 0.02;
      this.x += Math.sin(this.oscillation) * 0.7 + this.speedX;
      this.rotation += this.rotSpeed;

      if (this.y > pHeight + 30) {
        this.reset();
      }
    }

    draw() {
      pCtx.save();
      pCtx.globalAlpha = this.opacity;
      pCtx.translate(this.x, this.y);
      pCtx.rotate(this.rotation);

      // Draw elegant petal bezier shape
      pCtx.beginPath();
      pCtx.moveTo(0, 0);
      pCtx.bezierCurveTo(this.size / 2, -this.size / 2, this.size, 0, 0, this.size);
      pCtx.bezierCurveTo(-this.size, 0, -this.size / 2, -this.size / 2, 0, 0);
      pCtx.fillStyle = this.color;
      pCtx.fill();

      pCtx.restore();
    }
  }

  const petalCount = 22;
  for (let i = 0; i < petalCount; i++) {
    petals.push(new Petal());
  }

  function animatePetals() {
    if (!isPetalsEnabled) {
      petalAnimationFrame = null;
      pCtx.clearRect(0, 0, pWidth, pHeight);
      return;
    }

    pCtx.clearRect(0, 0, pWidth, pHeight);
    petals.forEach(function (petal) {
      petal.update();
      petal.draw();
    });
    petalAnimationFrame = requestAnimationFrame(animatePetals);
  }

  function updatePetalsControl() {
    if (!petalsToggleBtn) return;
    petalsToggleBtn.title = isPetalsEnabled ? 'Rose Petals: ON (Click to Hide)' : 'Rose Petals: OFF (Click to Show)';
    petalsToggleBtn.setAttribute('aria-pressed', String(isPetalsEnabled));
  }

  if (isPetalsEnabled) {
    petalAnimationFrame = requestAnimationFrame(animatePetals);
  } else {
    pCtx.clearRect(0, 0, pWidth, pHeight);
  }

  if (petalsToggleBtn) {
    updatePetalsControl();
    petalsToggleBtn.addEventListener('click', function () {
      isPetalsEnabled = !isPetalsEnabled;
      localStorage.setItem('love_petals_enabled', String(isPetalsEnabled));
      updatePetalsControl();
      if (isPetalsEnabled && petalAnimationFrame === null) {
        petalAnimationFrame = requestAnimationFrame(animatePetals);
      } else if (!isPetalsEnabled && petalAnimationFrame !== null) {
        cancelAnimationFrame(petalAnimationFrame);
        petalAnimationFrame = null;
        pCtx.clearRect(0, 0, pWidth, pHeight);
      }
      if (isPetalsEnabled) playLoveChime([783.99, 1046.50]); // G5, C6
    });
  }

  // -------------------------------------------------------------
  // 3. Live Love Milestone Relationship Clock
  // -------------------------------------------------------------
  const clockDays = document.getElementById('clockDays');
  const clockHours = document.getElementById('clockHours');
  const clockMins = document.getElementById('clockMins');
  const clockSecs = document.getElementById('clockSecs');

  if (clockDays && clockHours && clockMins && clockSecs) {
    // Relationship anniversary milestone anchor: February 8, 2026
    const loveStartDate = new Date('2026-02-08T00:00:00');

    function updateLoveClock() {
      const now = new Date();
      const diffMs = Math.max(0, now - loveStartDate);

      const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diffMs / (1000 * 60 * 60)) % 24);
      const mins = Math.floor((diffMs / (1000 * 60)) % 60);
      const secs = Math.floor((diffMs / 1000) % 60);

      clockDays.textContent = String(days).padStart(2, '0');
      clockHours.textContent = String(hours).padStart(2, '0');
      clockMins.textContent = String(mins).padStart(2, '0');
      clockSecs.textContent = String(secs).padStart(2, '0');
    }

    updateLoveClock();
    setInterval(updateLoveClock, 1000);
  }

  // -------------------------------------------------------------
  // 5. Daily Love Fortune / Secret Whispers Oracle
  // -------------------------------------------------------------
  const openFortuneBtn = document.getElementById('openFortuneBtn');
  const fortuneRevealBox = document.getElementById('fortuneRevealBox');
  const fortuneRevealedText = document.getElementById('fortuneRevealedText');
  const fortuneIcon = document.getElementById('fortuneIcon');

  const secretWhispers = [
    "Raj loves Ashmita's cute laugh more than anything in this universe! 💖",
    "Ashmita, you make every single ordinary day feel like Valentine's Day. ✨",
    "Secret Mission: Listen to 'Tum Se Hi' together tonight with eyes closed. 🎵",
    "A warm 10-second forehead hug is waiting for you next time you meet! 🫂",
    "In a sea of 8 billion people, my heart will always choose you. 🌹",
    "Two souls, one rhythm — Raj & Ashmita forever and always. 💍",
    "Every sweet memory with you is stamped permanently in our love diary. 📸",
    "You are the peace in my chaos and the smile to my mornings. 🥰",
    "Never forget how deeply and genuinely loved you are today. 💌",
    "Late-night food craving unlock: treat yourself and send a cute photo! 🍕"
  ];

  if (openFortuneBtn && fortuneRevealBox && fortuneRevealedText) {
    openFortuneBtn.addEventListener('click', function () {
      // 1. Play musical chime
      playLoveChime([523.25, 659.25, 783.99, 1046.50, 1318.51]);

      // 2. Confetti Explosion
      if (typeof confetti === 'function') {
        confetti({
          particleCount: 50,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#ff3366', '#f43f5e', '#be4bdb', '#ffb703', '#ffffff']
        });
      }

      // 3. Reveal Fortune
      const randomWhisper = secretWhispers[Math.floor(Math.random() * secretWhispers.length)];
      fortuneRevealedText.textContent = randomWhisper;
      fortuneRevealBox.classList.remove('d-none');

      if (fortuneIcon) {
        fortuneIcon.textContent = '💖';
        setTimeout(() => { fortuneIcon.textContent = '🎁'; }, 1500);
      }

      openFortuneBtn.innerHTML = '<i class="bi bi-arrow-repeat me-1"></i> Draw Another Whisper';
    });
  }

  // -------------------------------------------------------------
  // 6. 3D Tilt Card Physics Engine
  // -------------------------------------------------------------
  const tiltCards = document.querySelectorAll('.tilt-card, [data-tilt]');

  tiltCards.forEach(card => {
    card.addEventListener('mousemove', function (e) {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = ((y - centerY) / centerY) * -6; // max 6 deg
      const rotateY = ((x - centerX) / centerX) * 6;

      card.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.015, 1.015, 1.015)`;
    });

    card.addEventListener('mouseleave', function () {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
    });
  });

  // -------------------------------------------------------------
  // 7. Toast Auto-Dismissal
  // -------------------------------------------------------------
  const toasts = document.querySelectorAll('.toast');
  toasts.forEach(toastEl => {
    setTimeout(() => {
      toastEl.classList.remove('show');
    }, 4500);
  });

  // -------------------------------------------------------------
  // 8. Romantic Typewriter Effect (Landing Page)
  // -------------------------------------------------------------
  const typewriterEl = document.getElementById('typewriterText');
  if (typewriterEl) {
    const quotes = [
      "Two hearts. One endless love story.",
      "Every love story is beautiful, but ours is my favorite.",
      "Raj ❤️ Ashmita — Bound by love, sealed with forever.",
      "In a sea of people, my eyes will always search for you.",
      "A private haven for our sweetest memories and dreams."
    ];

    let quoteIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let typingSpeed = 65;

    function typeLoop() {
      const currentQuote = quotes[quoteIndex];

      if (isDeleting) {
        typewriterEl.textContent = currentQuote.substring(0, charIndex - 1);
        charIndex--;
        typingSpeed = 35;
      } else {
        typewriterEl.textContent = currentQuote.substring(0, charIndex + 1);
        charIndex++;
        typingSpeed = 65;
      }

      if (!isDeleting && charIndex === currentQuote.length) {
        typingSpeed = 2400;
        isDeleting = true;
      } else if (isDeleting && charIndex === 0) {
        isDeleting = false;
        quoteIndex = (quoteIndex + 1) % quotes.length;
        typingSpeed = 400;
      }

      setTimeout(typeLoop, typingSpeed);
    }

    setTimeout(typeLoop, 500);
  }

  // -------------------------------------------------------------
  // 9. Interactive Surprise Love Notes Generator (Landing Page)
  // -------------------------------------------------------------
  const loveQuotes = [
    "\"In a sea of people, my eyes will always search for you.\"",
    "\"Every moment spent with you is like a beautiful dream come true.\"",
    "\"You are my today, my tomorrow, and all of my forevers.\"",
    "\"Raj loves Ashmita more than all the stars in the night sky. ❤️\"",
    "\"I didn't choose you, my heart did.\"",
    "\"With you, every simple moment feels like a fairytale.\"",
    "\"Thank you for making my life full of smiles, warmth, and magic.\"",
    "\"No matter where life takes us, my home is always with you.\"",
    "\"Loving you is the easiest, sweetest thing I have ever done.\"",
    "\"You are the melody to my silence and the sunshine to my rain.\""
  ];

  const loveQuoteBtn = document.getElementById('nextLoveQuoteBtn');
  const loveQuoteText = document.getElementById('loveQuoteText');
  if (loveQuoteBtn && loveQuoteText) {
    let currentQuoteIdx = 0;
    loveQuoteBtn.addEventListener('click', function () {
      playLoveChime([783.99, 987.77, 1318.51]);

      loveQuoteText.style.opacity = '0';
      loveQuoteText.style.transform = 'translateY(-6px)';

      setTimeout(function () {
        let nextIdx;
        do {
          nextIdx = Math.floor(Math.random() * loveQuotes.length);
        } while (nextIdx === currentQuoteIdx && loveQuotes.length > 1);
        currentQuoteIdx = nextIdx;

        loveQuoteText.textContent = loveQuotes[currentQuoteIdx];
        loveQuoteText.style.opacity = '1';
        loveQuoteText.style.transform = 'translateY(0)';
      }, 220);
    });
  }

  // -------------------------------------------------------------
  // 10. Floating Particles Canvas (Landing Page)
  // -------------------------------------------------------------
  const canvas = document.getElementById('loveParticlesCanvas');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    let width, height;
    let particles = [];
    const symbols = ['❤️', '💖', '✨', '💕', '🌸', '💫'];

    function resize() {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    }

    window.addEventListener('resize', resize);
    resize();

    class LoveParticle {
      constructor(x, y) {
        this.reset(x, y);
      }

      reset(x, y) {
        this.x = x !== undefined ? x : Math.random() * width;
        this.y = y !== undefined ? y : height + Math.random() * 30;
        this.symbol = symbols[Math.floor(Math.random() * symbols.length)];
        this.size = Math.random() * 14 + 12;
        this.speedY = Math.random() * 0.7 + 0.35;
        this.speedX = (Math.random() - 0.5) * 0.5;
        this.opacity = Math.random() * 0.5 + 0.25;
        this.rotation = Math.random() * Math.PI * 2;
        this.rotSpeed = (Math.random() - 0.5) * 0.02;
        this.oscillation = Math.random() * 100;
      }

      update() {
        this.y -= this.speedY;
        this.oscillation += 0.02;
        this.x += Math.sin(this.oscillation) * 0.4 + this.speedX;
        this.rotation += this.rotSpeed;

        if (this.y < -40) {
          this.reset();
        }
      }

      draw() {
        ctx.save();
        ctx.globalAlpha = this.opacity;
        ctx.font = `${this.size}px serif`;
        ctx.translate(this.x, this.y);
        ctx.rotate(this.rotation);
        ctx.fillText(this.symbol, 0, 0);
        ctx.restore();
      }
    }

    const count = Math.min(28, Math.floor(window.innerWidth / 45));
    for (let i = 0; i < count; i++) {
      particles.push(new LoveParticle(Math.random() * width, Math.random() * height));
    }

    function renderParticles() {
      ctx.clearRect(0, 0, width, height);
      particles.forEach(p => {
        p.update();
        p.draw();
      });
      requestAnimationFrame(renderParticles);
    }

    renderParticles();
  }

  // -------------------------------------------------------------
  // 11. Gallery Dropzone & Instant Image Preview
  // -------------------------------------------------------------
  const photoInput = document.getElementById('photoInput');
  const dropzonePrompt = document.getElementById('dropzonePrompt');
  const dropzonePreview = document.getElementById('dropzonePreview');
  const previewImg = document.getElementById('previewImg');
  const removePreviewBtn = document.getElementById('removePreviewBtn');
  const photoCaption = document.getElementById('photoCaption');
  const captionCounter = document.getElementById('captionCounter');

  if (photoInput && previewImg) {
    photoInput.addEventListener('change', function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          previewImg.src = e.target.result;
          dropzonePrompt.classList.add('d-none');
          dropzonePreview.classList.remove('d-none');
          playLoveChime([523.25, 659.25]);
        };
        reader.readAsDataURL(file);
      }
    });

    if (removePreviewBtn) {
      removePreviewBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        photoInput.value = '';
        previewImg.src = '';
        dropzonePreview.classList.add('d-none');
        dropzonePrompt.classList.remove('d-none');
      });
    }

    if (photoCaption && captionCounter) {
      photoCaption.addEventListener('input', function () {
        captionCounter.textContent = `${this.value.length} / 200`;
      });
    }
  }

  // -------------------------------------------------------------
  // 12. Messages Quick Emoji Inserter & Character Counter
  // -------------------------------------------------------------
  const messageInput = document.getElementById('messageInput');
  const charCounter = document.getElementById('charCounter');
  const emojiBtns = document.querySelectorAll('.emoji-btn');

  if (messageInput) {
    if (charCounter) {
      messageInput.addEventListener('input', function () {
        charCounter.textContent = `${this.value.length} / 500`;
      });
    }

    emojiBtns.forEach(btn => {
      btn.addEventListener('click', function () {
        const emoji = this.getAttribute('data-emoji');
        const start = messageInput.selectionStart;
        const end = messageInput.selectionEnd;
        const text = messageInput.value;
        messageInput.value = text.substring(0, start) + emoji + text.substring(end);
        messageInput.focus();
        messageInput.selectionStart = messageInput.selectionEnd = start + emoji.length;
        if (charCounter) {
          charCounter.textContent = `${messageInput.value.length} / 500`;
        }
        playLoveChime([659.25, 880]);
      });
    });
  }

  // -------------------------------------------------------------
  // 13. Music Page Preset Song Chips Auto-Fill
  // -------------------------------------------------------------
  const songChips = document.querySelectorAll('.song-chip-btn');
  const songTitleInput = document.getElementById('songTitleInput');
  const youtubeUrlInput = document.getElementById('youtubeUrlInput');
  if (songChips.length > 0 && songTitleInput) {
    songChips.forEach(chip => {
      chip.addEventListener('click', function () {
        songTitleInput.value = this.getAttribute('data-song');
        if (youtubeUrlInput) youtubeUrlInput.value = this.dataset.youtubeUrl || '';
        songTitleInput.focus();
        playLoveChime([587.33, 880]);
      });
    });
  }

  // -------------------------------------------------------------
  // 14. Homepage In-Page Song Player
  // -------------------------------------------------------------
  const homeSongToggle = document.getElementById('homeSongToggle');
  const homeSongStatus = document.getElementById('homeSongStatus');
  const homeSongPlayerHost = document.getElementById('homeSongPlayer');

  if (homeSongToggle && homeSongStatus && homeSongPlayerHost) {
    const songId = 'mt9xg0mmt28';
    let playerFrame = null;
    let isPlaying = false;

    function updateHomeSongState(playing) {
      isPlaying = playing;
      homeSongToggle.classList.toggle('is-playing', playing);
      homeSongToggle.setAttribute('aria-pressed', String(playing));
      homeSongToggle.setAttribute('aria-label', playing ? 'Pause Tum Se Hi' : 'Play Tum Se Hi on this page');
      homeSongStatus.textContent = playing ? 'Playing here · Tap to pause' : 'Paused · Tap to listen here';
    }

    homeSongToggle.addEventListener('click', function () {
      if (!playerFrame) {
        playerFrame = document.createElement('iframe');
        playerFrame.title = 'Tum Se Hi audio player';
        playerFrame.width = '200';
        playerFrame.height = '200';
        playerFrame.allow = 'autoplay; encrypted-media; picture-in-picture';
        playerFrame.referrerPolicy = 'strict-origin-when-cross-origin';
        playerFrame.src = `https://www.youtube.com/embed/${songId}?autoplay=1&controls=0&enablejsapi=1&loop=1&playlist=${songId}&playsinline=1&origin=${encodeURIComponent(window.location.origin)}`;
        homeSongPlayerHost.replaceChildren(playerFrame);
        updateHomeSongState(true);
        return;
      }

      const command = isPlaying ? 'pauseVideo' : 'playVideo';
      playerFrame.contentWindow.postMessage(
        JSON.stringify({ event: 'command', func: command, args: [] }),
        'https://www.youtube.com'
      );
      updateHomeSongState(!isPlaying);
    });
  }

  // -------------------------------------------------------------
  // 15. Food Page Vibe Tag Auto-Fill
  // -------------------------------------------------------------
  const foodTags = document.querySelectorAll('.food-tag-btn');
  const foodNoteInput = document.getElementById('foodNoteInput');
  if (foodTags.length > 0 && foodNoteInput) {
    foodTags.forEach(tag => {
      tag.addEventListener('click', function () {
        foodNoteInput.value = this.getAttribute('data-note');
        foodNoteInput.focus();
        playLoveChime([659.25, 783.99]);
      });
    });
  }

  // -------------------------------------------------------------
  // 15. Login Page Password Toggle
  // -------------------------------------------------------------
  const passwordInput = document.getElementById('password');
  const togglePasswordBtn = document.getElementById('togglePasswordBtn');
  const togglePasswordIcon = document.getElementById('togglePasswordIcon');

  if (togglePasswordBtn && passwordInput && togglePasswordIcon) {
    togglePasswordBtn.addEventListener('click', function () {
      if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        togglePasswordIcon.classList.replace('bi-eye', 'bi-eye-slash');
      } else {
        passwordInput.type = 'password';
        togglePasswordIcon.classList.replace('bi-eye-slash', 'bi-eye');
      }
    });
  }

});
