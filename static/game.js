/* globals fetch, document, alert */
let loopId = null, ctx = null;
const ICONS = {};

const RESET_URL = window.RESET_URL || '/api/reset';
const STEP_URL  = window.STEP_URL  || '/api/step';
const STATE_URL = window.STATE_URL || '/api/state';


console.log('game.js loaded')

// 1. preload all icons
function loadIcons() {
  // узлы
  for (const color of ["green","red"]) {
    for (const kind of ["base","proxy","camp"]) {
      const name = `${color}_${kind}`;
      ICONS[name] = Object.assign(new Image(), {
        src: `/static/icons/${name}.png`
      });
    }
  }
  // только прокси и лагеря могут быть нейтральными
  for (const kind of ["proxy","camp"]) {
    const name = `neutral_${kind}`;
    ICONS[name] = Object.assign(new Image(), {
      src: `/static/icons/${name}.png`
    });
  }

  // юниты
  for (const color of ["green","red"]) {
    for (const unit of ["archer","cavalry","military"]) {
      const name = `${color}_${unit}`;
      ICONS[name] = Object.assign(new Image(), {
        src: `/static/icons/${name}.png`
      });
    }
  }
}



// 2. create and mount canvas
function setupCanvas() {
  const box = document.getElementById("gameContainer");
  box.innerHTML = ""; // clear any old canvas
  const c = document.createElement("canvas");
  c.width  = 1100;
  c.height = 700;
  box.appendChild(c);
  ctx = c.getContext("2d");
}

// 3. draw entire state
// 3. draw entire state
function draw(state) {
  if (!ctx) return;
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);

  // 1) Рисуем рёбра
  ctx.strokeStyle = "#888";
  ctx.lineWidth   = 4;
  state.edges.forEach(e => {
    const A = state.nodes.find(n => n.id === e.a);
    const B = state.nodes.find(n => n.id === e.b);
    if (!A || !B) return;
    ctx.beginPath();
    ctx.moveTo(A.x, A.y);
    ctx.lineTo(B.x, B.y);
    ctx.stroke();
  });


  // 2) Рисуем узлы
  state.nodes.forEach(n => {
    let owner;
    if (n.type === "main_base") {
      owner = n.id.includes("main_green") ? "green" : "red";
    } else {
      owner = n.owner === "player1" ? "green"
            : n.owner === "player2" ? "red"
            : "neutral";
    }
    const kind = n.type === "main_base" ? "base" : n.type;
    const img  = ICONS[`${owner}_${kind}`];
    if (img?.complete) {
      ctx.drawImage(img, n.x - 36, n.y - 36, 72, 72);
    }
    ctx.fillStyle = "#fff";
    ctx.font      = "14px Arial";
    ctx.textAlign = "center";
    ctx.fillText(n.id.replace(/_/g, " "), n.x, n.y - 48);
  });

  // 3) Рисуем юниты
   state.units
    .filter(u => u.unit_count > 0)
    .forEach(u => {
    const drawX = u.x;
    const drawY = u.y;
    const col = u.owner === "player1" ? "green" : "red";
    let ut = u.unit_type.endsWith("s") ? u.unit_type.slice(0, -1) : u.unit_type;
      if (ut === "infantry") ut = "military";
      const imgUnit = ICONS[`${col}_${ut}`];
      if (imgUnit?.complete) {
        ctx.drawImage(imgUnit, drawX - 27, drawY - 80, 54, 54);
      }
      ctx.fillStyle = col === "green" ? "lime" : "orangered";
      ctx.font      = "12px Arial";
      ctx.textAlign = "center";
      const txt = `${ut} N:${u.unit_count} Lv:${u.level}`
                + ` HP:${Math.round(u.hp)} ATK:${Math.round(u.attack)}`;
      ctx.fillText(txt, drawX, drawY - 88);
    }); // ← обязательно закрываем forEach здесь

  // 4) HUD
  document.getElementById("moneyG").textContent = state.money_green ?? 0;
  document.getElementById("moneyR").textContent = state.money_red   ?? 0;
  document.getElementById("turnN") .textContent = state.turn;
} // ← закрываем функцию draw





// 4. helper to call your endpoints
async function callUrl(url, method="GET") {
  const r = await fetch(url, { method });
  if (!r.ok) throw new Error(`${url} → ${r.status}`);
  return r.json();
}

// 5. button handlers
async function onStart() {
  // стоп старого цикла
  if (loopId) { clearInterval(loopId); loopId = null; }
  // сброс на сервере
  await callUrl(RESET_URL, "POST");
  // запустить цикл шагов
  loopId = setInterval(async () => {
    await callUrl(STEP_URL, "POST");
    const st = await callUrl(STATE_URL);
    draw(st);
    if (st.winner) {
      clearInterval(loopId);
      loopId = null;
      const reason = (st.events?.length) ? st.events[0] : '';
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            alert(`${st.winner} wins${reason ? ' — ' + reason : ''}!`);
     });
    })
   }
  }, 1400);
}

function onStop() {
  if (loopId) {
    clearInterval(loopId);
    loopId = null;
  }
}

async function onReset() {
  // 1) Останавливаем текущий цикл шагов, если он идёт
  if (loopId) {
    clearInterval(loopId);
    loopId = null;
  }
  // 2) Запрашиваем сброс состояния на сервере
  await callUrl(RESET_URL, "POST");
  // 3) Получаем вновь инициализированное состояние и рисуем его
  const st = await callUrl(STATE_URL);
      draw(st);
 }

// 6. wire it all up
window.addEventListener("DOMContentLoaded", async () => {
  loadIcons();
  setupCanvas();

  // навешиваем кнопки
  document.getElementById("btnStart").onclick = onStart;
  document.getElementById("btnStop") .onclick = onStop;
  document.getElementById("btnReset").onclick = onReset;

  // === авто-reset при заходе ===
  try {
    await callUrl(RESET_URL, "POST");
  } catch (err) {
    console.error("Auto-reset failed:", err);
  }
  // после сброса запрашиваем текущее состояние и рисуем
  const st = await callUrl(STATE_URL);
  draw(st);

  // (не стартуем цикл шагов — он стартует только по кнопке Start)
});

