"""Turn score files into the standard results table (docs/EVALUATION_PLAN.md §1).

  python eval/report.py --dev eval/scores/voice/aasist-l_pretrained__asvspoof2019_dev.csv ^
      eval/scores/voice/aasist-l_pretrained__asvspoof2019_eval.csv ^
      eval/scores/voice/aasist-l_pretrained__in_the_wild.csv --out eval/results/voice.md

Thresholds are frozen per method: each --dev file's EER threshold is applied
unchanged to every test file with the same method name (from its .meta.json).
Pass several --dev files to compare several methods in one table.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import metrics  # noqa: E402
import scorefile  # noqa: E402


def pct(x):
    return f"{100 * x:.2f}%"


def set_name(d):
    subsets = np.unique(d["subset"])
    return subsets[0] if subsets.size == 1 else ", ".join(subsets)


def eer_with_ci(d, n_boot):
    bona, attack = d["scores"][d["is_bona"]], d["scores"][~d["is_bona"]]
    value, thr = metrics.eer(bona, attack)
    groups = d["speaker_id"] if np.all(d["speaker_id"] != "") else None
    lo, hi = metrics.bootstrap_ci(lambda b, a: metrics.eer(b, a)[0], d["scores"], d["is_bona"],
                                  groups=groups, n_boot=n_boot)
    return value, thr, lo, hi


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+", help="test score files")
    p.add_argument("--dev", action="append", default=[], help="dev score file(s) to freeze thresholds from")
    p.add_argument("--by", default=None, help="also break EER down by this column, e.g. attack_type")
    p.add_argument("--n-boot", type=int, default=1000)
    p.add_argument("--out", default=None, help="write the markdown here as well as printing it")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252

    thresholds = {}
    for f in args.dev:
        d = scorefile.read(f)
        method = d["meta"].get("method", Path(f).stem)
        thresholds[method] = metrics.eer(d["scores"][d["is_bona"]], d["scores"][~d["is_bona"]])[1]

    lines = ["| Method | Test set | Bona fide / attack | EER [95% CI] | AUC | Frozen thr. | APCER | BPCER |",
             "|---|---|---|---|---|---|---|---|"]
    breakdowns = []
    for f in args.files:
        d = scorefile.read(f)
        method = d["meta"].get("method", Path(f).stem)
        bona, attack = d["scores"][d["is_bona"]], d["scores"][~d["is_bona"]]
        value, _, lo, hi = eer_with_ci(d, args.n_boot)
        thr = thresholds.get(method)
        apcer, bpcer = metrics.rates_at(bona, attack, thr) if thr is not None else (None, None)
        smoke = " ⚠ partial (--limit)" if d["meta"].get("limit") else ""
        lines.append(
            f"| {method} | {set_name(d)}{smoke} | {bona.size} / {attack.size} "
            f"| {pct(value)} [{pct(lo)}, {pct(hi)}] | {metrics.auc(bona, attack):.4f} "
            f"| {'—' if thr is None else f'{thr:.4f}'} "
            f"| {'—' if apcer is None else pct(apcer)} | {'—' if bpcer is None else pct(bpcer)} |")

        if args.by:
            rows = [f"\n**{method} — {set_name(d)}, EER by {args.by}** (each vs. all bona fide)\n",
                    f"| {args.by} | n | EER |", "|---|---|---|"]
            for key in sorted(np.unique(d[args.by][~d["is_bona"]])):
                sub = attack[d[args.by][~d["is_bona"]] == key]
                rows.append(f"| {key or '(none)'} | {sub.size} | {pct(metrics.eer(bona, sub)[0])} |")
            breakdowns.append("\n".join(rows))

    notes = ["", "EER is threshold-free (each set's own). APCER/BPCER use the threshold frozen from "
             "that method's dev set (docs/EVALUATION_PLAN.md §3). CIs: bootstrap, resampled by speaker where IDs exist."]
    text = "\n".join(lines + notes + breakdowns) + "\n"
    print(text)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
