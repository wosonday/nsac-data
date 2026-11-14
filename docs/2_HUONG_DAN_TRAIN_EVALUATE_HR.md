# Hướng dẫn bước tiếp theo: `train` và `evaluate` cho HR, tái lập run 11/11

> **Cập nhật 14/11 14:10, quy ước đặt tên.** Bước pipeline được đánh số theo thứ tự chạy; file hỗ trợ (ngoài luồng) có tiền tố `_`. Trong tài liệu này, tên cũ tương ứng với tên mới như sau:
> - `copydata.py` → `1_copydata.py`
> - `datacheck.py` → `2_datacheck.py`
> - `prepare/` → `3_prepare/`
> - `train.py` → `4_train.py`
> - `evaluate.py` → `5_evaluate.py`
> - `settings.py` → `_settings.py`; `runs.py` → `_runs.py`; `models.py` → `_models.py`; `artifacts.py` → `_artifacts.py`; `cli.py` → `_cli.py`
> - mới: `_hashing.py`, `_steps.py`
>
> File trong `runs/<task>/<run>/` mang số của bước tạo ra nó: `3_snapshot.json`, `3_table.csv.gz`, `3_features.json`; `4_oof.csv.gz`, `4_folds.json`, `4_models/`; `5_metrics.csv`, `5_summary.json`.
>
> Lệnh `sky-ml …` giữ nguyên. Lệnh mới `uv run sky-ml steps` in thứ tự các bước. **Code trong phần phụ lục của tài liệu này là bản trước khi đổi tên; bản đúng là các file trong `src/`.**


Nối tiếp `docs/HUONG_DAN_BUILD_COPY_PREPROCESS.md` (đã xong: copy-data → check → prepare hr). Đây là Task 5–6 của kế hoạch.

**Đã kiểm chứng trước khi bàn giao.** Tôi chạy `prepare → train → evaluate` trên đúng file `mmash_minutes.csv.gz` của NASA-cl và so với run ngày 11/11:

| Mô hình | MAE run 11/11 (NASA-cl) | MAE `sky-ml` | Chênh lệch |
|---|---|---|---|
| ridge | 3.917428446642468 | 3.917428446642468 | **0** |
| lightgbm | 4.066026551813598 | 4.066026551813598 | **0** |
| last_value (baseline) | 4.465221425659498 | 4.465221425659498 | **0** |
| Độ bao phủ khoảng 90% (ridge) | 0.9003961516694963 | 0.9003961516694963 | **0** |

Thời gian chạy khoảng 12 giây. Test nhanh: 23 passed.

## Bước 1. Ý nghĩa của bước này

- **Ý nghĩa:** chứng minh code mới, gọn hơn, cho ra **đúng** kết quả cũ. Đây là điều kiện trước khi tinh giản hay cải tiến.
- **Nguyên nhân phải tái lập trước:** nếu cải tiến luôn mà kết quả đổi, ta không biết thay đổi đến từ cải tiến hay từ lỗi port code.
- **Mục tiêu:** mọi số trùng đến 1e-6. Sau đó mới làm vòng 2: dự đoán OOF của người được giữ ra, phân vị phần dư, và logic ra quyết định.

## Bước 2. Các file thay đổi

| File | Loại | Vai trò |
|---|---|---|
| `configs/tasks.yaml` | sửa | Thêm `seed`, `interval_alpha`, `bootstrap_samples`, `permutation_tests` và **khối `models`** (mô hình khai báo bằng YAML) |
| `src/sky_ml/models.py` | mới | `LastValue` (baseline) và `build_model(spec, seed)`: dựng mô hình từ YAML |
| `src/sky_ml/train.py` | mới | `make_folds` (LOSO hoặc theo tháng) và `train_predict` (fit mọi mô hình trên cùng fold → OOF) |
| `src/sky_ml/evaluate.py` | mới | Metric theo fold, CI95 bootstrap, so với baseline, độ bao phủ khoảng 90% |
| `src/sky_ml/cli.py` | sửa | Thêm lệnh `train <task> [--run latest]` và `evaluate <task> [--run latest]` |
| `tests/test_models.py`, `test_train.py`, `test_evaluate.py` | mới | 9 test nhanh, dữ liệu giả |
| `tests/test_reproduce.py` | mới | Test `slow`: tái lập 11/11 trên dữ liệu thật |
| `src/sky_ml/tasks.py` | **xóa** | Đã thay bằng `configs/tasks.yaml` |

