# GhostQPU presenter notes (Q-Hack India 2026)

About 6 minutes, one chapter of the site at a time. Arrow keys move between chapters; every chapter has its own link.

## Morning checklist

0. Live site: https://jacklachan.github.io/GhostQPU/ · Slides: `docs/GhostQPU_QHack_India26.pptx` (speaker notes included).
1. `cd web` then `npm run dev`, open http://localhost:3000. If the page is blank or shows a build error, stop the
   server, delete `web/.next`, start it again.
2. Backup with no Wi-Fi and no dev server: `cd web && npm run build` writes a static copy to `web/out/` (do it the
   night before). Serve it with `python -m http.server 8080 -d web/out` and open http://localhost:8080. Opening the
   HTML file directly does not work. Also keep the demo video ready (`demo/GhostQPU_demo.mp4`).
3. Browser full screen (F11). Zoom 90% if the projector is low resolution.
4. Click through all six chapters once so the 3D scenes are warm.

## The story

### 1. The problem (`#problem`), 45 s

- "Quantum computing time is sold through resellers. You pay for QPU seconds, but you cannot check the job ever ran on
  a quantum computer."
- "IBM publishes calibration data for every machine. Anyone can turn it into a simulator that produces believable
  results. We built that Forger ourselves, using the exact calibration that was live when each real job ran: the
  strongest fair attacker."
- Point at the screen: the bright lattice is the real 156-qubit ibm_marrakesh chip from its published coupling map; the
  orange copy is the Forger. Hover a qubit to show its real T1, T2 and readout error.

### 2. The trap (`#trap`), 60 s

- Click **Reveal the Canaries**: "34 circuits look identical to the provider. 30 are Canaries with a known answer that
  probe physics the published calibration leaves out."
- Bloch sphere, click **Apply 128 X gates**: "Two X gates should bring the qubit home. Real pulses overshoot slightly
  and the error adds up coherently: the real qubit swings away. The Forger only knows random error, so it just fades.
  On kingston that is 45% versus 2%."

### 3. Run a job (`#run`), 60 s, the judge moment

- Hand a judge the mouse. Pick a machine, **Submit job**, ask them to guess Genuine or Forged before the Detector
  answers.
- Say: "This replays a real recorded IBM job. The shots, the features and the scores are the recorded ones; only the
  pacing is staged. Every score comes from a Detector that never saw that job's calibration cycle."

### 4. The evidence (`#evidence`), 45 s

- Coherent amplification: after 128 X gates hardware reads wrong far more often than the Forger predicts.
- Spectator crosstalk: an idle qubit shifts when its neighbor flips; gate-local noise models say zero.
- Readout depends on the neighbor's state; the Forger uses one number per qubit.

### 5. The verdict (`#verdict`), 60 s

- "We froze the Detector after training on two jobs from 10 October and never retrained it."
- "On every job since, on three IBM machines, it is 56 of 56: 28 real jobs and their forged copies, over 20
  calibration cycles and 4 days, including twelve jobs we ran this morning, on two machines it had never seen."
- Cost card: "Verification is cheap: 1.5 QPU seconds of Canary time still catches all 60 jobs, 85% less than we spend
  today. We checked it on hardware on two days: 12 of 12 real 250-shot runs called right."
- Forward in time: "Trained only on earlier days, it scores the next day 56 of 56."
- Day-to-day chart: "Real hardware wanders between calibrations. The Forger's line is flat. That gap is what we detect."

### 6. Break it (`#break`), 60 s

- Forger lab: "You be the Forger. These sliders copy real hardware physics into the forgery." Fake over-rotation:
  inconclusive. Add crosstalk: it passes as Genuine.
- The point: "To fool it, a Forger has to measure the real hardware's physics, which public calibration does not
  contain. GhostQPU turns a free attack into one that needs real QPU access."
- Disguised Canaries card: "And a provider can't just spot the traps: we hid Canaries inside random-looking circuits
  this morning, and the Forger was still too clean on 45 of 48 of them, on all three machines."
- Close: "We also tested a stronger Forger that fits these effects, and found a new Canary on hardware: repeated CNOTs
  read wrong 73% of the time on one qubit pair where the Forger predicts 10%."

## Numbers to remember

