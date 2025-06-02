def get_action(state):
    return {
        "archers":   {"action": "move", "target": "camp_2"},
        "swordsmen": {"action": "move", "target": "proxy_base_2"},
        "cavalry":   {"action": "move", "target": "proxy_base_2"}
    }
