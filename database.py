"""
database.py - SQLite Database Management for Hangman: The Neon Arcade

Stores game results, tracks individual player statistics, high scores,
streaks, and recent match histories using secure parameterized SQL queries.
"""

import os
import sqlite3
from typing import Dict, List, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "hangman.db")


def get_db_connection() -> sqlite3.Connection:
    """Creates a connection to SQLite database with row factory."""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initializes database tables and indexes."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                word TEXT NOT NULL,
                category TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                mode TEXT NOT NULL DEFAULT 'single',
                won INTEGER NOT NULL,
                score INTEGER NOT NULL,
                wrong_guesses INTEGER NOT NULL,
                remaining_lives INTEGER NOT NULL,
                time_seconds INTEGER NOT NULL,
                daily_date TEXT,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session ON games(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily ON games(session_id, daily_date)")
        conn.commit()


def save_game_result(
    session_id: str,
    word: str,
    category: str,
    difficulty: str,
    won: bool,
    score: int,
    wrong_guesses: int,
    remaining_lives: int,
    time_seconds: int,
    mode: str = "single",
    daily_date: Optional[str] = None
) -> int:
    """
    Saves a completed game outcome using parameterized SQL statement.
    Returns the newly inserted row ID.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO games (
                session_id, word, category, difficulty, mode,
                won, score, wrong_guesses, remaining_lives, time_seconds, daily_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            word.upper(),
            category,
            difficulty,
            mode,
            1 if won else 0,
            score,
            wrong_guesses,
            remaining_lives,
            time_seconds,
            daily_date
        ))
        conn.commit()
        return cursor.lastrowid or 0


def has_played_daily(session_id: str, daily_date: str) -> bool:
    """Checks if the user has already recorded a daily challenge for this date."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM games
            WHERE session_id = ? AND daily_date = ? AND mode = 'daily'
            LIMIT 1
        """, (session_id, daily_date))
        return cursor.fetchone() is not None


def get_player_statistics(session_id: str) -> Dict[str, Any]:
    """
    Calculates comprehensive statistics for the player:
    total games, wins, losses, win rate %, highest score, total score,
    current streak, and longest streak.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Aggregate metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_games,
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as games_won,
                SUM(CASE WHEN won = 0 THEN 1 ELSE 0 END) as games_lost,
                MAX(score) as high_score,
                SUM(score) as total_score
            FROM games
            WHERE session_id = ?
        """, (session_id,))
        agg = cursor.fetchone()

        total_games = agg["total_games"] if agg and agg["total_games"] else 0
        games_won = agg["games_won"] if agg and agg["games_won"] else 0
        games_lost = agg["games_lost"] if agg and agg["games_lost"] else 0
        high_score = agg["high_score"] if agg and agg["high_score"] else 0
        total_score = agg["total_score"] if agg and agg["total_score"] else 0

        win_rate = round((games_won / total_games * 100), 1) if total_games > 0 else 0.0

        # Calculate streaks
        cursor.execute("""
            SELECT won FROM games
            WHERE session_id = ?
            ORDER BY id ASC
        """, (session_id,))
        results = cursor.fetchall()

        current_streak = 0
        longest_streak = 0
        temp_streak = 0

        for row in results:
            if row["won"] == 1:
                temp_streak += 1
                if temp_streak > longest_streak:
                    longest_streak = temp_streak
            else:
                temp_streak = 0

        # Current streak is streak of the most recent games backwards
        for row in reversed(results):
            if row["won"] == 1:
                current_streak += 1
            else:
                break

        return {
            "total_games": total_games,
            "games_won": games_won,
            "games_lost": games_lost,
            "win_percentage": win_rate,
            "high_score": high_score,
            "total_score": total_score,
            "current_streak": current_streak,
            "longest_streak": longest_streak
        }


def get_recent_games(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetches the player's recent game history."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                id, word, category, difficulty, mode,
                won, score, wrong_guesses, remaining_lives, time_seconds,
                played_at
            FROM games
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (session_id, limit))
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "word": r["word"],
                "category": r["category"],
                "difficulty": r["difficulty"],
                "mode": r["mode"],
                "won": bool(r["won"]),
                "result": "WON" if r["won"] else "LOST",
                "score": r["score"],
                "wrong_guesses": r["wrong_guesses"],
                "remaining_lives": r["remaining_lives"],
                "time_seconds": r["time_seconds"],
                "played_at": r["played_at"]
            }
            for r in rows
        ]


def reset_player_stats(session_id: str) -> None:
    """Resets all recorded games for the given session ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM games WHERE session_id = ?", (session_id,))
        conn.commit()


# Initialize database upon module import
init_db()
