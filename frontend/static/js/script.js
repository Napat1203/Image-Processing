const themeToggle = document.querySelector(".theme-toggle input");

// Check saved theme
if (themeToggle && localStorage.getItem("theme") === "dark") {
    document.body.classList.add("dark-theme");
    themeToggle.checked = true;
}

// Change theme
if (themeToggle) {
    themeToggle.addEventListener("change", function () {

        if (themeToggle.checked) {
            document.body.classList.add("dark-theme");
            localStorage.setItem("theme", "dark");
        } else {
            document.body.classList.remove("dark-theme");
            localStorage.setItem("theme", "light");
        }

    });
}

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

            selectedModel = option.textContent;

            modelBtn.textContent = selectedModel + " ▼";

            modelMenu.style.display = "none";

        });

    });

}


// ================= Upload Image =================

const chooseFile = document.getElementById("choose-file");
const fileInput = document.getElementById("file-input");
const fileName = document.getElementById("file-name");
const imagePreview = document.getElementById("image-preview");

if (chooseFile && fileInput && fileName) {

    chooseFile.addEventListener("click", function () {
        fileInput.click();
    });
 fileInput.addEventListener("change", function () {

        if (fileInput.files.length > 0) {

            const file = fileInput.files[0];

            // Create image preview
            const imageURL = URL.createObjectURL(file);

            imagePreview.src = imageURL;
            imagePreview.style.display = "block";
            fileName.style.display = "none";
        }

    });

}

// ================= Generate =================

const generateBtn = document.getElementById("generate-btn");
const resultText = document.getElementById("result-text");
const resultImage = document.getElementById("result-image");
const downloadBtn = document.getElementById("download-btn");
const isWebcamPage = !!webcam;
const canvas = document.createElement("canvas");

if (generateBtn && resultText && resultImage) {

    generateBtn.addEventListener("click", function () {

        // Check image
        if (!isWebcamPage && !fileInput.files.length) {
            resultText.textContent = "Please upload an image.";
            resultImage.style.display = "none";
            return;
        }

        // Check webcam
        if (isWebcamPage && !cameraStream) {
            resultText.textContent = "Please start the webcam.";
            resultImage.style.display = "none";
            return;
        }

        if (isWebcamPage && !isFrozen) {
            resultText.textContent = "Please stop the webcam first.";
            resultImage.style.display = "none";
            return;
        }

        // Check model
        if (!selectedModel) {
            resultText.textContent = "Please select an AI model.";
            resultImage.style.display = "none";
            return;
        }

        // Processing
        resultText.textContent = "Processing...";
        resultImage.style.display = "none";

        generateBtn.disabled = true;
        generateBtn.textContent = "Processing...";

        setTimeout(function () {

            resultText.textContent = "";

            //Webcam 
            if (isWebcamPage){

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

                resultImage.src = canvas.toDataURL("image/png");

            }

            //Image Upload
            else {
                resultImage.src = imagePreview.src;
            }

            resultImage.style.display = "block";
            if (downloadBtn){
                downloadBtn.href = resultImage.src;
                downloadBtn.style.display = "inline-block";
            }

            generateBtn.disabled = false;
            generateBtn.textContent = "Generate";

        }, 1500);

    });

}