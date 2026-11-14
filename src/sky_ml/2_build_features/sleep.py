"""Sleep-EDF Expanded (SC, 10 đêm) → một hàng / epoch 30 s: năng lượng dải tần EEG/EOG → giai đoạn ngủ.

Port NASA-cl prepare_sleep. Đặc trưng dùng cả epoch trước/sau vì đây là CHẤM ĐIỂM HỒI CỨU cả đêm,
không phải dự báo. Giai đoạn 3 + 4 (R&K) gộp thành N3 theo AASM (Iber et al., 2007).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import welch

STAGES = {"Sleep stage W": "W", "Sleep stage 1": "N1", "Sleep stage 2": "N2",
          "Sleep stage 3": "N3", "Sleep stage 4": "N3", "Sleep stage R": "REM"}
CHANNELS = {"EEG Fpz-Cz": "fpz", "EEG Pz-Oz": "pz", "EOG horizontal": "eog"}
BANDS = {"delta": (0.5, 4), "theta": (4, 8), "alpha": (8, 12), "sigma": (12, 15), "beta": (15, 30)}
EPOCH_S = 30


def read_epochs(psg: Path, hypnogram: Path):
    """(tín hiệu µV [kênh × mẫu], fs, [(mẫu bắt đầu, nhãn)]). Bỏ epoch '?', movement, epoch vượt tín hiệu."""
    import mne
    raw = mne.io.read_raw_edf(psg, include=list(CHANNELS), preload=True, verbose="ERROR")
    fs = raw.info["sfreq"]
    signal = raw.get_data(picks=list(CHANNELS)) * 1e6
    epochs = []
    for a in mne.read_annotations(hypnogram):
        label = STAGES.get(a["description"])
        for k in range(round(a["duration"] / EPOCH_S)):
            start = round((a["onset"] + k * EPOCH_S) * fs)
            if label is not None and start + EPOCH_S * fs <= signal.shape[1]:
                epochs.append((start, label))
    return signal, fs, epochs


def band_powers(segments: np.ndarray, fs: float) -> dict:
    """log năng lượng 0,5–30 Hz + log tỷ lệ năng lượng 5 dải (Welch, cửa sổ 2 s)."""
    freqs, power = welch(segments, fs=fs, nperseg=int(2 * fs), axis=-1)
    total = power[:, (freqs >= 0.5) & (freqs <= 30)].sum(axis=1) + 1e-12
    out = {"logpow": np.log(total)}
    for band, (low, high) in BANDS.items():
        out[band] = np.log(power[:, (freqs >= low) & (freqs < high)].sum(axis=1) / total + 1e-12)
    return out


def night_features(psg: Path, hypnogram: Path, wake_margin: int) -> tuple[pd.DataFrame, list[str]]:
    signal, fs, epochs = read_epochs(psg, hypnogram)
    n = int(EPOCH_S * fs)
    night = pd.DataFrame({"subject_id": "sleep_edfx:" + psg.name[:5], "epoch": [s // n for s, _ in epochs],
                          "stage": [label for _, label in epochs]})
    base = []
    for i, short in enumerate(CHANNELS.values()):
        segments = np.stack([signal[i, s:s + n] for s, _ in epochs])
        for name, values in band_powers(segments, fs).items():
            night[f"{short}_{name}"] = values
            base.append(f"{short}_{name}")
    asleep = np.flatnonzero(night.stage != "W")          # cắt bớt đoạn thức dài đầu/cuối đêm
    night = night.iloc[max(0, asleep[0] - wake_margin): asleep[-1] + wake_margin + 1].reset_index(drop=True)
    for c in base:                                       # ngữ cảnh: epoch trước/sau (biên dùng chính nó)
        night[f"{c}_prev"] = night[c].shift(1).fillna(night[c])
        night[f"{c}_next"] = night[c].shift(-1).fillna(night[c])
    return night, base + [f"{c}_prev" for c in base] + [f"{c}_next" for c in base]


def build_sleep(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    psgs = sorted(data_dir / p for p in cfg["inputs"] if p.endswith("-PSG.edf"))
    hyps = {Path(p).name[:6]: data_dir / p for p in cfg["inputs"] if p.endswith("-Hypnogram.edf")}
    nights, available = [], []
    for psg in psgs:
        night, available = night_features(psg, hyps[psg.name[:6]], cfg["wake_margin_epochs"])
        nights.append(night)
    features = available if cfg.get("features") in (None, "all") else list(cfg["features"])
    unknown = set(features) - set(available)
    if unknown:
        raise ValueError(f"Đặc trưng sleep không tồn tại: {sorted(unknown)}")
    return pd.concat(nights, ignore_index=True), features