## Bước 3. Chạy

```powershell
cd D:\Project\nasa-hackathon
Remove-Item src\sky_ml\tasks.py           # file rỗng cũ, không còn dùng
uv run pytest -v                          # kỳ vọng: 23 passed, 1 deselected
uv run sky-ml train hr                    # kỳ vọng: hr: 22 fold × 3 mô hình → runs\hr\<run>\oof.csv.gz
uv run sky-ml evaluate hr                 # in bảng metrics + coverage (khớp bảng ở đầu tài liệu)
uv run pytest -m slow -v                  # tái lập từ đầu: prepare → train → evaluate, so 1e-6
git add . ; git commit -m "feat: train/evaluate hr reproduces 2026-11-11 run exactly"
```

`train` và `evaluate` mặc định dùng run **mới nhất** (`--run latest`). Muốn chạy trên một run cụ thể: `uv run sky-ml train hr --run 2026-11-14_115152`.

## Bước 4. Đọc code theo luồng dữ liệu

### 4.1. Mô hình khai báo bằng YAML (`configs/tasks.yaml` → `models.py`)

```yaml
models:
  last_value: {class: sky_ml.models.LastValue}
  ridge:      {class: sklearn.linear_model.Ridge, params: {alpha: 1.0}, scale: true}
  lightgbm:   {class: lightgbm.LGBMRegressor, params: {...}}
```

- `build_model` import lớp theo đường dẫn chuỗi, rồi truyền `params` vào.
- Nếu lớp có tham số `random_state`, hàm tự gắn `seed: 17`. Vì vậy LightGBM tái lập được kết quả, còn Ridge và LastValue không bị ảnh hưởng.
- `scale: true` bọc mô hình bằng `make_pipeline(StandardScaler(), model)`. **Nhờ vậy bộ chuẩn hóa chỉ học trên tập train của từng fold, không rò rỉ thông tin từ tập test.**
- **Ví dụ thử nghiệm:** đổi `alpha: 1.0` thành `alpha: 10.0`, chạy lại `train` và `evaluate`, rồi so MAE. Không phải sửa dòng code nào.

### 4.2. Chia fold (`train.make_folds`)

- `leave_one_subject_out`: 22 fold. Mỗi fold để riêng **toàn bộ** cửa sổ của một người làm tập test. Câu hỏi được trả lời: "mô hình có dùng được cho một người mới không?"
- `by_month` (dành cho task `dose` sau này): train trên các tháng trước, test trên một tháng, chừa `gap_days` ngày ở giữa.
- `assert … isdisjoint`: chặn cứng trường hợp một hàng nằm ở cả train lẫn test. Fold rỗng bị bỏ thay vì làm chương trình dừng.

### 4.3. Huấn luyện và dự đoán OOF (`train.train_predict`)

- Với mỗi fold: `clone(template)` tạo mô hình **mới**, fit trên tập train, dự đoán tập test.
- Đầu ra `oof.csv.gz` có các cột `fold, row, subject_id, model, y_true, y_pred`, mỗi cửa sổ × mỗi mô hình là một hàng (5.301 × 3).
- **Vì sao gọi là OOF (out-of-fold):** mỗi dự đoán đến từ một mô hình chưa từng thấy người đó. Đây là loại dự đoán duy nhất được phép hiển thị trên UI (theo thiết kế tích hợp v2, mục 0).

### 4.4. Đánh giá (`evaluate.py`)

| Hàm | Làm gì | Vì sao làm như vậy |
|---|---|---|
| `score_per_fold` | MAE của từng người × từng mô hình | Người có nhiều cửa sổ không lấn át người ít cửa sổ |
| `evaluate` | Trung bình theo người, CI95, `diff_vs_baseline` | So **cặp** trên cùng người. CI95 lấy mẫu lại **người**, không lấy mẫu lại dòng (lấy theo dòng sẽ làm CI hẹp giả tạo) |
| `interval_half_width` | Nửa độ rộng khoảng 90% = phân vị bậc ⌈(n+1)·0,9⌉ của \|sai số\| | Công thức split-conformal (Angelopoulos & Bates, 2021) |
| `interval_coverage` | Độ rộng cho fold k tính **chỉ từ các fold khác**, rồi đếm tỷ lệ fold k nằm trong khoảng | Kiểm tra trung thực: không tự chấm bằng chính dữ liệu đã dùng để đặt độ rộng |

