"""Redraw one clicked part and keep the rest of the photo.

The click grows a mask. White pixels are sent to Forge to be redrawn.
Black pixels stay as they were. The picture is resized to 512 first,
the same size as text-to-image, so a large upload does not reach Forge.
"""

import base64
import io

import numpy as np
import requests
from PIL import Image

from ai.forge_client import (
    FORGE_URL,
    ForgeError,
    _generate_lock,
    build_txt2img_payload,
    image_from_response,
    prepare_prompt,
)
from ai.segment import SegmentError, grow_part

FORGE_SIZE = 512


def inpaint_part(prompt, image_bytes, x, y, base_url=None, session=None, translator=None):
    """Return a base64 image with only the clicked part redrawn."""
    if not image_bytes:
        raise ForgeError("Image is empty")
    try:
        x = int(x)
        y = int(y)
    except (TypeError, ValueError) as exc:
        raise SegmentError("Click the part to change") from exc
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except (OSError, ValueError) as exc:
        raise ForgeError("Image could not be read") from exc

    mask = grow_part(np.array(image), x, y)
    image = image.resize((FORGE_SIZE, FORGE_SIZE), Image.LANCZOS)
    mask_image = Image.fromarray(mask).resize((FORGE_SIZE, FORGE_SIZE), Image.NEAREST)

    def png_b64(picture):
        buf = io.BytesIO()
        picture.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")

    with _generate_lock:
        text = prepare_prompt(prompt, translator=translator)
        payload = build_txt2img_payload(text)
        payload["init_images"] = [png_b64(image)]
        payload["mask"] = png_b64(mask_image)
        # 0.8 is high enough to draw a new pattern. The mask keeps the rest.
        payload["denoising_strength"] = 0.8
        payload["mask_blur"] = 4
        payload["inpainting_fill"] = 1
        payload["inpaint_full_res"] = True
        payload["inpaint_full_res_padding"] = 32
        payload["inpainting_mask_invert"] = 0
        payload["resize_mode"] = 0
        url = (base_url or FORGE_URL).rstrip("/") + "/sdapi/v1/img2img"
        http = session or requests
        try:
            response = http.post(url, json=payload, timeout=600)
        except requests.RequestException as exc:
            raise ForgeError("Start Forge first, then generate") from exc
        if response.status_code >= 400:
            raise ForgeError("Forge is not accepting requests. Launch it with --api")
        return image_from_response(response.json())