"""
game_logic.py - Core Hangman Game Mechanics for Hangman: The Neon Arcade

Implements the official 6-stage retro arcade Hangman game rules,
scoring algorithms, masked word generation, hint penalties, and state management.
Designed cleanly for academic demonstration and robust production execution.
"""

import time
import uuid
import random
from typing import Dict, List, Set, Optional, Any, Tuple
from words import word_manager
import database


class HangmanGame:
    """Encapsulates a single active or completed session of the Hangman game."""

    MAX_WRONG: int = 6

    def __init__(
        self,
        word: str,
        category: str,
        difficulty: str,
        clue: str,
        mode: str = "single",
        daily_date: Optional[str] = None
    ):
        self.game_id: str = str(uuid.uuid4())
        self.word: str = word.upper().strip()
        self.category: str = category
        self.difficulty: str = difficulty
        self.clue: str = clue
        self.mode: str = mode
        self.daily_date: Optional[str] = daily_date

        self.guessed_letters: Set[str] = set()
        self.correct_letters: Set[str] = set()
        self.wrong_letters: List[str] = []

        self.score: int = 0
        self.status: str = "in_progress"  # 'in_progress', 'won', 'lost'
        self.hint_clue_used: bool = False
        self.hint_letter_used: bool = False

        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self.elapsed_seconds: int = 0

    @property
    def remaining_lives(self) -> int:
        """Returns attempts left before complete loss (from 6 down to 0)."""
        return max(0, self.MAX_WRONG - len(self.wrong_letters))

    @property
    def hangman_stage(self) -> int:
        """Returns the hangman drawing stage (0=gallows only, 6=full figure)."""
        return min(self.MAX_WRONG, len(self.wrong_letters))

    def get_masked_word(self) -> List[Optional[str]]:
        """
        Returns list representing the word state for client display.
        Guessed letters are revealed; unguessed are returned as None or underscore.
        """
        return [char if char in self.correct_letters else None for char in self.word]

    def check_guess(self, letter: str) -> Dict[str, Any]:
        """
        Processes a player's letter guess.
        Validates character, handles duplicates, recalculates score and status.
        """
        if self.status != "in_progress":
            return {
                "valid": False,
                "error": "Game is already completed.",
                "status": self.status
            }

        if not letter or not isinstance(letter, str):
            return {"valid": False, "error": "Invalid letter input."}

        char = letter.upper().strip()
        if len(char) != 1 or not char.isalpha():
            return {"valid": False, "error": "Guess must be a single A-Z letter."}

        # Check for duplicate guess
        if char in self.guessed_letters:
            return {
                "valid": True,
                "is_duplicate": True,
                "char": char,
                "is_correct": char in self.correct_letters,
                "message": f"Letter '{char}' was already guessed.",
                "game_state": self.to_dict()
            }

        # Record new guess
        self.guessed_letters.add(char)

        if char in self.word:
            self.correct_letters.add(char)
            # Scoring: +10 for each correct guessed letter
            self.score += 10
            is_correct = True
            msg = f"Direct hit! Letter '{char}' is in the secret word."
        else:
            self.wrong_letters.append(char)
            is_correct = False
            msg = f"Miss! Letter '{char}' is not in the word."

        # Evaluate win/loss
        self._evaluate_game_status()

        return {
            "valid": True,
            "is_duplicate": False,
            "char": char,
            "is_correct": is_correct,
            "message": msg,
            "game_state": self.to_dict()
        }

    def request_hint(self, hint_type: int) -> Dict[str, Any]:
        """
        Handles Hint 1 (Text Clue) or Hint 2 (Auto Letter Reveal).
        Deducts 20 points per hint used (cannot become negative).
        """
        if self.status != "in_progress":
            return {"success": False, "error": "Cannot use hints after game finishes."}

        HINT_PENALTY = 20

        if hint_type == 1:
            if self.hint_clue_used:
                return {"success": False, "error": "Text clue has already been revealed this round."}
            self.hint_clue_used = True
            self.score = max(0, self.score - HINT_PENALTY)
            return {
                "success": True,
                "hint_type": 1,
                "clue": self.clue,
                "penalty": HINT_PENALTY,
                "game_state": self.to_dict()
            }

        elif hint_type == 2:
            if self.hint_letter_used:
                return {"success": False, "error": "Auto-letter hint has already been used this round."}

            # Find unrevealed letters
            unrevealed = [c for c in self.word if c not in self.correct_letters]
            if not unrevealed:
                return {"success": False, "error": "All letters are already revealed!"}

            revealed_char = random.choice(unrevealed)
            self.guessed_letters.add(revealed_char)
            self.correct_letters.add(revealed_char)
            self.hint_letter_used = True

            # Hint penalty (auto-revealed letters do not earn +10 guess points)
            self.score = max(0, self.score - HINT_PENALTY)

            self._evaluate_game_status()

            return {
                "success": True,
                "hint_type": 2,
                "revealed_letter": revealed_char,
                "penalty": HINT_PENALTY,
                "message": f"Arcade assistance: Letter '{revealed_char}' has been revealed!",
                "game_state": self.to_dict()
            }

        elif hint_type == 3:
            import string
            all_letters = set(string.ascii_uppercase)
            word_letters = set(self.word)
            wrong_pool = list(all_letters - word_letters - self.guessed_letters)

            if len(wrong_pool) < 1:
                return {"success": False, "error": "No remaining wrong letters to eliminate."}

            num_to_eliminate = min(3, len(wrong_pool))
            eliminated = random.sample(wrong_pool, num_to_eliminate)
            for ch in eliminated:
                self.guessed_letters.add(ch)

            self.score = max(0, self.score - HINT_PENALTY)

            return {
                "success": True,
                "hint_type": 3,
                "eliminated_letters": eliminated,
                "penalty": HINT_PENALTY,
                "message": f"Arcade assistance: Eliminated keys: {', '.join(eliminated)}!",
                "game_state": self.to_dict()
            }

        return {"success": False, "error": "Invalid hint type requested."}

    def _evaluate_game_status(self) -> None:
        """Checks if all letters have been identified or if lives ran out."""
        # Check Win
        if all(char in self.correct_letters for char in self.word):
            self.status = "won"
            self.end_time = time.time()
            self.elapsed_seconds = int(self.end_time - self.start_time)
            # Bonus points: +100 for completed word, +15 per remaining attempt
            completion_bonus = 100
            lives_bonus = self.remaining_lives * 15
            self.score += completion_bonus + lives_bonus

        # Check Loss
        elif len(self.wrong_letters) >= self.MAX_WRONG:
            self.status = "lost"
            self.end_time = time.time()
            self.elapsed_seconds = int(self.end_time - self.start_time)

    def get_elapsed_time(self) -> int:
        """Calculates current elapsed seconds."""
        if self.end_time is not None:
            return self.elapsed_seconds
        return int(time.time() - self.start_time)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes game state for frontend API consumption.
        SECURITY: The secret word is strictly masked during gameplay
        and only revealed once status is 'won' or 'lost'.
        """
        masked = self.get_masked_word()
        elapsed = self.get_elapsed_time()

        data = {
            "game_id": self.game_id,
            "category": self.category,
            "difficulty": self.difficulty,
            "mode": self.mode,
            "status": self.status,
            "score": self.score,
            "remaining_lives": self.remaining_lives,
            "max_lives": self.MAX_WRONG,
            "hangman_stage": self.hangman_stage,
            "masked_word": masked,
            "word_length": len(self.word),
            "guessed_letters": sorted(list(self.guessed_letters)),
            "wrong_letters": self.wrong_letters,
            "correct_letters": sorted(list(self.correct_letters)),
            "clue": self.clue,  # Always provided directly on screen for free
            "hint_clue_used": self.hint_clue_used,
            "hint_letter_used": self.hint_letter_used,
            "elapsed_seconds": elapsed,
            "daily_date": self.daily_date
        }

        # Reveal answer word only on game termination
        if self.status in ("won", "lost"):
            data["word"] = self.word

        return data


# =====================================================================
# Academic Functional Interface (College Demonstration Ready)
# =====================================================================

def choose_random_word(category: Optional[str] = None, difficulty: Optional[str] = None) -> Dict[str, str]:
    """Picks a random word dictionary from word database."""
    return word_manager.choose_random_word(category, difficulty)


def start_new_game(
    category: Optional[str] = "Technology",
    difficulty: Optional[str] = "medium",
    custom_word: Optional[str] = None,
    custom_clue: Optional[str] = None,
    mode: str = "single",
    daily_date: Optional[str] = None
) -> HangmanGame:
    """Factory creating and initializing a new HangmanGame instance."""
    if custom_word:
        clean_word = "".join(c for c in custom_word.upper() if c.isalpha())
        # Default category for two-player if not specifically overridden
        assigned_cat = "2-Player Custom" if (mode == "twoplayer" or category == "Technology" or not category) else category
        word_entry = {
            "word": clean_word,
            "category": assigned_cat,
            "difficulty": difficulty or "custom",
            "clue": custom_clue or "Custom word selected by Player 1"
        }
    elif mode == "daily":
        word_entry = word_manager.get_daily_word(daily_date)
    else:
        word_entry = word_manager.choose_random_word(category, difficulty)

    return HangmanGame(
        word=word_entry["word"],
        category=word_entry["category"],
        difficulty=word_entry["difficulty"],
        clue=word_entry["clue"],
        mode=mode,
        daily_date=daily_date
    )


def check_guess(game: HangmanGame, letter: str) -> Dict[str, Any]:
    """Evaluates player letter guess against game instance."""
    return game.check_guess(letter)


def get_masked_word(game: HangmanGame) -> List[Optional[str]]:
    """Returns currently revealed letters and masked slots."""
    return game.get_masked_word()


def calculate_score(correct_count: int, lives_left: int, won: bool, hints_used: int) -> int:
    """Calculates cumulative score based on standard arcade weights."""
    score = correct_count * 10
    if won:
        score += 100 + (lives_left * 15)
    score -= hints_used * 20
    return max(0, score)


def update_hangman(game: HangmanGame) -> int:
    """Returns the current SVG hangman stage (0 through 6)."""
    return game.hangman_stage


def check_win(game: HangmanGame) -> bool:
    """Returns True if the player successfully revealed the word."""
    return game.status == "won"


def check_loss(game: HangmanGame) -> bool:
    """Returns True if all 6 attempts have been exhausted."""
    return game.status == "lost"


def request_hint(game: HangmanGame, hint_type: int) -> Dict[str, Any]:
    """Applies hint logic and point deduction."""
    return game.request_hint(hint_type)


def save_game_result(game: HangmanGame, session_id: str) -> int:
    """Persists finished game outcome to SQLite database."""
    return database.save_game_result(
        session_id=session_id,
        word=game.word,
        category=game.category,
        difficulty=game.difficulty,
        won=(game.status == "won"),
        score=game.score,
        wrong_guesses=len(game.wrong_letters),
        remaining_lives=game.remaining_lives,
        time_seconds=game.get_elapsed_time(),
        mode=game.mode,
        daily_date=game.daily_date
    )


def get_player_statistics(session_id: str) -> Dict[str, Any]:
    """Queries persistent player statistics from database."""
    return database.get_player_statistics(session_id)
