#!/usr/bin/env python3
"""Draw the profile pictures: the animated header and one card per project.

Header: one tile per main project, Blinky's spanning both rows, each acting out what the project does in a short loop.
Motion runs on minimum-jerk curves sampled into keyframes, since CSS has no such easing.
The static state (no animation, reduced motion) shows every tile after its action.
Writes assets/projects-<theme>.svg and assets/cards/<project>-<theme>.svg for both themes.
"""

import base64
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TILE_W, TILE_H, GAP = 274, 176, 14
W, H = 4 * GAP + 3 * TILE_W, 3 * GAP + 2 * TILE_H
PERIOD_S = 12
SANS = "'IBM Plex Sans', Inter, 'Segoe UI', system-ui, sans-serif"
MONO = "ui-monospace, 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace"
PINK, INK, BLUSH = "#f2a7a0", "#1f1b1a", "#ff7f9b"
PRE = 'xml:space="preserve"'

THEMES = {
    "dark": {"bg": "#161616", "raise1": "#202020", "raise2": "#2a2a2a", "raise3": "#363636",
             "fg": "#e8e8e8", "sub": "#a6a6a6", "faint": "#6e6e6e"},
    "light": {"bg": "#f4f4f4", "raise1": "#e9e9e9", "raise2": "#dddddd", "raise3": "#d0d0d0",
              "fg": "#1a1a1a", "sub": "#555555", "faint": "#8c8c8c"},
}


def st(**k: float) -> dict:
    """A track state: opacity, translation in px and scale."""
    return {"o": 1, "x": 0, "y": 0, "sx": 1, "sy": 1} | k


def style(s: dict) -> str:
    return (f"opacity:{s['o']:.3f};transform:translate({s['x'] + 0:.2f}px,{s['y'] + 0:.2f}px) "
            f"scale({s['sx']:.3f},{s['sy']:.3f})")


def track(name: str, stops: list, still: dict, extra: str = "") -> str:
    """Keyframes through (percent, state) stops; `still` is the frame shown without motion."""
    frames = []
    for (p0, a), (p1, b) in zip(stops, stops[1:]):
        steps = 1 if a == b else 8
        for k in range(steps):
            u = k / steps
            e = 10 * u**3 - 15 * u**4 + 6 * u**5
            frames.append(f"{round(p0 + (p1 - p0) * u, 3):g}%{{{style({n: a[n] + (b[n] - a[n]) * e for n in a})}}}")
    frames.append(f"100%{{{style(stops[-1][1])}}}")
    return (f"@keyframes {name}{{{''.join(frames)}}}"
            f".{name}{{{style(still)};{extra}animation:{name} {PERIOD_S}s linear infinite}}")


def move(name: str, start: dict, end: dict, span: tuple[float, float], extra: str = "") -> str:
    """Go from start to end within span, hold, and snap back while the tile is faded out (see `loop`)."""
    return track(name, [(0, start), (span[0], start), (span[1], end), (94.5, end), (95, start), (100, start)],
                 end, extra)


def appear(name: str, at: float) -> str:
    return move(name, st(o=0), st(), (at, at + 2))


def text(x: float, y: float, value: str, fill: str, size: int = 11, extra: str = "") -> str:
    return f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{fill}" {extra}>{escape(value)}</text>'


# Blinky's terminal, a real run of its checks: (start in % of the period, baseline, colour role, text).
LINES = (
    (12, 52, "sub", "● Bash(python3 tools/check.py)"),
    (16, 72, "sub", "  └ 54 files checked"),
    (20, 92, "sub", "  └ Ran 32 tests   OK"),
    (24, 112, "sub", "  └ all checks passed"),
    (28, 140, "fg", "● All checks pass."),
)


