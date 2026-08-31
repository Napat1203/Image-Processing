import {
  HandLandmarker,
  FilesetResolver,
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14";

let handLandmarker;

async function init() {
  const vision = await FilesetResolver.forVisionTasks(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
  );

  handLandmarker = await HandLandmarker.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: "/static/models/hand_landmarker.task",
    },
    runningMode: "VIDEO",
    numHands: 2,
  });

  HandAI.isReady = true;
}

function detectForVideo(video, timestamp) {
  if (!video.videoWidth) return { landmarks: [] };
  return handLandmarker.detectForVideo(video, timestamp);
}

const HandAI = { init, detectForVideo, isReady: false };
window.HandAI = HandAI;
