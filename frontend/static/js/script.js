// ================= Webcam =================

const startCamera = document.getElementById("start-camera");
const webcam = document.getElementById("webcam");
const stopCamera = document.getElementById("stop-camera");

let cameraStream = null; 
let isFrozen = false;

// Start Camera
if (startCamera && webcam) {

    startCamera.addEventListener("click", async function () {

        // ถ้ากล้องเปิดอยู่ → ปิดกล้อง
        if (cameraStream) {

            cameraStream.getTracks().forEach(function (track) {
                track.stop();
            });

            cameraStream = null;
            webcam.srcObject = null;
            isFrozen = false;
            selectedWebcamPoint = null;
            if (webcamSelectionMarker) webcamSelectionMarker.hidden = true;
            if (colorPicker) colorPicker.style.display = "none";

            startCamera.textContent = "Start";
            stopCamera.textContent = "Stop";

            return;
        }

        // ถ้ากล้องยังไม่เปิด → เปิดกล้อง
        try {

            cameraStream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });

            webcam.srcObject = cameraStream;

            isFrozen = false;
            selectedWebcamPoint = null;
            if (webcamSelectionMarker) webcamSelectionMarker.hidden = true;
            if (colorPicker) colorPicker.style.display = "none";

            startCamera.textContent = "Close";
            stopCamera.textContent = "Stop";
            webcam.play();

        } catch (error) {

            console.error("Camera error:", error);

            alert("Cannot access the webcam.");

        }

    });

}

// Stop / Play Camera
if (stopCamera && webcam) {

    stopCamera.addEventListener("click", function () {

        if (!cameraStream) {
            return;
        }

        if (isFrozen) {

            // Play
            webcam.play();
            isFrozen = false;
            selectedWebcamPoint = null;
            if (webcamSelectionMarker) webcamSelectionMarker.hidden = true;
            if (colorPicker) colorPicker.style.display = "none";
            stopCamera.textContent = "Stop";

        } else {

            // Stop
            webcam.pause();
            isFrozen = true;
            stopCamera.textContent = "Play";

        }

    });

}

// ================= AI Model =================

const modelBtn = document.getElementById("model-btn");
const modelMenu = document.getElementById("model-menu");
const modelOptions = document.querySelectorAll(".model-option");

let selectedModel = "";
if (modelBtn && modelMenu) {

    // Open / Close menu
    modelBtn.addEventListener("click", function () {

        if (modelMenu.style.display === "block") {
            modelMenu.style.display = "none";
        } else {
            modelMenu.style.display = "block";
        }

    });

    // Select Model
    modelOptions.forEach(function (option) {

        option.addEventListener("click", function () {

            selectedModel = option.dataset.model || option.textContent.trim().toLowerCase();

            modelBtn.textContent = option.textContent + " ▼";
            modelMenu.style.display = "none";

            if (!["recolor", "inpaint"].includes(selectedModel)) {
                selectedImagePoint = null;
                if (imageSelectionMarker) imageSelectionMarker.hidden = true;
                selectedWebcamPoint = null;
                if (webcamSelectionMarker) webcamSelectionMarker.hidden = true;
                if (colorPicker) colorPicker.style.display = "none";
            }

            updateControlnetPromptVisibility();

            const currentImage = fileInput?.files?.[0];
            updatePosePreview(currentImage);

        });

    });

}


// ================= Upload Image =================

const chooseFile = document.getElementById("choose-file");
const fileInput = document.getElementById("file-input");
const fileName = document.getElementById("file-name");
const imagePreview = document.getElementById("image-preview");

let selectedImagePoint = null;
let selectedWebcamPoint = null;
let selectedTxtPoint = null;
let imageSelectionMarker = null;
let webcamSelectionMarker = null;

function getMediaPoint(event, element, mediaWidth, mediaHeight, fit = "contain") {
    if (!mediaWidth || !mediaHeight) return null;

    const rect = element.getBoundingClientRect();
    const scale = fit === "cover"
        ? Math.max(rect.width / mediaWidth, rect.height / mediaHeight)
        : Math.min(rect.width / mediaWidth, rect.height / mediaHeight);

    const displayedWidth = mediaWidth * scale;
    const displayedHeight = mediaHeight * scale;
    const offsetX = (rect.width - displayedWidth) / 2;
    const offsetY = (rect.height - displayedHeight) / 2;
    const x = (event.clientX - rect.left - offsetX) / scale;
    const y = (event.clientY - rect.top - offsetY) / scale;

    if (x < 0 || y < 0 || x >= mediaWidth || y >= mediaHeight) {
        return null;
    }

    return { x: Math.floor(x), y: Math.floor(y) };
}

