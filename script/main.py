import math
from PIL import Image, ImageDraw
import tomllib
import argparse
import os
from pprint import pprint

PRESET_LAYOUT_1 = """\
[dimension]
width = 595
height = 842

[margin]
top = 10
bottom = 10
left = 10
right = 10

[[guides]]
angle = 55.624
spacing = 10
lines = [{ color = 0xD9D9D9, width = 0 }]

[[guides]]
angle = 0
spacing = 0
lines = [
  { color = 0xD9D9D9, width = 0 },
  { gap = 7 },
]
"""

PRESET_LAYOUT_2 = """\
[dimension]
width = 595
height = 842

[margin]
top = 10
bottom = 10
left = 10
right = 10

[[guides]]
angle = 55.624
spacing = 10
lines = [{ color = 0xD9D9D9, width = 0 }]

[[guides]]
angle = 0
spacing = 3
lines = [
  { color = 0xD9D9D9, width = 0 },
  { gap = 7 },
  { color = 0xDDDDDD, width = 0 },
  { gap = 7 },
  { color = 0xDDDDDD, width = 0 },
  { gap = 7 },
  { color = 0xD9D9D9, width = 0 },
]
"""

PRESET_LAYOUT_3 = """\
[dimension]
width = 595
height = 842

[margin]
top = 10
bottom = 10
left = 10
right = 10

[[guides]]
angle = 55.624
spacing = 10
lines = [{ color = 0xD9D9D9, width = 0 }]

[[guides]]
angle = 0
spacing = 3
lines = [
  { color = 0xD9D9D9, width = 0 },
  { gap = 7 },
  { color = 0xDDDDDD, width = 0 },
  { gap = 7 },
  { color = 0xDDDDDD, width = 0 },
  { gap = 7 },
  { color = 0xDDDDDD, width = 0 },
  { gap = 7 },
  { color = 0xDDDDDD, width = 0 },
  { gap = 7 },
  { color = 0xD9D9D9, width = 0 },
]
"""

PRESETS = [PRESET_LAYOUT_1, PRESET_LAYOUT_2, PRESET_LAYOUT_3]