`summary.json` đổi tên trường thành `best_model_exploratory` và **không có** `payload_examples`. Lý do: bản NASA-cl chọn mô hình theo điểm OOF (lỗi Y1), rồi tạo payload bằng mô hình đã học trên chính các hàng đó. Vòng 2 sẽ làm đúng: chọn mô hình lồng nhau, và lấy dự đoán OOF của người được giữ ra.

## Bước 5. Cách đọc kết quả

| Số | Đọc là |
|---|---|
| ridge MAE 3,917 (CI95 3,61–4,24) | Dự báo HR 5 phút tới cho một người chưa từng thấy, sai trung bình khoảng 3,9 bpm |
| `diff_vs_baseline` −0,548 (CI −0,677…−0,426) | Ridge tốt hơn "giữ giá trị cuối" khoảng 0,55 bpm. Khoảng tin cậy không chứa 0, nên cải thiện là có thật |
| Bao phủ 0,900; nửa độ rộng trung vị 8,71 bpm | Dải "dự báo ± 8,7 bpm" chứa đúng 90% giá trị thật của người mới. Đây là cơ sở cho dải kỳ vọng trên UI |
| lightgbm 4,066 > ridge | Mô hình phức tạp hơn không thắng trên dữ liệu nhỏ, đúng như Grinsztajn và cộng sự (2022) nhận xét |

## Bước 6. Lỗi thường gặp

| Thông báo | Nguyên nhân | Cách xử lý |
|---|---|---|
| `Chưa có run cho hr; chạy: sky-ml prepare hr` | Chưa có thư mục `runs\hr\…` | Chạy `prepare hr` trước |
| `… thiếu oof.csv.gz; chạy: sky-ml train hr` | Gọi `evaluate` trên run chưa train | Chạy `train hr` |
| `ModuleNotFoundError: sky_ml.tasks` | Còn `import` cũ ở đâu đó | Kiểm tra `cli.py` đã là bản mới; xóa `tasks.py` |
| MAE lệch so với bảng | Khác phiên bản thư viện | Xem `snapshot.json`; sklearn phải là 1.9.1, lightgbm 4.7.0 |

## Bước 7 (bổ sung 14/11 13:50). Lưu mô hình đã huấn luyện

**Ý nghĩa.** `oof.csv.gz` chỉ là *dự đoán*. Muốn dùng lại mô hình (dự đoán cho persona nsac, kiểm toán, so phiên bản), phải lưu chính mô hình kèm thông tin để tái lập.

**Thiết kế.**

| Loại | File | Fit trên | Dùng để |
|---|---|---|---|
| `final` | `runs/<task>/<run>/models/<model>/final.joblib` | **Toàn bộ** người trong `table` | Dự đoán cho **người mới**: 6 persona thuộc cohort khác, dữ liệu mới. Tuyệt đối không dùng để chấm điểm trên chính những người đã học |
| `fold` (tùy chọn) | `models/<model>/folds/<fold>.joblib` | Toàn bộ người **trừ** người của fold đó | Kiểm toán: nạp lại và tái tạo đúng từng dòng của `oof.csv.gz` |
| `manifest.json` | `models/manifest.json` | — | SHA-256 và kích thước từng file, phiên bản Python/sklearn/LightGBM/numpy/joblib, `features`, `target`, `seed`, `model_specs` (chép từ YAML), `split`, `data_snapshot` |

Bật hoặc tắt trong `configs/tasks.yaml`:

```yaml
  save_models:
    final: true    # mặc định: 3 file (last_value 72 B, ridge ~1 KB, lightgbm ~73 KB)
    folds: false   # true: thêm 22 × 3 = 66 file (~1,9 MB với hr)
```

