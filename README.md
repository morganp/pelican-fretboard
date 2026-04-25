# pelican-fretboard

Pelican plugin that renders fretted instrument diagrams (chord charts, scale boxes, tab) from fenced code blocks. Diagrams are generated as SVGs and cached so subsequent builds are fast.

## Diagram types

### Chord diagrams

````markdown
```chord
name: C Major
tuning: EADGBE
frets: [x, 3, 2, 0, 1, 0]
fingers: [-, 3, 2, -, 1, -]
root_strings: [2]
```
````

- `frets`: one value per string (low to high). `x` = muted, `0` = open, `1-24` = fret number.
- `fingers`: optional finger numbers shown inside dots. Use `-` to omit.
- `root_strings`: 1-indexed string numbers to highlight in the primary accent colour.
- `start_fret`: if omitted or `1`, a nut is drawn. Set to `5` etc. to show a position indicator.
- `barre`: `{fret: 1, from_string: 1, to_string: 5}` draws a barre bar.
- `strings`: override number of strings (default: length of `tuning`).

### Scale diagrams

````markdown
```scale
name: A Minor Pentatonic
tuning: EADGBE
start_fret: 5
grid:
  - "R . . x ."
  - "R . x . ."
  - "R . x . ."
  - "R . x . ."
  - "R . . x ."
  - "R . . x ."
```
````

The `grid` is a list of rows, one per string (low E first). Each row is a space-separated sequence of fret values. Column 0 = `start_fret`.

- `R` = root note (primary accent colour)
- `x` or `X` = scale note (charcoal)
- `.` or `-` = not in scale

Set `num_frets` to override the default 6-fret window.

### Tab

````markdown
```tab
name: Intro Riff
tuning: EADGBe
tab: |
  e|---------|---------|
  B|---------|---------|
  G|---------|---------|
  D|--0-2-3--|---------|
  A|---------|---------|
  E|0--------|---------|
```
````

ASCII tab is rendered with the lizard-spock palette: cream background, charcoal string lines, charcoal note numbers, barlines in lighter charcoal.

## Installation

```bash
pip install -e path/to/pelican-fretboard --config-settings editable_mode=compat
```

Add to `pelicanconf.py`:

```python
PLUGINS = [..., "pelican.plugins.fretboard"]
```

## Configuration

All settings are optional. Defaults match the lizard-spock.co.uk palette.

```python
FRETBOARD_CACHE_PATH = "content/images/fretboard"
FRETBOARD_CACHE_URL  = "/images/fretboard"
FRETBOARD_COLORS = {
    "bg":        "#F5F2EC",
    "line":      "#2D2D2D",
    "line_light":"#4A4A4A",
    "note":      "#2D2D2D",
    "root":      "#7B35C2",
    "accent":    "#E07820",
    "dot_text":  "#FFFFFF",
}
```

## Instrument support

Any fretted instrument is supported. Set `tuning` to match string count and pitch names, and optionally `strings` to override the count.

```yaml
# Bass (4-string)
tuning: EADG
# Bass (5-string)
tuning: BEADG
# Ukulele
tuning: GCEA
```
