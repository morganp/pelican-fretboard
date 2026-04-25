import svgwrite

DEFAULT_COLORS = {
    "bg": "#F5F2EC",
    "line": "#2D2D2D",
    "line_light": "#4A4A4A",
    "note": "#2D2D2D",
    "root": "#7B35C2",
    "accent": "#E07820",
    "dot_text": "#F5F2EC",
}

STRING_SPACING = 30
FRET_SPACING = 36
DOT_RADIUS = 11
NUT_STROKE = 5
FRET_STROKE = 1.5
STRING_STROKE = 1.5
MARGIN_LEFT = 38
MARGIN_RIGHT = 30
MARGIN_TOP = 56
MARGIN_BOTTOM = 20
NUM_FRETS = 5

SERIF = 'Georgia, "Times New Roman", serif'


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
    frets_raw = data.get("frets", [0] * n)
    fingers_raw = data.get("fingers", [])
    harmony_raw = data.get("harmony", [])
    barre = data.get("barre", None)

    frets = [_parse_fret(f) for f in frets_raw]

    fingers = [str(f) for f in fingers_raw]
    while len(fingers) < n:
        fingers.append("-")

    harmony = [str(h).strip() for h in harmony_raw]
    while len(harmony) < n:
        harmony.append("-")

    has_harmony = any(h not in ("-", "0", "") for h in harmony)

    show_mode = str(data.get("show", "harmony" if has_harmony else "fingers"))
    labels = harmony if show_mode == "harmony" else fingers

    # Root strings: inferred from harmony array, or explicit root_strings
    if has_harmony:
        root_strings = {i for i, h in enumerate(harmony) if h.upper() == "R"}
    else:
        root_strings = set(int(x) - 1 for x in data.get("root_strings", []))

    # Legend: shown by default in harmony mode, off in fingers mode
    show_legend_default = show_mode == "harmony" and has_harmony
    show_legend = bool(data.get("legend", show_legend_default))

    fb_w = (n - 1) * STRING_SPACING
    fb_h = NUM_FRETS * FRET_SPACING
    svg_w = MARGIN_LEFT + fb_w + MARGIN_RIGHT
    svg_h = MARGIN_TOP + fb_h + MARGIN_BOTTOM

    dwg = svgwrite.Drawing(size=(svg_w, svg_h), profile="full")
    dwg.viewbox(0, 0, svg_w, svg_h)
    dwg.add(dwg.rect(insert=(0, 0), size=(svg_w, svg_h), fill=c["bg"]))

    if name:
        dwg.add(dwg.text(
            name,
            insert=(svg_w / 2, 18),
            text_anchor="middle",
            fill=c["line"],
            font_family=SERIF,
            font_size=14,
            font_weight="bold",
        ))

    if show_legend:
        sublabel = "Intervals" if show_mode == "harmony" else "Fingers"
        dwg.add(dwg.text(
            sublabel,
            insert=(svg_w / 2, 32),
            text_anchor="middle",
            fill=c["line_light"],
            font_family=SERIF,
            font_size=11,
            font_style="italic",
        ))

    _draw_open_muted(dwg, frets, n, c)
    _draw_nut_or_fret(dwg, start_fret, fb_w, c)
    _draw_fret_lines(dwg, fb_w, c)
    _draw_strings(dwg, n, fb_h, c)

    if barre:
        _draw_barre(dwg, barre, n, start_fret, c)

    for i, f in enumerate(frets):
        if f > 0:
            fret_pos = f - (start_fret - 1)
            if 1 <= fret_pos <= NUM_FRETS:
                x = MARGIN_LEFT + i * STRING_SPACING
                y = MARGIN_TOP + (fret_pos - 0.5) * FRET_SPACING
                dot_color = c["root"] if i in root_strings else c["note"]
                dwg.add(dwg.circle(center=(x, y), r=DOT_RADIUS, fill=dot_color))
                label = labels[i] if i < len(labels) else "-"
                if label not in ("-", "0", ""):
                    dwg.add(dwg.text(
                        label,
                        insert=(x, y + 4),
                        text_anchor="middle",
                        fill=c["dot_text"],
                        font_family=SERIF,
                        font_size=11,
                        font_weight="bold",
                    ))

    return dwg.tostring()



def _parse_fret(f):
    s = str(f).strip().upper()
    if s in ("X", "M"):
        return -1
    s = s.rstrip("R")
    try:
        return int(s)
    except ValueError:
        return 0


def _draw_open_muted(dwg, frets, n, c):
    y = MARGIN_TOP - 14
    for i, f in enumerate(frets):
        x = MARGIN_LEFT + i * STRING_SPACING
        if f == -1:
            s = 6
            dwg.add(dwg.line(start=(x - s, y - s), end=(x + s, y + s),
                             stroke=c["line"], stroke_width=2, stroke_linecap="round"))
            dwg.add(dwg.line(start=(x + s, y - s), end=(x - s, y + s),
                             stroke=c["line"], stroke_width=2, stroke_linecap="round"))
        elif f == 0:
            dwg.add(dwg.circle(center=(x, y), r=6,
                               fill="none", stroke=c["line"], stroke_width=1.5))


def _draw_nut_or_fret(dwg, start_fret, fb_w, c):
    y = MARGIN_TOP
    x1, x2 = MARGIN_LEFT, MARGIN_LEFT + fb_w
    if start_fret == 1:
        dwg.add(dwg.line(start=(x1, y), end=(x2, y),
                         stroke=c["line"], stroke_width=NUT_STROKE,
                         stroke_linecap="round"))
    else:
        dwg.add(dwg.line(start=(x1, y), end=(x2, y),
                         stroke=c["line_light"], stroke_width=FRET_STROKE))
        dwg.add(dwg.text(
            f"{start_fret}fr",
            insert=(x2 + 7, y + 5),
            fill=c["line_light"],
            font_family=SERIF,
            font_size=11,
        ))


def _draw_fret_lines(dwg, fb_w, c):
    for f in range(1, NUM_FRETS + 1):
        y = MARGIN_TOP + f * FRET_SPACING
        dwg.add(dwg.line(
            start=(MARGIN_LEFT, y), end=(MARGIN_LEFT + fb_w, y),
            stroke=c["line_light"], stroke_width=FRET_STROKE,
        ))


def _draw_strings(dwg, n, fb_h, c):
    for i in range(n):
        x = MARGIN_LEFT + i * STRING_SPACING
        dwg.add(dwg.line(
            start=(x, MARGIN_TOP), end=(x, MARGIN_TOP + fb_h),
            stroke=c["line"], stroke_width=STRING_STROKE,
        ))


def _draw_barre(dwg, barre, n, start_fret, c):
    barre_fret = int(barre.get("fret", 1))
    from_s = int(barre.get("from_string", 1)) - 1
    to_s = int(barre.get("to_string", n)) - 1
    fret_pos = barre_fret - (start_fret - 1)
    if not (1 <= fret_pos <= NUM_FRETS):
        return
    cy = MARGIN_TOP + (fret_pos - 0.5) * FRET_SPACING
    x1 = MARGIN_LEFT + from_s * STRING_SPACING
    x2 = MARGIN_LEFT + to_s * STRING_SPACING
    r = DOT_RADIUS
    dwg.add(dwg.rect(
        insert=(x1 - r, cy - r),
        size=(x2 - x1 + r * 2, r * 2),
        rx=r, ry=r,
        fill=c["note"],
    ))