function showSelectionMarker(event, mediaElement, marker) {
    const container = mediaElement.parentElement;
    if (!container) return marker;

    if (!marker) {
        marker = document.createElement("span");
        marker.className = "selection-marker";
        marker.setAttribute("aria-label", "ตำแหน่งที่เลือก");
        container.appendChild(marker);
    }

    const rect = container.getBoundingClientRect();
    marker.style.left = `${event.clientX - rect.left}px`;
    marker.style.top = `${event.clientY - rect.top}px`;
    marker.hidden = false;
    return marker;
}

if (chooseFile && fileInput && fileName) {

    chooseFile.addEventListener("click", function () {
        fileInput.click();
    });
 fileInput.addEventListener("change", function () {

        if (fileInput.files.length > 0) {

            const file = fileInput.files[0];
            selectedImagePoint = null;
            if (imageSelectionMarker) imageSelectionMarker.hidden = true;
            if (colorPicker) colorPicker.style.display = "none";
            updateControlnetPromptVisibility();

            // Create image preview
            const imageURL = URL.createObjectURL(file);

            imagePreview.addEventListener("load", function handlePreviewLoad() {
            updatePosePreview(file);
            }, { once: true });

            imagePreview.src = imageURL;
            imagePreview.style.display = "block";
            fileName.style.display = "none";
        }

    });

}

  // ================= Image Click Position =================

if (imagePreview) {
    imagePreview.addEventListener("click", function (event) {

        if (!["recolor", "inpaint"].includes(selectedModel)) {

            selectedImagePoint = null;
            if (imageSelectionMarker) imageSelectionMarker.hidden = true;
            if (colorPicker) colorPicker.style.display = "none";
            return;
        }

        selectedImagePoint = getMediaPoint(
            event,
            imagePreview,
            imagePreview.naturalWidth,
            imagePreview.naturalHeight,
            "contain"
        );

        if (!selectedImagePoint) {
            if (imageSelectionMarker) imageSelectionMarker.hidden = true;
            if (colorPicker) colorPicker.style.display = "none";
            return;
        }

        imageSelectionMarker = showSelectionMarker(
            event,
            imagePreview,
            imageSelectionMarker
        );
        if (colorPicker) {
            colorPicker.style.display =
                selectedModel === "recolor" ? "grid" : "none";
        }

        const pointInstruction = document.getElementById("point-instruction");
        if (pointInstruction) {
            pointInstruction.hidden = true;
        }

        console.log("Selected image point:", selectedImagePoint);
    });
}

// Webcam point selection uses the frozen video frame.
if (webcam) {
    webcam.addEventListener("click", function (event) {
        if (!["recolor", "inpaint"].includes(selectedModel)) {
            selectedWebcamPoint = null;
            if (webcamSelectionMarker) webcamSelectionMarker.hidden = true;
            if (colorPicker) colorPicker.style.display = "none";
            return;
        }

        if (!isFrozen) {
            alert("Please stop the webcam before selecting a point.");
            return;
        }

        selectedWebcamPoint = getMediaPoint(
            event,
            webcam,
            webcam.videoWidth,
            webcam.videoHeight,
            "cover"
        );

        if (selectedWebcamPoint) {
            webcamSelectionMarker = showSelectionMarker(
                event,
                webcam,
                webcamSelectionMarker
            );
            if (colorPicker) {
                colorPicker.style.display =
                    selectedModel === "recolor" ? "grid" : "none";
            }   
            console.log("Selected webcam point:", selectedWebcamPoint);
        } else if (webcamSelectionMarker) {
            webcamSelectionMarker.hidden = true;
            if (colorPicker) colorPicker.style.display = "none";
        }
    });
}

// ================= Generate =================

