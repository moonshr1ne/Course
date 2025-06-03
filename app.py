# project_folder/app.py

from flask import Flask, send_from_directory
import engine.server  # главные функции взяты из engine/server.py
from mmr import setup_routes

app = Flask(__name__, static_folder="static")

# Подключаем все маршруты из mmr.py
setup_routes(app)

# 1) Главная страница: отдаём index.html из папки static/
@app.route("/")
def serve_index():
    return send_from_directory("static", "index.html")

# 2) API-роуты для игры: делегируем их engine.server.*
@app.route("/state", methods=["GET"])
def get_state():
    return engine.server.get_state()

@app.route("/step", methods=["POST"])
def step():
    return engine.server.step()

@app.route("/reset", methods=["POST"])
def reset():
    return engine.server.reset()

if __name__ == "__main__":
    # Перед стартом сервера инициализируем состояние игры
    engine.server.init_game()
    app.run(debug=True)
