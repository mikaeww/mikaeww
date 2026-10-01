#!/usr/bin/env python3
"""Draw the profile pictures: the animated desk header and one card per project.

Header: an agent runs the checks in the terminal, then the blinky in its corner says it is
done. Its static state (no animation, reduced motion) is the finished scene.
Writes assets/header-<theme>.svg and assets/cards/<project>-<theme>.svg for both themes.
"""

import base64
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H = 880, 340
PERIOD_S = 12
SANS = "'IBM Plex Sans', Inter, 'Segoe UI', system-ui, sans-serif"
MONO = "ui-monospace, 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace"
PINK, NORI, INK, BLUSH = "#f2a7a0", "#9fd4b0", "#1f1b1a", "#ff7f9b"

THEMES = {
    "dark": {"bg": "#161616", "raise1": "#202020", "raise2": "#2a2a2a", "raise3": "#363636",
             "fg": "#e8e8e8", "sub": "#a6a6a6", "faint": "#6e6e6e"},
    "light": {"bg": "#f4f4f4", "raise1": "#e9e9e9", "raise2": "#dddddd", "raise3": "#d0d0d0",
              "fg": "#1a1a1a", "sub": "#555555", "faint": "#8c8c8c"},
}

# Terminal lines: (start of the line in % of the period, colour role, text).
LINES = (
    (14, "fg", "● Bash(python3 tools/check.py)"),
    (20, "sub", "  └ 53 files checked"),
    (26, "sub", "  └ Ran 32 tests   OK"),
    (31, "sub", "  └ all checks passed"),
    (36, "fg", "● All checks pass."),
)
PROMPT = "run the checks"
CHAR_W = 7.8
DONE_AT = 37


def css(t: dict) -> str:
    def show(name: str, at: int) -> str:
        return (f"@keyframes {name}{{0%,{at}%{{opacity:0}}{at + 1}%,93%{{opacity:1}}98%,100%{{opacity:0}}}}")

    typed = len(PROMPT) * CHAR_W
    rules = [show(f"l{i}", at) for i, (at, _, _) in enumerate(LINES)]
    rules += [show("done", DONE_AT), show("bubble", DONE_AT + 1),
              "@keyframes prompt{0%,93%{opacity:1}98%,100%{opacity:0}}",
              f"@keyframes type{{0%,2%{{transform:translateX(0)}}11%,100%{{transform:translateX({typed}px)}}}}",
              "@keyframes cursor{0%,11%{opacity:1}12%,100%{opacity:0}}",
              f"@keyframes open{{0%,{DONE_AT}%{{opacity:1}}{DONE_AT + 1}%,93%{{opacity:0}}98%,100%{{opacity:1}}}}",
              "@keyframes gaze{0%,12%{transform:translate(-3px,0)}15%,36%{transform:translate(0,3px)}"
              "40%,100%{transform:translate(0,0)}}",
              "@keyframes blink{0%,5%,7%,24%,26%,100%{transform:scaleY(1)}6%,25%{transform:scaleY(.1)}}",
              f"@keyframes hop{{0%,{DONE_AT}%,{DONE_AT + 4}%,100%{{transform:translateY(0)}}"
              f"{DONE_AT + 2}%{{transform:translateY(-6px)}}}}"]
    anim = f"{PERIOD_S}s linear infinite"
    rules += [f".l{i}{{animation:l{i} {anim}}}" for i in range(len(LINES))]
    rules += [f".done{{animation:done {anim}}}", f".bubble{{animation:bubble {anim}}}",
              f".prompt{{animation:prompt {anim}}}", f".cover{{transform:translateX({typed}px)}}",
              f".cover{{animation:type {anim};animation-timing-function:steps({len(PROMPT)},end)}}",
              f".cursor{{opacity:0;animation:cursor {anim}}}",
              f".open{{opacity:0;animation:open {anim}}}", f".gaze{{animation:gaze {anim}}}",
              f".lid{{transform-box:fill-box;transform-origin:center;animation:blink {anim}}}",
              f".hop{{animation:hop {anim}}}",
              "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"]
    return "".join(rules)


