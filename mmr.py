from flask import Flask, request, jsonify
from db import (
    get_user, register_user, update_mmr, save_match,
    get_leaderboard, get_match_history
)

def calculate_new_mmr(p1_mmr, p2_mmr, winner, k=32):
    expected1 = 1 / (1 + 10 ** ((p2_mmr - p1_mmr) / 400))
    expected2 = 1 / (1 + 10 ** ((p1_mmr - p2_mmr) / 400))

    if winner == "player1":
        p1_new = p1_mmr + k * (1 - expected1)
        p2_new = p2_mmr + k * (0 - expected2)
    elif winner == "player2":
        p1_new = p1_mmr + k * (0 - expected1)
        p2_new = p2_mmr + k * (1 - expected2)
    else:  # draw
        p1_new = p1_mmr + k * (0.5 - expected1)
        p2_new = p2_mmr + k * (0.5 - expected2)

    return round(p1_new), round(p2_new)

def setup_routes(app: Flask):
    @app.route("/report_match", methods=["POST"])
    def report_match():
        data = request.json
        p1 = data["player1"]
        p2 = data["player2"]
        winner = data["winner"]
        log = data.get("log", "")

        register_user(p1)
        register_user(p2)

        p1_id, p1_mmr = get_user(p1)
        p2_id, p2_mmr = get_user(p2)

        new_mmr1, new_mmr2 = calculate_new_mmr(p1_mmr, p2_mmr, winner)

        save_match(p1_id, p2_id, winner, log)
        update_mmr(p1_id, new_mmr1)
        update_mmr(p2_id, new_mmr2)

        return jsonify({
            "status": "ok",
            "new_mmr": {
                p1: new_mmr1,
                p2: new_mmr2
            }
        })

    @app.route("/leaderboard", methods=["GET"])
    def leaderboard():
        top = get_leaderboard()
        return jsonify([
            {"username": username, "mmr": mmr}
            for username, mmr in top
        ])

    @app.route("/match_history", methods=["GET"])
    def match_history():
        username = request.args.get("username")
        if not username:
            return jsonify({"error": "username required"}), 400

        history = get_match_history(username)
        return jsonify([
            {
                "match_id": match_id,
                "player1": p1,
                "player2": p2,
                "winner": winner,
                "created_at": created_at
            } for match_id, p1, p2, winner, created_at in history
        ])