**Code mới:**
- `src/sky_ml/artifacts.py`:
  - `save_model`: ghi qua file `.part` rồi mới đổi tên, nén joblib mức 3.
  - `write_manifest`.
  - `load_model(models_dir, name, kind="final")`: **kiểm SHA-256 trước khi nạp**, lệch thì từ chối.
- `train.py`:
  - `train_final` fit trên toàn bộ dữ liệu;
  - `train_predict(..., fold_models=dict)` gom mô hình của từng fold.
- `cli.py`: lệnh `train` lưu mô hình và in `Đã lưu N mô hình → …/models`.
- `pyproject.toml`: thêm `"joblib>=1.4"`.
- `tests/test_artifacts.py`:
  - nạp lại cho ra cùng dự đoán;
  - file bị sửa 1 byte thì bị từ chối.

**Đã kiểm chứng:**
- MAE vẫn trùng run 11/11 (3,917428 / 4,066027 / 4,465221), coverage 0,900396.
- 25 test đạt.
- Với `folds: true`: lưu 69 mô hình (1,9 MB), nạp lại mô hình fold `mmash:user_1` thành công.

**Chạy:**

```powershell
uv sync                                    # cài joblib (thường đã có sẵn theo scikit-learn)
uv run pytest -v                           # 25 passed, 1 deselected
uv run sky-ml train hr                     # ... Đã lưu 3 mô hình → runs\hr\<run>\models
uv run python -c "from pathlib import Path; import glob; from sky_ml.artifacts import load_model; d=Path(sorted(glob.glob('runs/hr/*'))[-1])/'models'; print(load_model(d,'ridge'))"
```

**Bảo mật.** joblib/pickle **có thể chạy mã khi nạp**. Chỉ nạp file do chính pipeline tạo ra, và luôn nạp qua `load_model` (có kiểm SHA-256). Không nạp file `.joblib` nhận từ nguồn khác. Khi chép mô hình sang nsac (TypeScript), không chép `.joblib`. Thay vào đó xuất **hệ số** (ridge: `coef_`, `intercept_`, cùng `mean_`/`scale_` của scaler) ra JSON; việc này thuộc Task 16 `export-nsac`.

**Lưu ý.** Chạy lại `train` trên **cùng một run** sẽ ghi đè `oof.csv.gz` và `models/` của run đó. Muốn giữ bản cũ, chạy `prepare` để tạo run mới trước.

## Bước tiếp theo

Task 13 (copy thêm dữ liệu UTMB + `prepare/utmb.py`), rồi Task 14 (`vitals`: train trên Campaign 3, test ngoài cohort trên 6 persona), rồi `decide/` theo `docs/LOGIC_RA_QUYET_DINH_SKY_2026-11-14.md`.

## Phụ lục: nội dung các file

### `configs/tasks.yaml`

```yaml
# Tham số từng task — giá trị chép từ NASA-cl/src/nasa_cl/pipeline/config.py (run 2026-11-11).
# Mô hình khai báo ở khóa `models` của từng task (dựng bằng sky_ml.models.build_model).
hr:
  description: "MMASH (22 người, mặt đất): HR trung bình 5 phút tới từ 30 phút trước"
  inputs:
    - processed/sample-v2/mmash_minutes.csv.gz
  kind: regression
  target: hr_next_5min
  unit: bpm
  window: {past: 30, future: 5, step: 5}     # đơn vị: phút
  valid_hr_range: [30.0, 220.0]              # ngưỡng kỹ thuật loại số đo hỏng, KHÔNG phải ngưỡng lâm sàng
  split: {type: leave_one_subject_out}
  baseline: last_value
  seed: 17
  interval_alpha: 0.10        # khoảng dự đoán 90%
  bootstrap_samples: 10000    # CI95 lấy mẫu lại theo người
  permutation_tests: 0        # 0 = bỏ qua (task này nhiều cửa sổ, tốn thời gian)
  # Mô hình: class = đường dẫn import; params = tham số; scale = chuẩn hóa trong pipeline (fit trên train của từng fold)
  models:
    last_value:
      class: sky_ml.models.LastValue
    ridge:
      class: sklearn.linear_model.Ridge
      params: {alpha: 1.0}
      scale: true
    lightgbm:
      class: lightgbm.LGBMRegressor
      params: {n_estimators: 300, learning_rate: 0.05, max_depth: 4, num_leaves: 15,
               min_child_samples: 50, reg_lambda: 5.0, verbose: -1, n_jobs: 2}
```

