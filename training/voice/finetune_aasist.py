"""Fine-tune AASIST-L from its pretrained weights, or train it from scratch,
with RawBoost + deployment-channel augmentation (training/voice/augment.py).

Runs in the AASIST venv (CUDA torch), like eval/voice/score_aasist.py:
  ..\\aasist\\.venv\\Scripts\\python.exe training/voice/finetune_aasist.py ^
      --root C:/.../datasets/ASVspoof2019/LA --run-name aasist-l_ft_both

  # ablation: same pipeline from random init
  ... --init scratch --epochs 30 --lr 1e-4 --run-name aasist-l_scratch_both

Data rules (docs/EVALUATION_PLAN.md §3): trains on ASVspoof 2019 LA *train* only;
model selection uses a fixed subset of LA *dev*, scored twice — clean, and
through a deterministic channel simulation — and picks the checkpoint with
the lowest mean dev EER. No eval set (LA eval, In-the-Wild, Indian sets, our
device recordings) is ever read here.

Outputs (outside the repo, weights are never committed) in <out-dir>/<run-name>/:
  best.pth, swa.pth, final.pth (whichever of best/SWA has the lower dev metric),
  last.pth (full training state for --resume), log.jsonl, summary.json
Then score final.pth with eval/voice/score_aasist.py --weights ... --method-name ...
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from torch import nn
from torch.optim.swa_utils import AveragedModel, update_bn
from torch.utils.data import DataLoader, Dataset, Subset

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "eval"))
import augment  # noqa: E402
import metrics  # noqa: E402
from voice import datasets  # noqa: E402

NB_SAMP = 64600
DEV_SEED = 20261028
_rng = np.random.default_rng()  # replaced per DataLoader worker in _seed_worker


def _seed_worker(_):
    global _rng
    _rng = np.random.default_rng(torch.utils.data.get_worker_info().seed % 2**32)


def _read(path):
    x, _ = sf.read(path, dtype="float32", always_2d=True)
    return x.mean(axis=1)


class TrainSet(Dataset):
    """Random 4 s crop (AASIST's pad_random) + random augmentation."""

    def __init__(self, items, aug):
        self.items, self.aug = items, aug

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        x = _read(self.items[i]["path"])
        if x.shape[0] > NB_SAMP:
            start = _rng.integers(0, x.shape[0] - NB_SAMP)
            x = x[start:start + NB_SAMP]
        x = augment.fix_length(x, NB_SAMP)
        if self.aug != "none":
            x = augment.augment(x, _rng, self.aug)
        return torch.from_numpy(x), int(self.items[i]["label"] == "bonafide")


class DevSet(Dataset):
    """First 4 s (AASIST's eval policy); optionally through a *deterministic* channel."""

    def __init__(self, items, with_channel):
        self.items, self.with_channel = items, with_channel

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        x = augment.fix_length(_read(self.items[i]["path"]), NB_SAMP)
        if self.with_channel:
            x = augment.channel(x, np.random.default_rng([DEV_SEED, i]), p=0.6)
        return torch.from_numpy(x), int(self.items[i]["label"] == "bonafide")


def dev_subset(items, n_attack, seed=0):
    """All bona fide dev clips + a fixed random sample of attacks."""
    bona = [it for it in items if it["label"] == "bonafide"]
    attack = [it for it in items if it["label"] == "attack"]
    pick = np.random.default_rng(seed).choice(len(attack), min(n_attack, len(attack)), replace=False)
    return bona + [attack[k] for k in sorted(pick)]


def evaluate(model, loader, device):
    model.eval()
    scores, labels = [], []
    with torch.no_grad():
        for x, y in loader:
            _, out = model(x.to(device, non_blocking=True))
            scores.append(out[:, 1].float().cpu().numpy())
            labels.append(y.numpy())
    s, lab = np.concatenate(scores), np.concatenate(labels).astype(bool)
    return metrics.eer(s[lab], s[~lab])[0]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root", required=True, help="ASVspoof 2019 LA folder")
    p.add_argument("--run-name", required=True)
    p.add_argument("--init", default="pretrained", choices=["pretrained", "scratch"])
    p.add_argument("--variant", default="AASIST-L", choices=["AASIST-L", "AASIST"])
    p.add_argument("--aasist-dir", default=str(REPO_ROOT.parent / "aasist"))
    p.add_argument("--out-dir", default=None, help="default: <aasist-dir>/runs")
    p.add_argument("--aug", default="both", choices=["none", "rawboost", "channel", "both"])
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--lr", type=float, default=2e-5, help="2e-5 for fine-tuning; ~1e-4 from scratch")
    p.add_argument("--lr-min", type=float, default=5e-6)
    p.add_argument("--batch-size", type=int, default=8,
                   help="8 with mixed precision fits the 6 GB GPU comfortably (~23 clips/s)")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--dev-attacks", type=int, default=3000, help="attack clips in the dev subset (all bona fide kept)")
    p.add_argument("--seed", type=int, default=1234)
    p.add_argument("--no-amp", action="store_true", help="disable mixed precision")
    p.add_argument("--resume", action="store_true", help="continue from <run>/last.pth")
    p.add_argument("--train-limit", type=int, default=None, help="smoke test only")
    p.add_argument("--dev-limit", type=int, default=None, help="smoke test only")
    args = p.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    amp = device == "cuda" and not args.no_amp
    torch.backends.cudnn.benchmark = True

    aasist_dir = Path(args.aasist_dir)
    sys.path.insert(0, str(aasist_dir))
    from models.AASIST import Model  # AASIST repo (MIT, clovaai)

    run_dir = Path(args.out_dir or aasist_dir / "runs") / args.run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    config = json.loads((aasist_dir / "config" / f"{args.variant}.conf").read_text())

    # ---- data (train + dev only, by construction)
    train_items = datasets.asvspoof2019_la(args.root, "train")
    dev_items = dev_subset(datasets.asvspoof2019_la(args.root, "dev"), args.dev_attacks)
    if args.train_limit:
        train_items = train_items[:: max(1, len(train_items) // args.train_limit)][: args.train_limit]
    if args.dev_limit:
        dev_items = dev_items[:: max(1, len(dev_items) // args.dev_limit)][: args.dev_limit]
    # Each Windows worker process loads its own copy of the CUDA DLLs; keeping train *and* dev
    # workers alive at once exhausted the paging file (WinError 1455). So only the train
    # loader's workers persist, and dev loaders start a few fresh ones per evaluation.
    train_loader = DataLoader(TrainSet(train_items, args.aug), batch_size=args.batch_size,
                              shuffle=True, drop_last=True, num_workers=args.workers,
                              pin_memory=device == "cuda", persistent_workers=args.workers > 0,
                              worker_init_fn=_seed_worker)
    dev_loaders = {name: DataLoader(DevSet(dev_items, ch), batch_size=16, shuffle=False,
                                    num_workers=min(args.workers, 3), pin_memory=device == "cuda")
                   for name, ch in (("clean", False), ("channel", True))}

    # ---- model / optimisation (loss, optimiser and SWA mirror AASIST's main.py)
    model = Model(config["model_config"]).to(device)
    if args.init == "pretrained":
        model.load_state_dict(torch.load(aasist_dir / "models" / "weights" / f"{args.variant}.pth",
                                         map_location=device))
    criterion = nn.CrossEntropyLoss(weight=torch.tensor([0.1, 0.9], device=device))
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, betas=(0.9, 0.999), weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs * len(train_loader), eta_min=args.lr_min)
    scaler = torch.amp.GradScaler(enabled=amp)
    swa_model = AveragedModel(model)  # torchcontrib's SWA is unmaintained; same idea, built into torch
    state = dict(epoch=0, best=float("inf"), swa_n=0)

    if args.resume and (run_dir / "last.pth").exists():
        ck = torch.load(run_dir / "last.pth", map_location=device, weights_only=False)
        for obj, key in ((model, "model"), (optimizer, "optimizer"), (scheduler, "scheduler"),
                         (scaler, "scaler"), (swa_model, "swa_model")):
            obj.load_state_dict(ck[key])
        state = ck["state"]
        print(f"resumed after epoch {state['epoch']}")
    else:
        (run_dir / "log.jsonl").unlink(missing_ok=True)

    (run_dir / "args.json").write_text(json.dumps(vars(args), indent=2))
    print(f"train {len(train_items)} clips, dev {len(dev_items)} clips x2 (clean, channel), "
          f"{len(train_loader)} steps/epoch, amp={amp}, out={run_dir}")

    if state["epoch"] == 0 and not args.resume:
        dev = {k: evaluate(model, dl, device) for k, dl in dev_loaders.items()}
        print(f"epoch 0 (before training): dev EER clean {100 * dev['clean']:.2f}%  "
              f"channel {100 * dev['channel']:.2f}%")
        _log(run_dir, dict(epoch=0, dev_eer_clean=dev["clean"], dev_eer_channel=dev["channel"]))

    for epoch in range(state["epoch"] + 1, args.epochs + 1):
        model.train()
        t0, running, n = time.time(), 0.0, 0
        for step, (x, y) in enumerate(train_loader, 1):
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
                _, out = model(x, Freq_aug=True)
            loss = criterion(out.float(), y)
            optimizer.zero_grad(set_to_none=True)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()
            running, n = running + loss.item() * len(y), n + len(y)
            if step % 100 == 0 or step == len(train_loader):
                rate = n / (time.time() - t0)
                print(f"\repoch {epoch}/{args.epochs}  step {step}/{len(train_loader)}  loss {running / n:.4f}  "
                      f"{rate:.0f} clips/s  epoch ETA {(len(train_loader) - step) * args.batch_size / rate / 60:.1f} min",
                      end="", flush=True)
        print()

        dev = {k: evaluate(model, dl, device) for k, dl in dev_loaders.items()}
        select = (dev["clean"] + dev["channel"]) / 2
        improved = select < state["best"]
        if improved:
            state["best"] = select
            torch.save(model.state_dict(), run_dir / "best.pth")
            swa_model.update_parameters(model)  # like AASIST: average the checkpoints that improved dev
            state["swa_n"] += 1
        state["epoch"] = epoch
        _log(run_dir, dict(epoch=epoch, train_loss=running / n, lr=scheduler.get_last_lr()[0],
                           dev_eer_clean=dev["clean"], dev_eer_channel=dev["channel"], select=select,
                           improved=improved, minutes=(time.time() - t0) / 60))
        print(f"epoch {epoch}: dev EER clean {100 * dev['clean']:.2f}%  channel {100 * dev['channel']:.2f}%"
              f"{'  * new best' if improved else ''}  ({(time.time() - t0) / 60:.1f} min)")
        torch.save(dict(model=model.state_dict(), optimizer=optimizer.state_dict(),
                        scheduler=scheduler.state_dict(), scaler=scaler.state_dict(),
                        swa_model=swa_model.state_dict(), state=state), run_dir / "last.pth")

    # ---- SWA: recompute BatchNorm statistics, then keep whichever of best/SWA wins on dev
    del train_loader  # shuts down its persistent workers before update_bn starts new ones
    summary = dict(best_select=state["best"], swa_checkpoints=state["swa_n"])
    final = "best"
    if state["swa_n"] > 1:
        bn_items = Subset(TrainSet(train_items, args.aug), range(0, len(train_items), max(1, len(train_items) // 2000)))
        update_bn(DataLoader(bn_items, batch_size=args.batch_size, num_workers=args.workers,
                             worker_init_fn=_seed_worker), swa_model, device)
        swa_dev = {k: evaluate(swa_model, dl, device) for k, dl in dev_loaders.items()}
        summary.update(swa_dev_eer_clean=swa_dev["clean"], swa_dev_eer_channel=swa_dev["channel"],
                       swa_select=(swa_dev["clean"] + swa_dev["channel"]) / 2)
        torch.save(swa_model.module.state_dict(), run_dir / "swa.pth")
        if summary["swa_select"] <= state["best"]:
            final = "swa"
        print(f"SWA of {state['swa_n']} checkpoints: dev EER clean {100 * swa_dev['clean']:.2f}%  "
              f"channel {100 * swa_dev['channel']:.2f}%")
    shutil.copyfile(run_dir / f"{final}.pth", run_dir / "final.pth")
    summary["final"] = final
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"final model = {final}.pth -> {run_dir / 'final.pth'}")


def _log(run_dir, record):
    with open(run_dir / "log.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    main()
