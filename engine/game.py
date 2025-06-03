# project/engine/game.py

from .state import *  # относительный импорт
import math

BASE_COST = {
    'archers': 50,
    'swordsmen': 80,
    'cavalry': 100
}

def find_edge(game_state, from_node, to_node):
    for edge in game_state.edges:
        if (edge.from_node, edge.to_node) == (from_node, to_node) or \
           (edge.to_node, edge.from_node) == (from_node, to_node):
            return edge
    return None

def get_travel_time(unit, edge):
    base = edge.travel_time
    if unit.unit_type == 'cavalry':
        return base * 1
    elif unit.unit_type == 'archers':
        return base * 2
    elif unit.unit_type == 'swordsmen':
        return base * 4
    else:
        return base

def get_multiplier(attacker_type, defender_type):
    if attacker_type == 'archers' and defender_type == 'swordsmen':
        return 1.5
    if attacker_type == 'swordsmen' and defender_type == 'cavalry':
        return 1.5
    if attacker_type == 'cavalry' and defender_type == 'archers':
        return 1.5
    if defender_type == 'archers' and attacker_type == 'swordsmen':
        return 0.75
    if defender_type == 'swordsmen' and attacker_type == 'cavalry':
        return 0.75
    if defender_type == 'cavalry' and attacker_type == 'archers':
        return 0.75
    return 1.0

def process_moving_combat(game_state):
    for i, u in enumerate(game_state.units):
        if u.status != 'moving':
            continue
        pos_u = u.position
        for j, v in enumerate(game_state.units):
            if j <= i or v.status != 'moving':
                continue
            pos_v = v.position
            if isinstance(pos_u, tuple) and isinstance(pos_v, tuple) and \
               pos_u[0] == pos_v[1] and pos_u[1] == pos_v[0]:
                mult_uv = get_multiplier(u.unit_type, v.unit_type)
                mult_vu = get_multiplier(v.unit_type, u.unit_type)
                damage_to_u = v.attack * mult_vu
                damage_to_v = u.attack * mult_uv
                u.hp -= damage_to_u
                v.hp -= damage_to_v

    survivors = []
    for u in game_state.units:
        if u.hp <= 0:
            print(f"[LOG] Unit died on road: ({u.owner} - {u.unit_type})")
        else:
            survivors.append(u)
    game_state.units = survivors

def move_unit(game_state, unit, target_node_name):
    if isinstance(unit.position, tuple):
        return
    edge = find_edge(game_state, unit.position, target_node_name)
    if not edge:
        return
    unit.status = 'moving'
    unit.turns_remaining = get_travel_time(unit, edge)
    unit.position = (unit.position, target_node_name)

def update_unit_positions(game_state):
    for unit in game_state.units:
        if unit.status == 'moving':
            unit.turns_remaining -= 1
            if unit.turns_remaining <= 0:
                unit.position = unit.position[1]
                unit.status = 'idle'

def process_income(game_state):
    for node in game_state.nodes.values():
        if node.owner:
            game_state.player_scores[node.owner] += node.income

def process_combat_at_nodes(game_state):
    location_map = {}
    for unit in game_state.units:
        if isinstance(unit.position, str):
            location_map.setdefault(unit.position, []).append(unit)

    for units in location_map.values():
        players = set(u.owner for u in units)
        if len(players) > 1:
            for u in units:
                total_damage = 0
                for v in units:
                    if v.owner != u.owner:
                        mult = get_multiplier(v.unit_type, u.unit_type)
                        total_damage += v.attack * mult
                u.hp -= total_damage

    survivors = []
    for u in game_state.units:
        if u.hp <= 0:
            print(f"[LOG] Unit died at node: ({u.owner} - {u.unit_type}) at position '{u.position}'")
        else:
            survivors.append(u)
    game_state.units = survivors

def process_base_capture(game_state):
    for node in game_state.nodes.values():
        if node.node_type in ['proxy', 'camp']:
            present = [u for u in game_state.units if u.position == node.name]
            owners = set(u.owner for u in present)
            if len(owners) == 1:
                node.owner = owners.pop()

def process_training_in_camps(game_state):
    for unit in game_state.units:
        if isinstance(unit.position, str) and game_state.nodes[unit.position].node_type == 'camp':
            camp = game_state.nodes[unit.position]
            if camp.owner == unit.owner:
                unit.gain_experience()

def check_victory_conditions(game_state):
    for node in game_state.nodes.values():
        if node.node_type == 'main_base':
            defenders = [u for u in game_state.units
                         if u.position == node.name and u.owner == node.owner]
            invaders = [u for u in game_state.units
                        if u.position == node.name and u.owner != node.owner]
            if node.owner and not defenders and invaders:
                game_state.winner = invaders[0].owner
                return

    has_p1 = any(u.owner == 'player1' for u in game_state.units)
    has_p2 = any(u.owner == 'player2' for u in game_state.units)

    if not has_p1 and not has_p2:
        game_state.winner = "draw"
        return
    if not has_p1 and has_p2:
        game_state.winner = 'player2'
        return
    if not has_p2 and has_p1:
        game_state.winner = 'player1'
        return

def apply_bot_commands(game_state, commands_player1, commands_player2):
    all_cmds = {'player1': commands_player1, 'player2': commands_player2}
    for player, cmds in all_cmds.items():
        for unit_type, command in cmds.items():
            unit = next((u for u in game_state.units
                         if u.unit_type == unit_type and u.owner == player and u.status == 'idle'), None)
            if not unit:
                continue
            if command['action'] == 'move':
                move_unit(game_state, unit, command['target'])
            elif command['action'] == 'add_unit':
                current_count = unit.unit_count
                base = BASE_COST[unit_type]
                cost = math.ceil(base * (1.15 ** current_count))
                if game_state.player_scores[player] >= cost:
                    game_state.player_scores[player] -= cost
                    unit.add_unit()
                else:
                    print(f"[LOG] {player} tried to buy '{unit_type}' but only has {game_state.player_scores[player]} points; needs {cost}.")

    process_moving_combat(game_state)
    update_unit_positions(game_state)
    process_combat_at_nodes(game_state)
    process_base_capture(game_state)
    process_training_in_camps(game_state)
    process_income(game_state)
    check_victory_conditions(game_state)
    game_state.turn += 1
