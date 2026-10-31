# ruff: noqa: E501  (slide text and SVG markup are long literals)
"""Writes GhostQPU README SVGs (vault theme, system fonts, 1200 viewBox). Usage: python readme_svgs.py <repo>/assets/readme"""

import sys
from pathlib import Path

OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
INK, NAVY, ICE, FROST, MUTE, GEN, FORGED = "#030b17", "#0b2747", "#8fd3ff", "#eaf4ff", "#8aa3c0", "#5aa0f2", "#eb6834"

# Real data: ibm_kingston job K1 (2026-10-29), mean P(1) over 4 placements after N plain X gates.
N = [0, 4, 8, 16, 32, 64, 128]
HW = [0.001, 0.003, 0.011, 0.025, 0.076, 0.348, 0.906]
FZ = [0.003, 0.001, 0.004, 0.005, 0.010, 0.011, 0.024]


def svg(h, title, desc, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{h}" viewBox="0 0 1200 {h}" role="img" '
        f'aria-labelledby="title desc">\n<title id="title">{title}</title>\n<desc id="desc">{desc}</desc>\n'
        f'<defs><radialGradient id="glow" cx="72%" cy="0%" r="90%"><stop offset="0" stop-color="#16406c"/>'
        f'<stop offset="1" stop-color="{INK}"/></radialGradient></defs>\n'
        f'<rect width="1200" height="{h}" rx="24" fill="url(#glow)"/>\n{body}\n</svg>\n'
    )


def ribs(cx, cy, h, n=16, opacity=0.16):
    out = []
    for i in range(1, n + 1):
        s = i * 70
        for side in (1, -1):
            out.append(
                f'<path d="M{cx + side * s} {h + 20} Q{cx + side * s * 1.08} {cy - 10} {cx + side * s * 0.05} {cy}" '
                f'fill="none" stroke="{ICE}" stroke-opacity="{opacity * (1 - i / (n + 4)):.3f}" stroke-width="1.2"/>'
            )
    for k in range(5):
        out.append(
            f'<ellipse cx="{cx}" cy="{cy + 30}" rx="{220 + k * 170}" ry="{50 + k * 38}" fill="none" '
            f'stroke="{ICE}" stroke-opacity="{0.05 + k * 0.012:.3f}" stroke-width="{6 if k == 2 else 1.2}"/>'
        )
    return "\n".join(out)


def hero():
    x0, y0, w, h = 690, 96, 440, 230
    def px(n):
        return x0 + n / 128 * w
    def py(p):
        return y0 + h - p * h
    def path(ys):
        return " ".join(
            f"{'M' if i == 0 else 'L'}{px(n):.1f},{py(p):.1f}" for i, (n, p) in enumerate(zip(N, ys, strict=False))
        )
    def dots(ys, c):
        return "".join(f'<circle cx="{px(n):.1f}" cy="{py(p):.1f}" r="5" fill="{c}"/>' for n, p in zip(N, ys, strict=False))
    grid = "".join(
        f'<line x1="{x0}" x2="{x0 + w}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="{ICE}" stroke-opacity="0.12"/>'
        f'<text x="{x0 - 12}" y="{py(v) + 6:.1f}" text-anchor="end" font-family="{MONO}" font-size="18" fill="{MUTE}">{v:.1f}</text>'
        for v in (0, 0.5, 1.0)
    )
    body = f"""{ribs(860, 120, 420)}
<g id="title">
  <text x="64" y="150" font-family="{SANS}" font-size="78" font-weight="700" fill="{FROST}" letter-spacing="-2">GhostQPU</text>
  <text x="66" y="206" font-family="{SANS}" font-size="30" fill="{FROST}">Catch quantum jobs that never</text>
  <text x="66" y="246" font-family="{SANS}" font-size="30" fill="{FROST}">touched a <tspan fill="{ICE}" font-weight="600">quantum computer</tspan>.</text>
  <text x="66" y="308" font-family="{MONO}" font-size="18" fill="{MUTE}">Hidden Canary circuits vs a Forger built from</text>
  <text x="66" y="334" font-family="{MONO}" font-size="18" fill="{MUTE}">IBM's public calibration data</text>
</g>
<g id="proof-chart">
  <rect x="610" y="40" width="550" height="360" rx="18" fill="#071a30" stroke="{ICE}" stroke-opacity="0.22"/>
  <text x="640" y="76" font-family="{MONO}" font-size="18" fill="{ICE}">P(error) after N X gates · ibm_kingston</text>
  {grid}
  <path d="{path(HW)}" fill="none" stroke="{GEN}" stroke-width="4" stroke-linejoin="round"/>{dots(HW, GEN)}
  <path d="{path(FZ)}" fill="none" stroke="{FORGED}" stroke-width="4" stroke-linejoin="round"/>{dots(FZ, FORGED)}
  <text x="{px(128) - 8:.1f}" y="{py(0.906) - 16:.1f}" text-anchor="end" font-family="{SANS}" font-size="22" font-weight="600" fill="{GEN}">real QPU 91%</text>
  <text x="{px(128) - 8:.1f}" y="{py(0.024) - 16:.1f}" text-anchor="end" font-family="{SANS}" font-size="22" font-weight="600" fill="{FORGED}">Forger 2%</text>
  <text x="{x0}" y="{y0 + h + 34}" font-family="{MONO}" font-size="18" fill="{MUTE}">N = 0</text>
  <text x="{x0 + w}" y="{y0 + h + 34}" text-anchor="end" font-family="{MONO}" font-size="18" fill="{MUTE}">128</text>
</g>"""
    (OUT / "hero.svg").write_text(
        svg(
            420,
            "GhostQPU",
            "Catch quantum jobs that never touched a quantum computer. Chart: after 128 X gates a "
            "real ibm_kingston qubit reads wrong 91% of the time; the calibration-matched Forger predicts 2%.",
            body,
        ),
        encoding="utf-8",
    )


