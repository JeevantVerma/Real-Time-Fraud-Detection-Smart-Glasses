"""Score a voice dataset with a pretrained (or fine-tuned) AASIST / AASIST-L model.

Runs in the AASIST training venv (CUDA torch), not the backend venv:
  ..\\aasist\\.venv\\Scripts\\python.exe eval/voice/score_aasist.py ^
      --dataset asvspoof2019 --split eval --root C:/.../datasets/ASVspoof2019/LA ^
      --out eval/scores/voice/aasist-l_pretrained__asvspoof2019_eval.csv

Input policy matches the AASIST reference eval exactly: mono, 16 kHz (resampled
if needed), first 64600 samples (~4 s), shorter clips tiled to length.
Score = the model's bona fide logit (higher = more genuine).
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # eval/
import scorefile  # noqa: E402
from voice import datasets  # noqa: E402

SAMPLE_RATE = 16000
NB_SAMP = 64600
DEFAULT_AASIST_DIR = Path(__file__).resolve().parents[3] / "aasist"


def load_audio(path):
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    x = x.mean(axis=1)
    if sr != SAMPLE_RATE:
        from math import gcd
        from scipy.signal import resample_poly  # only needed for non-16 kHz sets
        g = gcd(sr, SAMPLE_RATE)
        x = resample_poly(x, SAMPLE_RATE // g, sr // g).astype(np.float32)
    return x


def fix_length(x, n=NB_SAMP):
    if x.shape[0] >= n:
        return x[:n]
    return np.tile(x, n // x.shape[0] + 1)[:n]


class ScoringSet(Dataset):
    def __init__(self, items):
        self.items = items

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return torch.from_numpy(fix_length(load_audio(self.items[i]["path"]))), i


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    datasets.add_args(p)
    p.add_argument("--out", required=True)
    p.add_argument("--variant", default="AASIST-L", choices=["AASIST-L", "AASIST"])
    p.add_argument("--weights", default=None, help="checkpoint (default: the repo's pretrained weights)")
    p.add_argument("--aasist-dir", default=str(DEFAULT_AASIST_DIR))
    p.add_argument("--method-name", default=None, help="label for reports (default: <variant> pretrained)")
    p.add_argument("--batch-size", type=int, default=16,
                   help="16 fits a 6 GB GPU; above ~24 spills into shared memory and runs ~4x slower")
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args()

    aasist_dir = Path(args.aasist_dir)
    sys.path.insert(0, str(aasist_dir))
    from models.AASIST import Model  # AASIST repo (MIT, clovaai)

    config = json.loads((aasist_dir / "config" / f"{args.variant}.conf").read_text())
    weights = Path(args.weights) if args.weights else aasist_dir / "models" / "weights" / f"{args.variant}.pth"

    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.backends.cudnn.benchmark = True  # fixed input size; deterministic mode only slowed eval
    model = Model(config["model_config"]).to(device)
    model.load_state_dict(torch.load(weights, map_location=device))
    model.eval()

    items = datasets.load(args.dataset, args.root, args.split)
    if args.limit:
        items = items[:: max(1, len(items) // args.limit)][: args.limit]
    loader = DataLoader(ScoringSet(items), batch_size=args.batch_size, shuffle=False,
                        num_workers=args.workers, pin_memory=(device == "cuda"),
                        persistent_workers=args.workers > 0)

    scores = np.empty(len(items), dtype=np.float64)
    t0, done = time.time(), 0
    with torch.no_grad():
        for batch_no, (x, idx) in enumerate(loader, 1):
            _, out = model(x.to(device, non_blocking=True))
            scores[idx.numpy()] = out[:, 1].float().cpu().numpy()
            done += len(idx)
            if batch_no % 50 == 0 or done == len(items):
                rate = done / (time.time() - t0)
                print(f"\r{done}/{len(items)}  {rate:.0f} clips/s  ETA {(len(items) - done) / rate / 60:.1f} min",
                      end="", flush=True)
    print()

    rows = [dict(it, score=f"{s:.6f}") for it, s in zip(items, scores)]
    for r in rows:
        r.pop("path")
    scorefile.write(args.out, rows, dict(
        module="voice", method=args.method_name or f"{args.variant} pretrained",
        model=args.variant, weights=str(weights), dataset=args.dataset, split=args.split,
        dataset_root=str(args.root), limit=args.limit,
        input_policy="mono 16 kHz, first 64600 samples, tiled if shorter", device=device))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
