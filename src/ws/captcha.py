"""Minimal PNG reader and Windscribe slider captcha solver.

Windscribe's API asks for a slider puzzle to be solved on a fresh password
login. The desktop client renders the background image scaled to a 274px wide
widget, lets the user drag the puzzle piece and finally reports the piece's
left position converted back to background image pixels.

This module reproduces that: it decodes both PNGs (pure python, no third party
imaging library), finds the horizontal position where the piece fits and builds
a plausible drag trail in widget coordinates.
"""

import random
import struct
import zlib
from typing import NamedTuple

# widget geometry used by the official client (captchaitem.cpp)
CAPTCHA_WIDTH = 274
SLIDER_RUNNER_RADIUS = 16
SLIDER_HEIGHT = 24
SLIDER_OFFSET_Y = 12
MAX_TRAIL_SIZE = 50


class Image(NamedTuple):
    """Decoded 8 bit image."""

    width: int
    height: int
    gray: bytes
    alpha: bytes


class Solution(NamedTuple):
    """Captcha solution as expected by the api."""

    solution: int
    trail_x: list[float]
    trail_y: list[float]


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter(raw: bytes, width: int, height: int, channels: int) -> bytearray:
    stride = width * channels
    out = bytearray(stride * height)
    pos = 0
    for row in range(height):
        ftype = raw[pos]
        pos += 1
        line = bytearray(raw[pos : pos + stride])
        pos += stride
        base = row * stride
        prev = base - stride
        if ftype == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif ftype == 2:
            if row:
                for i in range(stride):
                    line[i] = (line[i] + out[prev + i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                up = out[prev + i] if row else 0
                line[i] = (line[i] + ((left + up) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                up = out[prev + i] if row else 0
                upleft = out[prev + i - channels] if row and i >= channels else 0
                line[i] = (line[i] + _paeth(left, up, upleft)) & 0xFF
        elif ftype != 0:
            raise ValueError(f"unsupported png filter: {ftype}")
        out[base : base + stride] = line
    return out


def decode_png(blob: bytes) -> Image:
    """Decode an 8 bit, non interlaced PNG into grayscale and alpha planes.

    Args:
        blob (bytes): Raw PNG data.

    Returns:
        Image: The decoded image.

    Raises:
        ValueError: If the PNG uses an unsupported feature.
    """
    if blob[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a png image")

    pos = 8
    header = None
    palette = b""
    trns = b""
    idat = bytearray()
    while pos < len(blob):
        (length,) = struct.unpack(">I", blob[pos : pos + 4])
        ctype = blob[pos + 4 : pos + 8]
        data = blob[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            header = struct.unpack(">IIBBBBB", data)
        elif ctype == b"PLTE":
            palette = data
        elif ctype == b"tRNS":
            trns = data
        elif ctype == b"IDAT":
            idat += data
        elif ctype == b"IEND":
            break

    if header is None:
        raise ValueError("png without IHDR")

    width, height, depth, color, _, _, interlace = header
    if depth != 8 or interlace != 0:
        raise ValueError(f"unsupported png: depth={depth} interlace={interlace}")

    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color)
    if channels is None:
        raise ValueError(f"unsupported png color type: {color}")

    pixels = _unfilter(zlib.decompress(bytes(idat)), width, height, channels)

    count = width * height
    gray = bytearray(count)
    alpha = bytearray(b"\xff" * count)
    for i in range(count):
        off = i * channels
        if color == 0:
            gray[i] = pixels[off]
        elif color == 4:
            gray[i] = pixels[off]
            alpha[i] = pixels[off + 1]
        elif color == 3:
            idx = pixels[off]
            red, green, blue = palette[idx * 3 : idx * 3 + 3]
            gray[i] = (red * 299 + green * 587 + blue * 114) // 1000
            if idx < len(trns):
                alpha[i] = trns[idx]
        else:
            red, green, blue = pixels[off], pixels[off + 1], pixels[off + 2]
            gray[i] = (red * 299 + green * 587 + blue * 114) // 1000
            if color == 6:
                alpha[i] = pixels[off + 3]

    return Image(width, height, bytes(gray), bytes(alpha))


def _find_offset(background: Image, piece: Image, top: int) -> int:
    """Find the piece's left position, in background pixels.

    The hole left in the background is noticeably darker than its surroundings,
    so the piece fits where its opaque pixels cover the darkest area while the
    transparent pixels around it still sit on bright background.

    Args:
        background (Image): Background image with the hole.
        piece (Image): Puzzle piece image.
        top (int): Vertical position of the hole, in background pixels.

    Returns:
        int: Horizontal position of the piece, in background pixels.
    """
    step = 2
    inside: list[tuple[int, int]] = []
    outside: list[tuple[int, int]] = []
    for y in range(0, piece.height, step):
        if not 0 <= top + y < background.height:
            continue
        row = y * piece.width
        for x in range(0, piece.width, step):
            value = piece.alpha[row + x]
            if value > 200:
                inside.append((x, y))
            elif value < 40:
                outside.append((x, y))

    if not inside:
        raise ValueError("puzzle piece is fully transparent")

    # the piece can only be dragged over the widget's usable width
    limit = (CAPTCHA_WIDTH - 2 * SLIDER_RUNNER_RADIUS) * background.width // CAPTCHA_WIDTH
    limit = min(limit, background.width - 1)

    best_offset = 0
    best_score = -1.0
    for offset in range(0, limit + 1):
        dark = 0
        for x, y in inside:
            col = offset + x
            if col >= background.width:
                continue
            dark += background.gray[(top + y) * background.width + col]
        bright = 0
        for x, y in outside:
            col = offset + x
            if col >= background.width:
                continue
            bright += background.gray[(top + y) * background.width + col]

        score = bright / len(outside) - dark / len(inside) if outside else -dark
        if score > best_score:
            best_score = score
            best_offset = offset

    return best_offset


def _build_trail(offset: int, background: Image) -> tuple[list[float], list[float]]:
    """Build a drag trail in widget coordinates.

    Args:
        offset (int): Solution offset in background pixels.
        background (Image): Background image, used for the widget scaling.

    Returns:
        tuple[list[float], list[float]]: The x and y coordinates of the trail.
    """
    scale = CAPTCHA_WIDTH / background.width
    target = offset * scale
    # the runner is grabbed near its centre and lives below the image
    start_x = SLIDER_RUNNER_RADIUS
    runner_y = background.height * scale + SLIDER_OFFSET_Y + SLIDER_HEIGHT / 2

    points = max(12, min(MAX_TRAIL_SIZE, int(target / 5)))
    trail_x: list[float] = []
    trail_y: list[float] = []
    for i in range(1, points + 1):
        progress = i / points
        eased = 1 - (1 - progress) ** 2
        trail_x.append(round(start_x + target * eased + random.uniform(-0.4, 0.4), 3))
        trail_y.append(round(runner_y + random.uniform(-1.5, 1.5), 3))

    trail_x[-1] = round(start_x + target, 3)
    trail_y[-1] = round(runner_y, 3)
    return trail_x, trail_y


def solve(background_png: bytes, slider_png: bytes, top: int) -> Solution:
    """Solve the slider captcha.

    Args:
        background_png (bytes): Background image with the hole.
        slider_png (bytes): Puzzle piece image.
        top (int): Vertical position of the hole, in background pixels.

    Returns:
        Solution: The offset and the drag trail to send to the api.
    """
    background = decode_png(background_png)
    piece = decode_png(slider_png)

    offset = _find_offset(background, piece, top)
    trail_x, trail_y = _build_trail(offset, background)
    return Solution(offset, trail_x, trail_y)


__all__ = ["Image", "Solution", "decode_png", "solve"]
