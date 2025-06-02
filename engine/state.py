import uuid, random

def node(x, y, kind, team=None):
    return {"x": x, "y": y, "kind": kind, "team": team}

def unit(team, kind, node):
    uid = str(uuid.uuid4())[:4]
    return {"id": uid, "team": team, "kind": kind, "hp": 100, "atk": 30, "lvl": 1, "node": node}

gold = {"green": 0, "red": 0}
game = None

def game_reset():
    global game, gold
    gold = {"green": 50, "red": 50}
    game = {
        "turn": 0,
        "nodes": {
            "g_base":  node(80, 80, "base", "green"),
            "r_base":  node(720, 460, "base", "red"),
            "proxy_1": node(80, 460, "proxy"),
            "proxy_2": node(720, 80, "proxy"),
            "camp_1":  node(280, 270, "camp"),
            "camp_2":  node(520, 270, "camp")
        },
        "edges": [
            ("g_base", "proxy_1"), ("g_base", "proxy_2"),
            ("r_base", "proxy_1"), ("r_base", "proxy_2"),
            ("g_base", "camp_1"), ("r_base", "camp_2"),
            ("g_base", "r_base"),
        ],
        "units": [
            unit("green", "cavalry", "g_base"),
            unit("red",   "cavalry", "r_base")
        ]
    }

def income():
    for team in ["green", "red"]:
        gold[team] += 10
    n = game["nodes"]
    if n["proxy_1"]["team"]:
        gold[n["proxy_1"]["team"]] += 5
    if n["proxy_2"]["team"]:
        gold[n["proxy_2"]["team"]] += 5

def buy_units():
    for team in ["green", "red"]:
        if gold[team] >= 30:
            n = "g_base" if team == "green" else "r_base"
            kinds = ["archer", "infantry", "cavalry"]
            k = random.choice(kinds)
            game["units"].append(unit(team, k, n))
            gold[team] -= 30

def move_units():
    for u in game["units"]:
        if u["node"] == "g_base":
            u["node"] = "proxy_2" if u["team"] == "green" else "proxy_1"
        elif u["node"] == "r_base":
            u["node"] = "proxy_1" if u["team"] == "green" else "proxy_2"
        elif u["node"].startswith("proxy"):
            camp = "camp_1" if u["node"] == "proxy_1" else "camp_2"
            u["node"] = camp
        elif u["node"].startswith("camp"):
            base = "r_base" if u["team"] == "green" else "g_base"
            u["node"] = base

def capture_nodes():
    for nid, n in game["nodes"].items():
        teams = {u["team"] for u in game["units"] if u["node"] == nid}
        if len(teams) == 1:
            n["team"] = next(iter(teams))

def game_step():
    income()
    buy_units()
    move_units()
    capture_nodes()
    game["turn"] += 1

def game_state():
    return {"turn": game["turn"], "nodes": game["nodes"], "edges": game["edges"],
            "units": game["units"], "gold": gold}

game_reset()
