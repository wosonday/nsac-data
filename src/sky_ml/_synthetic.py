"""DỮ LIỆU GIẢ ĐỊNH (synthetic) cho phần persona THIẾU dữ liệu thật — BTC cho phép, phải ghi rõ.

Nguyên tắc:
1. Mọi tham số ƯỚC LƯỢNG TỪ DỮ LIỆU THẬT trong data/1_source (không lấy số từ trí nhớ); ghi vào <tên>.params.json.
2. Mọi hàng có cột `is_synthetic` (True = sinh ra; False = giá trị thật được giữ làm điểm neo) và `generator`.
3. KHÔNG dùng để train hay đánh giá mô hình. Chỉ dùng làm ĐẦU VÀO hiển thị/dự đoán minh họa cho persona;
   dự đoán từ đầu vào giả định mang cờ `input_synthetic = True`.
4. Seed cố định → tái lập byte-by-byte. Mỗi file có README.md (data card) + dòng trong SYNTHETIC_MANIFEST.csv.

Mô hình sinh (chung): y_it = μ(t) + b_i + e_it ;  b_i ~ N(0, σ_b) ;  e_it = ρ·e_i,t−1 + ε ,  ε ~ N(0, σ_e·√(1−ρ²))
  μ(t)  : trung bình quần thể theo ngày nghiên cứu (nội suy tuyến tính giữa các mốc thật)
  σ_b   : SD giữa người của trung bình từng người ;  σ_e, ρ : SD và tự tương quan bậc 1 của phần dư trong người
"""
import importlib
from pathlib import Path

import numpy as np
import pandas as pd

GEN_VERSION = "sky-ml-synthetic-1.0"
nnx = importlib.import_module("sky_ml.2_build_features.cft70_nnx")
act = importlib.import_module("sky_ml.2_build_features.sleep_act")


def _components(frame: pd.DataFrame, value: str, time: str) -> dict:
    """Ước lượng μ(t), σ_b, σ_e, ρ từ dữ liệu thật dạng dài (subject_id, time, value)."""
    f = frame.dropna(subset=[value])
    mu = f.groupby(time)[value].mean()
    resid = f[value] - f[time].map(mu)
    person = resid.groupby(f.subject_id).mean()
    within = resid - f.subject_id.map(person)
    lag = pd.DataFrame({"e": within, "s": f.subject_id}).assign(prev=lambda d: d.groupby("s").e.shift())
    rho = float(lag.dropna()[["e", "prev"]].corr().iloc[0, 1])
    return {"mu": {float(k): float(v) for k, v in mu.items()}, "sigma_between": float(person.std(ddof=1)),
            "sigma_within": float(within.std(ddof=1)), "rho": max(0.0, min(rho, 0.95)),
            "n_people": int(f.subject_id.nunique()), "n_obs": len(f),
            "observed_min": float(f[value].min()), "observed_max": float(f[value].max())}


def _simulate(days, comp, rng, base=0.0):
    mu_t = np.interp(days, list(comp["mu"]), list(comp["mu"].values()))
    sd, rho = comp["sigma_within"], comp["rho"]
    e = np.zeros(len(days))
    e[0] = rng.normal(0, sd)
    for k in range(1, len(days)):
        e[k] = rho * e[k - 1] + rng.normal(0, sd * np.sqrt(1 - rho ** 2))
    return mu_t + base + rng.normal(0, comp["sigma_between"]) + e


def mood_c1(nlsp: Path, personas: dict, seed: int) -> tuple[pd.DataFrame, dict]:
    """POMS-TMD hằng tuần cho 3 persona Campaign 1 (không có POMS thật), theo lịch đo của CFT70 cắt ở 60 ngày."""
    real = nnx.poms(nlsp)
    comp = _components(real, "tmd", "study_day")
    # lịch C1: PRE −20,−13,−6,−1 · IN 3…59 mỗi 7 ngày · POST ngày 0 và 12 sau nằm giường (giống CFT70)
    pre = [-20, -13, -6, -1]
    inn = list(range(3, 60, 7))
    post_c1, post_cft = [60, 72], [70, 82]            # POST tính theo μ của CFT70 ở cùng khoảng cách sau nằm giường
    rng, rows = np.random.default_rng(seed), []
    for name, p in personas.items():
        days = np.array(pre + inn + post_c1, float)
        lookup = np.array(pre + inn + post_cft, float)
        y = np.clip(np.round(_simulate(lookup, comp, rng)), -32, 200)   # TMD lý thuyết: −32 … 200
        rows += [{"persona": name, "subject_id": p["analog"], "study_day": d, "tmd": v} for d, v in zip(days, y)]
    return pd.DataFrame(rows), {"source": "NNX10AP86G_CFT70_POMS_TMD.csv (24 người CFT70)", **comp}


