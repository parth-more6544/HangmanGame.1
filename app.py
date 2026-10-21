"""
app.py - Flask Server for Hangman: The Neon Arcade

Provides RESTful API endpoints and serves the immersive retro arcade web application.
Handles secure session tracking, server-side game state persistence,
and SQLite statistics integration.
"""

import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, session

import database
from words import word_manager, CATEGORIES, DIFFICULTIES
from game_logic import HangmanGame, start_new_game

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "arcade_neon_noir_secret_key_80s_retro")

# Server-side storage for active game sessions
ACTIVE_GAMES: Dict[str, HangmanGame] = {}


def get_current_kolkata_date() -> str:
    """Returns today's date formatted as YYYY-MM-DD in Asia/Kolkata timezone (UTC+5:30)."""
    kolkata_tz = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(kolkata_tz).strftime("%Y-%m-%d")


def get_player_session_id() -> str:
    """Ensures each client has a unique anonymous session identifier."""
    if "player_id" not in session:
        session["player_id"] = str(uuid.uuid4())
    return session["player_id"]


@app.route("/")
def index():
    """Renders the main arcade web application."""
    get_player_session_id()
    return render_template("index.html")


# =====================================================================
# API Endpoints
# =====================================================================

@app.route("/api/config", methods=["GET"])
def get_config():
    """Returns game configuration: categories, difficulties, and daily challenge info."""
    player_id = get_player_session_id()
    today_date = get_current_kolkata_date()
    has_played_daily = database.has_played_daily(player_id, today_date)

    return jsonify({
        "success": True,
        "categories": CATEGORIES,
        "difficulties": DIFFICULTIES,
        "daily_date": today_date,
        "has_played_daily": has_played_daily
    })


@app.route("/api/game/new", methods=["POST"])
def new_game():
    """Starts a new single player, daily challenge, or two-player game session."""
    player_id = get_player_session_id()
    data = request.get_json(silent=True) or {}

    mode = data.get("mode", "single")
    category = data.get("category", "Technology")
    difficulty = data.get("difficulty", "medium")
    custom_word = data.get("custom_word", None)
    custom_clue = data.get("custom_clue", None)
    today_date = get_current_kolkata_date()

    # Enforce Daily Challenge rules
    if mode == "daily":
        if database.has_played_daily(player_id, today_date):
            return jsonify({
                "success": False,
                "error": f"You have already completed the Daily Challenge for {today_date}! Check back tomorrow."
            }), 400

    # Two-player validation
    if mode == "twoplayer":
        if not custom_word or not isinstance(custom_word, str):
            return jsonify({"success": False, "error": "Player 1 must provide a secret word."}), 400
        clean_word = "".join(c for c in custom_word.upper() if c.isalpha())
        if len(clean_word) < 3 or len(clean_word) > 20:
            return jsonify({"success": False, "error": "Secret word must be between 3 and 20 alphabetic letters."}), 400

    # Instantiate game
    game = start_new_game(
        category=category,
        difficulty=difficulty,
        custom_word=custom_word,
        custom_clue=custom_clue,
        mode=mode,
        daily_date=today_date if mode == "daily" else None
    )

    ACTIVE_GAMES[game.game_id] = game

    # Security: Secret word is never transmitted in active gameplay
    return jsonify({
        "success": True,
        "game_state": game.to_dict()
    })


@app.route("/api/game/guess", methods=["POST"])
def make_guess():
    """Submits a single letter guess for an active game session."""
    player_id = get_player_session_id()
    data = request.get_json(silent=True) or {}

    game_id = data.get("game_id")
    letter = data.get("letter")

    if not game_id or game_id not in ACTIVE_GAMES:
        return jsonify({"success": False, "error": "Game session not found or expired. Please start a new game."}), 404

    game = ACTIVE_GAMES[game_id]

    res = game.check_guess(letter)
    if not res.get("valid"):
        return jsonify({"success": False, "error": res.get("error")}), 400

    # If the game concluded (won or lost), save result to database
    if game.status in ("won", "lost"):
        database.save_game_result(
            session_id=player_id,
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

    return jsonify({
        "success": True,
        "result": res,
        "game_state": game.to_dict()
    })


@app.route("/api/game/hint", methods=["POST"])
def use_hint():
    """Processes a request for Hint 1 (Text Clue) or Hint 2 (Auto Letter)."""
    data = request.get_json(silent=True) or {}
    game_id = data.get("game_id")
    hint_type = data.get("hint_type", 1)

    if not game_id or game_id not in ACTIVE_GAMES:
        return jsonify({"success": False, "error": "Active game session not found."}), 404

    game = ACTIVE_GAMES[game_id]
    res = game.request_hint(hint_type)

    if not res.get("success"):
        return jsonify({"success": False, "error": res.get("error")}), 400

    # Check if hint 2 caused a win
    if game.status in ("won", "lost"):
        player_id = get_player_session_id()
        database.save_game_result(
            session_id=player_id,
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

    return jsonify({
        "success": True,
        "hint": res,
        "game_state": game.to_dict()
    })


@app.route("/api/game/state/<game_id>", methods=["GET"])
def get_game_state(game_id: str):
    """Retrieves current game state snapshot."""
    if game_id not in ACTIVE_GAMES:
        return jsonify({"success": False, "error": "Game session not found."}), 404

    game = ACTIVE_GAMES[game_id]
    return jsonify({
        "success": True,
        "game_state": game.to_dict()
    })


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Retrieves player statistics and match history."""
    player_id = get_player_session_id()
    stats = database.get_player_statistics(player_id)
    recent = database.get_recent_games(player_id, limit=10)

    return jsonify({
        "success": True,
        "statistics": stats,
        "recent_games": recent
    })


@app.route("/api/stats/reset", methods=["POST"])
def reset_stats():
    """Clears player statistics history for current session."""
    player_id = get_player_session_id()
    database.reset_player_stats(player_id)
    return jsonify({
        "success": True,
        "message": "Player statistics have been reset successfully."
    })


if __name__ == "__main__":
    # Disable debug mode in production environment as per specifications
    app.run(host="0.0.0.0", port=5000, debug=True)