const generateBtn = document.getElementById("generate-btn");
const resultText = document.getElementById("result-text");
const resultImage = document.getElementById("result-image");
const downloadBtn = document.querySelector(".result-box .download-btn");
const isWebcamPage = !!webcam;
const canvas = document.createElement("canvas");
const recolorBtn = document.getElementById("recolor-btn");
const colorPicker = document.querySelector(".color-picker");
const colorWheel = document.getElementById("color-wheel");
const selectedColorInput = document.getElementById("selected-color");
const colorPreview = document.getElementById("color-preview");
const colorValue = document.getElementById("color-value");
const controlnetPromptBox = document.getElementById("controlnet-prompt-box");
const controlnetPromptInput = document.getElementById("controlnet-prompt");

const poseOverlay = document.getElementById("pose-overlay");
let posePreviewRequestId = 0;

async function updatePosePreview(imageBlob) {
    const requestId = ++posePreviewRequestId;

    if (!poseOverlay) return;

    if (selectedModel !== "controlnet" || !imageBlob) {
        poseOverlay.hidden = true;
        const context = poseOverlay.getContext("2d");
        context?.clearRect(0, 0, poseOverlay.width, poseOverlay.height);
        return;
    }

    const formData = new FormData();
    formData.append("image", imageBlob, "pose-input.png");

    try {
        const response = await fetch("/api/controlnet/preview", {
            method: "POST",
            body: formData
        });

        const contentType = response.headers.get("content-type") || "";
        if (!response.ok || !contentType.includes("application/json")) {
            throw new Error("Preview API ยังไม่พร้อม หรือส่งข้อมูลกลับมาไม่ใช่ JSON");
        }

        const data = await response.json();

        if (!data.image) {
            throw new Error("คำตอบจาก Preview API ไม่มีข้อมูลภาพ");
        }

        // ไม่วาดผลจากคำขอเก่าทับภาพที่เลือกใหม่
        if (requestId !== posePreviewRequestId) return;

        const previewImage = new Image();

        previewImage.onload = function () {
            if (requestId !== posePreviewRequestId) return;

            poseOverlay.width = previewImage.naturalWidth;
            poseOverlay.height = previewImage.naturalHeight;

            const context = poseOverlay.getContext("2d");
            context.clearRect(0, 0, poseOverlay.width, poseOverlay.height);
            context.drawImage(
                previewImage,
                0,
                0,
                poseOverlay.width,
                poseOverlay.height
            );

            poseOverlay.hidden = false;
        };

        previewImage.onerror = function () {
            console.error("โหลดภาพ ControlNet preview ไม่สำเร็จ");
            poseOverlay.hidden = true;
        };

        previewImage.src = data.image;

    } catch (error) {
        console.error("ControlNet preview error:", error);
        poseOverlay.hidden = true;
    }
}

function updateControlnetPromptVisibility() {
    const needsPrompt = ["controlnet", "inpaint"].includes(selectedModel);

    if (controlnetPromptBox) {
        controlnetPromptBox.hidden = !needsPrompt;

        const label = controlnetPromptBox.querySelector("label");
        if (label) {
            label.textContent =
                selectedModel === "inpaint"
                    ? "Prompt for Inpainting"
                    : "Prompt for ControlNet";
        }
    }

    if (colorPicker) {
        colorPicker.style.display =
            selectedModel === "recolor" && selectedImagePoint
                ? "grid"
                : "none";
    }

    const pointInstruction = document.getElementById("point-instruction");
    if (pointInstruction) {
        pointInstruction.hidden = true;
    }
}

updateControlnetPromptVisibility();

function hslToRgb(h, s, l) {
    const hue = h / 360;
    let r, g, b;

    if (s === 0) {
        r = g = b = l;
    } else {
        const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        const p = 2 * l - q;

        const hueToRgb = (t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1 / 6) return p + (q - p) * 6 * t;
            if (t < 1 / 2) return q;
            if (t < 2 / 3) return p + (q - p) * 6 * (2 / 3 - t);
            return p;
        };

        r = hueToRgb(hue + 1 / 3);
        g = hueToRgb(hue);
        b = hueToRgb(hue - 1 / 3);
    }

    return [
        Math.round(r * 255),
        Math.round(g * 255),
        Math.round(b * 255)
    ];
}

