import svgwrite

DEFAULT_COLORS = {
    "bg": "#F5F2EC",
    "line": "#2D2D2D",
    "line_light": "#4A4A4A",
    "note": "#2D2D2D",
    "root": "#7B35C2",
    "accent": "#E07820",
    "dot_text": "#FFFFFF",
}

STRING_SPACING = 30
FRET_SPACING = 36
DOT_RADIUS = 11
FRET_STROKE = 1.5
STRING_STROKE = 1.5
MARGIN_LEFT = 52       # wider: accommodates fret labels on the left
MARGIN_RIGHT = 15
MARGIN_TOP = 46
MARGIN_BOTTOM = 20
NUM_FRETS = 6
LABEL_GAP = 10         # gap between fret label right edge and note dot edge

SERIF = 'Georgia, "Times New Roman", serif'

# Grid cell values
ROOT = "R"
NOTE = "x"
EMPTY = "."


def render(data: dict, colors: dict | None = None) -> str:
    c = dict(DEFAULT_COLORS)
    if colors:
        c.update(colors)

    tuning_str = data.get("tuning", "EADGBE")
    tuning = list(tuning_str)
    n = data.get("strings", len(tuning))
    tuning = tuning[:n]
    while len(tuning) < n:
        tuning.append("?")

    name = data.get("name", "")
    start_fret = int(data.get("start_fret", 1))
    num_frets = int(data.get("num_frets", NUM_FRETS))

    grid = _parse_grid(data.get("grid", []), n, num_frets)

    fb_w = (n - 1) * STRING_SPACING
    fb_h = num_frets * FRET_SPACING
    svg_w = MARGIN_LEFT + fb_w + MARGIN_RIGHT
    svg_h = MARGIN_TOP + fb_h + MARGIN_BOTTOM

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
            font_size=13,
            font_weight="bold",
        ))

    _draw_grid(dwg, n, num_frets, fb_w, fb_h, c)
    _draw_fret_labels(dwg, start_fret, num_frets, c)
    _draw_notes(dwg, grid, n, num_frets, c)

    return dwg.tostring()


def _parse_grid(raw_grid, n_strings, num_frets):
    grid = []
    for row in raw_grid:
        if isinstance(row, str):
            cells = row.split()
        else:
            cells = [str(v) for v in row]
        while len(cells) < num_frets:
            cells.append(".")
        grid.append(cells[:num_frets])
    while len(grid) < n_strings:
        grid.append(["."] * num_frets)
    return grid


def _draw_grid(dwg, n, num_frets, fb_w, fb_h, c):
    for f in range(num_frets + 1):
        y = MARGIN_TOP + f * FRET_SPACING
        dwg.add(dwg.line(
            start=(MARGIN_LEFT, y), end=(MARGIN_LEFT + fb_w, y),
            stroke=c["line_light"], stroke_width=FRET_STROKE,
        ))
    for i in range(n):
        x = MARGIN_LEFT + i * STRING_SPACING
        dwg.add(dwg.line(
            start=(x, MARGIN_TOP), end=(x, MARGIN_TOP + fb_h),
            stroke=c["line"], stroke_width=STRING_STROKE,
        ))


def _draw_fret_labels(dwg, start_fret, num_frets, c):
    label_x = MARGIN_LEFT - DOT_RADIUS - LABEL_GAP
    for f in range(num_frets):
        label = str(start_fret + f)
        y = MARGIN_TOP + (f + 0.5) * FRET_SPACING + 4
        dwg.add(dwg.text(
            label,
            insert=(label_x, y),
            text_anchor="end",
            fill=c["line_light"],
            font_family=SERIF,
            font_size=11,
        ))


def _draw_notes(dwg, grid, n, num_frets, c):
    for string_i, row in enumerate(grid[:n]):
        x = MARGIN_LEFT + string_i * STRING_SPACING
        for fret_i, cell in enumerate(row[:num_frets]):
            val = str(cell).strip().upper()
            if val in ("", ".", "-"):
                continue
            y = MARGIN_TOP + (fret_i + 0.5) * FRET_SPACING
            dot_color = c["root"] if val == ROOT else c["note"]
            dwg.add(dwg.circle(center=(x, y), r=11, fill=dot_color))
            label = val if val not in ("X",) else ""
            if label:
                dwg.add(dwg.text(
                    label,
                    insert=(x, y + 4),
                    text_anchor="middle",
                    fill=c["dot_text"],
                    font_family=SERIF,
                    font_size=10,
                    font_weight="bold",
                ))
