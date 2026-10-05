"""Find the part a user clicked and paint it a new colour.

One click spreads across neighbouring pixels of a similar colour.
"""

import numpy as np

class SegmentError(Exception):
    pass

# Up, down, left, and right. Diagonal pixels are not neighbours.
# Row 0 is the top of the image, so the pixel above is dy=-1.

NEIGHBOURS_4 = (
    (1, 0),
    (-1, 0),
    (0, -1),
    (0, 1),
)

def parse_color(color):
    """Accept #rrggbb from the page, or r,g,b, or three numbers."""
    if isinstance(color, str) and color.startswith("#"):
        text = color[1:]
        if len(text) != 6:
            raise SegmentError("Color must be red, green, and blue")
        try:
            return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError as exc:
            raise SegmentError("Color must be red, green, and blue") from exc
    parts = color.split(",") if isinstance(color, str) else color
    try:
        rgb = tuple(int(part) for part in parts)
    except (TypeError, ValueError) as exc:
        raise SegmentError("Color must be red, green, and blue") from exc
    if len(rgb) != 3:
        raise SegmentError("Color must be red, green, and blue")
    return rgb

def color_threshold(image, color, max_diff=30):
    """Mark every pixel close to a colour, anywhere in the image.
    Neighbours are ignored. Each channel must fall within max_diff of
    the target, so a grey pixel is not treated as green just because
    it is equally bright.
    """
    image = np.asarray(image)
    if image.ndim != 3:
        raise SegmentError("Need a colour image")
    pixels = image[:, :, :3].astype(np.int16)
    target = np.array(color, dtype=np.int16)
    if target.shape != (3,):
        raise SegmentError("Color must be red, green, and blue")
    distance = np.max(np.abs(pixels - target), axis=2)
    mask = np.zeros(pixels.shape[:2], dtype=np.uint8)
    mask[distance <= max_diff] = 255
    return mask

def grow_part(image, seed_x, seed_y, max_seed=90, max_step=18):
    """Grow one coloured part from a click.

    The new pixel must stay within max_seed of the clicked colour, and
    within max_step of the pixel it spreads from. A small step follows
    a fold but stops at an edge, so a shirt does not run into skin.
    """
    image = np.asarray(image)
    if image.ndim != 3:
        raise SegmentError("Need a colour image")
    height, width = image.shape[:2]
    if not (0 <= seed_x < width and 0 <= seed_y < height):
        raise SegmentError("Seed is outside the image")
    pixels = image[:, :, :3].astype(np.int16)
    seed = pixels[seed_y, seed_x]
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[seed_y, seed_x] = 255
    queue = [(seed_x, seed_y)]
    head = 0
    while head < len(queue):
        x, y = queue[head]
        head += 1
        here = pixels[y, x]
        for dx, dy in NEIGHBOURS_4:
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue
            if mask[ny, nx] == 255:
                continue
            there = pixels[ny, nx]
            if np.max(np.abs(there - seed)) > max_seed:
                continue
            if np.max(np.abs(there - here)) > max_step:
                continue
            mask[ny, nx] = 255
            queue.append((nx, ny))
    return mask

def recolor(image, mask, color):
    """Paint masked pixels in a new colour and keep the old brightness.

    Each pixel is scaled by how bright it already was, so a fold stays
    darker than the cloth around it. Pixels outside the mask are unchanged.
    """
    image = np.asarray(image)
    if image.ndim != 3:
        raise SegmentError("Need a colour image")
    color = np.asarray(color, dtype=np.float32)
    if color.shape != (3,):
        raise SegmentError("Color must be red, green, and blue")
    pixels = image[:, :, :3].astype(np.float32)
    brightness = pixels.mean(axis=2, keepdims=True) / 255
    painted = np.clip(color * brightness, 0, 255).astype(np.uint8)
    keep = np.asarray(mask) != 255
    painted[keep] = pixels[:, :, :3].astype(np.uint8)[keep]
    return painted