### `src/sky_ml/models.py`

```python
"""Dựng mô hình sklearn từ khai báo YAML: {class, params, scale}."""
import importlib
import inspect

from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


class LastValue(BaseEstimator, RegressorMixin):
    """Baseline dự báo: giá trị sắp tới = giá trị đo cuối cùng (cột `last_value`)."""

    def __init__(self, column: str = "last_value"):
        self.column = column

    def fit(self, X, y):
        return self

    def predict(self, X):
        return X[self.column].to_numpy(dtype=float)


def build_model(spec: dict, seed: int):
    """`spec` = {class: "module.Class", params: {...}, scale: bool}. Gắn seed nếu lớp có `random_state`."""
    module, _, name = spec["class"].rpartition(".")
    cls = getattr(importlib.import_module(module), name)
    params = dict(spec.get("params") or {})
    if "random_state" in inspect.signature(cls).parameters:
        params.setdefault("random_state", seed)
    model = cls(**params)
    return make_pipeline(StandardScaler(), model) if spec.get("scale") else model
```

### `src/sky_ml/train.py`

```python
"""Bước train: chia fold (theo người / theo tháng), fit MỌI mô hình trên CÙNG các fold, trả dự đoán OOF."""
import pandas as pd
from sklearn.base import clone

from .models import build_model


def make_folds(table: pd.DataFrame, split: dict) -> list[dict]:
    """[{name, train, test}] — train/test là chỉ số hàng của `table`. Fold rỗng bị bỏ qua."""
    folds = []
    if split["type"] == "leave_one_subject_out":
        for subject in table.subject_id.unique():
            is_test = table.subject_id == subject
            folds.append({"name": subject, "train": table.index[~is_test], "test": table.index[is_test]})
    elif split["type"] == "by_month":
        time = pd.to_datetime(table.cutoff_time)
        for month in split["test_months"]:
            is_test = time.dt.month == month
            if not is_test.any():
                continue
            start = pd.Timestamp(year=time[is_test].min().year, month=month, day=1)
            is_train = time < start - pd.Timedelta(days=split["gap_days"])
            folds.append({"name": f"month_{month:02d}", "train": table.index[is_train], "test": table.index[is_test]})
    else:
        raise ValueError(f"split.type không hỗ trợ: {split['type']}")
    folds = [f for f in folds if len(f["train"]) and len(f["test"])]
    for f in folds:  # chống rò rỉ: một hàng không bao giờ ở cả train lẫn test
        assert set(f["train"]).isdisjoint(f["test"])
    return folds


def train_predict(table: pd.DataFrame, features: list[str], cfg: dict) -> pd.DataFrame:
    """OOF dạng dài: fold, row, subject_id, model, y_true, y_pred (+ p_<lớp> nếu phân loại)."""
    X, y = table[features], table[cfg["target"]]
    templates = {name: build_model(spec, cfg.get("seed", 17)) for name, spec in cfg["models"].items()}
    parts = []
    for fold in make_folds(table, cfg["split"]):
        test = table.loc[fold["test"]]
        for name, template in templates.items():
            model = clone(template).fit(X.loc[fold["train"]], y.loc[fold["train"]])
            part = pd.DataFrame({"fold": fold["name"], "row": test.index, "subject_id": test.subject_id.to_numpy(),
                                 "model": name, "y_true": test[cfg["target"]].to_numpy(),
                                 "y_pred": model.predict(test[features])})
            if cfg["kind"] == "classification":
                proba = pd.DataFrame(model.predict_proba(test[features]), columns=model.classes_)
                for c in cfg["classes"]:
                    part[f"p_{c}"] = proba[c].to_numpy() if c in proba else 0.0
            parts.append(part)
    return pd.concat(parts, ignore_index=True)
```

### `src/sky_ml/evaluate.py`