def blinky_tile(t: dict) -> tuple[str, str]:
    cx, cy, r = 236, 300, 18
    eyes = "".join(f'<rect class="bk-lid" x="{cx + side * 0.32 * r - 0.1 * r:.1f}" y="{cy - 0.26 * r:.1f}" '
                   f'width="{0.2 * r:.1f}" height="{0.42 * r:.1f}" rx="{0.1 * r:.1f}" fill="{INK}"/>' for side in (-1, 1))
    arches = "".join(f'<path d="M{cx + side * 0.32 * r - 0.15 * r:.1f} {cy - 0.04 * r:.1f}q{0.15 * r:.1f} {-0.36 * r:.1f} '
                     f'{0.3 * r:.1f} 0" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
                     for side in (-1, 1))
    blush = "".join(f'<ellipse cx="{cx + side * 0.58 * r:.1f}" cy="{cy + 0.34 * r:.1f}" rx="{0.18 * r:.1f}" '
                    f'ry="{0.1 * r:.1f}" fill="{BLUSH}" opacity=".42"/>' for side in (-1, 1))
    body = (f'<g font-family="{MONO}">{text(16, 30, ">", t["faint"])}{text(30, 30, "run the checks", t["fg"])}'
            + "".join(f'<g class="bk-l{i}">{text(16, y, line, t[role], 11, PRE)}</g>' for i, (_, y, role, line) in enumerate(LINES))
            + f'</g><g class="bk-bubble"><rect x="94" y="282" width="114" height="36" rx="10" fill="{t["raise3"]}"/>'
            f'{text(104, 297, "blinky · Claude", t["sub"], 10)}'
            f'{text(104, 311, "All checks pass.", t["fg"], 11, "font-weight=\"500\"")}</g>'
            f'<g class="bk-hop"><circle cx="{cx}" cy="{cy}" r="{r}" fill="{PINK}"/>{blush}'
            f'<g class="bk-eyes">{eyes}</g><g class="bk-done">{arches}</g></g>')
    lid = st()
    css = ("".join(appear(f"bk-l{i}", at) for i, (at, _, _, _) in enumerate(LINES)) + appear("bk-done", 30)
           + move("bk-eyes", st(), st(o=0), (30, 32))
           + track("bk-lid", [(0, lid), (6, lid), (7, st(sy=0.1)), (8, lid), (20, lid), (21, st(sy=0.1)),
                              (22, lid), (100, lid)], lid, "transform-box:fill-box;transform-origin:center;")
           + track("bk-hop", [(0, st()), (30, st()), (33, st(y=-6)), (36, st()), (100, st())], st())
           + move("bk-bubble", st(o=0, y=-8), st(), (32, 36)))
    return body, css


def pidra_tile(t: dict) -> tuple[str, str]:
    rows = (("spotify", "1.2 GB", 70), ("zen", "998 MB", 58), ("code", "640 MB", 37), ("discord", "410 MB", 24))
    out = [f'<g font-family="{MONO}">{text(16, 26, "PROCESS", t["faint"], 9)}{text(168, 26, "MEM", t["faint"], 9, "text-anchor=\"end\"")}',
           f'<rect class="pd-sel" x="10" y="36" width="254" height="20" rx="6" fill="{t["raise2"]}"/>']
    for i, (name, mem, bar) in enumerate(rows):
        y = 50 + i * 20
        cls = ("", "pd-zen", "pd-up", "pd-up")[i]
        out.append(f'<g class="{cls}">{text(20, y, name, t["fg"])}{text(168, y, mem, t["sub"], 11, "text-anchor=\"end\"")}'
                   f'<rect x="182" y="{y - 6}" width="{bar}" height="4" rx="2" fill="{t["raise3"]}"/></g>')
    out.append(f'<g class="pd-act">{text(16, 136, "zen →  [R] Restart  [S] Stop", t["sub"], 10, PRE)}</g>'
               f'<g class="pd-res">{text(16, 136, "zen    STOP    EXITED", t["sub"], 10, PRE)}</g></g>')
    hidden, shown = st(o=0), st()
    css = (move("pd-sel", st(), st(y=20), (14, 17))
           + track("pd-act", [(0, hidden), (18, hidden), (20, shown), (32, shown), (34, hidden), (100, hidden)], hidden)
           + move("pd-zen", st(), st(o=0, x=-12), (28, 32))
           + move("pd-up", st(), st(y=-20), (32, 36))
           + appear("pd-res", 35))
    return "".join(out), css


def rewa_tile(t: dict) -> tuple[str, str]:
    ticks = "".join(f'<rect x="{20 + i * 10}" y="{50 - h / 2}" width="5" height="{h}" rx="2" fill="{t["raise3"]}"/>'
                    for i, h in enumerate((8, 12, 6, 10) * 9))
    thumbs = "".join(f'<rect x="{16 + i * 72}" y="86" width="64" height="36" rx="6" fill="{t["raise2"]}"/>'
                     f'{text(22 + i * 72, 116, length, t["sub"], 9, f"font-family=\"{MONO}\"")}'
                     for i, length in enumerate(("1:12", "0:45")))
    body = (f'<clipPath id="strip"><rect x="16" y="40" width="242" height="20" rx="6"/></clipPath>'
            f'{text(16, 28, "Replay · 30 sec", t["sub"])}'
            f'<rect x="164" y="14" width="94" height="20" rx="6" fill="{t["raise2"]}"/>'
            f'<rect class="rw-key" x="164" y="14" width="94" height="20" rx="6" fill="{t["raise3"]}"/>'
            f'{text(211, 28, "Super+Shift+R", t["fg"], 10, f"text-anchor=\"middle\" font-family=\"{MONO}\"")}'
            f'<g clip-path="url(#strip)"><rect x="16" y="40" width="242" height="20" fill="{t["raise2"]}"/>'
            f'<g class="rw-roll">{ticks}</g></g>'
            f'{text(16, 78, "Library", t["faint"], 10)}<g class="rw-shift">{thumbs}</g>'
            f'<g class="rw-new"><rect x="16" y="86" width="64" height="36" rx="6" fill="{t["raise3"]}"/>'
            f'{text(22, 116, "0:30", t["fg"], 9, f"font-family=\"{MONO}\"")}</g>')
    off, on = st(o=0), st()
    css = ("@keyframes rw-roll{from{transform:translateX(0)}to{transform:translateX(-120px)}}"
           f".rw-roll{{animation:rw-roll {PERIOD_S}s linear infinite}}"
           + track("rw-key", [(0, off), (40, off), (41, on), (44, on), (46, off), (100, off)], off)
           + move("rw-shift", st(), st(x=72), (42, 47))
           + move("rw-new", st(o=0, y=-12), st(), (45, 49)))
    return body, css


