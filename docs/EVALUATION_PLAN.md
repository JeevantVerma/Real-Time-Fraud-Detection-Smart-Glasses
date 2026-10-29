# Evaluation Plan (draft — subject to change)

A single evaluation protocol for every module (voice, face, document, fusion, security, hardware), so results in the final report are directly comparable. Drafted 2026-10-27 at the start of the move from heuristics to trained models. Update this file when a decision here changes; record *why* it changed, since the paper's methodology section is written from it.

---

## 1. One shape for every detection module

Each ML module is compared the same way:

**Methods (always the same three rows):**
1. **Heuristic** — the current hand-tuned signal-processing code in `backend/utils/anti_spoofing.py`
2. **Pretrained** — a published model, used as-is
3. **Fine-tuned** — only if tests show a gap; if the pretrained model already performs well on our device data, we skip fine-tuning and report that honestly

**Test tiers (always the same three columns):**

| Tier | What it is | What it proves |
|---|---|---|
| **T1 — Benchmark** | Official test split of the dataset the model was trained on | Our setup reproduces published results |
| **T2 — Real-world / cross-dataset** | A *different* public dataset, Indian data where available | Generalization to unseen conditions and populations |
| **T3 — Our device** | Captured on our own hardware (ESP32, webcam), consented team members | Performance in the actual product |

Standard results table, used for every module:

| Method | T1 EER | T2 EER | T3 EER | APCER / BPCER @ frozen threshold | Params | CPU latency |
|---|---|---|---|---|---|---|

## 2. Metrics

All detection modules are binary *genuine (bona fide) vs. attack*, so one vocabulary (ISO/IEC 30107-3):

- **EER** — Equal Error Rate. Headline number.
- **APCER** — Attack Presentation Classification Error Rate: share of attacks wrongly accepted as genuine (false accept).
- **BPCER** — Bona fide Presentation Classification Error Rate: share of genuine samples wrongly flagged (false reject).
- **AUC** — optional.

Module-specific additions:
- **Voice:** min t-DCF on ASVspoof only (requires ASVspoof's ASV scores; computed with the AASIST repo's `evaluation.py`).
- **Face deepfake:** frame-level vs. video-level AUC, as is standard on FaceForensics++.
- **Face ↔ ID matching:** this is a *same person?* check, not genuine-vs-attack → **FMR / FNMR** (ISO/IEC 19795-1), TAR @ FAR.

## 3. Rules (fixed before seeing any results)

1. **Test sets are chosen up front.** No dataset is added or dropped after seeing its numbers.
2. **Never train on any test set.**
3. **Splits are by speaker / subject** — no person appears in both train and test.
4. **Threshold is set once, on T1's dev split, and frozen.** It is applied unchanged to T2 and T3, so real-world degradation is shown honestly. Each set's own EER (threshold-free) is reported alongside.
5. **95% confidence intervals** on every number (bootstrap; resampled by speaker/subject where IDs exist). Essential for T3, which is small.
6. **One score convention:** higher = more likely genuine. Before backend integration, raw model scores are calibrated on dev (Platt scaling) to 0–1, so 0.65 means the same thing for voice, face and document. Fusion weights and the 0.65 / 0.50 / 0.30 bands depend on this.

## 4. Per-module plan

| Module | T1 | T2 | T3 (own) | Status |
|---|---|---|---|---|
| **Voice** | ASVspoof 2019 LA eval | In-the-Wild (English, real-world); Kathbath (real) + IndicSynth (fake), Hindi, same speakers | ESP32 / laptop mic: real in person, real over a video call, consented voice clones over a call / speaker | T1 pretrained reproduced (AASIST-L EER 0.99%, min t-DCF 0.0309) |
| **Face liveness / deepfake** | FaceForensics++ test | Celeb-DF v2 | Webcam / ESP32: live, printed photo, screen replay, face-swap over a video call | Waiting on FF++ access |
| **Face ↔ ID match** | LFW verification protocol | — | Team ID-style photo vs. live selfie (consented) | Pretrained (Facenet), evaluate only |
| **Document** | SIDTD test split | Another MIDV-based set (TBD) | Printed mock / specimen IDs — never real IDs — genuine and tampered | Not started |

**Voice label definition:** *real human vs. synthetic voice, regardless of channel.* "Played through a speaker" is **not** an attack by itself — every voice on a video call goes through a speaker.

**Face threat scope (proposed):** deepfakes (synthetic face on a video call) are primary, matching the digital-arrest video-call scenario; presentation attacks (print / screen replay) secondary, tested on T3 only. Presentation-attack datasets (e.g. OULU-NPU) need separate license agreements.

## 5. Fusion, security and system levels

| Level | Method (no public dataset exists) | Metrics |
|---|---|---|
| **Fusion** | Labeled synthetic "interactions" built by combining per-module test samples (genuine/attack mixes), plus scripted end-to-end scam scenarios on real hardware | Confusion matrix over the 4 verdicts; **fusion vs. best single module** (key claim); escalation floor on vs. off; "Insufficient evidence" rate |
| **Security layer** | Functional test cases (not ML) | Tampered audit-log entries detected (target 100%); RBAC test matrix pass/fail; threat-intel lookup latency |
| **System / hardware** | Measured on the device | Capture-to-verdict latency (median, 95th percentile); upload success rate vs. Wi-Fi RSSI; power / battery |

## 6. Datasets and licenses

| Dataset | Used for | License | Notes |
|---|---|---|---|
| ASVspoof 2019 LA | Voice T1 (+ fine-tune train/dev) | ODC-By | Eval partition never trained on |
| In-the-Wild (Müller et al. 2022) | Voice T2 | CC BY-SA 4.0 | Test only |
| Kathbath (AI4Bharat) | Voice T2, real Hindi | CC BY 4.0 | Gated: accept terms on Hugging Face |
| IndicSynth (IIIT-Delhi, ACL 2025) | Voice T2, fake Hindi | **CC BY-NC 4.0** | Non-commercial — **test only, never in a shipped model** |
| Svarah (AI4Bharat) | Voice T2, real Indian-accent English (optional) | CC BY 4.0 per AIKosh (unconfirmed on HF card) | Gated |
| FaceForensics++ | Face T1 | Research-only, by request | Access form pending |
| Celeb-DF v2 | Face T2 | Research-only, by request | |
| SIDTD | Document T1 | CC BY-SA 4.0 | |

## 7. Shared tooling — `eval/`

One harness used by every module, so numbers are computed identically:

- Every scorer writes the same **score file**: CSV `id, label, score, subset, attack_type, device, speaker_id` (label ∈ `bonafide` / `attack`; higher score = more genuine), plus a `.meta.json` sidecar (method, model, dataset, input policy, date, git commit).
- `eval/metrics.py` — EER, APCER/BPCER at a threshold, bootstrap CIs, DET curve points. One implementation for all modules.
- `eval/report.py` — turns score files into the standard tables (and DET plots), with the threshold frozen from a dev score file.
- Score files are numbers only (no audio / images / biometric data). They live in `eval/scores/` (gitignored — some are several MB); the generated tables go to `eval/results/` and are committed.
- Datasets and our own recordings live **outside the repo** and never touch the backend's identity-check path (CLAUDE.md fresh-analysis rule).

Usage per module is documented at the top of each scorer script.

## 8. Report chapter outline

1. Evaluation methodology — this protocol, metrics glossary, dataset/license table
2. Voice → face → document results, each in the standard table template
3. Fusion results
4. Security and system performance
5. Limitations / threats to validity — small T3, non-commercial dataset licenses, attacks generated by us, single-device T3
