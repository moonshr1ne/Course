import sqlite3

DB_PATH = "game.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def register_user(username):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # username уже существует
    finally:
        conn.close()

def get_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, mmr FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result  # (id, mmr)

def update_mmr(user_id, new_mmr):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET mmr=? WHERE id=?", (new_mmr, user_id))
    conn.commit()
    conn.close()

def save_match(player1_id, player2_id, winner, log):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO matches (player1_id, player2_id, winner, log) VALUES (?, ?, ?, ?)",
        (player1_id, player2_id, winner, log)
    )
    conn.commit()
    conn.close()

def get_leaderboard(limit=10):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, mmr FROM users ORDER BY mmr DESC LIMIT ?", (limit,))
    results = c.fetchall()
    conn.close()
    return results

def get_match_history(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if not user:
        return []

    user_id = user[0]
    c.execute("""
        SELECT m.id, u1.username, u2.username, m.winner, m.created_at
        FROM matches m
        JOIN users u1 ON m.player1_id = u1.id
        JOIN users u2 ON m.player2_id = u2.id
        WHERE m.player1_id = ? OR m.player2_id = ?
        ORDER BY m.created_at DESC
    """, (user_id, user_id))
    results = c.fetchall()
    conn.close()
    return results