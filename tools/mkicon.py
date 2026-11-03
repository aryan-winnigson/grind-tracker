#!/usr/bin/env python3
"""Render the grind-tracker app icons as PNGs, no image libraries needed.

The mark is the year-at-a-glance strip from the app itself: a grid of day
cells on the app's dark ink colour, a few of them filled in.
"""
import struct, zlib, sys

INK = (0x16, 0x22, 0x3A)
FILL_A = (0xF4, 0xDD, 0x4C)   # highlight yellow
FILL_B = (0x7E, 0xA6, 0xEE)   # light accent blue
FILL_C = (0x4E, 0xC0, 0x84)   # green, for "on time"
EMPTY = (0x32, 0x42, 0x63)

SS = 3  # supersampling factor


def rounded_rect_cov(px, py, x, y, w, h, r):
    """Coverage test for a point inside a rounded rectangle."""
    if px < x or py < y or px > x + w or py > y + h:
        return False
    cx = min(max(px, x + r), x + w - r)
    cy = min(max(py, y + r), y + h - r)
    return (px - cx) ** 2 + (py - cy) ** 2 <= r * r


def render(size, maskable=False):
    S = size * SS
    # The rounded corners are supplied by the OS for maskable icons.
    bg_r = 0 if maskable else S * 0.22
    # Maskable icons must keep their content inside the middle 80%.
    inset = S * 0.26 if maskable else S * 0.18
    grid = S - 2 * inset
    n = 4
    gap = grid * 0.085
    cell = (grid - gap * (n - 1)) / n
    cr = cell * 0.26

    pattern = [
        [FILL_A, FILL_C, EMPTY, EMPTY],
        [FILL_C, FILL_A, FILL_B, EMPTY],
        [FILL_B, FILL_C, FILL_A, FILL_C],
        [FILL_C, EMPTY, FILL_C, FILL_A],
    ]

    cells = []
    for row in range(n):
        for col in range(n):
            cells.append((inset + col * (cell + gap), inset + row * (cell + gap), pattern[row][col]))

    rows = []
    for y in range(size):
        line = bytearray()
        for x in range(size):
            rs = gs = bs = as_ = 0
            for sy in range(SS):
                for sx in range(SS):
                    px = x * SS + sx + 0.5
                    py = y * SS + sy + 0.5
                    if bg_r and not rounded_rect_cov(px, py, 0, 0, S, S, bg_r):
                        continue  # outside the badge: transparent
                    col = INK
                    for (cxp, cyp, c) in cells:
                        if rounded_rect_cov(px, py, cxp, cyp, cell, cell, cr):
                            col = c
                            break
                    rs += col[0]; gs += col[1]; bs += col[2]; as_ += 255
            t = SS * SS
            line += bytes((rs // t, gs // t, bs // t, as_ // t))
        rows.append(bytes(line))

    raw = b"".join(b"\x00" + r for r in rows)
    return png(size, size, raw)


def png(w, h, raw):
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


if __name__ == "__main__":
    out = sys.argv[1]
    for name, size, mask in [("icon-192.png", 192, False), ("icon-512.png", 512, False),
                             ("icon-maskable-512.png", 512, True), ("apple-touch-icon.png", 180, False)]:
        with open(f"{out}/{name}", "wb") as f:
            f.write(render(size, mask))
        print("wrote", name, size)
