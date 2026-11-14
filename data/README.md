# data/ — dữ liệu của sky-ml (repo `nsac-data`)

Thư mục này chứa **dữ liệu đầu vào của mô hình, mô hình đã huấn luyện và dự đoán**, kèm danh mục (catalog) và hướng dẫn đọc cho agent của web nsac.
Phần **Danh mục dữ liệu** ở cuối file do `sky-ml` tự sinh từ `CATALOG.csv`; phần còn lại viết tay.

- Hướng dẫn chi tiết cho người: [`../docs/3_HUONG_DAN_DU_LIEU.md`](../docs/3_HUONG_DAN_DU_LIEU.md)
- Nguồn dữ liệu và trích dẫn: [`../docs/Du_lieu_nguon_mo_hinh_hr.xlsx`](../docs/Du_lieu_nguon_mo_hinh_hr.xlsx)
- Logic ra quyết định: [`../docs/LOGIC_RA_QUYET_DINH_SKY_2026-11-14.md`](../docs/LOGIC_RA_QUYET_DINH_SKY_2026-11-14.md)

## 1. Cấu trúc

| Thư mục | Nhóm | Bước tạo | Nội dung |
|---|---|---|---|
| `1_source/` | Bản copy nguồn (chỉ đọc) | 1 `load-data` | Chỉ đẩy lên git phần mô hình hiện tại dùng: `processed/sample-v2/` (MMASH đã QA), `raw/mmash/1.0.0/LICENSE.txt`, `COPY_MANIFEST.csv`. File lớn (Sleep-EDF ~480 MB, NLSP, RadLab) chỉ có trên máy, tạo lại bằng `sky-ml load-data`. |
| `2_features/<task>/<run_id>/` | **(1) Dữ liệu đã xử lý = đầu vào mô hình** | 2 `build-features` | `table.csv.gz`, `features.json`, `snapshot.json`, `README.md` |
| `3_models/<task>/<run_id>/` | **(3) Mô hình đã huấn luyện** | 3 `train`, 4 `evaluate` | `<model>/final.joblib`, `manifest.json`, `oof.csv.gz`, `folds.json`, `metrics.csv`, `summary.json`, `README.md` |
| `4_predictions/<task>/<run_id>/` | **(2) Dữ liệu dự đoán** | 5 `predict` | `<input>_<mode>_<model>_<YYYYmmdd_HHMMSS>.csv` + `.json`, `README.md` |
| `CATALOG.csv` | Sổ cái | mọi bước 2–5 | Mỗi file một dòng: `created_at_utc, kind, task, run_id, path, rows, bytes, sha256, produced_by` |

Cùng `run_id` ở 2–3–4 = cùng một chuỗi xử lý. Mỗi thư mục run có `README.md` riêng (data card: cột, đơn vị, số liệu chính, truy vết, giới hạn).

## 2. Hướng dẫn cho agent của web (nsac)

> Dành cho agent xây/duy trì web nsac (TypeScript + Bun + Drizzle SQLite). Đọc hết mục này trước khi dùng bất kỳ file nào trong `data/`.

### 2.1 Thứ tự đọc

1. Bảng **Danh mục dữ liệu** (cuối file) → lấy `Run mới nhất` và `Dự đoán mới nhất` của task.
2. File dự đoán `.csv` đó (dữ liệu hiển thị) + file `.json` cùng tên (thông tin lần chạy).
3. `3_models/<task>/<run_id>/summary.json` (chất lượng mô hình để hiển thị kèm).
4. `README.md` trong từng thư mục khi cần nghĩa của cột.

Chọn "mới nhất": `run_id` lớn nhất theo thứ tự chuỗi (`YYYY-MM-DD_HHMMSS`); trong cùng run, file dự đoán có hậu tố thời điểm lớn nhất. Kiểm tra toàn vẹn bằng `sha256` trong `CATALOG.csv`.

### 2.2 Hợp đồng dữ liệu — file dự đoán `.csv`

