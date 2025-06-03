from state import *
from game import apply_bot_commands
import json
import os

gs = GameState()
gs.nodes['main_base_1'] = Node('main_base_1', 'main_base', 'player1')
gs.nodes['main_base_2'] = Node('main_base_2', 'main_base', 'player2')
gs.nodes['proxy_base_1'] = Node('proxy_base_1', 'proxy')
gs.nodes['proxy_base_2'] = Node('proxy_base_2', 'proxy')
gs.nodes['camp_1'] = Node('camp_1', 'camp', 'player1')
gs.nodes['camp_2'] = Node('camp_2', 'camp', 'player2')

gs.edges.extend([
    Edge('main_base_1', 'proxy_base_1', 1),
    Edge('main_base_1', 'proxy_base_2', 3),
    Edge('main_base_2', 'proxy_base_1', 3),
    Edge('main_base_2', 'proxy_base_2', 1),
    Edge('main_base_1', 'camp_1', 1),
    Edge('main_base_2', 'camp_2', 1),
    Edge('main_base_1', 'main_base_2', 4),
])

for unit_type in ['archers', 'swordsmen', 'cavalry']:
    gs.units.append(UnitGroup(unit_type, 'player1', 'main_base_1'))
    gs.units.append(UnitGroup(unit_type, 'player2', 'main_base_2'))

cmd1 = {
    "archers": {"action": "move", "target": "proxy_base_1"},
    "swordsmen": {"action": "add_unit"},
    "cavalry": {"action": "add_unit"}
}

cmd2 = {
    "archers": {"action": "move", "target": "proxy_base_2"},
    "swordsmen": {"action": "add_unit"},
    "cavalry": {"action": "add_unit"}
}

output_folder = "json_output"
os.makedirs(output_folder, exist_ok=True)

def export_state(game_state, index):
    state = {
        "turn": game_state.turn,
        "nodes": {
            name: {"owner": node.owner} for name, node in game_state.nodes.items()
        },
        "units": [
            {"unit_type": u.unit_type, "owner": u.owner,
             "position": u.position if isinstance(u.position, str) else u.position[1]}
            for u in game_state.units
        ]
    }
    with open(f"{output_folder}/state_{index}.json", "w") as f:
        json.dump(state, f, indent=2)

for i in range(10):
    export_state(gs, i)
    apply_bot_commands(gs, cmd1, cmd2)
