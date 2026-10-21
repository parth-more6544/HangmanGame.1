/**
 * script.js - Hangman: The Neon Arcade
 * Full-stack Client Controller & Web Audio Chiptune Synthesizer
 */

(function () {
  'use strict';

  // ==================== AUDIO SYNTHESIZER (WEB AUDIO API) ====================
  class ArcadeAudioEngine {
    constructor() {
      this.ctx = null;
      this.soundEnabled = true;
      this.ambienceEnabled = false;
      this.ambientNode = null;
      this.ambientGain = null;
    }

    initContext() {
      if (!this.ctx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) {
          this.ctx = new AudioCtx();
        }
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume();
      }
    }

    playTone(freq, type = 'square', duration = 0.12, gainLevel = 0.15) {
      if (!this.soundEnabled) return;
      this.initContext();
      if (!this.ctx) return;

      try {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = type;
        osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

        gain.gain.setValueAtTime(gainLevel, this.ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start();
        osc.stop(this.ctx.currentTime + duration);
      } catch (e) {
        console.warn('Audio playTone error', e);
      }
    }

    playCoinSound() {
      if (!this.soundEnabled) return;
      this.initContext();
      if (!this.ctx) return;

      const now = this.ctx.currentTime;
      const osc1 = this.ctx.createOscillator();
      const osc2 = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc1.type = 'sine';
      osc2.type = 'triangle';
      osc1.frequency.setValueAtTime(987.77, now); // B5
      osc1.frequency.setValueAtTime(1318.51, now + 0.08); // E6
      osc2.frequency.setValueAtTime(1318.51, now);
      osc2.frequency.setValueAtTime(1975.53, now + 0.08); // B6

      gain.gain.setValueAtTime(0.2, now);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(this.ctx.destination);

      osc1.start(now);
      osc2.start(now);
      osc1.stop(now + 0.35);
      osc2.stop(now + 0.35);
    }

    playButtonSound() {
      this.playTone(240, 'triangle', 0.06, 0.12);
    }

    playCorrectSound() {
      if (!this.soundEnabled) return;
      this.initContext();
      if (!this.ctx) return;

      const notes = [659.25, 830.61, 987.77, 1318.51]; // E5, G#5, B5, E6
      notes.forEach((freq, i) => {
        setTimeout(() => {
          this.playTone(freq, 'sine', 0.12, 0.15);
        }, i * 65);
      });
    }

    playWrongSound() {
      if (!this.soundEnabled) return;
      this.initContext();
      if (!this.ctx) return;

      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(180, now);
      osc.frequency.exponentialRampToValueAtTime(65, now + 0.22);

      gain.gain.setValueAtTime(0.25, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + 0.25);
    }

    playHintSound() {
      if (!this.soundEnabled) return;
      this.initContext();
      if (!this.ctx) return;

      const freqs = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
      freqs.forEach((freq, idx) => {
        setTimeout(() => {
          this.playTone(freq, 'triangle', 0.15, 0.14);
        }, idx * 70);
      });
    }

    playWinSound() {
      if (!this.soundEnabled) return;
      this.initContext();
      if (!this.ctx) return;

      const melody = [
        { f: 523.25, d: 0.12 }, // C5
        { f: 659.25, d: 0.12 }, // E5
        { f: 783.99, d: 0.12 }, // G5
        { f: 1046.50, d: 0.28 }, // C6
        { f: 880.00, d: 0.14 }, // A5
        { f: 1046.50, d: 0.45 }  // C6
      ];

      let elapsed = 0;
      melody.forEach(n => {
        setTimeout(() => {
          this.playTone(n.f, 'square', n.d, 0.18);
        }, elapsed * 1000);
        elapsed += n.d + 0.03;
      });
    }

    playGameOverSound() {
      if (!this.soundEnabled) return;
      this.initContext();
      if (!this.ctx) return;

      const notes = [
        { f: 392.00, d: 0.18 }, // G4
        { f: 349.23, d: 0.18 }, // F4
        { f: 311.13, d: 0.22 }, // Eb4
        { f: 261.63, d: 0.45 }  // C4
      ];

      let elapsed = 0;
      notes.forEach(n => {
        setTimeout(() => {
          this.playTone(n.f, 'sawtooth', n.d, 0.2);
        }, elapsed * 1000);
        elapsed += n.d + 0.04;
      });
    }

    toggleAmbience(enable) {
      this.ambienceEnabled = enable;
      if (!enable) {
        if (this.ambientNode) {
          try {
            this.ambientNode.stop();
            this.ambientNode.disconnect();
          } catch (e) {}
          this.ambientNode = null;
        }
        return;
      }

      this.initContext();
      if (!this.ctx) return;

      try {
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(60, this.ctx.currentTime); // 60Hz cathode hum

        gain.gain.setValueAtTime(0.015, this.ctx.currentTime);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start();
        this.ambientNode = osc;
        this.ambientGain = gain;
      } catch (e) {
        console.warn('Ambience error', e);
      }
    }
  }

  // ==================== GLOBAL APP STATE ====================
  const audio = new ArcadeAudioEngine();

  const state = {
    activeGameId: null,
    gameStatus: 'idle', // 'idle', 'in_progress', 'won', 'lost'
    category: 'Technology',
    difficulty: 'medium',
    mode: 'single', // 'single', 'daily', 'twoplayer'
    score: 0,
    lives: 6,
    maxLives: 6,
    timerSeconds: 0,
    timerInterval: null,
    categoriesList: [],
    difficultiesList: [],
    dailyDate: '',
    hasPlayedDaily: false
  };

  // ==================== DOM ELEMENTS CACHE ====================
  const views = {
    home: document.getElementById('view-home'),
    setup: document.getElementById('view-setup'),
    game: document.getElementById('view-game')
  };

  const modals = {
    victory: document.getElementById('victory-modal'),
    gameover: document.getElementById('gameover-modal'),
    daily: document.getElementById('daily-modal'),
    twoplayer: document.getElementById('two-player-modal'),
    stats: document.getElementById('stats-modal'),
    rules: document.getElementById('rules-modal'),
    settings: document.getElementById('settings-modal')
  };

  const hud = {
    score: document.getElementById('hud-score'),
    livesText: document.getElementById('hud-lives-text'),
    livesTokens: document.querySelectorAll('.life-token'),
    timer: document.getElementById('hud-timer'),
    difficulty: document.getElementById('hud-difficulty'),
    mode: document.getElementById('hud-mode')
  };

  const gameBoard = {
    categoryName: document.getElementById('game-category-name'),
    wordLength: document.getElementById('game-word-length'),
    messageText: document.getElementById('game-message-text'),
    missionClueText: document.getElementById('mission-clue-text'),
    tilesDisplay: document.getElementById('word-tiles-display'),
    btnHintLetter: document.getElementById('btn-hint-letter'),
    btnHintEliminate: document.getElementById('btn-hint-eliminate'),
    btnForfeit: document.getElementById('btn-forfeit'),
    keyboard: document.getElementById('arcade-keyboard'),
    stageCaption: document.getElementById('stage-warning-text')
  };

  const screenPulse = document.getElementById('screen-pulse');

  // ==================== INITIALIZATION ====================
  async function initApp() {
    loadPreferences();
    setupEventListeners();
    await fetchConfiguration();
  }

  // Load local user preferences
  function loadPreferences() {
    const soundPref = localStorage.getItem('arcade_sound');
    if (soundPref !== null) {
      audio.soundEnabled = soundPref === 'true';
      const soundSwitch = document.getElementById('setting-sound');
      if (soundSwitch) soundSwitch.checked = audio.soundEnabled;
      updateSoundIcon();
    }

    const ambiencePref = localStorage.getItem('arcade_ambience');
    if (ambiencePref === 'true') {
      const ambSwitch = document.getElementById('setting-ambience');
      if (ambSwitch) ambSwitch.checked = true;
      audio.toggleAmbience(true);
    }

    const glowPref = localStorage.getItem('arcade_glow') || 'normal';
    document.body.classList.toggle('reduced-glow', glowPref === 'reduced');
    const glowSelect = document.getElementById('setting-glow');
    if (glowSelect) glowSelect.value = glowPref;

    const motionPref = localStorage.getItem('arcade_motion') || 'normal';
    document.body.classList.toggle('reduced-motion', motionPref === 'reduced');
    const motionSelect = document.getElementById('setting-motion');
    if (motionSelect) motionSelect.value = motionPref;

    const themePref = localStorage.getItem('arcade_theme') || 'neon';
    document.body.classList.toggle('contrast-theme', themePref === 'contrast');
    const themeSelect = document.getElementById('setting-theme');
    if (themeSelect) themeSelect.value = themePref;
  }

  function updateSoundIcon() {
    const iconSpan = document.getElementById('sound-icon');
    if (!iconSpan) return;
    if (audio.soundEnabled) {
      iconSpan.innerHTML = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>`;
      document.getElementById('sound-toggle-btn').title = 'Sound Effects: ON';
    } else {
      iconSpan.innerHTML = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>`;
      document.getElementById('sound-toggle-btn').title = 'Sound Effects: MUTED';
    }
  }

  // Fetch initial game settings & categories
  async function fetchConfiguration() {
    try {
      const res = await fetch('/api/config');
      const data = await res.json();
      if (data.success) {
        state.categoriesList = data.categories;
        state.difficultiesList = data.difficulties;
        state.dailyDate = data.daily_date;
        state.hasPlayedDaily = data.has_played_daily;

        updateDailyModalStatus();
      }
    } catch (e) {
      console.warn('Config fetch error', e);
    }
  }

  function updateDailyModalStatus() {
    const dateLabel = document.getElementById('daily-date-label');
    if (dateLabel) {
      dateLabel.textContent = `DATE: ${state.dailyDate} (ASIA/KOLKATA BOUNDARY)`;
    }

    const banner = document.getElementById('daily-status-banner');
    const startBtn = document.getElementById('btn-start-daily');
    if (!banner || !startBtn) return;

    if (state.hasPlayedDaily) {
      banner.className = 'daily-status-box completed';
      banner.innerHTML = `<strong>★ DAILY CHALLENGE COMPLETED</strong><br>You have already submitted today's score! Reset occurs at midnight IST.`;
      startBtn.disabled = true;
      startBtn.classList.add('disabled');
      startBtn.querySelector('span').textContent = 'COMPLETED FOR TODAY';
    } else {
      banner.className = 'daily-status-box ready';
      banner.innerHTML = `<strong>READY FOR TODAY'S RUN</strong><br>One official attempt. Words are standardized across all arcade machines worldwide today.`;
      startBtn.disabled = false;
      startBtn.classList.remove('disabled');
      startBtn.querySelector('span').textContent = "PLAY TODAY'S CHALLENGE";
    }
  }

  // ==================== VIEW ROUTING & MODAL CONTROLLERS ====================
  function switchView(viewName) {
    audio.playButtonSound();
    Object.keys(views).forEach(v => {
      if (views[v]) views[v].classList.remove('active');
    });

    if (views[viewName]) {
      views[viewName].classList.add('active');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Update Nav buttons
    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === viewName);
    });

    // Close mobile drawer if open
    const drawer = document.getElementById('mobile-drawer');
    if (drawer) drawer.classList.remove('open');
  }

  function openModal(modalId) {
    audio.playButtonSound();
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('open');
      if (modalId === 'stats-modal') {
        loadPlayerStats();
      } else if (modalId === 'daily-modal') {
        fetchConfiguration();
      }
    }
  }

  function closeModal(modalElement) {
    audio.playButtonSound();
    if (modalElement) {
      modalElement.classList.remove('open');
    } else {
      document.querySelectorAll('.arcade-modal').forEach(m => m.classList.remove('open'));
    }
  }

  // ==================== GAMEPLAY LIFECYCLE ====================
  async function startNewGame(options = {}) {
    audio.playButtonSound();
    stopTimer();

    // Prepare payload
    const payload = {
      mode: options.mode || state.mode || 'single',
      category: options.category || state.category,
      difficulty: options.difficulty || state.difficulty,
      custom_word: options.custom_word || null,
      custom_clue: options.custom_clue || null
    };

    try {
      const res = await fetch('/api/game/new', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!data.success) {
        alert(data.error || 'Failed to initialize game round.');
        return;
      }

      const gameState = data.game_state;
      state.activeGameId = gameState.game_id;
      state.gameStatus = gameState.status;
      state.mode = gameState.mode;
      state.category = gameState.category;
      state.difficulty = gameState.difficulty;
      state.score = gameState.score;
      state.lives = gameState.remaining_lives;
      state.maxLives = gameState.max_lives;

      // Render board
      renderFullGameState(gameState);
      resetKeyboard();
      resetHangmanSVG();
      startTimer();

      // Close open modals and switch to game view
      closeModal();
      switchView('game');
      triggerScreenPulse('green');
      audio.playCoinSound();

    } catch (e) {
      console.error('Error starting game:', e);
      alert('Could not connect to game backend.');
    }
  }

  async function submitGuess(letter) {
    if (state.gameStatus !== 'in_progress' || !state.activeGameId) return;

    audio.playButtonSound();
    const char = letter.toUpperCase();

    // Disable key visually
    const keyBtn = document.querySelector(`.key-btn[data-key="${char}"]`);
    if (keyBtn && (keyBtn.classList.contains('correct') || keyBtn.classList.contains('wrong'))) {
      return; // already guessed
    }

    try {
      const res = await fetch('/api/game/guess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_id: state.activeGameId,
          letter: char
        })
      });
      const data = await res.json();

      if (!data.success) {
        gameBoard.messageText.textContent = data.error || 'Guess rejected.';
        return;
      }

      const result = data.result;
      const gameState = data.game_state;

      // Update Key State
      if (keyBtn) {
        keyBtn.disabled = true;
        if (result.is_correct) {
          keyBtn.classList.add('correct');
        } else {
          keyBtn.classList.add('wrong');
        }
      }

      // Play Sound & Screen Effects
      if (result.is_correct) {
        audio.playCorrectSound();
        triggerScreenPulse('green');
      } else if (!result.is_duplicate) {
        audio.playWrongSound();
        triggerScreenPulse('red');
      }

      // Update Board State
      renderFullGameState(gameState);

      // Check Outcome
      if (gameState.status === 'won') {
        handleVictory(gameState);
      } else if (gameState.status === 'lost') {
        handleGameOver(gameState);
      }

    } catch (e) {
      console.error('Error submitting guess:', e);
    }
  }

  async function requestHint(hintType) {
    if (state.gameStatus !== 'in_progress' || !state.activeGameId) return;

    try {
      const res = await fetch('/api/game/hint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          game_id: state.activeGameId,
          hint_type: hintType
        })
      });
      const data = await res.json();

      if (!data.success) {
        alert(data.error || 'Hint unavailable.');
        return;
      }

      audio.playHintSound();
      const gameState = data.game_state;
      renderFullGameState(gameState);

      if (hintType === 2 && data.hint.revealed_letter) {
        const char = data.hint.revealed_letter;
        const keyBtn = document.querySelector(`.key-btn[data-key="${char}"]`);
        if (keyBtn) {
          keyBtn.disabled = true;
          keyBtn.classList.add('correct');
        }
        gameBoard.messageText.textContent = `INTEL APPLIED: Letter '${char}' unmasked across word! (-20 PTS)`;
      } else if (hintType === 3 && data.hint.eliminated_letters) {
        data.hint.eliminated_letters.forEach(char => {
          const keyBtn = document.querySelector(`.key-btn[data-key="${char}"]`);
          if (keyBtn) {
            keyBtn.disabled = true;
            keyBtn.classList.add('wrong');
          }
        });
        gameBoard.messageText.textContent = `INTEL APPLIED: Eliminated 3 incorrect keys: ${data.hint.eliminated_letters.join(', ')}! (-20 PTS)`;
      }

      // Check if Hint completed the word
      if (gameState.status === 'won') {
        handleVictory(gameState);
      }

    } catch (e) {
      console.error('Error requesting hint:', e);
    }
  }

  function forfeitGame() {
    if (state.gameStatus !== 'in_progress') return;
    if (confirm('Are you sure you want to forfeit this round?')) {
      audio.playWrongSound();
      // Guess remaining wrong letters to trigger loss
      const wrongs = ['Z', 'X', 'Q', 'J', 'K', 'V', 'W', 'B'];
      let idx = 0;
      const interval = setInterval(() => {
        if (state.gameStatus !== 'in_progress' || idx >= wrongs.length) {
          clearInterval(interval);
        } else {
          submitGuess(wrongs[idx++]);
        }
      }, 100);
    }
  }

  // ==================== RENDERING & UI UPDATES ====================
  function renderFullGameState(gameState) {
    state.gameStatus = gameState.status;
    state.score = gameState.score;
    state.lives = gameState.remaining_lives;

    // HUD Update
    hud.score.textContent = String(gameState.score).padStart(6, '0');
    hud.livesText.textContent = `${String(gameState.remaining_lives).padStart(2, '0')} / ${String(gameState.max_lives).padStart(2, '0')}`;
    hud.difficulty.textContent = gameState.difficulty.toUpperCase();
    hud.mode.textContent = gameState.mode.toUpperCase();

    // Lives LED Tokens
    hud.livesTokens.forEach((token, idx) => {
      token.classList.toggle('active', idx < gameState.remaining_lives);
    });

    // Word Category & Length Tags
    gameBoard.categoryName.textContent = gameState.category.toUpperCase();
    gameBoard.wordLength.textContent = `${gameState.word_length} LETTERS`;

    // Word Slots Rendering
    renderWordTiles(gameState.masked_word);

    // Hangman SVG Stage Rendering
    updateHangmanSVG(gameState.hangman_stage);

    // Hints Buttons State
    if (gameBoard.btnHintLetter) {
      gameBoard.btnHintLetter.disabled = gameState.hint_letter_used || state.gameStatus !== 'in_progress';
    }
    if (gameBoard.btnHintEliminate) {
      gameBoard.btnHintEliminate.disabled = gameState.hint_clue_used || state.gameStatus !== 'in_progress';
    }
    if (gameBoard.btnForfeit) {
      gameBoard.btnForfeit.disabled = state.gameStatus !== 'in_progress';
    }

    // Direct, Prominent Mission Clue / Definition (FREE INTEL)
    if (gameBoard.missionClueText) {
      gameBoard.missionClueText.textContent = gameState.clue || 'Identify the secret target word using the letters.';
    }
  }

  function renderWordTiles(maskedWord) {
    gameBoard.tilesDisplay.innerHTML = '';
    maskedWord.forEach(letter => {
      const tile = document.createElement('div');
      tile.className = 'word-tile';
      if (letter) {
        tile.textContent = letter;
        tile.classList.add('revealed');
      } else {
        tile.textContent = '_';
      }
      gameBoard.tilesDisplay.appendChild(tile);
    });
  }

  function resetKeyboard() {
    document.querySelectorAll('.key-btn').forEach(btn => {
      btn.disabled = false;
      btn.className = 'key-btn';
    });
  }

  function resetHangmanSVG() {
    document.querySelectorAll('.hangman-part').forEach(part => {
      part.classList.remove('visible');
    });
    gameBoard.stageCaption.textContent = 'STAGE 0 / 6 — GALLOWS CLEAR';
  }

  function updateHangmanSVG(stage) {
    const parts = [
      document.getElementById('part-head'),
      document.getElementById('part-torso'),
      document.getElementById('part-left-arm'),
      document.getElementById('part-right-arm'),
      document.getElementById('part-left-leg'),
      document.getElementById('part-right-leg')
    ];

    parts.forEach((p, idx) => {
      if (p) {
        p.classList.toggle('visible', idx < stage);
      }
    });

    const warningMessages = [
      'STAGE 0 / 6 — GALLOWS CLEAR',
      'STAGE 1 / 6 — HEAD ATTACHED',
      'STAGE 2 / 6 — TORSO CONNECTED',
      'STAGE 3 / 6 — LEFT ARM RAISED',
      'STAGE 4 / 6 — RIGHT ARM SECURED',
      'STAGE 5 / 6 — LEFT LEG PENDING',
      'STAGE 6 / 6 — STRIKES EXHAUSTED!'
    ];
    gameBoard.stageCaption.textContent = warningMessages[Math.min(stage, 6)];
  }

  function triggerScreenPulse(type = 'red') {
    if (!screenPulse) return;
    screenPulse.className = `screen-pulse pulse-${type}`;
    setTimeout(() => {
      screenPulse.className = 'screen-pulse';
    }, 280);
  }

  // ==================== TIMER ====================
  function startTimer() {
    stopTimer();
    state.timerSeconds = 0;
    updateTimerDisplay();
    state.timerInterval = setInterval(() => {
      state.timerSeconds++;
      updateTimerDisplay();
    }, 1000);
  }

  function stopTimer() {
    if (state.timerInterval) {
      clearInterval(state.timerInterval);
      state.timerInterval = null;
    }
  }

  function updateTimerDisplay() {
    const mins = String(Math.floor(state.timerSeconds / 60)).padStart(2, '0');
    const secs = String(state.timerSeconds % 60).padStart(2, '0');
    hud.timer.textContent = `${mins}:${secs}`;
  }

  // ==================== VICTORY & GAME OVER HANDLERS ====================
  function handleVictory(gameState) {
    stopTimer();
    audio.playWinSound();

    document.getElementById('win-word-text').textContent = gameState.word || 'COMPLETED';
    document.getElementById('win-score-val').textContent = String(gameState.score).padStart(6, '0');
    document.getElementById('win-lives-val').textContent = `${String(gameState.remaining_lives).padStart(2, '0')} / ${String(gameState.max_lives).padStart(2, '0')}`;
    
    const mins = String(Math.floor(gameState.elapsed_seconds / 60)).padStart(2, '0');
    const secs = String(gameState.elapsed_seconds % 60).padStart(2, '0');
    document.getElementById('win-time-val').textContent = `${mins}:${secs}`;

    setTimeout(() => {
      openModal('victory-modal');
    }, 450);
  }

  function handleGameOver(gameState) {
    stopTimer();
    audio.playGameOverSound();

    document.getElementById('lose-word-text').textContent = gameState.word || 'UNKNOWN';
    document.getElementById('lose-clue-text').textContent = gameState.clue || 'No clue provided.';
    document.getElementById('lose-score-val').textContent = String(gameState.score).padStart(6, '0');
    document.getElementById('lose-wrong-count').textContent = String(gameState.wrong_letters.length).padStart(2, '0');

    const mins = String(Math.floor(gameState.elapsed_seconds / 60)).padStart(2, '0');
    const secs = String(gameState.elapsed_seconds % 60).padStart(2, '0');
    document.getElementById('lose-time-val').textContent = `${mins}:${secs}`;

    setTimeout(() => {
      openModal('gameover-modal');
    }, 450);
  }

  // ==================== HALL OF FAME / STATS ====================
  async function loadPlayerStats() {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      if (!data.success) return;

      const st = data.statistics;
      document.getElementById('stat-total-games').textContent = st.total_games;
      document.getElementById('stat-games-won').textContent = st.games_won;
      document.getElementById('stat-games-lost').textContent = st.games_lost;
      document.getElementById('stat-win-rate').textContent = `${st.win_percentage}%`;
      document.getElementById('stat-high-score').textContent = st.high_score;
      document.getElementById('stat-total-score').textContent = st.total_score;
      document.getElementById('stat-curr-streak').textContent = st.current_streak;
      document.getElementById('stat-best-streak').textContent = st.longest_streak;

      // Render recent matches table
      const tbody = document.getElementById('recent-games-tbody');
      tbody.innerHTML = '';

      if (!data.recent_games || data.recent_games.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No games recorded yet. Step into the arcade to establish your record!</td></tr>`;
        return;
      }

      data.recent_games.forEach(game => {
        const tr = document.createElement('tr');
        const mins = String(Math.floor(game.time_seconds / 60)).padStart(2, '0');
        const secs = String(game.time_seconds % 60).padStart(2, '0');
        const dateStr = game.played_at ? game.played_at.split(' ')[0] : 'Today';

        tr.innerHTML = `
          <td class="${game.won ? 'match-won' : 'match-lost'}">${game.result}</td>
          <td><strong>${game.word}</strong></td>
          <td>${game.category}</td>
          <td>${game.difficulty.toUpperCase()}</td>
          <td>${game.score}</td>
          <td>${mins}:${secs}</td>
          <td>${dateStr}</td>
        `;
        tbody.appendChild(tr);
      });

    } catch (e) {
      console.warn('Failed to fetch statistics:', e);
    }
  }

  async function resetStatistics() {
    if (confirm('WARNING: Reset all your local high score and streak records?')) {
      try {
        const res = await fetch('/api/stats/reset', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
          audio.playWrongSound();
          loadPlayerStats();
          alert('Player statistics have been reset.');
        }
      } catch (e) {
        console.error('Error resetting statistics:', e);
      }
    }
  }

  // ==================== EVENT LISTENERS ====================
  function setupEventListeners() {
    // Navigation routing
    document.querySelectorAll('[data-view]').forEach(btn => {
      btn.addEventListener('click', e => {
        e.preventDefault();
        switchView(btn.dataset.view);
      });
    });

    // Modal Triggers
    document.querySelectorAll('[data-modal]').forEach(btn => {
      btn.addEventListener('click', e => {
        e.preventDefault();
        openModal(btn.dataset.modal);
      });
    });

    // Modal Close Triggers
    document.querySelectorAll('.close-modal-trigger, .close-modal-btn').forEach(btn => {
      btn.addEventListener('click', () => closeModal());
    });

    // Mobile Hamburger
    const mobileToggle = document.getElementById('mobile-toggle');
    const mobileDrawer = document.getElementById('mobile-drawer');
    if (mobileToggle && mobileDrawer) {
      mobileToggle.addEventListener('click', () => {
        mobileDrawer.classList.toggle('open');
      });
    }

    // Sound Header Button Toggle
    const soundToggleBtn = document.getElementById('sound-toggle-btn');
    if (soundToggleBtn) {
      soundToggleBtn.addEventListener('click', () => {
        audio.soundEnabled = !audio.soundEnabled;
        localStorage.setItem('arcade_sound', audio.soundEnabled);
        const soundSwitch = document.getElementById('setting-sound');
        if (soundSwitch) soundSwitch.checked = audio.soundEnabled;
        updateSoundIcon();
        if (audio.soundEnabled) audio.playCoinSound();
      });
    }

    // Hero "INSERT COIN • START GAME" Button
    const coinBtn = document.getElementById('btn-insert-coin');
    if (coinBtn) {
      coinBtn.addEventListener('click', () => {
        audio.playCoinSound();
        switchView('setup');
      });
    }

    // Setup: Difficulty selection
    document.querySelectorAll('.difficulty-card').forEach(card => {
      card.addEventListener('click', () => {
        audio.playButtonSound();
        document.querySelectorAll('.difficulty-card').forEach(c => {
          c.classList.remove('selected');
          c.setAttribute('aria-checked', 'false');
        });
        card.classList.add('selected');
        card.setAttribute('aria-checked', 'true');
        state.difficulty = card.dataset.diff;
      });
    });

    // Setup: Category selection
    document.querySelectorAll('.category-card').forEach(card => {
      card.addEventListener('click', () => {
        audio.playButtonSound();
        document.querySelectorAll('.category-card').forEach(c => {
          c.classList.remove('selected');
          c.setAttribute('aria-checked', 'false');
        });
        card.classList.add('selected');
        card.setAttribute('aria-checked', 'true');
        state.category = card.dataset.category;
      });
    });

    // Setup: Start Round
    const startRoundBtn = document.getElementById('btn-start-round');
    if (startRoundBtn) {
      startRoundBtn.addEventListener('click', () => {
        startNewGame({
          mode: 'single',
          category: state.category,
          difficulty: state.difficulty
        });
      });
    }

    const setupBackBtn = document.getElementById('btn-setup-back');
    if (setupBackBtn) {
      setupBackBtn.addEventListener('click', () => switchView('home'));
    }

    // Onscreen Keyboard Buttons
    if (gameBoard.keyboard) {
      gameBoard.keyboard.addEventListener('click', e => {
        const keyBtn = e.target.closest('.key-btn');
        if (keyBtn && !keyBtn.disabled) {
          submitGuess(keyBtn.dataset.key);
        }
      });
    }

    // Physical Hardware Keyboard Input
    window.addEventListener('keydown', e => {
      // Ignore if user is typing in form input or if a modal is open
      const activeModal = document.querySelector('.arcade-modal.open');
      if (activeModal && activeModal.id === 'two-player-modal') return;
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      if (e.key && e.key.length === 1 && /[a-zA-Z]/.test(e.key)) {
        if (state.gameStatus === 'in_progress' && views.game.classList.contains('active')) {
          submitGuess(e.key);
        }
      }
    });

    // Hint Buttons
    if (gameBoard.btnHintLetter) {
      gameBoard.btnHintLetter.addEventListener('click', () => requestHint(2));
    }
    if (gameBoard.btnHintEliminate) {
      gameBoard.btnHintEliminate.addEventListener('click', () => requestHint(3));
    }
    if (gameBoard.btnForfeit) {
      gameBoard.btnForfeit.addEventListener('click', forfeitGame);
    }

    // Modal Actions
    document.getElementById('btn-win-next').addEventListener('click', () => {
      closeModal();
      startNewGame({ mode: 'single', category: state.category, difficulty: state.difficulty });
    });
    document.getElementById('btn-win-stats').addEventListener('click', () => {
      closeModal();
      openModal('stats-modal');
    });
    document.getElementById('btn-win-menu').addEventListener('click', () => {
      closeModal();
      switchView('home');
    });

    document.getElementById('btn-lose-retry').addEventListener('click', () => {
      closeModal();
      startNewGame({ mode: state.mode, category: state.category, difficulty: state.difficulty });
    });
    document.getElementById('btn-lose-new').addEventListener('click', () => {
      closeModal();
      switchView('setup');
    });
    document.getElementById('btn-lose-menu').addEventListener('click', () => {
      closeModal();
      switchView('home');
    });

    // Daily Challenge Start
    const startDailyBtn = document.getElementById('btn-start-daily');
    if (startDailyBtn) {
      startDailyBtn.addEventListener('click', () => {
        closeModal();
        startNewGame({ mode: 'daily' });
      });
    }

    // Two-Player Secret Word Mask Toggle
    const toggleWordMask = document.getElementById('toggle-word-mask');
    const p1WordInput = document.getElementById('p1-word-input');
    if (toggleWordMask && p1WordInput) {
      toggleWordMask.addEventListener('click', () => {
        const isPass = p1WordInput.type === 'password';
        p1WordInput.type = isPass ? 'text' : 'password';
        toggleWordMask.textContent = isPass ? '🔒' : '👁️';
      });
    }

    // Two-Player Form Submit
    const twoPlayerForm = document.getElementById('twoplayer-form');
    if (twoPlayerForm) {
      twoPlayerForm.addEventListener('submit', e => {
        e.preventDefault();
        const word = p1WordInput.value.trim();
        const clue = document.getElementById('p1-clue-input').value.trim();

        const clean = word.replace(/[^a-zA-Z]/g, '');
        if (clean.length < 3 || clean.length > 20) {
          alert('Secret word must contain between 3 and 20 alphabetic letters.');
          return;
        }

        closeModal();
        // Visual transition
        alert('PASS CONTROL TO PLAYER 2 TO BEGIN GUESSING!');
        startNewGame({
          mode: 'twoplayer',
          custom_word: clean,
          custom_clue: clue || 'Secret word entered by Player 1',
          category: '2-Player Custom',
          difficulty: clean.length <= 6 ? 'easy' : clean.length <= 8 ? 'medium' : 'hard'
        });
        p1WordInput.value = '';
        document.getElementById('p1-clue-input').value = '';
      });
    }

    // Reset Statistics Button
    const resetStatsBtn = document.getElementById('btn-reset-stats');
    if (resetStatsBtn) {
      resetStatsBtn.addEventListener('click', resetStatistics);
    }

    // Settings Controls
    const settingSound = document.getElementById('setting-sound');
    if (settingSound) {
      settingSound.addEventListener('change', () => {
        audio.soundEnabled = settingSound.checked;
        localStorage.setItem('arcade_sound', audio.soundEnabled);
        updateSoundIcon();
        if (audio.soundEnabled) audio.playCoinSound();
      });
    }

    const settingAmbience = document.getElementById('setting-ambience');
    if (settingAmbience) {
      settingAmbience.addEventListener('change', () => {
        localStorage.setItem('arcade_ambience', settingAmbience.checked);
        audio.toggleAmbience(settingAmbience.checked);
      });
    }

    const settingGlow = document.getElementById('setting-glow');
    if (settingGlow) {
      settingGlow.addEventListener('change', () => {
        const val = settingGlow.value;
        localStorage.setItem('arcade_glow', val);
        document.body.classList.toggle('reduced-glow', val === 'reduced');
      });
    }

    const settingMotion = document.getElementById('setting-motion');
    if (settingMotion) {
      settingMotion.addEventListener('change', () => {
        const val = settingMotion.value;
        localStorage.setItem('arcade_motion', val);
        document.body.classList.toggle('reduced-motion', val === 'reduced');
      });
    }

    const settingTheme = document.getElementById('setting-theme');
    if (settingTheme) {
      settingTheme.addEventListener('change', () => {
        const val = settingTheme.value;
        localStorage.setItem('arcade_theme', val);
        document.body.classList.toggle('contrast-theme', val === 'contrast');
      });
    }
  }

  // Auto initialize on DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
  } else {
    initApp();
  }

})();