function drawColorWheel() {
    if (!colorWheel) return;

    const ctx = colorWheel.getContext("2d");
    const image = ctx.createImageData(colorWheel.width, colorWheel.height);
    const centerX = colorWheel.width / 2;
    const centerY = colorWheel.height / 2;
    const radius = Math.min(centerX, centerY) - 1;

    for (let y = 0; y < colorWheel.height; y++) {
        for (let x = 0; x < colorWheel.width; x++) {
            const dx = x - centerX;
            const dy = y - centerY;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const index = (y * colorWheel.width + x) * 4;

            if (distance <= radius) {
                const hue =
                    (Math.atan2(dy, dx) * 180 / Math.PI + 360) % 360;
                const saturation = distance / radius;
                const [r, g, b] = hslToRgb(hue, saturation, 0.5);

                image.data[index] = r;
                image.data[index + 1] = g;
                image.data[index + 2] = b;
                image.data[index + 3] = 255;
            }
        }
    }

    ctx.putImageData(image, 0, 0);
}

if (colorWheel && selectedColorInput && colorPreview && colorValue) {
    drawColorWheel();

    colorWheel.addEventListener("click", function (event) {
        const rect = colorWheel.getBoundingClientRect();
        const x = (event.clientX - rect.left) * colorWheel.width / rect.width;
        const y = (event.clientY - rect.top) * colorWheel.height / rect.height;
        const centerX = colorWheel.width / 2;
        const centerY = colorWheel.height / 2;
        const dx = x - centerX;
        const dy = y - centerY;
        const radius = Math.min(centerX, centerY) - 1;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance > radius) return;

        const hue =
            (Math.atan2(dy, dx) * 180 / Math.PI + 360) % 360;
        const saturation = distance / radius;
        const [r, g, b] = hslToRgb(hue, saturation, 0.5);
        const hex = "#" + [r, g, b]
            .map(value => value.toString(16).padStart(2, "0"))
            .join("");

        selectedColorInput.value = hex;
        colorPreview.style.backgroundColor = hex;
        colorValue.textContent = hex;
    });
}

if (generateBtn && resultText && resultImage) {

    generateBtn.addEventListener("click", async function () {

        // Check model
        if (!selectedModel) {
            resultText.textContent = "Please select an AI model.";
            resultImage.style.display = "none";
            return;
        }

        const selectedPoint = isWebcamPage
            ? selectedWebcamPoint
            : selectedImagePoint;

        if (selectedModel === "controlnet" && !controlnetPromptInput?.value.trim()) {
            resultText.textContent = "Please enter a prompt for ControlNet.";
            resultImage.style.display = "none";
            controlnetPromptInput?.focus();
            return;
        } 

        if (selectedModel === "recolor" && !selectedPoint) {
                resultText.textContent = "Click the part of the image you want to recolor first.";
                resultImage.style.display = "none";
                return;
            }

        if (selectedModel === "inpaint") {
            if (!controlnetPromptInput?.value.trim()) {
                resultText.textContent = "Please enter a prompt for Inpainting.";
                resultImage.style.display = "none";
                controlnetPromptInput?.focus();
                return;
            }

            if (!selectedPoint) {
                resultText.textContent =
                    "Click the part of the image you want to redraw first.";
                resultImage.style.display = "none";
                return;
            }
        }

        // ================= Prepare image =================

        let imageBlob;

        // Image page
        if (!isWebcamPage) {

            if (!fileInput.files.length) {
                resultText.textContent = "Please upload an image.";
                resultImage.style.display = "none";
                return;
            }

            imageBlob = fileInput.files[0];

        }

        // Webcam page
        else {

            if (!cameraStream) {
                resultText.textContent = "Please start the webcam.";
                resultImage.style.display = "none";
                return;
            }

            if (!isFrozen) {
                resultText.textContent = "Please stop the webcam first.";
                resultImage.style.display = "none";
                return;
            }

            canvas.width = webcam.videoWidth;
            canvas.height = webcam.videoHeight;

            const ctx = canvas.getContext("2d");

            ctx.drawImage(
                webcam,
                0,
                0,
                canvas.width,
                canvas.height
            );

            imageBlob = await new Promise(function (resolve) {
                canvas.toBlob(resolve, "image/png");
            });
        }

        // ================= Send to AI =================

        resultText.textContent = "Processing...";
        resultImage.style.display = "none";

        generateBtn.disabled = true;
        generateBtn.textContent = "Processing...";

        try {

            const formData = new FormData();
            formData.append("image", imageBlob, "source.png");

            let endpoint = "/api/process-image";

            if (selectedModel === "recolor") {
                endpoint = "/api/recolor";
                formData.append("x", String(selectedPoint.x));
                formData.append("y", String(selectedPoint.y));
                formData.append("color", selectedColorInput.value);
                formData.append("source", isWebcamPage ? "webcam" : "upload");
            } else {
                formData.append("model", selectedModel);

                if (selectedModel === "controlnet" || selectedModel === "inpaint") {
                    formData.append("prompt", controlnetPromptInput.value.trim());
                }

                if (selectedModel === "inpaint") {
                    formData.append("x", String(selectedPoint.x));
                    formData.append("y", String(selectedPoint.y));
                }
            }

            const response = await fetch(endpoint, {
                method: "POST",
                body: formData
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    data.message || "AI processing failed."
                );
            }

            // ================= AI Success =================

            resultText.textContent = data.note || "Processing completed.";

            if (data.image) {
                resultImage.src = "data:image/png;base64," + data.image;
                resultImage.style.display = "block";
            }

            if (downloadBtn) {
                downloadBtn.href = "data:image/png;base64," + data.image;
                downloadBtn.style.display = "inline-flex";
            }

        } catch (error) {

            console.error("AI processing error:", error);

            resultText.textContent =
                error.message || "Something went wrong.";

            resultImage.style.display = "none";

        } finally {

            generateBtn.disabled = false;
            generateBtn.textContent = "Generate";

        }

    });

}

