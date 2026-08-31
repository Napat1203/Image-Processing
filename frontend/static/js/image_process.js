const imageInput = document.getElementById("image-input");
const modelSelect = document.getElementById("model-select");
const processButton = document.getElementById("btn-process");
const processStatus = document.getElementById("process-status");

let selectedFile = null;


// ========================================
// เลือกรูปภาพ
// ========================================

imageInput.addEventListener("change", function () {

    const file = this.files[0];

    if (!file) {
        return;
    }

    // ตรวจสอบว่าเป็นไฟล์รูปภาพ
    if (!file.type.startsWith("image/")) {

        processStatus.textContent =
            "กรุณาเลือกไฟล์รูปภาพ";

        selectedFile = null;
        return;
    }

    selectedFile = file;

    processStatus.textContent =
        `เลือกรูปแล้ว: ${file.name}`;
});


// ========================================
// กดปุ่มประมวลผล
// ========================================

processButton.addEventListener("click", async function () {

    // ตรวจสอบว่ามีรูปหรือยัง
    if (!selectedFile) {

        processStatus.textContent =
            "กรุณาเลือกรูปภาพก่อน";

        return;
    }


    // ตรวจสอบ Model
    const model = modelSelect.value;

    if (!model) {

        processStatus.textContent =
            "กรุณาเลือกโมเดล";

        return;
    }


    processStatus.textContent =
        "กำลังส่งข้อมูลไป Backend...";

    processButton.disabled = true;


    try {

        // สร้าง FormData
        const formData = new FormData();

        formData.append("image", selectedFile);
        formData.append("model", model);


        // ส่งไปยัง Flask Frontend
        const response = await fetch(
            "/api/process-image",
            {
                method: "POST",
                body: formData
            }
        );


        // ตรวจสอบ HTTP status
        if (!response.ok) {

            throw new Error(
                `HTTP Error: ${response.status}`
            );
        }


        // อ่าน JSON ที่ Backend ส่งกลับมา
        const result = await response.json();


        if (result.success) {

            processStatus.textContent =
                "ส่งข้อมูลสำเร็จ";

            console.log("Backend response:", result);

        } else {

            processStatus.textContent =
                result.message || "ประมวลผลไม่สำเร็จ";
        }


    } catch (error) {

        console.error("Error:", error);

        processStatus.textContent =
            "ไม่สามารถเชื่อมต่อ Backend ได้";

    } finally {

        processButton.disabled = false;
    }

});