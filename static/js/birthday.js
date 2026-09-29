/**
 * Birthday Celebration & Romantic Hindi Music Player
 * Specially created for Raj & Ashmita
 */

(function () {
  let ytPlayer = null;
  let isPlaying = false;
  let isMuted = false;
  let currentSongIndex = 0;
  let songsList = [];

  // Fetch playlist from server or fallback to default
  const defaultPlaylist = [
    { id: "LUgpPmj6nR8", title: "Khat", movie: "Single", artist: "Navjot Ahuja" },
    { id: "mt9xg0mmt28", title: "Tum Se Hi", movie: "Jab We Met", artist: "Mohit Chauhan" },
    { id: "BddP6PYo2gs", title: "Kesariya", movie: "Brahmāstra", artist: "Arijit Singh" },
    { id: "gvyUuxdRdR4", title: "Raataan Lambiyan", movie: "Shershaah", artist: "Jubin Nautiyal & Asees Kaur" },
    { id: "ElZfdU54Cp8", title: "Apna Bana Le", movie: "Bhediya", artist: "Arijit Singh" },
    { id: "pElk1ShPrcE", title: "Pehla Nasha", movie: "Jo Jeeta Wohi Sikandar", artist: "Udit Narayan & Sadhana Sargam" },
    { id: "3X81L48qYv0", title: "Tera Ban Jaunga", movie: "Kabir Singh", artist: "Akhil Sachdeva & Tulsi Kumar" },
    { id: "Z9AZkZ5Zq2U", title: "Janam Janam", movie: "Dilwale", artist: "Arijit Singh & Antara Mitra" },
    { id: "cYOB941gyXI", title: "Hawayein", movie: "Jab Harry Met Sejal", artist: "Arijit Singh" },
    { id: "IJq0cmW6DVo", title: "Tum Hi Ho", movie: "Aashiqui 2", artist: "Arijit Singh" },
    { id: "2mxeYgJ_u4E", title: "Subhanallah", movie: "Yeh Jawaani Hai Deewani", artist: "Sreerama Chandra" }
  ];

  songsList = defaultPlaylist;
  currentSongIndex = 0;

  // 1. Confetti Effects
  function fireConfettiBurst() {
    if (typeof confetti !== "function") return;

    // Center burst
    confetti({
      particleCount: 70,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#ff4081', '#f50057', '#ffd700', '#ba68c8', '#ffffff']
    });

    // Left and right cannons
    setTimeout(function () {
      confetti({
        particleCount: 50,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors: ['#f05ca7', '#ffd8e3', '#ffc107', '#442a6e']
      });
      confetti({
        particleCount: 50,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors: ['#f05ca7', '#ffd8e3', '#ffc107', '#442a6e']
      });
    }, 250);
  }

  function fireHeartConfetti() {
    if (typeof confetti !== "function") return;
    confetti({
      particleCount: 40,
      spread: 60,
      shapes: ['circle', 'square'],
      colors: ['#e91e63', '#9c27b0', '#ffeb3b', '#00e676']
    });
  }

  // 2. Load YouTube Iframe API
  function loadYouTubeApi() {
    if (window.YT && window.YT.Player) {
      initPlayer();
      return;
    }
    const tag = document.createElement('script');
    tag.src = "https://www.youtube.com/iframe_api";
    const firstScriptTag = document.getElementsByTagName('script')[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
  }

  window.onYouTubeIframeAPIReady = function () {
    initPlayer();
  };

  function initPlayer() {
    const curSong = songsList[currentSongIndex];
    updateSongInfoUI(curSong);

    ytPlayer = new YT.Player('ytBirthdayAudioPlayer', {
      height: '100',
      width: '100',
      videoId: curSong.id,
      playerVars: {
        autoplay: 0,
        controls: 0,
        loop: 0,
        modestbranding: 1,
        rel: 0,
        playsinline: 1
      },
      events: {
        'onReady': onPlayerReady,
        'onStateChange': onPlayerStateChange,
        'onError': onPlayerError
      }
    });
  }

  function onPlayerReady(event) {
    // Player is ready
    updateSoundWave(false);
  }

  function onPlayerStateChange(event) {
    if (event.data === YT.PlayerState.PLAYING) {
      isPlaying = true;
      updatePlayPauseButtonUI(true);
      updateSoundWave(true);
    } else if (event.data === YT.PlayerState.PAUSED) {
      isPlaying = false;
      updatePlayPauseButtonUI(false);
      updateSoundWave(false);
    } else if (event.data === YT.PlayerState.ENDED) {
      // Song ended: automatically play another random romantic Hindi song!
      playRandomSong();
    }
  }

  function onPlayerError(event) {
    console.warn("YouTube player error, trying next random song...", event.data);
    setTimeout(playRandomSong, 1200);
  }

  function playSongAtIndex(index) {
    currentSongIndex = index;
    const song = songsList[currentSongIndex];
    updateSongInfoUI(song);

    if (ytPlayer && ytPlayer.loadVideoById) {
      ytPlayer.loadVideoById(song.id);
      ytPlayer.playVideo();
      isPlaying = true;
      updatePlayPauseButtonUI(true);
      updateSoundWave(true);
    }
  }

  function playRandomSong() {
    if (songsList.length <= 1) return;
    let nextIndex;
    do {
      nextIndex = Math.floor(Math.random() * songsList.length);
    } while (nextIndex === currentSongIndex);

    playSongAtIndex(nextIndex);
    fireHeartConfetti();
  }

  function togglePlayPause() {
    if (!ytPlayer || !ytPlayer.playVideo) {
      // Fallback: reload API
      loadYouTubeApi();
      return;
    }

    if (isPlaying) {
      ytPlayer.pauseVideo();
    } else {
      ytPlayer.playVideo();
      fireHeartConfetti();
    }
  }

  function toggleMute() {
    if (!ytPlayer || !ytPlayer.isMuted) return;
    const muteIcon = document.getElementById('muteIcon');
    if (ytPlayer.isMuted()) {
      ytPlayer.unMute();
      isMuted = false;
      if (muteIcon) muteIcon.className = "bi bi-volume-up";
    } else {
      ytPlayer.mute();
      isMuted = true;
      if (muteIcon) muteIcon.className = "bi bi-volume-mute";
    }
  }

  function updateSongInfoUI(song) {
    const titleEl = document.getElementById('bdayPlayerSongTitle');
    const artistEl = document.getElementById('bdayPlayerArtist');
    if (titleEl) titleEl.textContent = song.title;
    if (artistEl) artistEl.textContent = song.movie + " • " + song.artist;
  }

  function updatePlayPauseButtonUI(playing) {
    const icon = document.getElementById('playPauseIcon');
    const btnMusicText = document.getElementById('bdayBtnMusicText');
    const disc = document.getElementById('musicDiscIcon');

    if (icon) {
      icon.className = playing ? "bi bi-pause-fill" : "bi bi-play-fill";
    }
    if (btnMusicText) {
      btnMusicText.textContent = playing ? "Playing ♪" : "Play Songs";
    }
    if (disc) {
      if (playing) {
        disc.classList.add('rotating');
      } else {
        disc.classList.remove('rotating');
      }
    }
  }

  function updateSoundWave(playing) {
    const soundWave = document.getElementById('soundWaveBar');
    if (soundWave) {
      if (playing) {
        soundWave.classList.add('active');
      } else {
        soundWave.classList.remove('active');
      }
    }
  }

  // 3. UI Interactions & DOM Setup
  document.addEventListener('DOMContentLoaded', function () {
    // Initial celebration burst
    setTimeout(fireConfettiBurst, 500);

    // Occasional gentle confetti every 35s
    setInterval(function () {
      if (document.visibilityState === 'visible') {
        confetti({
          particleCount: 15,
          spread: 45,
          origin: { y: 0.2 },
          colors: ['#ff4081', '#ffd700', '#f05ca7']
        });
      }
    }, 35000);

    // Show Wish Modal automatically once per browser session
    const modalEl = document.getElementById('birthdayWishModal');
    if (modalEl && typeof bootstrap !== "undefined" && !sessionStorage.getItem('bday_modal_seen')) {
      setTimeout(function () {
        const modalInstance = new bootstrap.Modal(modalEl);
        modalInstance.show();
        sessionStorage.setItem('bday_modal_seen', 'true');
        fireConfettiBurst();
      }, 700);
    }

    // Top Bar Play Music button
    const topBarMusicBtn = document.getElementById('bdayPlayMusicBtn');
    if (topBarMusicBtn) {
      topBarMusicBtn.addEventListener('click', function () {
        togglePlayPause();
      });
    }

    // Top Bar Confetti button
    const confettiBtn = document.getElementById('bdayConfettiBurstBtn');
    if (confettiBtn) {
      confettiBtn.addEventListener('click', function () {
        fireConfettiBurst();
      });
    }

    // Modal Play Romantic Music button
    const modalPlayBtn = document.getElementById('modalPlayRomanticBtn');
    if (modalPlayBtn) {
      modalPlayBtn.addEventListener('click', function () {
        if (typeof bootstrap !== "undefined" && modalEl) {
          const inst = bootstrap.Modal.getInstance(modalEl);
          if (inst) inst.hide();
        }
        if (ytPlayer && ytPlayer.playVideo) {
          ytPlayer.playVideo();
        } else {
          togglePlayPause();
        }
        fireConfettiBurst();
      });
    }

    // Floating Player Controls
    const playPauseBtn = document.getElementById('bdayPlayPauseBtn');
    if (playPauseBtn) {
      playPauseBtn.addEventListener('click', togglePlayPause);
    }

    const randomSongBtn = document.getElementById('bdayPrevOrRandomBtn');
    if (randomSongBtn) {
      randomSongBtn.addEventListener('click', playRandomSong);
    }

    const muteBtn = document.getElementById('bdayMuteToggleBtn');
    if (muteBtn) {
      muteBtn.addEventListener('click', toggleMute);
    }

    // Minimize / Expand Floating Player
    const toggleSizeBtn = document.getElementById('togglePlayerSizeBtn');
    const playerWidget = document.getElementById('floatingBirthdayMusicPlayer');
    const toggleIcon = document.getElementById('togglePlayerIcon');
    if (toggleSizeBtn && playerWidget) {
      toggleSizeBtn.addEventListener('click', function () {
        playerWidget.classList.toggle('minimized');
        if (playerWidget.classList.contains('minimized')) {
          toggleIcon.className = "bi bi-chevron-up";
        } else {
          toggleIcon.className = "bi bi-chevron-down";
        }
      });
    }

    // Load YouTube API
    loadYouTubeApi();
  });
})();