| Claim | Number | Source |
|---|---|---|
| Frozen Detector on later jobs | 56/56 (28 Genuine + 28 Twins), 20 cycles, 3 machines, 4 days | `scripts/score_fresh.py` |
| Error-rate bound with 0 mistakes | 0.12 per job, 0.15 per cycle (95%, one-sided) | same |
| Each cycle held out, all data | 60/60, AUC 1.00, 21 cycles | `docs/research/cost-and-forward.md` |
| Forward in time | 56/56, AUC 1.00, worst real job 0.29 | same |
| Cheapest setting catching all | 1.5 QPU s of Canary time (19 circuits x 250 shots) vs 9.7 s | same |
| Real 250-shot runs on hardware | 12/12 called right (6 jobs + Twins, 2 days); billed 4 to 5 s each incl. about 2 s IBM overhead | same |
| Null test (simulator vs simulator) | AUC 0.52, near chance: PASS | `python -m ghostqpu null-test` |
| Kingston over-rotation, 128 X gates | about 90% vs 3% for the Forger | `docs/research/cross-backend-kingston.md` |
| CNOT Canary, marrakesh 107-108, N=32 | 73% vs 10% | `docs/research/cnot-pilot-hardware.md` |
| Per job cost | 34 circuits x 1000 shots, 11 QPU s billed | IBM usage |

## Hard questions

**"AUC 1.00 looks too good. Is it faked, or is your simulator just bad?"** It is real, and here is why it is 1.00:
IBM's public calibration contains only average random error rates, so a simulator built from it (our Forger, the same
way Qiskit's fake backends work) has no coherent over-rotation at all. Our Canaries amplify exactly that: after 128 X
gates hardware is 30 to 90% wrong and the Forger 2 to 4%, so any threshold separates them. Proof it is not a pipeline
artifact: simulator vs simulator scores 0.52 (chance), and it stayed perfect on two machines and on days it never saw.
The honest catch: our stronger Forger, which learns those effects from one real job, fooled the original Detector
(0.07 and 0.11); retrained, it catches it only weakly (0.64, 0.80). So say "1.00 against a public-data Forger".

**"What's the backend?"** The `ghostqpu` Python package: it builds Batches, submits to IBM Quantum through Qiskit
Runtime, collects results with the execution-time calibration, runs the Forger in Qiskit Aer, computes Signatures and
runs the Detector. It is served over HTTP by a FastAPI app (`uvicorn ghostqpu.api:app`, docs at /docs) with endpoints
for every Run, a Verdict per job and the Detector's weights. The website is a static front-end over its exported results,
so it stays fast and works offline.

**"What about a smarter forger?"** We tested one on 13 job pairs: learning from an earlier real job on the same qubits,
it fooled the frozen Detector 12 times. Retrained on that attacker's output from other days, the Detector caught 12 of 13
with one false alarm. It is an arms race, and the defender can keep up; the forger also has to pay for real QPU time.

**"Your test set is tiny."** Yes. 28 real jobs in 20 cycles. With zero errors the 95% upper bound on the false-positive
rate is still 0.12 to 0.15. The value is the method plus a pre-registered frozen test that holds across days and
machines; the next step is one job per machine per day for weeks.

**"Could a smarter Forger beat it?"** Yes, and we show it. Our stronger Forger fits over-rotation, crosstalk and
readout from one real probe job and fooled the original Detector. But it needs real hardware access to fit those
effects, it does not generalize to the customer's own circuits (no better than the stock Forger on 6 of 7), and adding
Canaries (like the CNOT one) raises the number of effects it must fit per qubit pair.

**"Couldn't the provider spot the Canaries and run only those on hardware?"** Running even the Canaries on real
hardware already costs QPU time. And we tested Canaries that look exactly like customer circuits (a random circuit then
its reverse): on all three machines the Forger was too clean on 45 of 48 (`docs/research/mirror-canaries.md`). A Forger
could add uniform noise to close that gap, but the X-chain Canaries test the shape of the error, so it has to fake both.

**"Is the Detector just memorizing qubits?"** The frozen Detector was trained on four qubit pairs on one machine and
scored fez and kingston, different machines and qubits, correctly. The null test (simulator on both sides) scores 0.52,
so it is not picking up a formatting difference.

**"Why not cryptographic verification?"** Protocols like Mahadev's need far larger and cleaner machines than exist.
GhostQPU works on today's hardware, per job, for seconds of QPU time.

**"Isn't this just device fingerprinting?"** Closest prior work (Wu, Hu and Li 2024) catches a provider swapping in a
different device. We catch a provider swapping in a simulator built from the device's own public calibration, which a
calibration-matched fingerprint would not flag. See `docs/research/prior-work.md`.

**"What was the closest call?"** J3 and J4 on marrakesh, 30 October: 0.36 and 0.43 with the frozen Detector, inside our
inconclusive band. Two separate jobs agreed, so it is that cycle, not noise: after the next recalibration the same qubits
(J5) score 0.00.

**"How would a customer use it?"** One command per job: `python -m ghostqpu verify <job folder>` prints Genuine,
Forged or Inconclusive with the score.

**"How much QPU time did this use?"** 11 seconds per job. The whole study used a few hundred seconds of IBM's free plan.
