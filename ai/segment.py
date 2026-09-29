"""Select a region from a click and drop everything outside it.

One click spreads across neighbouring pixels of similar brightness.
Pixels outside that region become transparent.
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

def to_intensity(image):
    """Average the colour channels so two pixels can be compared by brightness."""
    if image.ndim == 2:
        return image
    return image.mean(axis=2).astype(np.uint8)

def grow_region(image, seed_x, seed_y, max_diff=10):
    """Return a mask grown from one click.

    255 is kept and 0 is outside the region. Brightness is compared with
    the clicked pixel, so the region cannot drift across the whole picture.
    """
    gray = to_intensity(image)
    height, width = gray.shape
    if not (0 <= seed_x < width and 0 <= seed_y < height):
        raise SegmentError("Seed is outside the image")

    seed_value = int(gray[seed_y, seed_x])
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[seed_y, seed_x] = 255
    # Spread outward from the click. A pixel already in the mask is skipped.
    queue = [(seed_x, seed_y)]
    head = 0
    while head < len(queue):
        x, y = queue[head]
        head += 1
        for dx, dy in NEIGHBOURS_4:
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= width or ny < 0 or ny >= height:
                continue
            if mask[ny, nx] == 255:
                continue
            if abs(int(gray[ny, nx]) - seed_value) <= max_diff:
                mask[ny, nx] = 255
                queue.append((nx, ny))
    return mask
                
def grow_from_clicks(image, seeds, max_diff=10):
    """Merge several clicks into one mask.

    One click only covers pixels close to that colour. Skin, hair, and
    clothes need their own clicks.
    """
    gray = to_intensity(np.asarray(image))
    mask = np.zeros(gray.shape, dtype=np.uint8)
    for seed_x, seed_y in seeds:
        part = grow_region(gray, seed_x, seed_y, max_diff=max_diff)
        mask[part == 255] = 255
    return mask

def apply_mask(image, mask):
    """Keep masked pixels and make the rest transparent.

    The mask becomes the alpha channel. 255 stays visible and 0 does not.
    """
    image = np.asarray(image)
    if image.ndim == 2:
        color = np.stack((image, image, image), axis=2)
    else:
        color = image[:, :, :3]
    alpha = np.asarray(mask)
    return np.dstack([color, alpha])


def erode_mask(mask):
    """Remove one layer of pixels from the edge of the mask.
    Pixels on the edge are a blend of the object and the background,
    so a colour test keeps them. Shrinking the mask drops that rim.
    A pixel stays only when it and its four neighbours are inside.
    """

    mask = np.asarray(mask)
    height, width = mask.shape
    shrunk = np.zeros_like(mask)
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if mask[y, x] != 255:
               continue
            inside = True
            for dx, dy in NEIGHBOURS_4:
                if mask[y + dy, x + dx] != 255:
                    inside = False
                    break
            if inside:
                shrunk[y, x] = 255
    return shrunk

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