def blinky(cx: float, cy: float, r: float, color: str, blush: bool, finishes: bool) -> str:
    """One blinky as drawn by BlinkyFace.qml: tall eyes, ^^ once its agent is done."""
    w, h, split, ey = 0.2 * r, 0.42 * r, 0.32 * r, cy - 0.05 * r
    parts = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>',
             f'<ellipse cx="{cx - 0.37 * r:.1f}" cy="{cy - 0.57 * r:.1f}" rx="{0.25 * r:.1f}" ry="{0.15 * r:.1f}" '
             f'fill="#fff" opacity=".38" transform="rotate(-24 {cx - 0.37 * r:.1f} {cy - 0.57 * r:.1f})"/>']
    if blush:
        for side in (-1, 1):
            parts.append(f'<ellipse cx="{cx + side * 0.58 * r:.1f}" cy="{cy + 0.34 * r:.1f}" rx="{0.18 * r:.1f}" '
                         f'ry="{0.1 * r:.1f}" fill="{BLUSH}" opacity=".42"/>')
    eyes = "".join(f'<rect class="lid" x="{cx + side * split - w / 2:.1f}" y="{ey - h / 2:.1f}" width="{w:.1f}" '
                   f'height="{h:.1f}" rx="{w / 2:.1f}" fill="{INK}"/>' for side in (-1, 1))
    if not finishes:
        return f'<g>{"".join(parts)}<g class="gaze"><g>{eyes}</g></g></g>'
    aw, ah, ay = 0.3 * r, 0.18 * r, ey - 0.08 * r
    arches = "".join(f'<path d="M{cx + side * split - aw / 2:.1f} {ay + ah / 2:.1f}q{aw / 2:.1f} {-2 * ah:.1f} '
                     f'{aw:.1f} 0" fill="none" stroke="{INK}" stroke-width="{max(1.2, 0.11 * r):.1f}" '
                     f'stroke-linecap="round"/>' for side in (-1, 1))
    return (f'<g class="hop">{"".join(parts)}<g class="open"><g class="gaze"><g>{eyes}</g></g></g>'
            f'<g class="done">{arches}</g></g>')


def bar(t: dict) -> str:
    marks = "".join(f'<rect x="{28 + i * 20}" y="22" width="14" height="14" rx="4" '
                    f'fill="{t["fg"] if i == 0 else t["raise3"]}"/>' for i in range(3))
    return (f'<rect x="14" y="14" width="88" height="30" rx="9" fill="{t["raise1"]}"/>{marks}'
            f'<rect x="400" y="14" width="80" height="30" rx="9" fill="{t["raise1"]}"/>'
            f'<text x="440" y="34" text-anchor="middle" font-family="{SANS}" font-size="13" font-weight="500" '
            f'fill="{t["sub"]}">12:30</text>'
            f'<rect x="790" y="14" width="76" height="30" rx="9" fill="{t["raise1"]}"/>'
            f'{blinky(812, 29, 9, PINK, True, True)}{blinky(838, 29, 9, NORI, False, False)}')


def terminal(t: dict) -> str:
    x, y = 34, 90
    out = [f'<rect x="14" y="56" width="476" height="270" rx="14" fill="{t["raise1"]}"/>',
           f'<g font-family="{MONO}" font-size="13">',
           f'<g class="prompt"><text x="{x}" y="{y}" fill="{t["faint"]}">&gt;</text>'
           f'<text x="{x + 16}" y="{y}" fill="{t["fg"]}">{PROMPT}</text></g>',
           f'<g class="cover"><rect x="{x + 15}" y="{y - 14}" width="{len(PROMPT) * CHAR_W + 12}" height="20" '
           f'fill="{t["raise1"]}"/><rect class="cursor" x="{x + 16}" y="{y - 12}" width="7" height="16" rx="1" '
           f'fill="{t["fg"]}"/></g>']
    for i, (_, role, text) in enumerate(LINES):
        line_y = y + 30 + i * 22 + (10 if i == len(LINES) - 1 else 0)
        out.append(f'<text class="l{i}" x="{x}" y="{line_y}" fill="{t[role]}" xml:space="preserve">{text}</text>')
    out.append("</g>")
    out.append(f'<g class="bubble"><rect x="262" y="262" width="148" height="44" rx="10" fill="{t["raise3"]}"/>'
               f'<text x="274" y="280" font-family="{SANS}" font-size="11" fill="{t["sub"]}">blinky · Claude</text>'
               f'<text x="274" y="297" font-family="{SANS}" font-size="12" font-weight="500" '
               f'fill="{t["fg"]}">All checks pass.</text></g>')
    out.append(blinky(446, 284, 22, PINK, True, True))
    return "".join(out)


