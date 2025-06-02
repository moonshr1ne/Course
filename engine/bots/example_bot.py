# example_bot.py

import requests
import random
import time

# Адрес движка. Если ты менял префикс, поправь его здесь
API_BASE = "http://127.0.0.1:5000/api"

def get_state():
    resp = requests.get(f"{API_BASE}/state")
    resp.raise_for_status()
    return resp.json()

def send_step():
    resp = requests.post(f"{API_BASE}/step")
    resp.raise_for_status()
    return resp.json()

def choose_commands(state):
    """
    Пример очень простого поведения:
      - Для каждого своего отряда ("green") выбираем случайную цель среди узлов.
      - Возвращаем список команд для печати (движок их в данном демо не обрабатывает,
        но ты сможешь сюда в будущем подставить реальные POST-запросы).
    """
    cmds = []
    for u in state["units"]:
        if u["team"] != "green":
            continue
        possible = list(state["nodes"].keys())
        target = random.choice(possible)
        cmds.append({"unit_id": u["id"], "target": target})
    return cmds

if __name__ == "__main__":
    print("Starting example_bot...")
    # Делаем reset, чтобы начать с чистого листа
    requests.post(f"{API_BASE}/reset")
    time.sleep(0.5)

    while True:
        st = get_state()
        cmds = choose_commands(st)
        print(f"Turn {st['turn']} → commands:", cmds)
        send_step()
        if st.get("winner"):
            print("Game over:", st["winner"])
            break
        time.sleep(1)
