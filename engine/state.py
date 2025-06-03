# project/engine/state.py

class Node:
    def __init__(self, name, node_type, owner=None):
        self.name = name
        self.node_type = node_type
        self.owner = owner
        self.income = 1  # или другое значение по умолчанию

class Edge:
    def __init__(self, from_node, to_node, travel_time):
        self.from_node = from_node
        self.to_node = to_node
        self.travel_time = travel_time

class UnitGroup:
    def __init__(self, unit_type, owner, position):
        self.unit_type = unit_type   # "archers", "swordsmen", "cavalry"
        self.owner = owner           # "player1" или "player2"
        self.position = position     # строка (имя узла) или кортеж (from,to)
        self.status = 'idle'
        self.turns_remaining = 0
        self.unit_count = 1
        self.hp = 100
        self.attack = 30
        self.level = 1
        self.exp = 0

    def add_unit(self):
        self.unit_count += 1
        factor = 0.99 ** (self.unit_count - 1)
        self.hp = 100 * self.unit_count * factor
        self.attack = 30 * self.unit_count * factor

    def gain_experience(self):
        self.exp += 1
        if self.exp >= self.level * 5:  # пример: на каждый уровень нужно level*5 exp
            self.exp = 0
            self.level += 1
            self.hp *= 1.5  # бонус за уровень
            self.attack *= 1.5

class GameState:
    def __init__(self):
        self.nodes = {}  # name → Node
        self.edges = []  # список Edge
        self.units = []  # список UnitGroup
        self.player_scores = {"player1": 0, "player2": 0}
        self.turn = 0
        self.winner = None