def glucose_daily(nlsp: Path, personas: dict, seed: int) -> tuple[pd.DataFrame, dict]:
    """Đường huyết lúc đói HẰNG NGÀY cho 6 persona. CFT70: neo vào giá trị OGTT phút 0 THẬT của chính người đó
    (giữ nguyên các ngày có đo, is_synthetic=False); C1: mức nền và xu hướng lấy từ quần thể CFT70."""
    o = nnx.ogtt(nlsp)
    f0 = o[o.minute.eq(0)].dropna(subset=["glucose"])
    pre = f0[f0.phase.eq("PRE_TEST")]
    within_pre = pre.groupby("subject_id").glucose.std(ddof=1).dropna()       # biến thiên ngày-ngày trong người
    person_pre = pre.groupby("subject_id").glucose.mean()
    phase_mean = f0.groupby(f0.study_day.round(-1).clip(-20, 90)).glucose.mean()
    params = {"source": "NNX10AP86G_CFT70_OGTT.csv, phút 0 (24 người)",
              "sigma_within_day": float(np.sqrt((within_pre ** 2).mean())),   # SD trong người, gộp từ các lần PRE
              "sigma_between": float(person_pre.std(ddof=1)), "pre_mean": float(person_pre.mean()),
              "population_trend": {float(k): float(v - person_pre.mean()) for k, v in phase_mean.items()},
              "observed_min": float(f0.glucose.min()), "observed_max": float(f0.glucose.max())}
    rng, rows = np.random.default_rng(seed), []
    tdays, tvals = list(params["population_trend"]), list(params["population_trend"].values())
    for name, p in personas.items():
        days = np.arange(-10, p["bed_rest_days"] + 8)
        own = f0[f0.subject_id.eq(p["analog"])].groupby("study_day").glucose.mean()
        if len(own):     # CFT70: nội suy giữa các mốc thật của CHÍNH người đó
            level = np.interp(days, own.index.to_numpy(float), own.to_numpy(float))
        else:            # C1: mức nền ngẫu nhiên quanh quần thể + xu hướng quần thể
            level = rng.normal(params["pre_mean"], params["sigma_between"]) + np.interp(days, tdays, tvals)
        y = level + rng.normal(0, params["sigma_within_day"], len(days))
        y = np.clip(np.round(y, 1), params["observed_min"], params["observed_max"])
        for d, v in zip(days, y):
            real = d in own.index
            rows.append({"persona": name, "subject_id": p["analog"], "study_day": int(d),
                         "glucose_fasting": float(own[d]) if real else float(v), "is_synthetic": not real})
    return pd.DataFrame(rows), params


