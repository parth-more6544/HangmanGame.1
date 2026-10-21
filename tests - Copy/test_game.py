"""
tests/test_game.py - Comprehensive Automated Test Suite for Hangman: The Neon Arcade

Covers all 17 required verification aspects:
1. Correct guesses
2. Incorrect guesses
3. Duplicate guesses
4. Invalid input handling
5. Uppercase/lowercase normalization
6. Repeated letters in words
7. Winning condition evaluation
8. Losing condition evaluation
9. Six-stage Hangman drawing logic (0 to 6)
10. Hint 1 and Hint 2 functionality
11. Score calculation and bonus formulas
12. Game initialization and restart
13. Category filtering
14. Difficulty filtering
15. Two-player input validation
16. Daily Challenge deterministic generation
17. SQLite database persistence and streak tracking
"""

import os
import sys
import unittest
import uuid

# Add parent directory to module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from words import word_manager, WordManager
from game_logic import (
    HangmanGame, start_new_game, check_guess, get_masked_word,
    calculate_score, update_hangman, check_win, check_loss,
    request_hint, save_game_result, get_player_statistics
)
import database


class TestHangmanGame(unittest.TestCase):

    def setUp(self):
        self.test_session = f"test_session_{uuid.uuid4().hex[:8]}"

    def test_01_correct_guess(self):
        """1. Verify correct letter guesses reveal slots and award points."""
        game = HangmanGame(word="PYTHON", category="Technology", difficulty="easy", clue="Language")
        res = game.check_guess("P")
        self.assertTrue(res["valid"])
        self.assertTrue(res["is_correct"])
        self.assertIn("P", game.correct_letters)
        self.assertEqual(game.score, 10)
        self.assertEqual(game.remaining_lives, 6)

    def test_02_incorrect_guess(self):
        """2. Verify incorrect letter guesses deduct lives and advance hangman stage."""
        game = HangmanGame(word="PYTHON", category="Technology", difficulty="easy", clue="Language")
        res = game.check_guess("Z")
        self.assertTrue(res["valid"])
        self.assertFalse(res["is_correct"])
        self.assertEqual(game.remaining_lives, 5)
        self.assertEqual(game.hangman_stage, 1)
        self.assertIn("Z", game.wrong_letters)

    def test_03_duplicate_guess(self):
        """3. Verify duplicate guesses are flagged without penalizing lives."""
        game = HangmanGame(word="PYTHON", category="Technology", difficulty="easy", clue="Language")
        game.check_guess("P")
        dup_res = game.check_guess("P")
        self.assertTrue(dup_res["valid"])
        self.assertTrue(dup_res["is_duplicate"])
        self.assertEqual(game.score, 10)  # No extra points
        self.assertEqual(game.remaining_lives, 6)

        # Duplicate wrong guess
        game.check_guess("X")
        dup_wrong = game.check_guess("X")
        self.assertTrue(dup_wrong["is_duplicate"])
        self.assertEqual(game.remaining_lives, 5)  # Lives not deducted twice

    def test_04_invalid_input(self):
        """4. Verify non-alphabetic, multi-char, and empty inputs are rejected."""
        game = HangmanGame(word="PYTHON", category="Technology", difficulty="easy", clue="Language")
        for bad_input in ["1", "!", "PY", "", None]:
            res = game.check_guess(bad_input)
            self.assertFalse(res["valid"])
            self.assertIn("error", res)

    def test_05_case_insensitivity(self):
        """5. Verify lowercase guesses correctly match uppercase words."""
        game = HangmanGame(word="PYTHON", category="Technology", difficulty="easy", clue="Language")
        res = game.check_guess("p")
        self.assertTrue(res["valid"])
        self.assertTrue(res["is_correct"])
        self.assertIn("P", game.correct_letters)

    def test_06_repeated_letters_in_word(self):
        """6. Verify all occurrences of repeated letters are revealed simultaneously."""
        game = HangmanGame(word="BANANA", category="General Knowledge", difficulty="easy", clue="Yellow fruit")
        res = game.check_guess("A")
        self.assertTrue(res["is_correct"])
        masked = game.get_masked_word()
        # Word is B A N A N A -> indices 1, 3, 5 must be 'A'
        self.assertEqual(masked, [None, "A", None, "A", None, "A"])

    def test_07_winning_condition(self):
        """7. Verify winning occurs when all letters are guessed, awarding bonuses."""
        game = HangmanGame(word="CAT", category="Animals", difficulty="easy", clue="Pet")
        game.check_guess("C")
        game.check_guess("A")
        res = game.check_guess("T")
        self.assertEqual(game.status, "won")
        self.assertTrue(check_win(game))
        # 3 correct letters (3*10=30) + completion bonus 100 + 6 lives remaining (6*15=90) = 220
        self.assertEqual(game.score, 220)
        # Word is revealed in export once won
        self.assertEqual(game.to_dict()["word"], "CAT")

    def test_08_losing_condition(self):
        """8. Verify 6 wrong guesses ends game as lost and halts further guesses."""
        game = HangmanGame(word="DOG", category="Animals", difficulty="easy", clue="Pet")
        wrongs = ["A", "B", "C", "E", "F", "H"]
        for letter in wrongs:
            game.check_guess(letter)
        self.assertEqual(game.status, "lost")
        self.assertTrue(check_loss(game))
        self.assertEqual(game.remaining_lives, 0)
        self.assertEqual(game.hangman_stage, 6)

        # Subsequent guess must be rejected
        late_guess = game.check_guess("D")
        self.assertFalse(late_guess["valid"])

    def test_09_six_stage_hangman_logic(self):
        """9. Verify hangman stage increments strictly 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6."""
        game = HangmanGame(word="CODE", category="Technology", difficulty="easy", clue="Logic")
        self.assertEqual(update_hangman(game), 0)
        wrong_sequence = ["A", "B", "F", "G", "H", "I"]
        for expected_stage, letter in enumerate(wrong_sequence, start=1):
            game.check_guess(letter)
            self.assertEqual(update_hangman(game), expected_stage)

    def test_10_hint_functionality(self):
        """10. Verify Hint 1 reveals clue and Hint 2 reveals missing letter with 20pt penalty."""
        game = HangmanGame(word="ROBOT", category="Technology", difficulty="easy", clue="Automated machine")
        game.check_guess("R")  # Score: 10
        game.check_guess("O")  # Score: 20

        # Hint 1: Clue
        h1 = game.request_hint(1)
        self.assertTrue(h1["success"])
        self.assertEqual(h1["clue"], "Automated machine")
        self.assertEqual(game.score, 0)  # 20 - 20 = 0 (floor)

        # Repeated Hint 1 fails
        h1_repeat = game.request_hint(1)
        self.assertFalse(h1_repeat["success"])

        # Earn some score
        game.score = 50
        # Hint 2: Auto reveal letter
        h2 = game.request_hint(2)
        self.assertTrue(h2["success"])
        revealed = h2["revealed_letter"]
        self.assertIn(revealed, ["B", "T"])
        self.assertIn(revealed, game.correct_letters)
        self.assertEqual(game.score, 30)  # 50 - 20 = 30

    def test_11_score_calculation(self):
        """11. Verify standalone calculate_score utility matches game formula."""
        score_won = calculate_score(correct_count=5, lives_left=4, won=True, hints_used=1)
        # 5*10 + 100 + 4*15 - 20 = 50 + 100 + 60 - 20 = 190
        self.assertEqual(score_won, 190)

        score_lost = calculate_score(correct_count=2, lives_left=0, won=False, hints_used=0)
        # 2*10 = 20
        self.assertEqual(score_lost, 20)

    def test_12_game_restart(self):
        """12. Verify factory function starts fresh independent game instances."""
        game1 = start_new_game("Technology", "easy")
        game2 = start_new_game("Technology", "easy")
        self.assertNotEqual(game1.game_id, game2.game_id)
        self.assertEqual(game1.score, 0)
        self.assertEqual(game2.remaining_lives, 6)

    def test_13_category_selection(self):
        """13. Verify word manager accurately filters by category."""
        animals = word_manager.filter_words(category="Animals")
        self.assertGreater(len(animals), 0)
        self.assertTrue(all(w["category"] == "Animals" for w in animals))

    def test_14_difficulty_selection(self):
        """14. Verify word manager accurately filters by difficulty tier."""
        hard_words = word_manager.filter_words(difficulty="hard")
        self.assertGreater(len(hard_words), 0)
        self.assertTrue(all(w["difficulty"] == "hard" for w in hard_words))

    def test_15_two_player_input_validation(self):
        """15. Verify 2-player mode cleanses custom word and hides it in state."""
        custom = start_new_game(
            custom_word="galaxy 101!",
            custom_clue="Cosmic system of stars",
            mode="twoplayer"
        )
        self.assertEqual(custom.word, "GALAXY")
        self.assertEqual(custom.category, "2-Player Custom")
        # Word is NOT exposed in dict while in progress
        state = custom.to_dict()
        self.assertNotIn("word", state)
        self.assertEqual(len(state["masked_word"]), 6)

    def test_16_daily_challenge_rules(self):
        """16. Verify daily challenge produces the exact same word for a specific date."""
        word_today_1 = word_manager.get_daily_word("2026-10-21")
        word_today_2 = word_manager.get_daily_word("2026-10-21")
        self.assertEqual(word_today_1["word"], word_today_2["word"])

        word_tomorrow = word_manager.get_daily_word("2026-10-22")
        # Ensure different dates hash appropriately
        self.assertIsNotNone(word_tomorrow["word"])

    def test_17_database_persistence_and_stats(self):
        """17. Verify SQLite saving, streak computation, metrics aggregation, and reset."""
        session_id = f"test_user_{uuid.uuid4().hex}"

        # Save a Win
        database.save_game_result(
            session_id=session_id,
            word="PYTHON",
            category="Technology",
            difficulty="easy",
            won=True,
            score=150,
            wrong_guesses=2,
            remaining_lives=4,
            time_seconds=35
        )

        # Save another Win
        database.save_game_result(
            session_id=session_id,
            word="ARCADE",
            category="Technology",
            difficulty="easy",
            won=True,
            score=180,
            wrong_guesses=1,
            remaining_lives=5,
            time_seconds=28
        )

        # Save a Loss
        database.save_game_result(
            session_id=session_id,
            word="CIPHER",
            category="Technology",
            difficulty="hard",
            won=False,
            score=20,
            wrong_guesses=6,
            remaining_lives=0,
            time_seconds=50
        )

        stats = database.get_player_statistics(session_id)
        self.assertEqual(stats["total_games"], 3)
        self.assertEqual(stats["games_won"], 2)
        self.assertEqual(stats["games_lost"], 1)
        self.assertEqual(stats["high_score"], 180)
        self.assertEqual(stats["longest_streak"], 2)
        self.assertEqual(stats["current_streak"], 0)  # Last game was a loss

        # Recent games
        recent = database.get_recent_games(session_id, limit=5)
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[0]["word"], "CIPHER")

        # Reset stats
        database.reset_player_stats(session_id)
        cleared_stats = database.get_player_statistics(session_id)
        self.assertEqual(cleared_stats["total_games"], 0)


if __name__ == "__main__":
    unittest.main()