def proof():
    cards = [
        ("56/56", "jobs called right by a", "Detector frozen on 10 Oct"),
        ("3 · 20", "IBM machines ·", "calibration cycles"),
        ("1.5 s", "of QPU time for Canaries", "still catches all 60 jobs"),
    ]
    g = []
    for i, (big, a, b) in enumerate(cards):
        x = 48 + i * 376
        g.append(
            f'<rect x="{x}" y="40" width="352" height="220" rx="18" fill="#071a30" stroke="{ICE}" stroke-opacity="0.22"/>'
            f'<text x="{x + 32}" y="138" font-family="{SANS}" font-size="64" font-weight="300" fill="{FROST}" letter-spacing="-2">{big}</text>'
            f'<text x="{x + 34}" y="190" font-family="{SANS}" font-size="22" fill="{MUTE}">{a}</text>'
            f'<text x="{x + 34}" y="220" font-family="{SANS}" font-size="22" fill="{MUTE}">{b}</text>'
        )
    (OUT / "proof.svg").write_text(
        svg(
            300,
            "GhostQPU results",
            "56 of 56 later jobs called correctly by a Detector frozen on 10 October; "
            "3 IBM machines and 20 calibration cycles; 1.5 QPU seconds of Canaries still catches all 60 jobs.",
            "\n".join(g),
        ),
        encoding="utf-8",
    )


def how():
    def box(x, y, w, h, l1, l2, stroke=ICE, fill="#071a30"):
        return (
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}" stroke="{stroke}" stroke-opacity="0.6" stroke-width="1.5"/>'
            f'<text x="{x + w / 2}" y="{y + h / 2 - 4}" text-anchor="middle" font-family="{SANS}" font-size="22" font-weight="600" fill="{FROST}">{l1}</text>'
            f'<text x="{x + w / 2}" y="{y + h / 2 + 24}" text-anchor="middle" font-family="{SANS}" font-size="18" fill="{MUTE}">{l2}</text>'
        )

    def arrow(x1, y1, x2, y2, c=ICE):
        return (
            f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{c}" stroke-opacity="0.7" stroke-width="2" fill="none"/>'
            f'<circle cx="{x2}" cy="{y2}" r="4" fill="{c}"/>'
        )

    body = "\n".join(
        [
            box(40, 140, 220, 100, "Your Batch", "30 hidden Canaries"),
            arrow(260, 190, 330, 110),
            arrow(260, 190, 330, 270, FORGED),
            box(330, 60, 260, 100, "IBM quantum computer", "honest provider", GEN),
            box(330, 220, 260, 100, "Forger", "Aer + public calibration", FORGED),
            arrow(590, 110, 650, 190),
            arrow(590, 270, 650, 190, FORGED),
            box(650, 140, 230, 100, "Signature", "12 features × 8 chunks"),
            arrow(880, 190, 930, 190),
            box(930, 110, 230, 76, "|GENUINE〉", "", GEN, "#0a2340"),
            box(930, 200, 230, 76, "|FORGED〉", "", FORGED, "#2a1408"),
            f'<text x="40" y="380" font-family="{MONO}" font-size="18" fill="{MUTE}">Canaries measure what the calibration leaves out: '
            f"over-rotation, neighbor crosstalk, readout context, drift.</text>",
        ]
    )
    (OUT / "how-it-works.svg").write_text(
        svg(
            420,
            "How GhostQPU works",
            "Your Batch hides 30 Canary circuits. Either an IBM quantum computer "
            "or the Forger (Aer plus public calibration) runs it. Twelve Canary features over eight time "
            "chunks feed the Detector, which returns Genuine or Forged.",
            body,
        ),
        encoding="utf-8",
    )


def divider(gate, name):
    body = (
        f'<line x1="150" x2="1050" y1="40" y2="40" stroke="{ICE}" stroke-opacity="0.45" stroke-width="2"/>'
        f'<text x="96" y="47" font-family="{MONO}" font-size="22" fill="{ICE}">|0〉</text>'
        f'<rect x="560" y="18" width="80" height="44" rx="8" fill="{INK}" stroke="{ICE}" stroke-width="2"/>'
        f'<text x="600" y="48" text-anchor="middle" font-family="{MONO}" font-size="22" fill="{ICE}">{gate}</text>'
        f'<rect x="1050" y="18" width="56" height="44" rx="8" fill="{INK}" stroke="{ICE}" stroke-opacity="0.7" stroke-width="2"/>'
        f'<path d="M1062 52 A16 16 0 0 1 1094 52" stroke="{ICE}" stroke-width="2" fill="none"/>'
        f'<line x1="1078" y1="52" x2="1088" y2="30" stroke="{ICE}" stroke-width="2"/>'
    )
    s = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="80" viewBox="0 0 1200 80" role="img" aria-labelledby="title">'
        f'<title id="title">Qubit wire divider</title><rect width="1200" height="80" rx="16" fill="{INK}"/>{body}</svg>\n'
    )
    (OUT / f"wire-{name}.svg").write_text(s, encoding="utf-8")


hero()
proof()
how()
for g, n in (("H", "how"), ("U", "run"), ("M", "results")):
    divider(g, n)
print(sorted(p.name for p in OUT.iterdir()))