def draw(layout: dict, output_file: str, quality: int):
    p_span_x = layout["dimension"]["width"]
    p_span_y = layout["dimension"]["height"]
    margin_top = layout["margin"]["top"]
    margin_bot = layout["margin"]["bottom"]
    margin_lft = layout["margin"]["left"]
    margin_rgt = layout["margin"]["right"]

    im = Image.new("RGB", (p_span_x, p_span_y), 0xFFFFFF)
    draw = ImageDraw.Draw(im)

    def rotc(angle, x0, y0) -> tuple[int, int]:
        xc, yc = p_span_x / 2, p_span_y / 2
        angle *= -1
        x1 = ((x0 - xc) * math.cos(angle)) - ((y0 - yc) * math.sin(angle)) + xc
        y1 = ((x0 - xc) * math.sin(angle)) + ((y0 - yc) * math.cos(angle)) + yc
        return (round(x1, 3), round(y1, 3))

    def pdist(angle: float, x1: float, y1: float, x2: float, y2: float):
        angle *= -1
        m = math.tan(angle)
        c1 = (-m * x1) + y1
        c2 = (-m * x2) + y2
        d = abs(c1 - c2) / math.sqrt(1 + (m * m))
        return round(d, 3)

    def pp2mr(pa: tuple[float, float], pb: tuple[float, float]):
        xa, ya = pa[0], pa[1]
        xb, yb = pb[0], pb[1]
        if (xb - xa) == 0:
            m = 0
        else:
            m = (yb - ya) / (xb - xa)
        return (-m, 1, ya - (m * xa))

    def lalg(
        mr1: tuple[float, float, float],
        mr2: tuple[float, float, float],
    ):
        x1, y1, c1 = mr1[0], mr1[1], mr1[2]
        x2, y2, c2 = mr2[0], mr2[1], mr2[2]
        if (det := (x1 * y2) - (x2 * y1)) == 0:
            return None

        ax1, ay1 = y2, -y1
        ax2, ay2 = -x2, x1
        ix1, iy1 = (1 / det) * ax1, (1 / det) * ay1
        ix2, iy2 = (1 / det) * ax2, (1 / det) * ay2

        sx = (ix1 * c1) + (iy1 * c2)
        sy = (ix2 * c1) + (iy2 * c2)
        return (sx, sy)

    for guide in layout["guides"]:
        angle = (guide["angle"] % 360) * math.pi / 180
        spacing = guide["spacing"]
        lines = guide["lines"]

        if (angle >= 0 and angle < math.pi / 2) or (
            angle >= math.pi and angle < math.pi * 3 / 2
        ):
            span_x = pdist(angle + (math.pi / 2), 0, p_span_y, p_span_x, 0)
            span_y = pdist(angle, 0, 0, p_span_x, p_span_y)
        else:
            span_x = pdist(angle + (math.pi / 2), 0, 0, p_span_x, p_span_y)
            span_y = pdist(angle, 0, p_span_y, p_span_x, 0)

        ext_x = (span_x - p_span_x) / 2
        ext_y = (span_y - p_span_y) / 2
        lim_x_lo = -ext_x
        lim_x_hi = p_span_x + ext_x
        lim_y_lo = -ext_y + margin_top
        lim_y_hi = p_span_y + ext_y - margin_bot

        guide_span_y = sum(x["gap"] for x in filter(lambda x: x.get("gap"), lines))
        guide_count = (lim_y_hi - lim_y_lo + spacing) // (guide_span_y + spacing)
        field_span_y = (guide_count * (guide_span_y + spacing)) - spacing
        y_offset = ((lim_y_hi - lim_y_lo) - field_span_y) / 2

        x_start = lim_x_lo
        x_end = lim_x_hi
        y_start = lim_y_lo + y_offset
        y_end = lim_y_hi - y_offset

        x_lo = margin_lft
        x_hi = p_span_x - margin_rgt
        y_lo = margin_top
        y_hi = p_span_y - margin_bot

        y = y_start
        while True:
            if y + guide_span_y > y_end:
                break

            for line in lines:
                if gap := line.get("gap"):
                    y += gap
                    continue

                color = line["color"]
                width = line["width"]
                xa, ya = rotc(angle, x_start, y)
                xb, yb = rotc(angle, x_end, y)
                mr = pp2mr((xa, ya), (xb, yb))

                if xa < x_lo:
                    if sol := lalg(mr, (1, 0, x_lo)):
                        xa, ya = sol
                if xb < x_lo:
                    if sol := lalg(mr, (1, 0, x_lo)):
                        xb, yb = sol

                if xa > x_hi:
                    if sol := lalg(mr, (1, 0, x_hi)):
                        xa, ya = sol
                if xb > x_hi:
                    if sol := lalg(mr, (1, 0, x_hi)):
                        xb, yb = sol

                if ya < y_lo:
                    if sol := lalg(mr, (0, 1, y_lo)):
                        xa, ya = sol
                    else:
                        ya = y_lo
                if yb < y_lo:
                    if sol := lalg(mr, (0, 1, y_lo)):
                        xb, yb = sol
                    else:
                        yb = y_lo

                if ya > y_hi:
                    if sol := lalg(mr, (0, 1, y_hi)):
                        xa, ya = sol
                    else:
                        ya = y_hi
                if yb > y_hi:
                    if sol := lalg(mr, (0, 1, y_hi)):
                        xb, yb = sol
                    else:
                        yb = y_hi

                draw.line((xa, ya, xb, yb), fill=color, width=width)

            y += spacing

    im.save(output_file, quality=quality)
    print(f"`{output_file}` has been created! ✨")


def main():
    LAYOUT_FILE = "layout-config.toml"
    DEFAULT_OUTPUT_FILE = "calligraphy-sheet.jpg"
    DEFAULT_QUALITY = 100

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-t",
        "--template",
        action="store_true",
        help="create template layout file",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_FILE,
        help="output calligraphy sheet",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=DEFAULT_QUALITY,
        help="quality of the sheet",
    )
    parser.add_argument(
        "-p",
        "--preset",
        type=int,
        choices=range(1, 4),
        help="preset layout (1-3)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="verbose",
    )

    args = parser.parse_args()

    if not args.preset:
        preset = None
    else:
        assert args.preset <= 3
        preset = PRESETS[args.preset - 1]

    if args.template:
        if preset is None:
            preset = PRESET_LAYOUT_1
        with open(LAYOUT_FILE, "w") as f:
            f.write(preset)
            print(f"`{LAYOUT_FILE}` has been created! ✨")
        layout = tomllib.loads(preset)
    else:
        if preset is None:
            if not os.path.exists(LAYOUT_FILE):
                layout = tomllib.loads(PRESET_LAYOUT_1)
            else:
                with open(LAYOUT_FILE, "rb") as f:
                    layout = tomllib.load(f)
        else:
            layout = tomllib.loads(preset)

    draw(layout, args.output, args.quality)

    if args.verbose:
        print()
        pprint(layout)


if __name__ == "__main__":
    raise SystemExit(main())
