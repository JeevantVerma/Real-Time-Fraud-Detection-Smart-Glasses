"""Ablation: give the voice heuristic its best shot by *learning* its weights.

Answers "why not just tune the heuristic?". Uses exactly the deployed features
(backend/utils/anti_spoofing.py: voice_features — HF energy ratio, spectral
centroid std, energy variance), log-scaled and standardized, and fits a
class-balanced logistic regression on ASVspoof 2019 LA *train*. Nothing is
tuned on any test set. Writes standard score files for dev (threshold
freezing), LA eval and In-the-Wild.

Runs in the backend venv:
  backend\\.venv\\Scripts\\python.exe training/voice/heuristic_logreg.py ^
      --asvspoof-root C:/.../datasets/ASVspoof2019/LA ^
      --itw-root C:/.../datasets/InTheWild/release_in_the_wild
"""

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "eval"))
sys.path.insert(0, str(REPO_ROOT / "backend"))
import scorefile  # noqa: E402
from utils.anti_spoofing import voice_features  # noqa: E402
from voice import datasets  # noqa: E402

METHOD = "Heuristic, learned weights"


def features_one(path):
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    return voice_features(x.mean(axis=1), sr)


def extract(items, cache: Path, workers):
    if cache.exists():
        return np.load(cache)["f"]
    t0 = time.time()
    with Pool(workers) as pool:
        f = np.array(pool.map(features_one, [it["path"] for it in items], chunksize=64))
    print(f"  {len(items)} clips in {(time.time() - t0) / 60:.1f} min")
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cache, f=f)
    return f


def transform(f):
    return np.log(np.maximum(f, 1e-12))


def fit_logreg(X, y, l2=1e-3, iters=50):
    """Class-balanced L2 logistic regression by Newton's method (IRLS)."""
    Xb = np.c_[np.ones(len(X)), X]
    w = np.zeros(Xb.shape[1])
    sample_w = np.where(y, 0.5 / y.mean(), 0.5 / (1 - y.mean()))
    for _ in range(iters):
        p = 1 / (1 + np.exp(-Xb @ w))
        grad = Xb.T @ (sample_w * (p - y)) + l2 * np.r_[0, w[1:]]
        H = (Xb * (sample_w * p * (1 - p))[:, None]).T @ Xb + l2 * np.diag(np.r_[0, np.ones(len(w) - 1)])
        step = np.linalg.solve(H, grad)
        w -= step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--asvspoof-root", required=True)
    p.add_argument("--itw-root", required=True)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--out-dir", default=str(REPO_ROOT / "eval" / "scores" / "voice"))
    args = p.parse_args()
    out = Path(args.out_dir)
    cache = out / "_features"

    sets = {
        "asvspoof2019_train": datasets.asvspoof2019_la(args.asvspoof_root, "train"),
        "asvspoof2019_dev": datasets.asvspoof2019_la(args.asvspoof_root, "dev"),
        "asvspoof2019_eval": datasets.asvspoof2019_la(args.asvspoof_root, "eval"),
        "in_the_wild": datasets.in_the_wild(args.itw_root),
    }
    feats = {}
    for name, items in sets.items():
        print(f"features: {name}")
        feats[name] = transform(extract(items, cache / f"heuristic_features__{name}.npz", args.workers))

    # Fit on train only; standardization statistics also from train only.
    mu, sd = feats["asvspoof2019_train"].mean(0), feats["asvspoof2019_train"].std(0) + 1e-12
    y = np.array([it["label"] == "bonafide" for it in sets["asvspoof2019_train"]], dtype=float)
    w = fit_logreg((feats["asvspoof2019_train"] - mu) / sd, y)
    print("weights (bias, log hf_ratio, log centroid_std, log energy_variance):", np.round(w, 3))

    for name in ("asvspoof2019_dev", "asvspoof2019_eval", "in_the_wild"):
        scores = np.c_[np.ones(len(feats[name])), (feats[name] - mu) / sd] @ w
        rows = [dict({k: v for k, v in it.items() if k != "path"}, score=f"{s:.6f}")
                for it, s in zip(sets[name], scores)]
        scorefile.write(out / f"heuristic-lr__{name}.csv", rows, dict(
            module="voice", method=METHOD, model="logistic regression on voice_features (log, standardized)",
            trained_on="asvspoof2019_la_train", weights=[round(float(v), 6) for v in w],
            dataset=name, input_policy="whole clip, native sample rate (as deployed)"))
        print(f"wrote heuristic-lr__{name}.csv")


if __name__ == "__main__":
    main()
