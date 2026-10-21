"""
words.py - Word Management Module for Hangman: The Neon Arcade

Handles word dataset loading, category filtering, difficulty selection,
validation, and deterministic Daily Challenge word generation.
"""

import os
import json
import random
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Tuple

CATEGORIES = [
    "Animals",
    "Countries",
    "Technology",
    "Movies",
    "Sports",
    "General Knowledge"
]

DIFFICULTIES = ["easy", "medium", "hard"]

# Fallback words if file cannot be read
DEFAULT_FALLBACK_WORDS = [
    {"word": "PYTHON", "category": "Technology", "difficulty": "easy", "clue": "High-level programming language known for readability."},
    {"word": "ARCADE", "category": "General Knowledge", "difficulty": "easy", "clue": "Venue filled with coin-operated video games."},
    {"word": "CIRCUIT", "category": "Technology", "difficulty": "medium", "clue": "A complete and closed path through which electric current can flow."},
    {"word": "ALGORITHM", "category": "Technology", "difficulty": "hard", "clue": "Step-by-step procedure for solving a computational problem."}
]


class WordManager:
    """Manages word repository, filtering, and daily challenge generation."""

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_path = os.path.join(base_dir, "data", "words.json")
        self.data_path = data_path
        self.words: List[Dict[str, str]] = []
        self.load_words()

    def load_words(self) -> None:
        """Loads words from JSON dataset with fallback safety."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        self.words = [
                            {
                                "word": item["word"].upper().strip(),
                                "category": item["category"].strip(),
                                "difficulty": item["difficulty"].lower().strip(),
                                "clue": item["clue"].strip()
                            }
                            for item in data
                            if "word" in item and "category" in item and "difficulty" in item and "clue" in item
                        ]
                        return
            except Exception as e:
                print(f"[Warning] Failed to load words from {self.data_path}: {e}")

        # Fallback if file load fails
        self.words = list(DEFAULT_FALLBACK_WORDS)

    def get_categories(self) -> List[str]:
        """Returns the list of available game categories."""
        return list(CATEGORIES)

    def get_difficulties(self) -> List[str]:
        """Returns the list of supported difficulty tiers."""
        return list(DIFFICULTIES)

    def filter_words(self, category: Optional[str] = None, difficulty: Optional[str] = None) -> List[Dict[str, str]]:
        """Filters word list by category and/or difficulty."""
        filtered = self.words

        if category and category.lower() != "random":
            filtered = [w for w in filtered if w["category"].lower() == category.lower()]

        if difficulty:
            filtered = [w for w in filtered if w["difficulty"].lower() == difficulty.lower()]

        return filtered if filtered else self.words

    def choose_random_word(self, category: Optional[str] = None, difficulty: Optional[str] = None) -> Dict[str, str]:
        """Picks a random word matching the specified category and difficulty."""
        pool = self.filter_words(category, difficulty)
        return random.choice(pool)

    def get_daily_word(self, date_str: Optional[str] = None) -> Dict[str, str]:
        """
        Generates a deterministic daily challenge word for a given date in Asia/Kolkata timezone.
        Uses date string hash to pick consistently across all users without external APIs.
        """
        if not date_str:
            # Asia/Kolkata is UTC+5:30
            kolkata_tz = timezone(timedelta(hours=5, minutes=30))
            now_kolkata = datetime.now(kolkata_tz)
            date_str = now_kolkata.strftime("%Y-%m-%d")

        # Stable hash integer
        hash_digest = hashlib.sha256(f"hangman_daily_{date_str}".encode("utf-8")).hexdigest()
        hash_int = int(hash_digest, 16)

        # Pick from medium and hard words for a proper daily challenge
        challenging_words = [w for w in self.words if w["difficulty"] in ("medium", "hard")]
        if not challenging_words:
            challenging_words = self.words

        chosen_index = hash_int % len(challenging_words)
        chosen = dict(challenging_words[chosen_index])
        chosen["daily_date"] = date_str
        return chosen


# Global singleton instance
word_manager = WordManager()
