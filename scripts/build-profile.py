#!/usr/bin/env python3
"""Draw the profile pictures: the header and one card per project.

Header: one calm panel that shows the projects one at a time, crossfading between them.
Motion runs on minimum-jerk curves sampled into keyframes, since CSS has no such easing.
The static state (no animation, reduced motion) shows the first project.
Writes assets/spotlight-<theme>.svg and assets/cards/<project>-<theme>.svg for both themes.
"""

import base64
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H, PAD = 880, 152, 32
SLOT_S, FADE_S = 4, 0.5
SANS = "'IBM Plex Sans', Inter, 'Segoe UI', system-ui, sans-serif"
NUM = 'text-anchor="end" font-weight="500" style="font-variant-numeric:tabular-nums"'

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


def track(name: str, stops: list, still: dict, period_s: float) -> str:
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
            f".{name}{{{style(still)};animation:{name} {period_s:g}s linear infinite}}")


def text(x: float, y: float, value: str, fill: str, size: int = 11, extra: str = "") -> str:
    return f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{fill}" {extra}>{escape(value)}</text>'


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


def spotlight(t: dict) -> str:
    """Each project holds the panel for SLOT_S seconds; the next one rises in as the last one leaves."""
    period = SLOT_S * len(CARDS)
    slot, fade = 100 / len(CARDS), 100 * FADE_S / period
    below, shown, above = st(o=0, y=6), st(), st(o=0, y=-6)
    groups, rules = [], []
    for i, (_, name, _, stack, lines) in enumerate(CARDS):
        a, b = i * slot, (i + 1) * slot
        stops = [(0, below)] + ([(a, below)] if i else []) + [(a + fade, shown), (b - fade, shown), (b, above)]
        stops += [] if i == len(CARDS) - 1 else [(100, above)]
        rules.append(track(f"pj{i}", stops, shown if i == 0 else above, period))
        groups.append(f'<g class="pj{i}">'
                      f'{text(W - PAD, 40, f"{i + 1} / {len(CARDS)}", t["faint"], 11, NUM)}'
                      f'{text(PAD, 88, name, t["fg"], 28, "font-weight=\"600\" letter-spacing=\"-0.3\"")}'
                      f'{text(W - PAD, 88, stack, t["faint"], 12, "text-anchor=\"end\" font-weight=\"500\"")}'
                      f'{text(PAD, 116, " ".join(lines), t["sub"], 15)}</g>')
    rules.append("@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
    names = ", ".join(c[1] for c in CARDS)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
            f'aria-label="My projects, one at a time: {names}">'
            f'<style>{"".join(rules)}</style><rect width="{W}" height="{H}" rx="18" fill="{t["bg"]}"/>'
            f'<g font-family="{SANS}">{text(PAD, 40, "PROJECTS", t["faint"], 11, "font-weight=\"500\" letter-spacing=\"1.2\"")}'
            f'{"".join(groups)}</g></svg>\n')


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
        (ROOT / "assets" / f"spotlight-{theme}.svg").write_text(spotlight(tokens))
        for slug, name, icon, stack, lines in CARDS:
            (ROOT / "assets" / "cards" / f"{slug}-{theme}.svg").write_text(card(tokens, name, icon, stack, lines))
    print(f"assets/spotlight-*.svg and {len(CARDS) * len(THEMES)} cards written")


if __name__ == "__main__":
    main()
