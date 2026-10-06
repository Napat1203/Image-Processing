"""Remove a background with the ready-made rembg model.

The model returns a PNG that already has a transparent background.
u2net stays small enough for the notebook CPU.
"""

import threading

from rembg import new_session, remove

_session = None
_lock = threading.Lock()


def remove_background(image_bytes):
    """Return PNG bytes with the background removed."""
    global _session
    if not image_bytes:
        raise ValueError("Image is empty")
    with _lock:
        if _session is None:
            _session = new_session("u2net")
        return remove(image_bytes, session=_session)