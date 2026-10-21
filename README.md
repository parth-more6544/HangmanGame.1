# HANGMAN: THE NEON ARCADE
### GUESS. SURVIVE. WIN.

A full-stack, cinematic retro arcade **Hangman Word Guessing Game** built with **Python 3, Flask, SQLite, HTML5, CSS3, and JavaScript**.

---

## 🕹️ Project Overview

**HANGMAN: The Neon Arcade** is a college Python mini project designed to marry robust computer science fundamentals with an authentic late-1980s neon noir gaming room aesthetic.

The visual identity recreates a dimly lit, narrow retro arcade corridor dominated by deep black shadows, warm crimson-red neon signs, industrial ceiling pipes, reflective wet floor tiles, and blue CRT screen glows.

---

## ✨ Key Features

1. **Authentic Retro Arcade Environment:**
   - 65% deep blacks & dark navy shadows (`#080A18`, `#09070E`).
   - 25% crimson and red-orange neon lighting (`#D52724`, `#F04432`, `#D95932`).
   - 10% selective cool cyan-blue CRT screen accents (`#4F96B8`, `#2B496B`).
   - Pure CSS scanlines, curved CRT vignette, and tactile button underglow.

2. **Core 6-Stage Hangman Drawing:**
   - Vector SVG gallows and animated neon character lines.
   - Smooth progressive drawing transitions:
     `Gallows (0) → Head (1) → Torso (2) → Left Arm (3) → Right Arm (4) → Left Leg (5) → Right Leg (6)`.
   - Dynamic red screen pulse on miss.

3. **Curated Word Database (288 Words):**
   - 6 Categories: **Technology**, **Movies**, **Animals**, **Countries**, **Sports**, **General Knowledge**.
   - 3 Difficulty Tiers:
     - **Rookie (Easy):** 4–6 letters
     - **Player (Medium):** 6–8 letters
     - **Legend (Hard):** 8–12 letters
   - Every word includes a verified clue/definition for hint reveal.

4. **Multiple Game Modes:**
   - **Classic Single Player:** Select category and difficulty or choose "Random".
   - **Daily Arcade Challenge:** Deterministic word selection based on the `Asia/Kolkata` calendar date. One scored attempt per day.
   - **Local 2-Player Versus:** Player 1 inputs a secret word and clue; Player 2 takes control of the cabinet to solve it.

5. **Hint System:**
   - **Hint 1 (Clue):** Unveils thematic word description (-20 pts).
   - **Hint 2 (Auto-Reveal):** Unmasks one remaining letter across all its positions (-20 pts).

6. **Arcade Scoring & Timer:**
   - Correct letter: **+10 PTS**
   - Completed word: **+100 PTS**
   - Remaining attempts bonus: **+15 PTS** per remaining attempt
   - Elapsed timer tracked in real-time format `MM:SS`.

7. **Persistent Hall of Fame (SQLite):**
   - Tracks games played, wins, losses, win rate percentage, high scores, total points, and win streaks.
   - Match history table logging word, category, score, and duration.
   - Reset statistics feature with user confirmation.

8. **Zero-Dependency Web Audio Synthesizer:**
   - Synthesizes 8-bit chiptune sound cues natively via the Web Audio API: coin insert, switch clicks, correct chimes, wrong buzzer, victory fanfare, and game-over cadence.
   - Optional 60Hz cathode electrical hum ambience.
   - Instant mute toggle.

9. **Accessibility & Control Customization:**
   - High-contrast color mode.
   - Reduced neon glow mode.
   - Reduced motion mode.
   - Full keyboard support (Physical keyboard A-Z or touchscreen arcade keys).
   - Fully responsive on mobile (320px–430px), tablet, and desktop.

---

## 📁 Project Architecture

```text
College Computing in python project/
│
├── app.py                  # Flask web server & REST API endpoints
├── game_logic.py           # Core Hangman rules, state, scoring & SVG logic
├── words.py                # Word dataset loader, filtering & daily hash generator
├── database.py             # SQLite persistence, streaks & high-score tracking
├── generate_words.py       # Dataset generator (288 curated words)
├── requirements.txt        # Python dependency manifest
├── README.md               # Project documentation
├── .gitignore              # Git ignored patterns
│
├── data/
│   ├── words.json          # 288 words across 18 category/difficulty combos
│   └── hangman.db          # SQLite persistent database (auto-created)
│
├── templates/
│   └── index.html          # Semantic HTML5 single-page arcade interface
│
├── static/
│   ├── css/
│   │   └── style.css       # Neon Noir retro arcade design system & CRT shaders
│   ├── js/
│   │   └── script.js       # Web Audio synthesizer, event handling & API binding
│   └── images/
│       ├── arcade-background.jpg  # Photorealistic retro arcade corridor
│       ├── cabinet-hero.jpg       # Arcade cabinet reference
│       └── logo.svg               # Illuminated vector arcade marquee
│
└── tests/
    └── test_game.py        # 17 automated unit tests covering all rules
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.8 or higher.
- `pip` (Python package manager).

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Automated Test Suite
Verify that all 17 automated game tests pass:
```bash
python tests/test_game.py
```

### 4. Launch the Game Server
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Testing Coverage (17 Test Suites)
The `tests/test_game.py` module executes 17 test suites verifying:
1. Correct letter guesses & scoring
2. Incorrect guesses & life deduction
3. Duplicate guess handling (no duplicate penalties)
4. Invalid character rejection
5. Case-insensitivity (lowercase/uppercase normalization)
6. Multiple occurrences of repeated letters
7. Victory detection & bonuses
8. Loss detection (6 strikes) & game freeze
9. 6-stage progressive SVG Hangman drawing (0 → 6)
10. Hint 1 (clue) and Hint 2 (letter reveal) penalties
11. Standalone score calculation formulas
12. Game restart & session isolation
13. Word category filtering
14. Difficulty tier filtering
15. 2-player secret word validation & backend masking
16. Daily Challenge deterministic date hashing
17. SQLite persistence, streak calculation & stats reset
