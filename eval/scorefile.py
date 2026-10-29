"""The one score-file format every scorer writes and report.py reads.

CSV columns: id, label, score, subset, attack_type, device, speaker_id
  label  ∈ {"bonafide", "attack"}
  score  higher = more likely genuine
Plus a `<name>.meta.json` sidecar describing how the scores were produced.
Score files hold numbers only — never audio, images or other biometric data.
"""

import csv
import datetime
import json
import subprocess
from pathlib import Path

import numpy as np

COLUMNS = ["id", "label", "score", "subset", "attack_type", "device", "speaker_id"]
LABELS = ("bonafide", "attack")
REPO_ROOT = Path(__file__).resolve().parent.parent


def write(path, rows, meta: dict):
    """rows: iterable of dicts with COLUMNS keys (missing optional keys become "")."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            if r["label"] not in LABELS:
                raise ValueError(f"bad label {r['label']!r} for {r['id']}")
            w.writerow({k: r.get(k, "") for k in COLUMNS})
            n += 1
    meta = dict(meta, n_rows=n, created=datetime.datetime.now().isoformat(timespec="seconds"),
                git_commit=_git_commit())
    path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def read(path) -> dict:
    """Return column arrays: scores (float), is_bona (bool), and the string columns."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = {k: np.array([r[k] for r in rows]) for k in COLUMNS if k not in ("score", "label")}
    out["scores"] = np.array([float(r["score"]) for r in rows])
    out["is_bona"] = np.array([r["label"] == "bonafide" for r in rows])
    meta_path = Path(path).with_suffix(".meta.json")
    out["meta"] = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    return out


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT,
                              capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""