def calendary_tile(t: dict) -> tuple[str, str]:
    col, gap = 43.6, 6
    out = []
    for i, day in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri")):
        x = 16 + i * (col + gap)
        role = "fg" if i == 3 else "faint"
        out.append(text(x + col / 2, 28, day, t[role], 10, 'text-anchor="middle" font-weight="500"')
                   + f'<rect x="{x:.1f}" y="38" width="{col}" height="94" rx="8" fill="{t["raise2"]}"/>')
    for day, top, height in ((0, 46, 22), (2, 70, 30), (4, 50, 18), (3, 104, 20)):
        out.append(f'<rect x="{16 + day * (col + gap) + 4:.1f}" y="{top}" width="{col - 8}" height="{height}" '
                   f'rx="5" fill="{t["raise3"]}"/>')
    x = 16 + col + gap + 4
    out.append(f'<g class="cal-move"><g class="cal-draw"><rect x="{x:.1f}" y="62" width="{col - 8}" height="34" rx="5" '
               f'fill="{t["fg"]}"/></g><g class="cal-label">{text(x + 5, 76, "Review", t["bg"], 9, "font-weight=\"600\"")}'
               f'{text(x + 5, 88, "14:00", t["bg"], 9)}</g></g>')
    shift = 2 * (col + gap)
    css = (move("cal-move", st(), st(x=shift), (40, 46))
           + move("cal-draw", st(sy=0), st(), (18, 24), "transform-box:fill-box;transform-origin:top;")
           + appear("cal-label", 24))
    return "".join(out), css


def filyy_tile(t: dict) -> tuple[str, str]:
    def rows(cls: str, names: tuple, folder: bool) -> str:
        icon = (lambda y: f'<rect x="20" y="{y - 9}" width="12" height="10" rx="3" fill="{t["sub"]}"/>') if folder else \
               (lambda y: f'<rect x="22" y="{y - 10}" width="9" height="12" rx="2" fill="{t["faint"]}"/>')
        return f'<g class="{cls}">' + "".join(icon(52 + i * 20) + text(40, 52 + i * 20, n, t["fg"])
                                              for i, n in enumerate(names)) + "</g>"
    crumb = f'<tspan fill="{t["sub"]}">Home › </tspan>Projekte'
    body = (f'<g font-family="{MONO}"><text x="16" y="28" font-size="11" fill="{t["fg"]}">{crumb}</text>'
            f'<g class="fl-crumb"><text x="16" y="28" font-size="11" fill="{t["fg"]}">'
            f'<tspan fill-opacity="0">Home › Projekte</tspan> › src</text></g>'
            f'<rect class="fl-sel" x="10" y="38" width="254" height="20" rx="6" fill="{t["raise2"]}"/>'
            f'{rows("fl-a", ("assets", "docs", "src", "tests"), True)}'
            f'{rows("fl-b", ("app.py", "board.qml", "files.py"), False)}</g>')
    sel = [(0, st()), (16, st()), (19, st(y=20)), (24, st(y=20)), (27, st(y=40)), (36, st(y=40)), (40, st()), (100, st())]
    b_off, b_on = st(o=0, x=40), st()
    css = (track("fl-sel", sel, st())
           + move("fl-a", st(), st(o=0, x=-40), (36, 40))
           + move("fl-b", b_off, b_on, (37, 41))
           + appear("fl-crumb", 38))
    return body, css


def loop() -> str:
    """Every tile fades out at the end of the period, resets unseen and fades back in at its start."""
    on, off = st(), st(o=0)
    return track("loop", [(0, on), (91, on), (94, off), (96, off), (99, on), (100, on)], on)


