# ruff: noqa: E501  (slide text and SVG markup are long literals)
"""Rewrite the bullet text of the team's Q-Hack template deck in place, keeping each slide's own formatting.

Usage: python edit_deck.py <unpacked dir> <pooled_line>
"""

import copy
import sys
from pathlib import Path

from lxml import etree

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}
A = "{{{}}}".format(NS["a"])
ROOT = Path(sys.argv[1]) / "ppt" / "slides"
POOLED = sys.argv[2]


def load(n):
    path = ROOT / f"slide{n}.xml"
    return path, etree.parse(str(path))


def body_with(tree, anchor):
    for tx in tree.iter(A.replace("}", "}") + "txBody") if False else tree.iter("{{{}}}txBody".format(NS["p"])):
        if anchor in "".join(tx.itertext()):
            return tx
    raise KeyError(anchor)


def set_bullets(n, anchor, items):
    """Replace the bullet paragraphs (those starting with the red square) of the text body containing anchor."""
    path, tree = load(n)
    tx = body_with(tree, anchor)
    paras = tx.findall(A + "p")
    bullets = [p for p in paras if "".join(p.itertext()).startswith("■")]
    tpl = bullets[0]
    runs = tpl.findall(A + "r")
    ppr = tpl.find(A + "pPr")
    mark_rpr = runs[0].find(A + "rPr")
    rest = [r.find(A + "rPr") for p in bullets for r in p.findall(A + "r")[1:]]
    bold_rpr = next(rp for rp in rest if rp.get("b") == "1")
    norm_rpr = next((rp for rp in rest if rp.get("b") != "1"), bold_rpr)
    anchor_el = bullets[0].getprevious()
    for p in bullets:
        tx.remove(p)
    insert_at = list(tx).index(anchor_el) + 1 if anchor_el is not None and anchor_el.getparent() is tx else len(tx)
    for k, (label, text) in enumerate(items):
        p = etree.Element(A + "p")
        if ppr is not None:
            p.append(copy.deepcopy(ppr))
        for t, rpr in (("■  ", mark_rpr), (label + " ", bold_rpr), (text, norm_rpr)):
            r = etree.SubElement(p, A + "r")
            rp = copy.deepcopy(rpr)
            rp.attrib.pop("err", None)
            if t is not text or rpr is norm_rpr:
                pass
            if rpr is norm_rpr and norm_rpr is bold_rpr:
                rp.set("b", "0")
            r.append(rp)
            etree.SubElement(r, A + "t").text = t
        tx.insert(insert_at + k, p)
    tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone=True)


def replace_text(n, old, new):
    path, tree = load(n)
    exact = [t for t in tree.iter(A + "t") if t.text and t.text.strip() == old]
    hits = exact if len(exact) == 1 else [t for t in tree.iter(A + "t") if t.text and old in t.text]
    assert len(hits) == 1, (n, old, len(hits))
    hits[0].text = hits[0].text.replace(old, new)
    tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone=True)


# Slide 1: the template's label and value boxes are too narrow, so their text wraps over the pills. Keep each on one line.
path, tree = load(1)
LABEL_SZ = {"Team Name:": "3000", "Team Lead Name:": "3000", "Track:": "3000", "Problem Statement title:": "3000"}
VALUES = ("lwyrup", "Neelagiri Karthikeya", "Quantum Security & Cryptography", "Detecting Faked Quantum Cloud Jobs")
for tx in tree.iter("{{{}}}txBody".format(NS["p"])):
    text = "".join(tx.itertext()).strip()
    if text in LABEL_SZ or text in VALUES:
        tx.find(A + "bodyPr").set("wrap", "none")
    if text in LABEL_SZ:
        for r in tx.iter(A + "rPr"):
            r.set("sz", LABEL_SZ[text])
tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone=True)

