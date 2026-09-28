"""Deterministic, dependency-free RGB PNG fixture illustrations."""

from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path
from typing import Any

from .economics import calculate_economics

CAPTION = "Generated illustration from fixture data, not measured data"
WIDTH, HEIGHT = 800, 450

_FONT = {
    "A": ("010", "101", "111", "101", "101"), "B": ("110", "101", "110", "101", "110"),
    "C": ("011", "100", "100", "100", "011"), "D": ("110", "101", "101", "101", "110"),
    "E": ("111", "100", "110", "100", "111"), "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"), "H": ("101", "101", "111", "101", "101"),
    "I": ("111", "010", "010", "010", "111"), "J": ("001", "001", "001", "101", "010"),
    "K": ("101", "101", "110", "101", "101"), "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"), "N": ("101", "111", "111", "111", "101"),
    "O": ("010", "101", "101", "101", "010"), "P": ("110", "101", "110", "100", "100"),
    "Q": ("010", "101", "101", "111", "011"), "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"), "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"), "V": ("101", "101", "101", "101", "010"),
    "W": ("101", "101", "111", "111", "101"), "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"), "Z": ("111", "001", "010", "100", "111"),
    "0": ("111", "101", "101", "101", "111"), "1": ("010", "110", "010", "010", "111"),
    "2": ("110", "001", "010", "100", "111"), "3": ("110", "001", "010", "001", "110"),
    "4": ("101", "101", "111", "001", "001"), "5": ("111", "100", "110", "001", "110"),
    "6": ("011", "100", "110", "101", "010"), "7": ("111", "001", "010", "010", "010"),
    "8": ("010", "101", "010", "101", "010"), "9": ("010", "101", "011", "001", "110"),
    ":": ("000", "010", "000", "010", "000"), ".": ("000", "000", "000", "000", "010"),
    ",": ("000", "000", "000", "010", "100"), "-": ("000", "000", "111", "000", "000"),
    "/": ("001", "001", "010", "100", "100"), "%": ("101", "001", "010", "100", "101"),
    "=": ("000", "111", "000", "111", "000"), "+": ("000", "010", "111", "010", "000"),
    " ": ("000", "000", "000", "000", "000"),
}


class Canvas:
    def __init__(self, width: int = WIDTH, height: int = HEIGHT) -> None:
        self.width, self.height = width, height
        self.pixels = bytearray([255, 255, 255] * width * height)

    def pixel(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.width + x) * 3
            self.pixels[offset:offset + 3] = bytes(color)

    def rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int], fill: bool = True) -> None:
        if fill:
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    self.pixel(xx, yy, color)
        else:
            self.line(x, y, x + w, y, color); self.line(x, y + h, x + w, y + h, color)
            self.line(x, y, x, y + h, color); self.line(x + w, y, x + w, y + h, color)

    def line(self, x1: int, y1: int, x2: int, y2: int, color: tuple[int, int, int]) -> None:
        dx, dy = abs(x2 - x1), -abs(y2 - y1)
        sx, sy = (1 if x1 < x2 else -1), (1 if y1 < y2 else -1)
        error = dx + dy
        while True:
            self.pixel(x1, y1, color)
            if x1 == x2 and y1 == y2:
                break
            twice = 2 * error
            if twice >= dy:
                error += dy; x1 += sx
            if twice <= dx:
                error += dx; y1 += sy

    def text(self, x: int, y: int, value: str, color: tuple[int, int, int], scale: int = 2) -> None:
        cursor = x
        for char in value.upper():
            glyph = _FONT.get(char, _FONT[" "])
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "1":
                        self.rect(cursor + col * scale, y + row * scale, scale, scale, color)
            cursor += 4 * scale

    def png(self, caption: str = CAPTION) -> bytes:
        raw = b"".join(b"\x00" + bytes(self.pixels[y * self.width * 3:(y + 1) * self.width * 3]) for y in range(self.height))
        def chunk(kind: bytes, data: bytes) -> bytes:
            body = kind + data
            return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">2I5B", self.width, self.height, 8, 2, 0, 0, 0))
                + chunk(b"tEXt", b"Description\x00" + caption.encode("latin-1"))
                + chunk(b"IDAT", zlib.compress(raw, level=9)) + chunk(b"IEND", b""))


