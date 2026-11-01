"""Training-time audio augmentation for voice anti-spoofing (16 kHz mono float32).

Two families, applied identically to genuine and spoofed clips so the model
can't use the channel itself as a cue:

1. RawBoost (Tak et al., ICASSP 2022) — data-agnostic signal distortions,
   re-implemented here from the paper's description:
     - LnL: linear + non-linear convolutive noise (random multi-band FIR
       filters, outputs raised to increasing powers and summed)
     - ISD: impulsive signal-dependent noise on a random subset of samples
     - SSI: stationary signal-independent coloured noise at random SNR
2. Channel simulation of our deployment path (docs/EVALUATION_PLAN.md):
     video-call codec (Opus / MP3) -> laptop/phone speaker -> room ->
     ESP32 PDM mic band limit + noise.

All randomness comes from the numpy Generator passed in, so a fixed seed
gives a fixed augmentation (used for the deterministic "channel dev" set).
"""

import io

import numpy as np
import scipy.signal
import soundfile as sf

SR = 16000
NYQ = SR / 2


# --------------------------------------------------------------------- RawBoost

def _random_multiband_fir(rng, n_bands=5, min_f=20, max_f=8000, min_bw=100, max_bw=1000,
                          min_taps=10, max_taps=100):
    """Sum of random band-pass FIR filters (the building block of LnL / SSI)."""
    taps = int(rng.integers(min_taps, max_taps + 1)) | 1  # odd length for firwin
    h = np.zeros(taps)
    for _ in range(n_bands):
        fc = rng.uniform(min_f, max_f)
        bw = rng.uniform(min_bw, max_bw)
        lo, hi = max(fc - bw / 2, 1.0), min(fc + bw / 2, NYQ - 1.0)
        if hi - lo < 10:
            continue
        h += scipy.signal.firwin(taps, [lo, hi], pass_zero=False, fs=SR)
    return h if np.any(h) else np.r_[1.0, np.zeros(taps - 1)]


def rawboost_lnl(x, rng, n_f=5):
    y = np.zeros_like(x)
    for j in range(1, n_f + 1):
        gain_db = 0.0 if j == 1 else rng.uniform(-20, -5)  # higher-order terms weaker
        f = scipy.signal.lfilter(_random_multiband_fir(rng), 1.0, x)
        y += 10 ** (gain_db / 20) * f ** j
    return _peak_normalize(y, like=x)


def rawboost_isd(x, rng, max_ratio=0.10, g_sd=2.0):
    y = x.copy()
    n = int(x.size * rng.uniform(0, max_ratio))
    idx = rng.choice(x.size, n, replace=False)
    y[idx] += g_sd * x[idx] * rng.uniform(-1, 1, n)
    return _peak_normalize(y, like=x)


def rawboost_ssi(x, rng, snr_db=(10, 40)):
    noise = scipy.signal.lfilter(_random_multiband_fir(rng), 1.0, rng.standard_normal(x.size))
    return add_noise(x, noise, rng.uniform(*snr_db))


def rawboost(x, rng):
    """One of the RawBoost combinations, chosen at random (as in the paper's ablations)."""
    choice = rng.integers(0, 4)
    if choice == 0:
        return rawboost_lnl(x, rng)
    if choice == 1:
        return rawboost_isd(x, rng)
    if choice == 2:
        return rawboost_ssi(x, rng)
    return rawboost_isd(rawboost_lnl(x, rng), rng)


# ------------------------------------------------------------ channel simulation

def codec(x, rng):
    """Round-trip through a lossy speech/music codec, like a video-call app."""
    fmt, subtype = ("OGG", "OPUS") if rng.random() < 0.75 else ("MP3", "MPEG_LAYER_III")
    buf = io.BytesIO()
    sf.write(buf, np.clip(x, -1, 1), SR, format=fmt, subtype=subtype,
             compression_level=float(rng.uniform(0.3, 0.95)))
    buf.seek(0)
    y, _ = sf.read(buf, dtype="float32")
    return fix_length(y, x.size)


def speaker(x, rng):
    """Small laptop/phone loudspeaker: weak bass, rolled-off treble, mild distortion."""
    hp = rng.uniform(150, 400)
    lp = rng.uniform(5000, 7600)
    sos = scipy.signal.butter(2, [hp, lp], btype="bandpass", fs=SR, output="sos")
    y = scipy.signal.sosfilt(sos, x)
    drive = rng.uniform(1.0, 3.0)
    y = np.tanh(drive * y / (np.max(np.abs(y)) + 1e-9)) / np.tanh(drive)
    return _peak_normalize(y, like=x)


def room(x, rng):
    """Synthetic room impulse response: direct path + exponentially decaying tail."""
    rt60 = rng.uniform(0.15, 0.7)
    n = int(rt60 * SR)
    t = np.arange(n) / SR
    rir = rng.standard_normal(n) * np.exp(-6.9 * t / rt60)  # -60 dB at rt60
    # Direct-to-reverberant ratio 0–10 dB: listener ~0.5–1.5 m from the speaker in a small room.
    tail_energy = np.sum(rir[1:] ** 2)
    rir[0] = np.sqrt(tail_energy * 10 ** (rng.uniform(0, 10) / 10))
    rir /= np.sqrt(np.sum(rir ** 2))
    y = scipy.signal.fftconvolve(x, rir)[: x.size]
    return _peak_normalize(y, like=x)


def mic(x, rng):
    """Cheap MEMS/PDM mic (e.g. ESP32-S3 Sense): band limit plus self/room noise."""
    lp = rng.uniform(3500, 7600)
    sos = scipy.signal.butter(4, [rng.uniform(50, 200), lp], btype="bandpass", fs=SR, output="sos")
    y = scipy.signal.sosfilt(sos, x)
    return add_noise(y, rng.standard_normal(x.size), rng.uniform(15, 40))


def channel(x, rng, p=0.5):
    """Deployment chain; each stage applied with probability p, in physical order."""
    for stage in (codec, speaker, room, mic):
        if rng.random() < p:
            x = stage(x, rng)
    gain = 10 ** (rng.uniform(-6, 6) / 20)
    return np.clip(x * gain, -1, 1).astype(np.float32)


def augment(x, rng, mode):
    """mode ∈ none / rawboost / channel / both (both: RawBoost then channel)."""
    if mode in ("rawboost", "both") and rng.random() < 0.5:
        x = rawboost(x, rng)
    if mode in ("channel", "both") and rng.random() < 0.8:
        x = channel(x, rng)
    return x.astype(np.float32)


# ----------------------------------------------------------------------- helpers

def add_noise(x, noise, snr_db):
    p_sig = np.mean(x ** 2) + 1e-12
    p_noise = np.mean(noise ** 2) + 1e-12
    return x + noise * np.sqrt(p_sig / (p_noise * 10 ** (snr_db / 10)))


def fix_length(x, n):
    if x.shape[0] >= n:
        return x[:n]
    return np.tile(x, n // max(x.shape[0], 1) + 1)[:n]


def _peak_normalize(y, like):
    """Rescale y to the peak level of the original clip (filters change loudness)."""
    peak = np.max(np.abs(y))
    return y * (np.max(np.abs(like)) / peak) if peak > 0 else y