| Cột | Kiểu | Ý nghĩa / cách dùng |
|---|---|---|
| `subject_id` | string | Mã có namespace nguồn, vd. `mmash:user_1`. **Không phải phi hành gia** — xem 2.4. |
| `cutoff_time` | int | Phút tương đối trong nghiên cứu tại thời điểm dự báo. **Không** đổi sang ngày/giờ thật. |
| `model` | string | Mô hình đã dùng (mặc định `ridge` = `deploy_model`). |
| `unit` | string | Đơn vị của `prediction`, `low90`, `high90` (task `hr`: `bpm`). |
| `prediction` | float \| rỗng | Nhịp tim dự báo cho 5 phút tới. Rỗng khi `abstain=True`. |
| `low90`, `high90` | float \| rỗng | Khoảng dự đoán 90% (split-conformal; độ bao phủ OOF thực tế ≈ 0,90). |
| `abstain` | bool (`True`/`False`) | `True` = mô hình từ chối dự báo. |
| `reasons` | string | Lý do từ chối, phân tách bằng `;`: `missing_features`, `out_of_training_range`. |
| `in_sample` | bool | `True` = người này nằm trong dữ liệu huấn luyện. |
| `y_true`, `abs_error` | float | Chỉ có ở chế độ `backtest`. |

File `.json` cùng tên: `task, run_id, model, mode, input, half_width_90, n_rows, n_abstain, n_in_sample` (+ `mae_backtest` khi backtest).

### 2.3 Quy tắc hiển thị (bắt buộc)

- `abstain=True` → **không hiển thị số**; hiển thị trạng thái `UNKNOWN` ("không đủ dữ liệu") kèm `reasons`. Không tự nội suy hoặc thay bằng giá trị trước đó.
- Luôn hiển thị `prediction` **kèm khoảng** `low90–high90` và đơn vị; không làm tròn quá 0 chữ số thập phân với bpm.
- `in_sample=True` → gắn nhãn "minh họa trên dữ liệu huấn luyện"; **không** dùng các dòng này làm bằng chứng độ chính xác.
- Độ chính xác hiển thị lấy từ `summary.json › metrics` (`mae`, `ci95_low`, `ci95_high` theo **người**, LOSO) và `interval_coverage.observed_coverage` — không tự tính lại từ file dự đoán.
- Không tự đặt ngưỡng cảnh báo từ dự báo. Ngưỡng và hành động theo `docs/LOGIC_RA_QUYET_DINH_SKY_2026-11-14.md` (mỗi ngưỡng phải có nhãn bằng chứng `[NASA-STD]/[GUIDELINE]/[STUDY]/[LOCAL]/[HEURISTIC]`).
- Ghi nguồn khi hiển thị: MMASH (Rossi et al., 2020, PhysioNet, doi:10.13026/cerq-fc86), giấy phép ODbL v1.0.

### 2.4 Những điều không làm

- **Không nạp `.joblib` trong web.** Đây là pickle của Python (có thể chạy mã khi nạp, TS không đọc được). Web chỉ đọc CSV/JSON. Dự báo mới phải chạy bằng `sky-ml predict`.
- **Không gán `mmash:user_N` cho 6 phi hành gia hư cấu.** Ánh xạ persona ↔ người analog (`configs/crew_map.yaml`) và bundle `export-nsac` v2 **chưa xây**; dữ liệu hiện tại chỉ là dữ liệu minh họa của task `hr`.
- Không gộp các cohort (MMASH, UTMB, Sleep-EDF, RadLab) theo ID hay thời gian.
- Không sửa file trong `data/` bằng tay, kể cả phần Danh mục bên dưới (sẽ bị ghi đè).

### 2.5 Trạng thái hiện tại (14/11/2026)

| Chỉ số nsac | Task sky-ml | Có dữ liệu? |
|---|---|---|
| Nhịp tim | `hr` (dự báo 5 phút, MMASH) | Có — ridge MAE 3,92 bpm (CI95 3,61–4,24), 22 người |
| Huyết áp, nhiệt độ cơ thể | `vitals` (UTMB CRF) | Chưa |
| Tâm trạng | `mood` (POMS) | Chưa |
| Hoạt động và giấc ngủ | `sleep_act` | Chưa |
| Đường huyết | `glucose` | Chưa |

## 3. Tạo lại dữ liệu

