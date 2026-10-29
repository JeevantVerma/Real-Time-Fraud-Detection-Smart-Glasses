"""Score a voice dataset with the current heuristic (backend/utils/anti_spoofing.py).

This is the "Heuristic" baseline row of every results table. Runs in the
backend venv, exactly as the backend runs it (whole clip, native sample rate):
  backend\\.venv\\Scripts\\python.exe eval/voice/score_heuristic.py ^
      --dataset asvspoof2019 --split eval --root C:/.../datasets/ASVspoof2019/LA ^
      --out eval/scores/voice/heuristic__asvspoof2019_eval.csv

Score = voice_liveness_score (0.05–0.98, higher = more genuine). It only takes a
handful of distinct values, so EER is computed over heavily tied scores.
"""

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # eval/
import scorefile  # noqa: E402
from voice import datasets  # noqa: E402

sys.path.insert(0, str(scorefile.REPO_ROOT / "backend"))
from utils.anti_spoofing import analyze_voice_liveness  # noqa: E402


def score_one(path):
    return analyze_voice_liveness(path)["voice_liveness_score"]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    datasets.add_args(p)
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=8)
    args = p.parse_args()

    items = datasets.load(args.dataset, args.root, args.split)
    if args.limit:
        items = items[:: max(1, len(items) // args.limit)][: args.limit]

    scores, t0 = [], time.time()
    with Pool(args.workers) as pool:
        for i, s in enumerate(pool.imap(score_one, [it["path"] for it in items], chunksize=64), 1):
            scores.append(s)
            if i % 2000 == 0 or i == len(items):
                rate = i / (time.time() - t0)
                print(f"\r{i}/{len(items)}  {rate:.0f} clips/s  ETA {(len(items) - i) / rate / 60:.1f} min",
                      end="", flush=True)
    print()

    rows = [dict(it, score=f"{s:.6f}") for it, s in zip(items, scores)]
    for r in rows:
        r.pop("path")
    scorefile.write(args.out, rows, dict(
        module="voice", method="Heuristic", model="analyze_voice_liveness",
        dataset=args.dataset, split=args.split, dataset_root=str(args.root), limit=args.limit,
        input_policy="whole clip, native sample rate (as deployed)"))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
