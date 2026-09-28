"""Remove a background with the ready-made rembg model.

The model returns a PNG that already has a transparent background.
u2net stays small enough for the notebook CPU.
"""

from rembg import new_session, remove
import threading

_session = None
_generate_lock = threading.Lock()

def remove_background(image_bytes):
    """Return PNG bytes with the background removed."""
    with _generate_lock:

        global _session
        if not image_bytes:
            raise ValueError("Image is empty")
        if _session is None:
            _session = new_session("u2net")
        return remove(image_bytes, session=_session)