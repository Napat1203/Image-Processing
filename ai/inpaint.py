"""Redraw one clicked part and keep the rest of the photo.

The click grows a mask. White pixels are sent to Forge to be redrawn.
Black pixels stay as they were. The picture is resized to 512 first,
the same size as text-to-image, so a large upload does not reach Forge.
"""

import base64
import io

import numpy as np
from PIL import Image

from ai.forge_client import (
    ForgeError,
    _generate_lock,
    build_txt2img_payload,
    post_to_forge,
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
        payload.update(
            init_images=[png_b64(image)],
            mask=png_b64(mask_image),
            # 0.8 is high enough to draw a new pattern. The mask keeps the rest.
            denoising_strength=0.8,
            mask_blur=4,
            inpainting_fill=1,
            inpaint_full_res=True,
            inpaint_full_res_padding=32,
            inpainting_mask_invert=0,
            resize_mode=0,
        )
        return post_to_forge("/sdapi/v1/img2img", payload, base_url, session)