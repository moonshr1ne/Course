# engine/server.py
import uuid, random, math
from flask import Blueprint, jsonify, request

bp = Blueprint("engine", __name__)   # ← must match the name you register

# ────────── map definition ──────────
MAP_NODES = {
    "main_green": {"x":  120, "y":  120, "type": "main_base"},
    "main_red":   {"x": 1000, "y": 580, "type": "main_base"},
    "proxy_1":    {"x":  120, "y": 580, "type": "proxy"},
    "proxy_2":    {"x": 1000, "y":  120, "type": "proxy"},
    "camp_1":     {"x": 300, "y": 300, "type": "camp"},
    "camp_2":     {"x": 820, "y": 300, "type": "camp"},
}

EDGES = [
    ("main_green","proxy_1"), ("main_red","proxy_1"),
    ("main_green","proxy_2"), ("main_red","proxy_2"),
    ("main_green","camp_1"),  ("main_red","camp_2"),
    ("main_green", "main_red")
]

UNIT_SPEED = {"cavalry":1, "archer":2, "infantry":4}

# ────────── global state ──────────
state   = {}
turn    = 0
winner  = None
events  = []

# ────────── helpers ──────────
def init_game():
    global state, turn, winner
    turn, winner = 0, None
    state = {
        "nodes": {nid:{**v, "owner": None} for nid,v in MAP_NODES.items()},
        "units": [],
        "money_green": 0,
        "money_red":   0,

    }
    events = []
    _spawn_units()

def _spawn_units():
    for team, nid in (("player1","main_green"), ("player2","main_red")):
        for t in ("archer","infantry","cavalry"):
            state["units"].append({
                "id": uuid.uuid4().hex,
                "owner": team,
                "unit_type": t + "s",
                "hp":100, "attack":30, "level":1,
                "unit_count":1,
                "position": nid,
                "path": [nid],
                "steps": 0,
                "x": MAP_NODES[nid]["x"],
                "y": MAP_NODES[nid]["y"],
            })
    # initial income
    state["money_green"] = 10
    state["money_red"]   = 10

def _advance():
    global turn, winner
    turn += 1

    # построение нового пути и назначение шагов
    for u in state["units"]:
        if len(u["path"]) == 1 and turn % 2 == 0:
            cur = u["path"][0]
            neigh = [b for a,b in EDGES if a==cur] + [a for a,b in EDGES if b==cur]
            target = random.choice(neigh)
            u["path"].insert(0, target)
            speed = UNIT_SPEED[u["unit_type"].rstrip("s")]
            # сохраняем параметры анимации
            u["from_x"], u["from_y"] = u["x"], u["y"]
            u["to_x"], u["to_y"] = MAP_NODES[target]["x"], MAP_NODES[target]["y"]
            u["steps"] = speed
            u["total_steps"] = speed

        for u in state["units"]:
            if u.get("steps", 0) > 0:
                u["steps"] -= 1
                progress = (u["total_steps"] - u["steps"]) / u["total_steps"]
                u["x"] = u["from_x"] * (1 - progress) + u["to_x"] * progress
                u["y"] = u["from_y"] * (1 - progress) + u["to_y"] * progress

        # по окончании анимации закрепляем новое положение

                if u["steps"] == 0 and len(u["path"]) > 1:
                    new_pos = u["path"].pop(0)
                    u["position"] = new_pos
                    for k in ("from_x", "from_y", "to_x", "to_y", "total_steps"):
                        u.pop(k, None)

    # проверка победы на основании фактической позиции
    for u in state["units"]:
        if u["position"] == "main_red"  and u["owner"] == "player1":
            winner = "Green"
            events.append("Green captured Red’s main base")
        if u["position"] == "main_green" and u["owner"] == "player2":
            winner = "Red"
            events.append("Red captured Green’s main base")

def _serialize():
    # 1) соберём узлы с owner
    nodes = [
        {
          "id": nid,
          "x": nd["x"],
          "y": nd["y"],
          "type": nd["type"],
          # здесь важно подтягивать кто владеет узлом, например:
          "owner": nd.get("owner"),  # должно быть "player1", "player2" или None
        }
        for nid, nd in MAP_NODES.items()
    ]

    # 2) рёбра
    edges = [
        {"a": a, "b": b}
        for a, b in EDGES
    ]

    # 3) юниты — тоже с owner
    units = []
    for u in state["units"]:
        units.append({
            "position": u["position"],
            "unit_type": u["unit_type"],
            "owner":     u.get("owner"),      # <-- тоже
            "level":     u.get("level", 1),
            "hp":        u.get("hp", 0),
            "attack":    u.get("attack", 0),
            "unit_count":u.get("unit_count", 0),
            "x": u.get("x"),
            "y": u.get("y")
        })

    return {
        "nodes":         nodes,
        "edges":         edges,
        "units":         units,
        "turn":          turn,
        "money_green":   state.get("money_green", 0),
        "money_red":     state.get("money_red",   0),
        "winner":        winner,
        "events": events
    }

# ────────── routes ──────────
@bp.route("/reset", methods=["POST"])
def api_reset():
    init_game()
    return jsonify({"status":"reset", "turn":turn})

@bp.route("/step", methods=["POST"])
def api_step():
    if not winner:
        _advance()
    return jsonify({"status":"ok", "turn":turn})

@bp.route("/state", methods=["GET"])
def api_state():
    return jsonify(_serialize())

# initialize on import
init_game()
