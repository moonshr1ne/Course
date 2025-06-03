# project_folder/engine/server.py

from flask import jsonify
from .state import GameState, Node, Edge, UnitGroup
from .game import apply_bot_commands, BASE_COST, get_multiplier  # если нужно

import importlib.util
import os

bot1_path = os.path.join(os.path.dirname(__file__), "bot_player1.py")
bot2_path = os.path.join(os.path.dirname(__file__), "bot_player2.py")

def load_bot(path):
    spec = importlib.util.spec_from_file_location("bot_module", path)
    bot_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bot_module)
    return bot_module.get_action

bot1 = load_bot(bot1_path)
bot2 = load_bot(bot2_path)
gs = None

def init_game():
    global gs
    gs = GameState()
    gs.nodes["main_base_1"] = Node("main_base_1", "main_base", "player1")
    gs.nodes["main_base_2"] = Node("main_base_2", "main_base", "player2")
    gs.nodes["proxy_base_1"] = Node("proxy_base_1", "proxy")
    gs.nodes["proxy_base_2"] = Node("proxy_base_2", "proxy")
    gs.nodes["camp_1"] = Node("camp_1", "camp", "player1")
    gs.nodes["camp_2"] = Node("camp_2", "camp", "player2")

    gs.edges.extend([
        Edge("main_base_1", "proxy_base_1", 1),
        Edge("main_base_1", "proxy_base_2", 1),
        Edge("main_base_2", "proxy_base_1", 1),
        Edge("main_base_2", "proxy_base_2", 1),
        Edge("main_base_1", "camp_1", 1),
        Edge("main_base_2", "camp_2", 1),
        Edge("main_base_1", "main_base_2", 2),
    ])

    for t in ["archers", "swordsmen", "cavalry"]:
        gs.units.append(UnitGroup(t, "player1", "main_base_1"))
        gs.units.append(UnitGroup(t, "player2", "main_base_2"))

def get_state():
    if gs is None:
        init_game()
    data = {
        "turn": gs.turn,
        "nodes": {n: {"owner": node.owner} for n, node in gs.nodes.items()},
        "units": [],
        "player_scores": gs.player_scores,
        "winner": gs.winner
    }
    for u in gs.units:
        pos = u.position[1] if isinstance(u.position, tuple) else u.position
        data["units"].append({
            "unit_type": u.unit_type,
            "owner": u.owner,
            "position": pos,
            "hp": u.hp,
            "attack": u.attack,
            "unit_count": u.unit_count,
            "level": u.level,
            "exp": u.exp
        })
    return jsonify(data)

def step():
    if gs is None:
        init_game()
    state_dict = get_state().json
    cmd1 = bot1(state_dict)
    cmd2 = bot2(state_dict)
    apply_bot_commands(gs, cmd1, cmd2)
    return jsonify({"status": "ok", "turn": gs.turn})

def reset():
    init_game()
    return jsonify({"status": "reset"})
