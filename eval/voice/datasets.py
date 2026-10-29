"""Voice dataset adapters. Each returns a list of dicts:
  id, path, label ("bonafide"/"attack"), subset, attack_type, device, speaker_id

Datasets live outside the repo (see docs/EVALUATION_PLAN.md §6); pass their root.
"""

import csv
from pathlib import Path


def asvspoof2019_la(root, split):
    """ASVspoof 2019 LA. root = the extracted LA/ folder; split ∈ train/dev/eval."""
    root = Path(root)
    proto = root / "ASVspoof2019_LA_cm_protocols" / (
        f"ASVspoof2019.LA.cm.{split}.{'trn' if split == 'train' else 'trl'}.txt")
    audio_dir = root / f"ASVspoof2019_LA_{split}" / "flac"
    items = []
    for line in proto.read_text().splitlines():
        spk, key, _, attack, label = line.split()
        items.append(dict(id=key, path=str(audio_dir / f"{key}.flac"),
                          label="bonafide" if label == "bonafide" else "attack",
                          subset=f"asvspoof2019_la_{split}",
                          attack_type="" if attack == "-" else attack,
                          device="studio_digital", speaker_id=spk))
    return items


def in_the_wild(root):
    """In-the-Wild (Müller et al. 2022). root = folder containing meta.csv and the wavs."""
    meta = next(Path(root).rglob("meta.csv"))
    items = []
    with open(meta, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            items.append(dict(id=r["file"], path=str(meta.parent / r["file"]),
                              label="bonafide" if "bona" in r["label"].lower() else "attack",
                              subset="in_the_wild", attack_type="",
                              device="internet", speaker_id=r["speaker"]))
    return items


def labeled_folder(root):
    """Our own recordings (T3). root contains labels.csv with columns
    path,label[,attack_type,device,speaker_id]; paths are relative to root."""
    root = Path(root)
    items = []
    with open(root / "labels.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            label = r["label"].strip().lower()
            items.append(dict(id=r["path"], path=str(root / r["path"]),
                              label="bonafide" if label in ("bonafide", "bona-fide", "genuine", "real") else "attack",
                              subset=root.name, attack_type=r.get("attack_type", ""),
                              device=r.get("device", ""), speaker_id=r.get("speaker_id", "")))
    return items


def load(name, root, split=None):
    if name == "asvspoof2019":
        return asvspoof2019_la(root, split or "eval")
    if name == "in_the_wild":
        return in_the_wild(root)
    if name == "folder":
        return labeled_folder(root)
    raise ValueError(f"unknown dataset {name!r}")


def add_args(parser):
    parser.add_argument("--dataset", required=True, choices=["asvspoof2019", "in_the_wild", "folder"])
    parser.add_argument("--root", required=True, help="dataset root folder")
    parser.add_argument("--split", default=None, help="asvspoof2019 only: train/dev/eval (default eval)")
    parser.add_argument("--limit", type=int, default=None,
                        help="score only the first N items (smoke test; output is not a valid result)")