```powershell
uv run sky-ml load-data
uv run sky-ml build-features hr
uv run sky-ml train hr
uv run sky-ml evaluate hr
uv run sky-ml predict hr --input data/1_source/processed/sample-v2/mmash_minutes.csv.gz
```

## 4. Danh mục dữ liệu

<!-- CATALOG:START -->

_Tự sinh bởi `sky-ml` từ `CATALOG.csv` — không sửa tay phần này._

| Task | Run mới nhất | Dự đoán mới nhất |
|---|---|---|
| `hr` | `2026-11-14_145321` | [`4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.csv`](4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.csv) |

| Nhóm | Task | Run | File | Số hàng | Byte | SHA-256 (12 ký tự đầu) | Lệnh tạo |
|---|---|---|---|---|---|---|---|
| (2) dự đoán | `hr` | `2026-11-14_145321` | [`4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.json`](4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.json) |  | 267 | `ec0dde115c05` | `sky-ml predict hr --input mmash_minutes.csv.gz --mode latest` |
| (2) dự đoán | `hr` | `2026-11-14_145321` | [`4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.csv`](4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.csv) | 22 | 1880 | `75af977c9b5a` | `sky-ml predict hr --input mmash_minutes.csv.gz --mode latest` |
| (3) mô hình | `hr` | `2026-11-14_145321` | [`3_models/hr/2026-11-14_145321/summary.json`](3_models/hr/2026-11-14_145321/summary.json) |  | 1167 | `e9d8a96980f5` | `sky-ml evaluate hr` |
| (3) mô hình | `hr` | `2026-11-14_145321` | [`3_models/hr/2026-11-14_145321/ridge/final.joblib`](3_models/hr/2026-11-14_145321/ridge/final.joblib) |  | 1028 | `93eae992c514` | `sky-ml train hr` |
| (3) mô hình | `hr` | `2026-11-14_145321` | [`3_models/hr/2026-11-14_145321/oof.csv.gz`](3_models/hr/2026-11-14_145321/oof.csv.gz) | 15903 | 276000 | `ba2e037e1dab` | `sky-ml train hr` |
| (3) mô hình | `hr` | `2026-11-14_145321` | [`3_models/hr/2026-11-14_145321/metrics.csv`](3_models/hr/2026-11-14_145321/metrics.csv) |  | 477 | `37ab62ab5d5b` | `sky-ml evaluate hr` |
| (3) mô hình | `hr` | `2026-11-14_145321` | [`3_models/hr/2026-11-14_145321/manifest.json`](3_models/hr/2026-11-14_145321/manifest.json) |  | 2558 | `f4360176da40` | `sky-ml train hr` |
| (3) mô hình | `hr` | `2026-11-14_145321` | [`3_models/hr/2026-11-14_145321/lightgbm/final.joblib`](3_models/hr/2026-11-14_145321/lightgbm/final.joblib) |  | 76340 | `cc253a24e2d3` | `sky-ml train hr` |
| (3) mô hình | `hr` | `2026-11-14_145321` | [`3_models/hr/2026-11-14_145321/last_value/final.joblib`](3_models/hr/2026-11-14_145321/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train hr` |
| (3) mô hình | `hr` | `2026-11-14_145321` | [`3_models/hr/2026-11-14_145321/folds.json`](3_models/hr/2026-11-14_145321/folds.json) |  | 1798 | `6e2ddfaf5171` | `sky-ml train hr` |
| (1) đã xử lý | `hr` | `2026-11-14_145321` | [`2_features/hr/2026-11-14_145321/table.csv.gz`](2_features/hr/2026-11-14_145321/table.csv.gz) | 5301 | 284536 | `d695ec43546e` | `sky-ml build-features hr` |
| (1) đã xử lý | `hr` | `2026-11-14_145321` | [`2_features/hr/2026-11-14_145321/snapshot.json`](2_features/hr/2026-11-14_145321/snapshot.json) |  | 373 | `bcab76d5fb2e` | `sky-ml build-features hr` |
| (1) đã xử lý | `hr` | `2026-11-14_145321` | [`2_features/hr/2026-11-14_145321/features.json`](2_features/hr/2026-11-14_145321/features.json) |  | 116 | `64943d993dfa` | `sky-ml build-features hr` |

<!-- CATALOG:END -->