```python
"""Bước evaluate: so baseline (theo đơn vị độc lập = người/tháng), CI95 bootstrap, độ bao phủ khoảng 90%."""
import math

import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, cohen_kappa_score, f1_score


def bootstrap_ci(values, n_samples: int, seed: int = 0) -> tuple[float, float]:
    """CI95 của giá trị trung bình, lấy mẫu lại CÁC ĐƠN VỊ (không lấy lại từng dòng)."""
    values = np.asarray(values, dtype=float)
    means = np.random.default_rng(seed).choice(values, (n_samples, len(values))).mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def score(group: pd.DataFrame, kind: str) -> float:
    if kind == "regression":
        return float(np.mean(np.abs(group.y_true - group.y_pred)))   # MAE: càng nhỏ càng tốt
    return float(f1_score(group.y_true, group.y_pred, average="macro"))  # macro-F1: càng lớn càng tốt


def score_per_fold(oof: pd.DataFrame, kind: str) -> pd.DataFrame:
    return oof.groupby(["fold", "model"]).apply(score, kind=kind, include_groups=False).unstack("model")


def evaluate(oof: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    kind, n_boot = cfg["kind"], cfg.get("bootstrap_samples", 10000)
    metric = "mae" if kind == "regression" else "macro_f1"
    per_fold = score_per_fold(oof, kind)
    baseline = per_fold[cfg["baseline"]]
    rows = []
    for model in per_fold.columns:
        diff = per_fold[model] - baseline                    # so cặp trên cùng một người/tháng
        low, high = bootstrap_ci(per_fold[model], n_boot)
        dlow, dhigh = bootstrap_ci(diff, n_boot)
        row = {"model": model, "units": len(per_fold), metric: per_fold[model].mean(), "ci95_low": low,
               "ci95_high": high, "diff_vs_baseline": diff.mean(), "diff_ci95_low": dlow, "diff_ci95_high": dhigh}
        pooled = oof[oof.model == model]
        if kind == "regression":
            row["rmse"] = float(np.sqrt(np.mean((pooled.y_true - pooled.y_pred) ** 2)))
        else:
            truth = np.column_stack([pooled.y_true == c for c in cfg["classes"]]).astype(float)
            proba = pooled[[f"p_{c}" for c in cfg["classes"]]].to_numpy()
            row["balanced_accuracy"] = balanced_accuracy_score(pooled.y_true, pooled.y_pred)
            row["cohen_kappa"] = cohen_kappa_score(pooled.y_true, pooled.y_pred)
            row["brier"] = float(np.mean(np.sum((proba - truth) ** 2, axis=1)))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(metric, ascending=kind == "regression").reset_index(drop=True)


def interval_half_width(abs_errors, alpha: float) -> float:
    """Split-conformal: phân vị bậc ceil((n+1)(1-alpha)) của |sai số|; quá ít sai số → vô hạn."""
    errors = np.sort(np.asarray(abs_errors, dtype=float))
    k = math.ceil((len(errors) + 1) * (1 - alpha))
    return math.inf if k > len(errors) else float(errors[k - 1])


def interval_coverage(oof: pd.DataFrame, model: str, alpha: float) -> dict:
    """Độ rộng cho fold k tính CHỈ từ sai số của các fold khác → đếm tỷ lệ fold k nằm trong khoảng."""
    r = oof[oof.model == model].assign(abs_error=lambda d: (d.y_true - d.y_pred).abs())
    inside, widths = [], []
    for fold, part in r.groupby("fold"):
        hw = interval_half_width(r.abs_error[r.fold != fold], alpha)
        inside.extend(part.abs_error <= hw)
        widths.append(hw)
    return {"model": model, "target_coverage": 1 - alpha,
            "observed_coverage": float(np.mean(inside)), "median_half_width": float(np.median(widths))}


def confusion(oof: pd.DataFrame, model: str, classes: list[str]) -> pd.DataFrame:
    r = oof[oof.model == model]
    return pd.crosstab(r.y_true, r.y_pred).reindex(index=classes, columns=classes, fill_value=0)
```

### `src/sky_ml/cli.py`

