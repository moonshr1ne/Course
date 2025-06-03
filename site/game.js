// == game.js ==
// Live-визуализация: canvas 1000×700, каждые 1.5 сек делаем POST /step, затем GET /state, рисуем карту и юнитов.
// При получении winner – останавливаем «живой» режим и показываем alert().

let stickman = new Image();
stickman.src = "stickman.png";

let liveInterval = null;

function initGame(container) {
  console.log("[initGame] called");

  // Создаем canvas 1000×700 и вставляем в .game-container
  const canvas = document.createElement("canvas");
  canvas.width = 1000;
  canvas.height = 700;
  canvas.style.position = "absolute";
  canvas.style.top = "0";
  canvas.style.left = "0";

  container.innerHTML = "";
  container.appendChild(canvas);
  const ctx = canvas.getContext("2d");

  // Ждем загрузки stickman.png, а потом первый кадр
  stickman.onload = () => {
    drawLiveState(ctx);
  };
}

function drawLiveState(ctx) {
  console.log("[drawLiveState] fetching /state...");
  fetch("http://localhost:5000/state")
    .then(res => res.json())
    .then(gameState => {
      console.log("[drawLiveState] state received:", gameState);
      drawGameState(gameState, ctx);

      // Если появился winner, останавливаем live-режим и показываем alert
      if (gameState.winner) {
        stopLiveMode();
        setTimeout(() => {
          if (gameState.winner === "player1") {
            alert("Player 1 Wins! Все юниты player2 уничтожены или база захвачена.");
          } else if (gameState.winner === "player2") {
            alert("Player 2 Wins! Все юниты player1 уничтожены или база захвачена.");
          }
        }, 100);
      }
    })
    .catch(err => {
      console.error("[drawLiveState] fetch error:", err);
    });
}

function startLiveMode() {
  const canvas = document.querySelector("canvas");
  if (!canvas) {
    console.warn("No canvas found for live mode");
    return;
  }
  const ctx = canvas.getContext("2d");
  if (liveInterval) return;
  console.log("[startLiveMode] starting interval");
  liveInterval = setInterval(() => {
    console.log("[startLiveMode] posting /step");
    fetch("http://localhost:5000/step", { method: "POST" })
      .then(() => drawLiveState(ctx));
  }, 1500);
}

function stopLiveMode() {
  console.log("[stopLiveMode] stopping interval");
  if (liveInterval) {
    clearInterval(liveInterval);
    liveInterval = null;
  }
}

function resetLiveGame() {
  stopLiveMode();
  console.log("[resetLiveGame] posting /reset");
  fetch("http://localhost:5000/reset", { method: "POST" })
    .then(() => {
      const canvas = document.querySelector("canvas");
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      drawLiveState(ctx);
    });
}

function drawGameState(gameState, ctx) {
  console.log("[drawGameState] drawing state...");

  // 1) Узлы (nodes) с координатами и типом:
  const nodes = {
    main_base_1:  { x: 150, y: 150, type: "main_base" },  // левый верх
    main_base_2:  { x: 850, y: 550, type: "main_base" },  // правый низ
    camp_1:       { x: 150, y: 550, type: "camp" },       // левый низ
    camp_2:       { x: 850, y: 150, type: "camp" },       // правый верх
    proxy_base_1: { x: 400, y: 350, type: "proxy" },      // центр
    proxy_base_2: { x: 600, y: 350, type: "proxy" }
  };

  // 2) Рёбра (edges): границы прямоугольника, диагональ, веточки к лагерям
  const edges = [
    ["main_base_1", "camp_2"],   // верхняя грань
    ["camp_2", "main_base_2"],   // правая грань
    ["main_base_2", "camp_1"],   // нижняя грань
    ["camp_1", "main_base_1"],   // левая грань
    ["main_base_1", "main_base_2"], // диагональ
    ["main_base_1", "camp_1"],   // внутренняя веточка к camp_1
    ["main_base_2", "camp_2"]    // внутренняя веточка к camp_2
  ];

  // 3) Очищаем canvas
  ctx.clearRect(0, 0, 1000, 700);

  // 4) Рисуем рёбра (толстая серая линия)
  ctx.strokeStyle = "#888";
  ctx.lineWidth = 3;
  edges.forEach(([from, to]) => {
    const A = nodes[from];
    const B = nodes[to];
    if (!A || !B) return;
    ctx.beginPath();
    ctx.moveTo(A.x, A.y);
    ctx.lineTo(B.x, B.y);
    ctx.stroke();
  });

  // 5) Рисуем кружки-узлы (arc)
  Object.entries(nodes).forEach(([name, node]) => {
    const owner = gameState.nodes[name]?.owner || null;
    ctx.beginPath();
    ctx.fillStyle = owner === "player1"
      ? "green"
      : owner === "player2"
        ? "red"
        : "gray";
    let radius = 12;
    if (node.type === "main_base") radius = 26;
    else if (node.type === "camp")    radius = 22;
    else if (node.type === "proxy")   radius = 12;
    ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
    ctx.fill();

    // Подпись (имя узла) над кружком
    ctx.fillStyle = "white";
    ctx.font = "12px Arial";
    ctx.textAlign = "center";
    ctx.fillText(name, node.x, node.y - radius - 8);
  });

  // 6) Рисуем юнит-группы (stickman) и их характеристики
  if (stickman.complete) {
    console.log("[drawGameState] drawing units...");
    gameState.units.forEach(unit => {
      const pos = unit.position;
      if (typeof pos !== "string") return;
      const node = nodes[pos];
      if (!node) return;

      // Смещение по X: player1 → +14, player2 → -14
      let offsetX = 0;
      if (unit.owner === "player1") offsetX = +14;
      else if (unit.owner === "player2") offsetX = -14;

      // Рисуем stickman (16×16)
      ctx.drawImage(stickman, node.x + offsetX, node.y - 18, 16, 16);

      // Текстовые характеристики рядом с иконкой
      const textColor = unit.owner === "player1" ? "limegreen" : "orangered";
      ctx.fillStyle = textColor;
      ctx.font = "14px Arial";
      ctx.textAlign = unit.owner === "player1" ? "left" : "right";

      // Строка 1: [Team] (unit_type) (Lv level)
      const teamText = unit.owner === "player1" ? "[Green Team]" : "[Red Team]";
      const typeText = `(${unit.unit_type})`;
      const lvText   = `(Lv ${unit.level})`;

      // Строка 2: HP:…, ATK:…, N:…
      const statsText = `HP:${unit.hp.toFixed(0)} ATK:${unit.attack.toFixed(0)} N:${unit.unit_count}`;

      // Координаты для текста
      const textX  = node.x + offsetX + (unit.owner === "player1" ? 16 : -16);
      const textY1 = node.y - 22;
      const textY2 = node.y - 6;

      // Рисуем первую строку:
      ctx.fillText(`${teamText} ${typeText} ${lvText}`, textX, textY1);
      // Рисуем вторую строку:
      ctx.fillText(statsText, textX, textY2);
    });
  }
}

// При загрузке страницы сразу запускаем initGame
window.onload = () => {
  console.log("[window.onload] page loaded");
  initGame(document.getElementById("gameContainer"));
};