def _draw_blocks() -> Canvas:
    canvas = Canvas()
    navy, blue, green, ink = (29, 54, 86), (70, 130, 180), (80, 150, 115), (28, 37, 48)
    canvas.text(28, 28, "FIXTURE TO BRIEFING FLOW", ink, 3)
    boxes = [(35, "SOURCE PACK", navy), (225, "CLAIMS AND", blue), (415, "ARITHMETIC", green), (605, "BRIEFING", navy)]
    for x, label, color in boxes:
        canvas.rect(x, 160, 150, 100, color)
        canvas.text(x + 12, 185, label, (255, 255, 255), 2)
    for x in (185, 375, 565):
        canvas.line(x, 210, x + 28, 210, ink)
        canvas.line(x + 20, 202, x + 28, 210, ink)
        canvas.line(x + 20, 218, x + 28, 210, ink)
    canvas.text(30, 310, "SYNTHETIC DATA / SOURCE TAGS / WORKED NUMBERS", ink, 2)
    canvas.text(28, HEIGHT - 22, CAPTION, ink, 1)
    return canvas


def _draw_bar(pack: dict[str, Any]) -> Canvas:
    canvas = Canvas(); ink, blue, orange = (28, 37, 48), (58, 123, 190), (220, 135, 55)
    rows = [entry for entry in pack["entries"] if entry.get("kind") == "approach"]
    values = [float(entry["throughput_per_second"]) for entry in rows]
    maximum = max(values) or 1
    canvas.text(28, 28, "FIXTURE APPROACH COMPARISON", ink, 3)
    for index, (entry, value) in enumerate(zip(rows, values)):
        y = 130 + index * 100
        canvas.text(35, y, entry["name"][:22], ink, 2)
        canvas.rect(35, y + 30, int(value / maximum * 570), 34, blue if index == 0 else orange)
        canvas.text(620, y + 38, f"{value:g} TPS", ink, 2)
    canvas.text(30, 355, "BAR LENGTH USES FIXTURE THROUGHPUT VALUES", ink, 2)
    canvas.text(28, HEIGHT - 22, CAPTION, ink, 1)
    return canvas


def _draw_cost(pack: dict[str, Any]) -> Canvas:
    canvas = Canvas(); ink, blue, orange, grid = (28, 37, 48), (58, 123, 190), (220, 135, 55), (220, 225, 230)
    economics = calculate_economics(pack)["calculations"]
    approaches = [entry for entry in pack["entries"] if entry.get("kind") == "approach"]
    per_million = [float(next(c["result"] for c in economics if c["id"] == f"{entry['id']}-million-cost")) for entry in approaches]
    canvas.text(28, 28, "FIXTURE WORKLOAD COST CURVES", ink, 3)
    left, top, width, height = 75, 100, 650, 250
    for fraction in (0, .25, .5, .75, 1):
        y = top + int(height * fraction)
        canvas.line(left, y, left + width, y, grid)
    canvas.line(left, top, left, top + height, ink); canvas.line(left, top + height, left + width, top + height, ink)
    max_cost = max(per_million) * 100 or 1
    for index, amount in enumerate(per_million):
        color = blue if index == 0 else orange
        points = []
        for volume in (1, 10, 100):
            x = left + int((volume - 1) / 99 * width)
            y = top + height - int((amount * volume) / max_cost * height)
            points.append((x, y))
        for a, b in zip(points, points[1:]):
            canvas.line(*a, *b, color)
        for x, y in points:
            canvas.rect(x - 4, y - 4, 9, 9, color)
    canvas.text(75, 370, "1M", ink, 2); canvas.text(385, 370, "10M", ink, 2); canvas.text(690, 370, "100M UNITS", ink, 2)
    canvas.text(28, HEIGHT - 22, CAPTION, ink, 1)
    return canvas


def generate_diagrams(pack: dict[str, Any], output_dir: str | Path) -> list[Path]:
    output = Path(output_dir); output.mkdir(parents=True, exist_ok=True)
    images = [
        ("briefing-flow.png", _draw_blocks()),
        ("approach-comparison.png", _draw_bar(pack)),
        ("workload-cost-curves.png", _draw_cost(pack)),
    ]
    paths: list[Path] = []
    for name, canvas in images:
        path = output / name
        path.write_bytes(canvas.png())
        paths.append(path)
    caption_file = output / "captions.json"
    caption_file.write_text(json.dumps({path.name: CAPTION for path in paths}, indent=2) + "\n", encoding="utf-8", newline="\n")
    return paths
