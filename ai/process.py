"""Choose which AI job to run for one uploaded image.

The page sends a model name. Unknown names keep the demo reply so the
current route still works. Each job imports its model only when it runs,
so starting the server does not load rembg or the translator.
"""

import base64

from ai.forge_client import ForgeError
from ai.segment import SegmentError

DEMO_NOTE = "(Demo)Image processed successfully!"


def process(image_bytes, user_id, model=None, prompt=None, already_skeleton=False, x=None, y=None, color=None):
    """Return a result dict. image_bytes is the picture to send back."""
    job = JOBS.get(model)
    if job is None:
        return _reply(user_id, "ok", DEMO_NOTE, image_bytes)
    try:
        note, picture = job(
            image_bytes,
            prompt=prompt,
            already_skeleton=already_skeleton,
            x=x,
            y=y,
            color=color,
        )
    except (ValueError, ForgeError, SegmentError) as exc:
        return _reply(user_id, "error", str(exc))
    return _reply(user_id, "ok", note, picture)


def _reply(user_id, status, note, image_bytes=b""):
    return {
        "user_id": user_id,
        "status": status,
        "note": note,
        "image_bytes": image_bytes,
    }


def _require(value, note):
    # 0 is a real click position, so only None and "" count as missing.
    if value is None or value == "":
        raise ValueError(note)


def _remove_background(image_bytes, **_):
    from ai.remove_background import remove_background

    return "Background removed", remove_background(image_bytes)


def _controlnet(image_bytes, prompt, already_skeleton, **_):
    from ai.controlnet import generate_from_pose

    _require(prompt, "Enter a prompt first")
    picture = generate_from_pose(prompt, image_bytes, already_skeleton=already_skeleton)
    return "Pose image generated", base64.b64decode(picture)


def _recolor(image_bytes, x, y, color, **_):
    import io

    import numpy as np
    from PIL import Image

    from ai.segment import grow_part, parse_color, recolor

    _require(x, "Click the part to change")
    _require(y, "Click the part to change")
    _require(color, "Choose a color first")
    try:
        rgb = parse_color(color)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        pixels = np.array(image)
        mask = grow_part(pixels, int(x), int(y))
        painted = recolor(pixels, mask, rgb)
    except (SegmentError, TypeError, ValueError, OSError) as exc:
        raise SegmentError(str(exc)) from exc
    buf = io.BytesIO()
    Image.fromarray(painted).save(buf, format="PNG")
    return "Clicked part recolored", buf.getvalue()


def _inpaint(image_bytes, prompt, x, y, **_):
    from ai.inpaint import inpaint_part

    _require(prompt, "Enter a prompt first")
    _require(x, "Click the part to change")
    _require(y, "Click the part to change")
    picture = inpaint_part(prompt, image_bytes, x, y)
    return "Clicked part redrawn", base64.b64decode(picture)


JOBS = {
    "remove-background": _remove_background,
    "controlnet": _controlnet,
    "recolor": _recolor,
    "inpaint": _inpaint,
}