```python
"""sky-ml copy-data | check | prepare <task> | train <task> | evaluate <task>"""
import argparse
import json

import pandas as pd

from .copydata import copy_data
from .datacheck import snapshot, verify_copy
from .evaluate import confusion, evaluate, interval_coverage
from .prepare import PREPARE
from .runs import new_run, require, resolve_run
from .settings import load_settings, load_tasks
from .train import make_folds, train_predict


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sky-ml")
    parser.add_argument("--config", default="sky_ml.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("copy-data").add_argument("--dry-run", action="store_true")
    sub.add_parser("check")
    sub.add_parser("prepare").add_argument("task", choices=sorted(PREPARE))
    for name in ("train", "evaluate"):
        p = sub.add_parser(name)
        p.add_argument("task")
        p.add_argument("--run", default="latest", help="tên thư mục run hoặc 'latest'")
    args = parser.parse_args(argv)
    settings = load_settings(args.config)

    if args.command == "copy-data":
        table = copy_data(settings, dry_run=args.dry_run)
        if not args.dry_run:
            print(table.status.value_counts().to_string(), f"\n→ {settings.data_dir}")
    elif args.command == "check":
        print(f"OK {verify_copy(settings)} files")
    elif args.command == "prepare":
        cfg = load_tasks(settings)[args.task]
        verify_copy(settings, cfg["inputs"])
        table, features = PREPARE[args.task](settings.data_dir, cfg)
        run = new_run(settings, args.task)
        table.to_csv(run / "table.csv.gz", index=False)
        (run / "features.json").write_text(json.dumps(features, indent=2))
        (run / "snapshot.json").write_text(json.dumps(snapshot(settings, cfg["inputs"]), indent=2))
        print(f"{args.task}: {len(table)} hàng, {table.subject_id.nunique()} người → {run}")
    elif args.command == "train":
        cfg = load_tasks(settings)[args.task]
        run = resolve_run(settings, args.task, args.run)
        table = pd.read_csv(require(run, "table.csv.gz", f"prepare {args.task}"))
        features = json.loads(require(run, "features.json", f"prepare {args.task}").read_text())
        folds = make_folds(table, cfg["split"])
        oof = train_predict(table, features, cfg)
        oof.to_csv(run / "oof.csv.gz", index=False)
        (run / "folds.json").write_text(json.dumps(
            [{"name": str(f["name"]), "n_train": len(f["train"]), "n_test": len(f["test"])} for f in folds], indent=2))
        print(f"{args.task}: {len(folds)} fold × {len(cfg['models'])} mô hình → {run / 'oof.csv.gz'}")
    elif args.command == "evaluate":
        cfg = load_tasks(settings)[args.task]
        run = resolve_run(settings, args.task, args.run)
        oof = pd.read_csv(require(run, "oof.csv.gz", f"train {args.task}"))
        metrics = evaluate(oof, cfg)
        best = metrics.model[0]   # chỉ để BÁO CÁO (so sánh khám phá), không dùng để chọn mô hình triển khai
        summary = {"task": args.task, "samples": int(oof.row.nunique()), "units": int(metrics.units[0]),
                   "best_model_exploratory": best, "metrics": metrics.round(6).to_dict("records")}
        if cfg["kind"] == "regression":
            summary["interval_coverage"] = interval_coverage(oof, best, cfg.get("interval_alpha", 0.10))
        else:
            confusion(oof, best, cfg["classes"]).to_csv(run / "confusion.csv")
        metrics.to_csv(run / "metrics.csv", index=False)
        (run / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
        print(metrics.round(4).to_string(index=False))
        if "interval_coverage" in summary:
            print("coverage:", {k: round(v, 4) if isinstance(v, float) else v for k, v in summary["interval_coverage"].items()})


if __name__ == "__main__":
    main()
```

### `tests/test_models.py`

```python
import pandas as pd
from sklearn.pipeline import Pipeline

from sky_ml.models import LastValue, build_model


def test_build_ridge_with_scaling():
    m = build_model({"class": "sklearn.linear_model.Ridge", "params": {"alpha": 1.0}, "scale": True}, seed=17)
    assert isinstance(m, Pipeline) and m.steps[-1][1].alpha == 1.0


def test_seed_injected_when_supported():
    m = build_model({"class": "lightgbm.LGBMRegressor", "params": {"n_estimators": 5}}, seed=17)
    assert m.random_state == 17


def test_last_value_predicts_column():
    X = pd.DataFrame({"last_value": [70.0, 80.0], "other": [1, 2]})
    assert list(LastValue().fit(X, None).predict(X)) == [70.0, 80.0]
```