def sleep_cft70(nlsp: Path, personas: dict, seed: int) -> tuple[pd.DataFrame, dict]:
    """Hiệu suất + thời lượng ngủ theo đêm cho 3 persona CFT70 (không có actigraphy thật), từ BRSMAct Campaign 1."""
    n = act.nights(act.read_actigraphy(nlsp))
    phase0 = n.groupby("subject_id").apply(lambda g: g[g.phase.eq("IN_TEST")].date.min(), include_groups=False)
    n["study_day"] = (n.date - n.subject_id.map(phase0)).dt.days + 1
    n["study_day"] = n.study_day.where(n.phase.ne("PRE_TEST"), n.study_day - 1)
    comps = {m: _components(n.assign(sb=(n.study_day // 7) * 7), m, "sb") for m in ("efficiency", "duration")}
    rng, rows = np.random.default_rng(seed), []
    for name, p in personas.items():
        days = np.arange(-2, p["bed_rest_days"] + 7)
        lookup = np.clip(days, n.study_day.min(), n.study_day.max())     # sau ngày 60 dùng μ cuối của C1
        ce, cd = comps["efficiency"], comps["duration"]          # cắt trong khoảng QUAN SÁT THẬT
        eff = np.clip(_simulate((lookup // 7) * 7, ce, rng), ce["observed_min"], ce["observed_max"])
        dur = np.clip(_simulate((lookup // 7) * 7, cd, rng), cd["observed_min"], cd["observed_max"])
        rows += [{"persona": name, "subject_id": p["analog"], "study_day": int(d),
                  "date": (pd.Timestamp("2000-01-01") + pd.Timedelta(days=int(d))).date().isoformat(),
                  "efficiency": round(float(e), 1), "duration": round(float(u), 2)} for d, e, u in zip(days, eff, dur)]
    out = pd.DataFrame(rows)
    return out, {"source": "BRSMACT_Campagin_1_Actigraphy.csv (3 người C1 — rất ít)", "efficiency": comps["efficiency"],
                 "duration": comps["duration"],
                 "date_note": "Cột date là LỊCH NHÂN TẠO (2000-01-01 + study_day) chỉ để tạo lưới ngày; không phải ngày thật"}


DATASETS = {
    "mood_c1_poms": (mood_c1, "campaign_1", "Điểm POMS-TMD hằng tuần cho 3 persona Campaign 1 (không có POMS thật)"),
    "glucose_daily_personas": (glucose_daily, None, "Đường huyết lúc đói hằng ngày cho 6 persona (CFT70 neo vào OGTT thật)"),
    "sleep_cft70_actigraphy": (sleep_cft70, "cft70", "Hiệu suất/thời lượng ngủ theo đêm cho 3 persona CFT70 (không có actigraphy thật)"),
}


def generate(nlsp: Path, crew: dict, seed: int = 17) -> dict[str, tuple[pd.DataFrame, dict, str]]:
    out = {}
    for name, (fn, cohort, title) in DATASETS.items():
        personas = {k: v for k, v in crew["personas"].items() if cohort in (None, v["cohort"])}
        frame, params = fn(nlsp, personas, seed)
        if "is_synthetic" not in frame:
            frame["is_synthetic"] = True
        frame["generator"] = GEN_VERSION
        out[name] = (frame, {"title": title, "seed": seed, "generator": GEN_VERSION, **params}, title)
    return out


def validation(name: str, frame: pd.DataFrame, nlsp: Path) -> pd.DataFrame:
    """So thống kê dữ liệu GIẢ ĐỊNH với dữ liệu THẬT dùng để sinh: trung bình, SD, tự tương quan bậc 1 trong người."""
    def stats(f, value, label):
        f = f.dropna(subset=[value]).sort_values(["subject_id", "study_day"])
        lag = f.groupby("subject_id")[value].shift()
        ok = lag.notna()
        return {"dataset": label, "variable": value, "people": f.subject_id.nunique(), "rows": len(f),
                "mean": f[value].mean(), "sd": f[value].std(), "min": f[value].min(), "max": f[value].max(),
                "lag1_autocorr": np.corrcoef(f[value][ok], lag[ok])[0, 1] if ok.sum() > 2 else np.nan}
    rows = []
    if name == "mood_c1_poms":
        rows = [stats(nnx.poms(nlsp), "tmd", "THẬT – POMS CFT70"), stats(frame, "tmd", "GIẢ ĐỊNH – C1")]
    elif name == "glucose_daily_personas":
        o = nnx.ogtt(nlsp)
        rows = [stats(o[o.minute.eq(0)].rename(columns={"glucose": "glucose_fasting"}), "glucose_fasting", "THẬT – OGTT phút 0"),
                stats(frame[frame.is_synthetic], "glucose_fasting", "GIẢ ĐỊNH – hằng ngày")]
    elif name == "sleep_cft70_actigraphy":
        n = act.nights(act.read_actigraphy(nlsp)).assign(study_day=lambda d: (d.date - d.date.min()).dt.days)
        rows = [stats(n, m, f"THẬT – actigraphy C1 ({m})") for m in ("efficiency", "duration")]
        rows += [stats(frame, m, f"GIẢ ĐỊNH – CFT70 ({m})") for m in ("efficiency", "duration")]
    return pd.DataFrame(rows)