// ================= Recolor Image / Webcam =================

if (recolorBtn && selectedColorInput && resultImage) {
    recolorBtn.addEventListener("click", async function () {
        const point = isWebcamPage
            ? selectedWebcamPoint
            : selectedImagePoint;

        if (!point) {
            alert("Click the part of the image you want to recolor first.");
            return;
        }

        let imageBlob;

        if (isWebcamPage) {
            if (!cameraStream || !isFrozen) {
                alert("Please stop the webcam before recoloring.");
                return;
            }

            canvas.width = webcam.videoWidth;
            canvas.height = webcam.videoHeight;
            const context = canvas.getContext("2d");
            context.drawImage(webcam, 0, 0, canvas.width, canvas.height);

            imageBlob = await new Promise(resolve => {
                canvas.toBlob(resolve, "image/png");
            });
        } else {
            if (!fileInput?.files?.length) {
                alert("Please upload an image first.");
                return;
            }

            imageBlob = fileInput.files[0];
        }

        if (!imageBlob) {
            alert("Could not prepare the image for recoloring.");
            return;
        }

        const formData = new FormData();
        formData.append("image", imageBlob, "source.png");
        formData.append("x", String(point.x));
        formData.append("y", String(point.y));
        formData.append("color", selectedColorInput.value);
        formData.append("source", isWebcamPage ? "webcam" : "upload");

        recolorBtn.disabled = true;
        recolorBtn.textContent = "Recoloring...";
        resultText.textContent = "Recoloring...";

        try {
            const response = await fetch("/api/recolor", {
                method: "POST",
                body: formData
            });
            const data = await response.json();

            if (!response.ok || !data.success || !data.image) {
                throw new Error(data.message || "Recoloring failed.");
            }

            const imageUrl = "data:image/png;base64," + data.image;
            resultImage.src = imageUrl;
            resultImage.style.display = "block";
            resultText.textContent = data.note || "Recoloring completed.";

            if (downloadBtn) {
                downloadBtn.href = imageUrl;
                downloadBtn.style.display = "inline-flex";
            }
        } catch (error) {
            console.error("Recoloring error:", error);
            resultText.textContent = error.message || "Recoloring failed.";
            alert(resultText.textContent);
        } finally {
            recolorBtn.disabled = false;
            recolorBtn.textContent = "Change Color";
        }
    });
}

// ================= TXT2img =================

const promptInput = document.getElementById("prompt-input");
const txtGenerateBtn = document.getElementById("txt-generate-btn");

const generatedResult = document.getElementById("generated-result");
const imageActions = document.getElementById("image-actions");

const editBtn = document.getElementById("edit-btn");
const downloadFirstBtn = document.getElementById("download-first-btn");

const editProcess = document.getElementById("edit-process");
const editGenerateBtn = document.getElementById("edit-generate-btn");

const finalResult = document.getElementById("final-result");
const finalResultImage = document.getElementById("final-result-image");
const finalDownloadBtn = document.getElementById("download-btn");