def files(t: dict) -> str:
    out = [f'<rect x="502" y="56" width="364" height="129" rx="14" fill="{t["raise1"]}"/>']
    for i, width in enumerate((52, 64, 44, 58)):
        fill = t["raise3"] if i == 0 else t["raise2"]
        out.append(f'<rect x="516" y="{72 + i * 22}" width="{width}" height="10" rx="4" fill="{fill}"/>')
    out.append(f'<rect x="602" y="{66 + 22}" width="252" height="20" rx="6" fill="{t["raise2"]}"/>')
    for i, (width, folder) in enumerate(((96, True), (128, True), (84, False), (110, False), (72, False))):
        row_y = 71 + i * 22
        icon = t["sub"] if folder else t["faint"]
        out.append(f'<rect x="612" y="{row_y}" width="12" height="11" rx="3" fill="{icon}"/>'
                   f'<rect x="634" y="{row_y + 2}" width="{width}" height="7" rx="3" fill="{t["raise3"]}"/>'
                   f'<rect x="814" y="{row_y + 2}" width="28" height="7" rx="3" fill="{t["raise3"]}"/>')
    return "".join(out)


def calendar(t: dict) -> str:
    left, col = 514, 340 / 7
    out = [f'<rect x="502" y="197" width="364" height="129" rx="14" fill="{t["raise1"]}"/>',
           f'<rect x="{left + 3 * col + 2:.1f}" y="206" width="{col - 4:.1f}" height="110" rx="8" '
           f'fill="{t["raise2"]}"/>']
    for i, day in enumerate(("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")):
        role = "fg" if i == 3 else "faint"
        out.append(f'<text x="{left + i * col + col / 2:.1f}" y="222" text-anchor="middle" font-family="{SANS}" '
                   f'font-size="10" font-weight="500" fill="{t[role]}">{day}</text>')
    events = ((0, 234, 22), (1, 250, 34), (2, 230, 16), (2, 272, 26), (3, 244, 30), (4, 238, 40), (6, 288, 18))
    for day, top, height in events:
        out.append(f'<rect x="{left + day * col + 5:.1f}" y="{top}" width="{col - 10:.1f}" height="{height}" '
                   f'rx="5" fill="{t["raise3"]}"/>')
    return "".join(out)


def scene(name: str) -> str:
    t = THEMES[name]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="A desk with a terminal, Filyy and Calendary; a blinky reports that the checks pass">'
            f'<style>{css(t)}</style><rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>'
            f'{bar(t)}{terminal(t)}{files(t)}{calendar(t)}</svg>\n')


# Projects: (slug, name, icon in assets/icons, stack, description in two lines).
CARDS = (
    ("rewa", "Rewa", "rewa.svg", "Rust", ("Instant replay recorder for Windows and", "Arch Linux, GPU-encoded, held in memory")),
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
        (ROOT / "assets" / f"header-{theme}.svg").write_text(scene(theme))
        for slug, name, icon, stack, lines in CARDS:
            (ROOT / "assets" / "cards" / f"{slug}-{theme}.svg").write_text(card(tokens, name, icon, stack, lines))
    print(f"assets/header-*.svg and {len(CARDS) * len(THEMES)} cards written")


if __name__ == "__main__":
    main()
