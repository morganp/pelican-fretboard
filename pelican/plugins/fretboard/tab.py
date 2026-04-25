import svgwrite

DEFAULT_COLORS = {
    "bg": "#F5F2EC",
    "line": "#2D2D2D",
    "line_light": "#4A4A4A",
    "note": "#2D2D2D",
    "root": "#7B35C2",
    "accent": "#E07820",
}

STRING_HEIGHT = 22
MARGIN_LEFT = 32
MARGIN_RIGHT = 20
MARGIN_TOP = 36
MARGIN_BOTTOM = 16
CHAR_WIDTH = 10
STRING_STROKE = 1.2
BAR_STROKE = 1.8
FONT_SIZE = 12

SERIF = 'Georgia, "Times New Roman", serif'
MONO = '"Courier New", Courier, monospace'


def render(data: dict, colors: dict | None = None) -> str:
    c = dict(DEFAULT_COLORS)
    if colors:
        c.update(colors)

    name = data.get("name", "")
    tuning_str = data.get("tuning", "EADGBe")
    tab_raw = data.get("tab", "")

    lines = _parse_tab(tab_raw, tuning_str)
    if not lines:
        return ""

    n_strings = len(lines)
    max_len = max(len(line["content"]) for line in lines)
    content_width = max_len * CHAR_WIDTH
    label_width = max(len(line["label"]) for line in lines) * (FONT_SIZE * 0.65)

    svg_w = int(MARGIN_LEFT + label_width + content_width + MARGIN_RIGHT)
    svg_h = int(MARGIN_TOP + (n_strings - 1) * STRING_HEIGHT + STRING_HEIGHT + MARGIN_BOTTOM)

    dwg = svgwrite.Drawing(size=(svg_w, svg_h), profile="full")
    dwg.viewbox(0, 0, svg_w, svg_h)
    dwg.add(dwg.rect(insert=(0, 0), size=(svg_w, svg_h), fill=c["bg"]))

    if name:
        dwg.add(dwg.text(
            name,
            insert=(svg_w / 2, 16),
            text_anchor="middle",
            fill=c["line"],
            font_family=SERIF,
            font_size=12,
            font_weight="bold",
            font_style="italic",
        ))

    content_x = MARGIN_LEFT + label_width

    top_y = MARGIN_TOP
    bottom_y = MARGIN_TOP + (n_strings - 1) * STRING_HEIGHT
    bar_extend = STRING_HEIGHT * 0.45

    # Collect barline x positions from all strings (should be consistent)
    barline_xs = set()
    for line in lines:
        for ci, ch in enumerate(line["content"]):
            if ch == "|":
                barline_xs.add(content_x + ci * CHAR_WIDTH + CHAR_WIDTH / 2)

    # Draw string lines and labels
    for idx, line in enumerate(lines):
        y = MARGIN_TOP + idx * STRING_HEIGHT
        dwg.add(dwg.text(
            line["label"],
            insert=(MARGIN_LEFT, y + 4),
            fill=c["line"],
            font_family=MONO,
            font_size=FONT_SIZE,
        ))
        dwg.add(dwg.line(
            start=(content_x, y),
            end=(content_x + content_width, y),
            stroke=c["line"], stroke_width=STRING_STROKE,
        ))

    # Draw barlines as full-height lines spanning all strings
    for bx in barline_xs:
        dwg.add(dwg.line(
            start=(bx, top_y - bar_extend),
            end=(bx, bottom_y + bar_extend),
            stroke=c["line_light"], stroke_width=BAR_STROKE,
        ))

    # Draw note numbers on top of string lines with cream knockout
    for idx, line in enumerate(lines):
        y = MARGIN_TOP + idx * STRING_HEIGHT
        for ci, ch in enumerate(line["content"]):
            if ch in ("|", "-", " "):
                continue
            cx = content_x + ci * CHAR_WIDTH + CHAR_WIDTH / 2
            # Cream rect to knock out the string line behind the number
            dwg.add(dwg.rect(
                insert=(cx - CHAR_WIDTH * 0.45, y - FONT_SIZE * 0.7),
                size=(CHAR_WIDTH * 0.9, FONT_SIZE * 0.95),
                fill=c["bg"],
            ))
            dwg.add(dwg.text(
                ch,
                insert=(cx, y + 4),
                text_anchor="middle",
                fill=c["note"],
                font_family=MONO,
                font_size=FONT_SIZE,
                font_weight="bold",
            ))

    return dwg.tostring()


def _parse_tab(raw: str, tuning_str: str) -> list[dict]:
    lines = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            parts = line.split("|", 1)
            label = parts[0].strip()
            content = "|" + parts[1] if len(parts) > 1 else ""
        else:
            label = ""
            content = line
        lines.append({"label": label, "content": content})

    if lines:
        return lines

    tuning = list(reversed(tuning_str))
    for note in tuning:
        lines.append({"label": note, "content": ""})
    return lines