### `tests/test_train.py`

```python
import numpy as np
import pandas as pd

from sky_ml.train import make_folds, train_predict

CFG = {"kind": "regression", "target": "y", "seed": 17, "split": {"type": "leave_one_subject_out"},
       "models": {"last_value": {"class": "sky_ml.models.LastValue"},
                  "ridge": {"class": "sklearn.linear_model.Ridge", "params": {"alpha": 1.0}, "scale": True}}}


def _table():
    rng = np.random.default_rng(0)
    subj = np.repeat(["a", "b", "c"], 10)
    x = rng.normal(70, 5, 30)
    return pd.DataFrame({"subject_id": subj, "last_value": x, "y": x + rng.normal(0, 1, 30)})


def test_loso_holds_out_whole_subject():
    t = _table()
    for f in make_folds(t, CFG["split"]):
        assert set(t.loc[f["test"], "subject_id"]) == {f["name"]}
        assert f["name"] not in set(t.loc[f["train"], "subject_id"])


def test_by_month_respects_gap():
    times = pd.date_range("2022-01-01", "2022-06-30", freq="D")
    t = pd.DataFrame({"subject_id": "dev", "cutoff_time": times})
    for f in make_folds(t, {"type": "by_month", "test_months": [4, 5], "gap_days": 1}):
        first_test = t.loc[f["test"], "cutoff_time"].min()
        assert t.loc[f["train"], "cutoff_time"].max() < first_test - pd.Timedelta(days=1)


def test_oof_has_one_row_per_test_row_per_model():
    oof = train_predict(_table(), ["last_value"], CFG)
    assert len(oof) == 30 * 2 and set(oof.model) == {"last_value", "ridge"}
    assert oof.groupby("model").row.nunique().eq(30).all()
```

### `tests/test_evaluate.py`

```python
import math

import pandas as pd

from sky_ml.evaluate import evaluate, interval_half_width


def test_half_width_infinite_when_too_few():
    assert interval_half_width([1.0] * 8, 0.10) == math.inf      # k = ceil(9*0.9)=9 > 8


def test_half_width_order_statistic():
    assert interval_half_width(list(range(1, 20)), 0.10) == 18.0  # n=19 → k=18


def test_evaluate_sorts_best_first_and_diff_vs_baseline():
    rows = []
    for fold in ["a", "b", "c"]:
        rows += [{"fold": fold, "row": 0, "subject_id": fold, "model": "base", "y_true": 10, "y_pred": 12},
                 {"fold": fold, "row": 0, "subject_id": fold, "model": "good", "y_true": 10, "y_pred": 11}]
    m = evaluate(pd.DataFrame(rows), {"kind": "regression", "baseline": "base", "bootstrap_samples": 200})
    assert list(m.model) == ["good", "base"] and m.loc[0, "diff_vs_baseline"] == -1.0
```

### `tests/test_reproduce.py`

```python
"""Tái lập run NASA-cl 2026-11-11 trên dữ liệu thật. Chạy: uv run pytest -m slow -v"""
import json
from pathlib import Path

import pandas as pd
import pytest

from sky_ml.cli import main
from sky_ml.runs import resolve_run
from sky_ml.settings import load_settings

ROOT = Path(__file__).parents[1]
EXPECTED = {"hr": ({"ridge": 3.917428446642468, "lightgbm": 4.066026551813598, "last_value": 4.465221425659498},
                   0.9003961516694963)}


@pytest.mark.slow
@pytest.mark.parametrize("task", sorted(EXPECTED))
def test_reproduce_2026_11_11(task):
    cfg = str(ROOT / "sky_ml.yaml")
    for step in ("prepare", "train", "evaluate"):
        main(["--config", cfg, step, task])
    run = resolve_run(load_settings(ROOT / "sky_ml.yaml"), task)
    metrics = pd.read_csv(run / "metrics.csv").set_index("model")
    mae, coverage = EXPECTED[task]
    for model, value in mae.items():
        assert metrics.loc[model, "mae"] == pytest.approx(value, abs=1e-6)
    summary = json.loads((run / "summary.json").read_text())
    assert summary["interval_coverage"]["observed_coverage"] == pytest.approx(coverage, abs=1e-6)
```

