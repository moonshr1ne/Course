// static/game.js

let liveInterval = null;
const ICONS = {};

function preloadIcons() {
  const names = [
    "green_archer",  "green_base",  "green_camp",  "green_cavalry",
    "green_military","green_proxy",
    "red_archer",    "red_base",    "red_camp",    "red_cavalry",
    "red_military",  "red_proxy",
    "neutral_camp",  "neutral_proxy"
  ];
  for (const name of names) {
    const img = new Image();
    img.src = "/static/icons/" + name + ".png";
    ICONS[name] = img;
  }
}

function drawGameState(gameState, ctx) {
  // Полная очистка канваса
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

  // -----------------------------------------------------------------------
  // 1) Задаём координаты узлов (nodes):
  //    – main_base_1 (зелёная главная база)    = (100, 100)
  //    – proxy_2 (правый верхний прокси-узел)  = (900, 100)
  //    – main_base_2 (красная главная база)    = (900, 600)
  //    – proxy_1 (левый нижний прокси-узел)    = (100, 600)
  //    – camp_1 (зелёный лагерь)              = (350, 350)
  //    – camp_2 (красный лагерь)              = (650, 350)
  // -----------------------------------------------------------------------
  const nodes = {
    main_base_1: { x: 100, y: 100, type: "base" },
    proxy_2:     { x: 900, y: 100, type: "proxy" },
    main_base_2: { x: 900, y: 600, type: "base" },
    proxy_1:     { x: 100, y: 600, type: "proxy" },
    camp_1:      { x: 350, y: 350, type: "camp" },
    camp_2:      { x: 650, y: 350, type: "camp" }
  };

  // -----------------------------------------------------------------------
  // 2) Задаём рёбра (edges). Теперь:
  //    – proxy_1 связан только с обеими базами (main_base_1 & main_base_2)
  //    – proxy_2 связан только с обеими базами (main_base_1 & main_base_2)
  //    – camp_1 связан только с main_base_1
  //    – camp_2 связан только с main_base_2
  //    – main_base_1 ↔ main_base_2 (диагональ)
  // -----------------------------------------------------------------------
  const edges = [
    ["main_base_1", "proxy_1"],
    ["main_base_2", "proxy_1"],
    ["main_base_1", "proxy_2"],
    ["main_base_2", "proxy_2"],
    ["main_base_1", "camp_1"],
    ["main_base_2", "camp_2"],
    ["main_base_1", "main_base_2"]
  ];

  // -----------------------------------------------------------------------
  // 3) Рисуем линии (дороги):
  // -----------------------------------------------------------------------
  ctx.strokeStyle = "#888";
  ctx.lineWidth = 4;
  edges.forEach(([from, to]) => {
    const A = nodes[from];
    const B = nodes[to];
    if (!A || !B) return;
    ctx.beginPath();
    ctx.moveTo(A.x, A.y);
    ctx.lineTo(B.x, B.y);
    ctx.stroke();
  });

  // -----------------------------------------------------------------------
  // 4) Рисуем узлы (иконки) и подписи их имён.
  //
  //    – Размер иконок узлов (base/camp/proxy) = 72×72 (увеличены в 1.5×).
  //    – Цвет зависит от владельца:
  //       owner=player1 → "green_*"
  //       owner=player2 → "red_*"
  //       иначе        → "neutral_*"
  // -----------------------------------------------------------------------
  for (const [name, node] of Object.entries(nodes)) {
    const owner = gameState.nodes[name]?.owner || "neutral";
    const color = owner === "player1"
      ? "green"
      : owner === "player2"
        ? "red"
        : "neutral";

    const iconKey = `${color}_${node.type}`; // e.g. "green_camp"
    const img = ICONS[iconKey];

    // Рисуем иконку (72×72), центрировано по node.x, node.y
    if (img && img.complete && img.naturalWidth > 0) {
      ctx.drawImage(img, node.x - 36, node.y - 36, 72, 72);
    }

    // Подпись имени узла чуть над иконкой
    ctx.fillStyle = "white";
    ctx.font = "12px Arial";
    ctx.textAlign = "center";
    ctx.fillText(name, node.x, node.y - 44);
  }

  // -----------------------------------------------------------------------
  // 5) Рисуем юниты (отряды):
  //
  //    – Если unit.position — строка (например, "camp_1"), берём соответствующий node.
  //    – Цвет команды: player1 → "green", player2 → "red".
  //    – Размер иконки юнита = 54×54 (увеличены в 1.5×).
  //    – Рисуем её чуть выше узловой иконки: (node.x - 27, node.y - 90).
  //    – Над иконкой выводим текст:
  //         [Green Team] (cavalry) Lv … HP:… ATK:… N:…
  //         [Red Team]   (archer)  Lv … HP:… ATK:… N:…
  //      Цвет текста = lime (player1) или orangered (player2).
  // -----------------------------------------------------------------------
  for (const unit of gameState.units) {
    const pos = unit.position;
    if (typeof pos !== "string") continue;
    const node = nodes[pos];
    if (!node) continue;

    // Определяем цвет команды и тип без "s" на конце
    const color = unit.owner === "player1" ? "green" : "red";
    let ut = unit.unit_type;
    if (ut.endsWith("s")) ut = ut.slice(0, -1); // "archers" → "archer"

    const iconKey = `${color}_${ut}`; // e.g. "red_cavalry"
    const img = ICONS[iconKey];

    // Рисуем иконку юнита (54×54), слегка выше узловой иконки
    if (img && img.complete && img.naturalWidth > 0) {
      ctx.drawImage(img, node.x - 27, node.y - 90, 54, 54);
    }

    // Рисуем текст с характеристиками
    ctx.fillStyle = unit.owner === "player1" ? "lime" : "orangered";
    ctx.font = "13px Arial";
    ctx.textAlign = "center";
    const text = `[${unit.owner === "player1" ? "Green Team" : "Red Team"}] ` +
                 `(${ut}) Lv ${unit.level} HP:${Math.round(unit.hp)} ATK:${Math.round(unit.attack)} N:${unit.unit_count}`;
    ctx.fillText(text, node.x, node.y - 104);
  }
}