# Section titles that wrap out of their pills in the template.
for n, title in ((4, "Proposed Solution"), (5, "Why Quantum?"), (6, "Implementation and Architecture"), (8, "Results / Validation")):
    path, tree = load(n)
    tx = body_with(tree, title)
    tx.find(A + "bodyPr").set("wrap", "none")
    # LibreOffice ignores wrap="none" here, so also widen the box around its centre to fit the text.
    xfrm = tx.getparent().find("{{{}}}spPr/{}xfrm".format(NS["p"], A))
    off, ext = xfrm.find(A + "off"), xfrm.find(A + "ext")
    size = int(tx.find(".//" + A + "rPr").get("sz")) / 100
    need = int(len(title) * 0.6 * size * 12700)
    cx = int(ext.get("cx"))
    if need > cx:
        off.set("x", str(int(off.get("x")) - (need - cx) // 2))
        ext.set("cx", str(need))
    tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone=True)

# Slide 1: whole team.

# Slide 4: proposed solution.
set_bullets(
    4,
    "Hidden canaries",
    [
        (
            "Hidden canaries:",
            "30 small test circuits ride inside each 34-circuit job, compiled and shuffled so the provider can't tell which are tests.",
        ),
        (
            "Physics a simulator leaves out:",
            "canaries trigger coherent error build-up, neighbor crosstalk, context-dependent readout and drift.",
        ),
        (
            "Detector:",
            "turns canary results into a verdict (Genuine, Forged or Inconclusive). One command: python -m ghostqpu verify <job>.",
        ),
        (
            "We built the attacker too:",
            "a Forger using the exact calibration live when each job ran, plus a stronger Forger that learns hardware effects.",
        ),
        (
            "Disguised canaries:",
            "a random circuit followed by its reverse looks like customer work, yet still exposes the Forger.",
        ),
    ],
)

# Slide 5: why quantum.
set_bullets(
    5,
    "The evidence is quantum",
    [
        (
            "The evidence is quantum:",
            "the fingerprint is the physical noise of the real chip, which only exists on quantum hardware.",
        ),
        (
            "Canaries amplify it:",
            "128 repeated X gates turn tiny coherent over-rotations into a 91% error on ibm_kingston, where the Forger predicts 2%.",
        ),
        (
            "Why calibration can't fake it:",
            "published calibration describes each gate on its own with average error rates. Real qubits have coherent, correlated, time-varying noise.",
        ),
        (
            "Real hardware:",
            "three 156-qubit IBM Heron devices (ibm_marrakesh, ibm_fez, ibm_kingston) through Qiskit Runtime, on the free plan.",
        ),
    ],
)

# Slide 6: implementation.
set_bullets(
    6,
    "Calibration snapshot",
    [
        (
            "",
            "Calibration snapshot → Batch builder (canaries + workload, shuffled) → IBM QPU (Qiskit Runtime Sampler, twirling and dynamical decoupling off) → Collect, plus the calibration live at execution → Forger (Qiskit Aer + that calibration) → Signature (12 features per time chunk) → Detector → Verdict",
        ),
        (
            "Quantum components:",
            "3 canary families on 4 isolated qubit pairs at transpiler level 0, plus CNOT and disguised mirror pilot circuits.",
        ),
        (
            "Classical components:",
            "Python, Qiskit 2.5, Qiskit Aer, scikit-learn logistic regression, Next.js + three.js site deployed on GitHub Pages.",
        ),
        (
            "Engineering:",
            "CLI (submit / collect / verify / evaluate / null-test), 36 automated tests, hardware-simulator bit-order parity test, seeded Forger.",
        ),
    ],
)

# Slide 7: prototype.
set_bullets(
    7,
    "Working end-to-end",
    [
        ("Working end-to-end tool:", "python -m ghostqpu submit / collect / verify / evaluate / null-test."),
        (
            "Real hardware runs:",
            "44 IBM jobs on marrakesh, fez and kingston over 4 days: 30 full batches with forged twins, plus 6 short, 5 CNOT and 3 disguised-canary jobs.",
        ),
        (
            "Live site:",
            "jacklachan.github.io/GhostQPU, a six-chapter story with a console that replays real IBM jobs for a blind verdict.",
        ),
        (
            "Interactive:",
            "a Bloch sphere driven by measured data, and a lab where you play the Forger against the real frozen Detector.",
        ),
        (
            "Pilots on hardware:",
            "CNOT canaries, disguised mirror canaries and real 250-shot cost checks on all three machines.",
        ),
        ("Open:", "every run, calibration snapshot and research note is in the GitHub repo."),
    ],
)

# Slide 8: results table and bullets.
for old, new in (
    ("Error after 128 X gates", "Error after 128 X gates (kingston)"),
    ("32%", "91%"),
    ("4%", "2%"),
    ("Idle-qubit shift from neighbor (16 us)", "Idle-qubit shift from neighbor (fez)"),
    ("7.8%", "30%"),
    ("0.4%", "4%"),
    ("Readout error", "Disguised canary all-zero rate (marrakesh)"),
    ("1.1 to 1.4%", "76%"),
    ("0.3 to 0.5%", "88%"),
):
    replace_text(8, old, new)
set_bullets(
    8,
    "Null test",
    [
        ("Frozen Detector, scored blind:", "56 of 56 later jobs correct (28 real, 28 forged), 20 cycles, 3 machines."),
        ("Held out by cycle:", POOLED + " Earlier days only: 56 of 56. Trained on 10 jobs: 40 of 40."),
        ("Null test:", "simulator vs Forger scores AUC 0.52 (chance), so it detects physics, not formatting."),
        ("Cost:", "1.5 QPU seconds of canaries still calls all 60 jobs right."),
        (
            "Why AUC is 1.00:",
            "public calibration has no coherent error, so the Forger is 2-4% wrong where hardware is 30-90%.",
        ),
        ("Smarter Forger:", "learning from a real job fooled the frozen Detector 12/13; retrained, caught 12/13."),
    ],
)

# Slide 9: roadmap.
set_bullets(
    9,
    "Cross-day validation",
    [
        (
            "Done since 10 Oct:",
            "cross-day and cross-backend validation (ibm_fez, ibm_kingston), 85% lower canary cost, disguised canaries.",
        ),
        (
            "Canary-aware forger:",
            "our stronger Forger fooled the original Detector; next, require evidence from two canary families.",
        ),
        (
            "CNOT canary family:",
            "73% vs 10% on marrakesh qubits 107-108, detected on 13 of 16 pairs; make it a production family.",
        ),
        (
            "Customer SDK:",
            "a drop-in wrapper that injects canaries into every job and returns a signed verification report.",
        ),
        ("Scale the evidence:", "weeks of daily runs and more cloud providers to tighten the false-alarm bound."),
    ],
)

# Slide 10: references.
set_bullets(
    10,
    "Prior work",
    [
        (
            "Prior work:",
            "Martina et al. 2022; Pirnay et al. 2022 (forged single-qubit fingerprints); Mutolo et al. 2025 (fingerprinting, no tested forger); Wu, Hu, Li 2024 (catches device substitution, not simulation).",
        ),
        ("IBM Quantum Platform:", "Open plan, Heron backends and published calibration data (quantum.cloud.ibm.com)."),
        ("Software:", "Qiskit, Qiskit Aer, Qiskit IBM Runtime, scikit-learn, Next.js, three.js."),
        (
            "Our code and site:",
            "github.com/Karthikeya47/GhostQPU · jacklachan.github.io/GhostQPU (all implementation is the team's own work).",
        ),
        ("Team lwyrup:", "Neelagiri Karthikeya (lead), L Mohit Jain, Tanvi Jain, Aditi Gorti."),
    ],
)
print("edited")