# Tiles: (draw, name, stack, column, row, rows spanned); Blinky takes the full height on the left.
TILES = ((blinky_tile, "Blinky", "Python · QML", 0, 0, 2), (pidra_tile, "PIDRA", "Rust · Ratatui", 1, 0, 1),
         (rewa_tile, "Rewa", "Rust", 2, 0, 1), (calendary_tile, "Calendary", "Python · Qt Quick", 1, 1, 1),
         (filyy_tile, "Filyy", "Python · Qt Quick", 2, 1, 1))


def scene(name: str) -> str:
    t = THEMES[name]
    tiles, rules = [], []
    for draw, title, stack, column, row, span in TILES:
        x, y = GAP + column * (TILE_W + GAP), GAP + row * (TILE_H + GAP)
        h = span * TILE_H + (span - 1) * GAP
        body, css = draw(t)
        rules.append(css)
        tiles.append(f'<g transform="translate({x},{y})"><clipPath id="clip-{title}"><rect width="{TILE_W}" '
                     f'height="{h}" rx="14"/></clipPath><rect width="{TILE_W}" height="{h}" rx="14" '
                     f'fill="{t["raise1"]}"/><g clip-path="url(#clip-{title})" font-family="{SANS}"><g class="loop">{body}</g>'
                     f'{text(16, h - 18, title, t["fg"], 13, "font-weight=\"600\"")}'
                     f'{text(TILE_W - 16, h - 18, stack, t["faint"], 10, "text-anchor=\"end\" font-weight=\"500\"")}</g></g>')
    rules.append(loop())
    rules.append("@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="Five projects acting out what they do: Blinky, PIDRA, Rewa, Calendary and Filyy">'
            f'<style>{"".join(rules)}</style><rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>{"".join(tiles)}</svg>\n')


# Projects: (slug, name, icon in assets/icons, stack, description in two lines).
CARDS = (
    ("rewa", "Rewa", "rewa.png", "Rust", ("Instant replay recorder for Windows and", "Arch Linux, GPU-encoded, held in memory")),
    ("calendary", "Calendary", "calendary.svg", "Python · Qt Quick",
     ("Desktop calendar for Google and iCloud,", "on Linux and with a Windows installer")),
    ("filyy", "Filyy", "filyy.png", "Python · Qt Quick", ("Keyboard-friendly file manager", "for Hyprland")),
    ("blinky", "Blinky", "blinky.svg", "Python · QML", ("A small character for every Claude Code", "and Codex session, on its terminal")),
    ("pidra", "PIDRA", "pidra.png", "Rust · Ratatui", ("Keyboard-first process manager", "for the terminal")),
    ("crosshype", "Crosshype", "crosshype.svg", "Python", ("Crosshair overlay for Wayland, with a TUI", "builder that previews the real overlay")),
)
CARD_W, CARD_H = 436, 104


def card(t: dict, name: str, icon: str, stack: str, lines: tuple[str, str]) -> str:
    """A project card in the header's style; the icon is embedded since a README image cannot load others."""
    path = ROOT / "assets" / "icons" / icon
    mime = "image/svg+xml" if path.suffix == ".svg" else "image/png"
    data = base64.b64encode(path.read_bytes()).decode()
    text = "".join(f'<text x="84" y="{66 + i * 19}" font-size="13" fill="{t["sub"]}">{escape(line)}</text>'
                   for i, line in enumerate(lines))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W} {CARD_H}" width="{CARD_W}" '
            f'height="{CARD_H}" role="img" aria-label="{escape(name)}: {escape(" ".join(lines))}">'
            f'<rect width="{CARD_W}" height="{CARD_H}" rx="14" fill="{t["bg"]}"/>'
            f'<image href="data:{mime};base64,{data}" x="22" y="22" width="44" height="44"/>'
            f'<g font-family="{SANS}"><text x="84" y="42" font-size="16" font-weight="600" '
            f'fill="{t["fg"]}">{escape(name)}</text>'
            f'<text x="{CARD_W - 22}" y="42" text-anchor="end" font-size="11" font-weight="500" '
            f'fill="{t["faint"]}">{escape(stack)}</text>{text}</g></svg>\n')


def main() -> None:
    (ROOT / "assets" / "cards").mkdir(exist_ok=True)
    for theme, tokens in THEMES.items():
        (ROOT / "assets" / f"projects-{theme}.svg").write_text(scene(theme))
        for slug, name, icon, stack, lines in CARDS:
            (ROOT / "assets" / "cards" / f"{slug}-{theme}.svg").write_text(card(tokens, name, icon, stack, lines))
    print(f"assets/projects-*.svg and {len(CARDS) * len(THEMES)} cards written")


if __name__ == "__main__":
    main()
