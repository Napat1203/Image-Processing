"""Choose which AI job to run for one uploaded image.

The page sends a model name. Unknown names keep the demo reply so the
current route still works.
"""

import base64


def process(image_bytes, user_id, model=None, prompt=None, already_skeleton=False, x=None, y=None, color=None):
    """Return a result dict. image_bytes is the picture to send back."""
    if model == "remove-background":
        from ai.remove_background import remove_background

        try:
            cut = remove_background(image_bytes)
        except ValueError as exc:
            return {
                "user_id": user_id,
                "status": "error",
                "note": str(exc),
                "image_bytes": b"",
            }
        return {
            "user_id": user_id,
            "status": "ok",
            "note": "Background removed",
            "image_bytes": cut,
        }

    if model == "controlnet":
        if not prompt:
            return {
                "user_id": user_id,
                "status": "error",
                "note": "Enter a prompt first",
                "image_bytes": b"",
            }
        from ai.controlnet import generate_from_pose
        from ai.forge_client import ForgeError

        try:
            picture = generate_from_pose(
                prompt,
                image_bytes,
                already_skeleton=already_skeleton,
            )
        except ForgeError as exc:
            return {
                "user_id": user_id,
                "status": "error",
                "note": str(exc),
                "image_bytes": b"",
            }
        return {
            "user_id": user_id,
            "status": "ok",
            "note": "Pose image generated",
            "image_bytes": base64.b64decode(picture),
        }

    if model == "recolor":
        if x is None or y is None:
            return {
                "user_id": user_id,
                "status": "error",
                "note": "Click the part to change",
                "image_bytes": b"",
            }
        if color is None:
            return {
                "user_id": user_id,
                "status": "error",
                "note": "Choose a color first",
                "image_bytes": b"",
            }
        import io

        import numpy as np
        from PIL import Image

        from ai.segment import SegmentError, grow_part, recolor

        try:
            if isinstance(color, str):
                rgb = tuple(int(part) for part in color.split(","))
            else:
                rgb = tuple(int(part) for part in color)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            pixels = np.array(image)
            mask = grow_part(pixels, int(x), int(y))
            painted = recolor(pixels, mask, rgb)
        except (SegmentError, TypeError, ValueError, OSError) as exc:
            return {
                "user_id": user_id,
                "status": "error",
                "note": str(exc),
                "image_bytes": b"",
            }
        buf = io.BytesIO()
        Image.fromarray(painted).save(buf, format="PNG")
        return {
            "user_id": user_id,
            "status": "ok",
            "note": "Clicked part recolored",
            "image_bytes": buf.getvalue(),
        }

    if model == "inpaint":
        if not prompt:
            return {
                "user_id": user_id,
                "status": "error",
                "note": "Enter a prompt first",
                "image_bytes": b"",
            }
        if x is None or y is None:
            return {
                "user_id": user_id,
                "status": "error",
                "note": "Click the part to change",
                "image_bytes": b"",
            }
        from ai.inpaint import inpaint_part
        from ai.forge_client import ForgeError
        from ai.segment import SegmentError

        try:
            picture = inpaint_part(prompt, image_bytes, x, y)
        except (ForgeError, SegmentError) as exc:
            return {
                "user_id": user_id,
                "status": "error",
                "note": str(exc),
                "image_bytes": b"",
            }
        return {
            "user_id": user_id,
            "status": "ok",
            "note": "Clicked part redrawn",
            "image_bytes": base64.b64decode(picture),
        }

    return {
        "user_id": user_id,
        "status": "ok",
        "note": "(Demo)Image processed successfully!",
        "image_bytes": image_bytes,
    }