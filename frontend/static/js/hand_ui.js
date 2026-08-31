// ดึง DOM Elements
const video = document.getElementById("webcam");
const canvas = document.getElementById("overlay");
const ctx = canvas.getContext("2d");
const statusEl = document.getElementById("hand-status");
let stream = null;
let looping = false;

// นิยามคู่เส้นเชื่อมต่อข้อต่อมือทั้ง 21 จุด (0 - 20)
const HAND_CONNECTIONS = [
  [0, 1], [1, 2], [2, 3], [3, 4],         // นิ้วโป้ง
  [0, 5], [5, 6], [6, 7], [7, 8],         // นิ้วชี้
  [5, 9], [9, 10], [10, 11], [11, 12],     // นิ้วกลาง + ฐาน
  [9, 13], [13, 14], [14, 15], [15, 16],   // นิ้วนาง + ฐาน
  [13, 17], [17, 18], [18, 19], [19, 20], // นิ้วก้อย + ฐาน
  [0, 17]                                 // ฐานฝ่ามือ
];

// ฟังก์ชันวาดเส้นสีเขียวและจุดสีแดงลงบน Canvas
function draw(result) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (!result || !result.landmarks) return;

  for (const hand of result.landmarks) {
    // 1. วาดเส้นเชื่อมต่อสีเขียว (#00ff00)
    ctx.strokeStyle = "#00ff00";
    ctx.lineWidth = 3;
    for (const [i, j] of HAND_CONNECTIONS) {
      const p1 = hand[i];
      const p2 = hand[j];
      if (p1 && p2) {
        ctx.beginPath();
        ctx.moveTo(p1.x * canvas.width, p1.y * canvas.height);
        ctx.lineTo(p2.x * canvas.width, p2.y * canvas.height);
        ctx.stroke();
      }
    }

    // 2. วาดจุดพิกัด Landmark สีแดง (#ff0000)
    ctx.fillStyle = "#ff0000";
    for (const p of hand) {
      ctx.beginPath();
      ctx.arc(p.x * canvas.width, p.y * canvas.height, 5, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

async function loop() {
  if (!looping) return;
  const result = HandAI.detectForVideo(video, performance.now());
  draw(result);

  // เช็กจำนวนมือจากความยาวของ array landmarks โดยตรง
  if (result && result.landmarks && result.landmarks.length > 0) {
    const count = result.landmarks.length;
    let handNames = [];
    if (result.handedness && result.handedness.length > 0) {
      handNames = result.handedness.map((h) => {
        const item = Array.isArray(h) ? h[0] : h;
        return item?.displayName || item?.categoryName || item || "Hand";
      });
    }
    const namesText = handNames.length > 0 ? ": " + handNames.join(", ") : "";
    statusEl.textContent = `เจอ ${count} มือ${namesText}`;
  } else {
    statusEl.textContent = "ยังไม่เจอมือ";
  }

  requestAnimationFrame(loop);
}

document.getElementById("btn-start").onclick = async function () {
  statusEl.textContent = "กำลังโหลดโมเดล...";
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    await video.play();
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    await HandAI.init();
    looping = true;
    loop();
  } catch (err) {
    statusEl.textContent = "พัง: " + err.message;
    console.error(err);
  }
};

document.getElementById("btn-stop").onclick = function () {
  looping = false;
  if (stream) {
    stream.getTracks().forEach(function (t) { t.stop(); });
    stream = null;
  }
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  statusEl.textContent = "หยุดแล้ว";
};