function startLiveMode() {
  const canvas = document.querySelector("canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (liveInterval) return;

  liveInterval = setInterval(() => {
    fetch("/step", { method: "POST" })
      .then(() => fetch("/state"))
      .then(res => res.json())
      .then(state => {
        drawGameState(state, ctx);
        if (state.winner) {
          clearInterval(liveInterval);
          liveInterval = null;
          if (state.winner === "draw") {
            alert("Ничья! Все юниты уничтожены.");
          } else {
            alert(`${state.winner} победил!`);
          }
        }
      })
      .catch(err => console.error("Ошибка при запросе /step или /state:", err));
  }, 1000);
}

function stopLiveMode() {
  if (liveInterval) {
    clearInterval(liveInterval);
    liveInterval = null;
  }
}

function resetLiveGame() {
  stopLiveMode();
  fetch("/reset", { method: "POST" })
    .then(() => fetch("/state"))
    .then(res => res.json())
    .then(state => {
      const canvas = document.querySelector("canvas");
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      drawGameState(state, ctx);
    })
    .catch(err => console.error("Ошибка при запросе /reset или /state:", err));
}

window.onload = () => {
  preloadIcons();

  const container = document.getElementById("gameContainer");

  // Создаём canvas 1000×700
  const canvas = document.createElement("canvas");
  canvas.width = 1000;
  canvas.height = 700;
  container.appendChild(canvas);

  const ctx = canvas.getContext("2d");
  fetch("/state")
    .then(res => res.json())
    .then(state => {
      drawGameState(state, ctx);
    })
    .catch(err => console.error("Ошибка при первичном запросе /state:", err));
};