const txtModelBtn = document.getElementById("txt-model-btn");
const txtModelMenu = document.getElementById("txt-model-menu");
const txtModelOptions = document.querySelectorAll(".txt-model-option");

let txtSelectedModel = "";

// Select a point on the generated image for the TXT2img edit request.
if (promptInput && resultImage) {
    resultImage.addEventListener("click", function (event) {
        selectedTxtPoint = getMediaPoint(
            event,
            resultImage,
            resultImage.naturalWidth,
            resultImage.naturalHeight,
            "contain"
        );

        if (selectedTxtPoint) {
            console.log("Selected TXT2img point:", selectedTxtPoint);
        }
    });
}


// ================= First Generate =================
if (promptInput) {

    promptInput.addEventListener("click", function () {

        // ถ้ายังไม่มีข้อความ
        if (this.value === "") {
            this.setSelectionRange(0, 0);
        }

    });

}

if (promptInput && txtGenerateBtn) {
    txtGenerateBtn.addEventListener("click", async function () {
        const prompt = promptInput.value.trim();

        if (!prompt) {
            alert("Please enter a prompt.");
            return;
        }

        txtGenerateBtn.disabled = true;
        txtGenerateBtn.textContent = "Generating...";
        selectedTxtPoint = null;
        resultImage.style.display = "none";

        try {
            const response = await fetch("/api/txt2img/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt })
            });

            const data = await response.json();

            if (!response.ok || !data.success || !data.image) {
                throw new Error(data.message || "Image generation failed.");
            }

            const imageUrl = "data:image/png;base64," + data.image;
            resultImage.src = imageUrl;
            resultImage.style.display = "block";
            generatedResult.style.display = "flex";
            imageActions.style.display = "flex";
            editBtn.style.display = "inline-flex";

            downloadFirstBtn.href = imageUrl;
            downloadFirstBtn.style.display = "inline-flex";
        } catch (error) {
            alert(error.message || "Image generation failed.");
        } finally {
            txtGenerateBtn.disabled = false;
            txtGenerateBtn.textContent = "Generate";
        }
    });
}

// ================= Edit Image =================

if (editBtn && editProcess) {
    editBtn.addEventListener("click", function () {
        editProcess.style.display = "flex";
        editBtn.style.display = "none";

        downloadFirstBtn.style.display = "none";
    });
}

// ================= TXT2img Model =================

if (txtModelBtn && txtModelMenu) {

    txtModelBtn.addEventListener("click", function () {

        if (txtModelMenu.style.display === "block") {
            txtModelMenu.style.display = "none";
        } else {
            txtModelMenu.style.display = "block";
        }

    });

    txtModelOptions.forEach(function (option) {

        option.addEventListener("click", function () {

            txtSelectedModel = option.dataset.model || option.textContent;

            txtModelBtn.textContent =
                option.textContent + " ▼";

            txtModelMenu.style.display = "none";

        });

    });

}
// ================= Edit Generate =================

if (editGenerateBtn && promptInput && resultImage && finalResultImage) {
    editGenerateBtn.addEventListener("click", async function () {
        if (!selectedTxtPoint) {
            alert("Click a point on the generated image first.");
            return;
        }

        if (!txtSelectedModel) {
            alert("Please select an AI model.");
            return;
        }

        const payload = {
            image_url: resultImage.currentSrc || resultImage.src,
            x: selectedTxtPoint.x,
            y: selectedTxtPoint.y,
            model: txtSelectedModel,
            prompt: promptInput.value.trim()
        };

        editGenerateBtn.disabled = true;
        editGenerateBtn.textContent = "Generating...";

        try {
            const response = await fetch("/api/txt2img/edit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await response.json();

            if (!response.ok || (!data.image_url && !data.image)) {
                throw new Error(data.message || "Image editing failed.");
            }

            const outputUrl = data.image_url ||
                "data:image/png;base64," + data.image;
            finalResultImage.src = outputUrl;
            finalResult.style.display = "flex";

            if (finalDownloadBtn) {
                finalDownloadBtn.href = outputUrl;
                finalDownloadBtn.style.display = "inline-flex";
            }
        } catch (error) {
            console.error("TXT2img edit error:", error);
            alert(error.message || "Image editing failed.");
        } finally {
            editGenerateBtn.disabled = false;
            editGenerateBtn.textContent = "Generate";
        }
    });
}
