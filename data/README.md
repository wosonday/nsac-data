# data/ — dữ liệu của sky-ml (repo `nsac-data`)

Thư mục này chứa **dữ liệu đầu vào của mô hình, mô hình đã huấn luyện và dự đoán**, kèm danh mục (catalog) và hướng dẫn đọc cho agent của web nsac.
Phần **Danh mục dữ liệu** ở cuối file do `sky-ml` tự sinh từ `CATALOG.csv`; phần còn lại viết tay.

- Hướng dẫn chi tiết cho người: [`../docs/3_HUONG_DAN_DU_LIEU.md`](../docs/3_HUONG_DAN_DU_LIEU.md)
- Nguồn dữ liệu và trích dẫn: [`../docs/Du_lieu_nguon_mo_hinh.xlsx`](../docs/Du_lieu_nguon_mo_hinh.xlsx)
- Logic ra quyết định: [`../docs/LOGIC_RA_QUYET_DINH_SKY_2026-11-14.md`](../docs/LOGIC_RA_QUYET_DINH_SKY_2026-11-14.md)

## 1. Cấu trúc

| Thư mục | Nhóm | Bước tạo | Nội dung |
|---|---|---|---|
| `1_source/` | Bản copy nguồn (chỉ đọc) | 1 `load-data` | Đẩy lên git mọi file các mô hình dùng: MMASH `processed/sample-v2/` (hr), `raw/radlab/instruments/Lidal/` (dose), `raw/nlsp/{MR080G,MR079G,BRSMImmune}.zip` + `download_manifest.csv` (cpet), giấy phép/manifest Sleep-EDF, `COPY_MANIFEST.csv`. **Không đẩy** 20 file EDF Sleep-EDF (~480 MB) — tạo lại bằng `sky-ml load-data`. |
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
- Ghi nguồn khi hiển thị (đầy đủ ở sheet `Trich_dan` của file Excel): MMASH — Rossi et al. 2020, doi:10.13026/cerq-fc86 (ODbL); Sleep-EDF — Kemp et al. 2000, doi:10.13026/C2X676 (ODC-By); UTMB CFT70 — NASA NLSP; RadLab — NASA OSDR.

### 2.4 Những điều không làm

- **Không nạp `.joblib` trong web.** Đây là pickle của Python (có thể chạy mã khi nạp, TS không đọc được). Web chỉ đọc CSV/JSON. Dự báo mới phải chạy bằng `sky-ml predict`.
- **Không gán `mmash:user_N` cho 6 phi hành gia hư cấu.** Ánh xạ persona ↔ người analog (`configs/crew_map.yaml`) và bundle `export-nsac` v2 **chưa xây**; dữ liệu hiện tại chỉ là dữ liệu minh họa của task `hr`.
- Không gộp các cohort (MMASH, UTMB, Sleep-EDF, RadLab) theo ID hay thời gian; mỗi task là một nguồn riêng.
- Không sửa file trong `data/` bằng tay, kể cả phần Danh mục bên dưới (sẽ bị ghi đè).

### 2.5 Đọc theo từng task

| Task | Loại | Đơn vị / nhãn | Hiển thị gì | Lưu ý riêng |
|---|---|---|---|---|
| `hr` | hồi quy, dự báo 5 phút | bpm | `4_predictions` (latest) | `subject_id` = người MMASH, không phải phi hành gia |
| `dose` | hồi quy, dự báo 1 giờ | uGy/h | `4_predictions` (latest): liều 1 giờ tới sau điểm đo cuối | Một chuỗi thiết bị (`radlab:Lidal`) nên `in_sample` luôn True — nghĩa là chuỗi đã được học, KHÔNG có nghĩa giờ dự báo đã được thấy. `cutoff_time` giữ như nguồn, chưa xác minh UTC. |
| `cpet` | hồi quy, 1 hàng/người | `source_REL_VO2PK` (≈ mL/kg/min) | `3_models/cpet/<run>/oof.csv.gz`, lọc `model == deploy_model` | Chưa có dự đoán cho người mới; OOF = dự đoán khi người đó bị giữ ra. Có đặc trưng nhóm can thiệp (GROUP) — phi hành gia không có. |
| `cpet_physio` | như cpet, chỉ `pre_vo2` + `age` | như cpet | như cpet | Contract dùng được cho phi hành gia. Ridge không tốt hơn `mean_delta` khi bỏ GROUP. |
| `sleep` | phân loại 5 lớp / epoch 30 s | W, N1, N2, N3, REM | `3_models/sleep/<run>/oof.csv.gz` (`y_pred`, `p_W`…`p_REM`) và `confusion.csv` | Chấm điểm hồi cứu cả đêm, không phải dự báo. Dự đoán mới cần bảng đặc trưng (`--mode table`). |

Với task phân loại, file dự đoán có `prediction` là nhãn và `p_<lớp>` là xác suất; không có `low90/high90`. Độ chính xác hiển thị dùng `macro_f1` (CI95 theo người) trong `summary.json`.

### 2.6 Trạng thái hiện tại (14/11/2026) — tái lập đúng run NASA-cl 11/11 (sai lệch ≤ 1e-15)

| Task | Mô hình triển khai | Kết quả OOF (CI95 theo đơn vị độc lập) | Baseline |
|---|---|---|---|
| `hr` | ridge | MAE 3,92 bpm (3,61–4,24), 22 người; bao phủ 90% = 0,900 | last_value 4,47 |
| `dose` | lightgbm | MAE 0,769 uGy/h (0,686–0,871), 9 tháng; bao phủ 90% = 0,898 | last_value 2,14 |
| `cpet` | mean_delta | ridge MAE 2,84 (2,12–3,64), 33 người, hoán vị p = 0,005; mean_delta 3,62 | persistence 4,13 |
| `cpet_physio` | mean_delta | mean_delta MAE 3,62 (2,66–4,75); ridge 3,67 | persistence 4,13 |
| `sleep` | lightgbm | macro-F1 0,784 (0,760–0,807), 10 người; kappa 0,777 | majority 0,119 |

| Chỉ số nsac | Task sky-ml | Có dữ liệu? |
|---|---|---|
| Nhịp tim | `hr` | Có |
| Hoạt động và giấc ngủ | `sleep` (giai đoạn ngủ, Sleep-EDF) | Có một phần — chưa có actigraphy/hoạt động (`sleep_act`, UTMB) |
| Huyết áp, nhiệt độ cơ thể | `vitals` (UTMB CRF) | Chưa |
| Tâm trạng | `mood` (POMS) | Chưa |
| Đường huyết | `glucose` | Chưa |
| (ngoài 6 chỉ số) Thể lực hiếu khí, liều bức xạ | `cpet`, `cpet_physio`, `dose` | Có — dùng cho thẻ thể lực / môi trường nếu web có |

## 3. Tạo lại dữ liệu

```powershell
uv run sky-ml load-data
foreach ($t in "hr","dose","cpet","cpet_physio","sleep") {
  uv run sky-ml build-features $t; uv run sky-ml train $t; uv run sky-ml evaluate $t
}
uv run sky-ml predict hr   --input data/1_source/processed/sample-v2/mmash_minutes.csv.gz
uv run sky-ml predict dose --input data/1_source/raw/radlab/instruments/Lidal/2022-05-01_2023-01-01.csv
uv run sky-ml predict cpet --input <bảng có subject_id, pre_vo2, age, group_*> --mode table
```

## 4. Danh mục dữ liệu

<!-- CATALOG:START -->

_Tự sinh bởi `sky-ml` từ `CATALOG.csv` — không sửa tay phần này._

| Task | Run mới nhất | Dự đoán mới nhất |
|---|---|---|
| `cpet` | `2026-11-14_164613` | — |
| `cpet_physio` | `2026-11-14_164654` | — |
| `dose` | `2026-11-14_164606` | [`4_predictions/dose/2026-11-14_164606/2022-05-01_2023-01-01_latest_lightgbm_20261114_164835.csv`](4_predictions/dose/2026-11-14_164606/2022-05-01_2023-01-01_latest_lightgbm_20261114_164835.csv) |
| `hr` | `2026-11-14_145321` | [`4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.csv`](4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.csv) |
| `sleep` | `2026-11-14_164909` | — |

| Nhóm | Task | Run | File | Số hàng | Byte | SHA-256 (12 ký tự đầu) | Lệnh tạo |
|---|---|---|---|---|---|---|---|
| (3) mô hình | `sleep` | `2026-11-14_164909` | [`3_models/sleep/2026-11-14_164909/summary.json`](3_models/sleep/2026-11-14_164909/summary.json) |  | 1167 | `a58c686628f7` | `sky-ml evaluate sleep` |
| (3) mô hình | `sleep` | `2026-11-14_164909` | [`3_models/sleep/2026-11-14_164909/oof.csv.gz`](3_models/sleep/2026-11-14_164909/oof.csv.gz) | 29739 | 1098114 | `85413f8c49ef` | `sky-ml train sleep` |
| (3) mô hình | `sleep` | `2026-11-14_164909` | [`3_models/sleep/2026-11-14_164909/metrics.csv`](3_models/sleep/2026-11-14_164909/metrics.csv) |  | 597 | `af1dbe43dd82` | `sky-ml evaluate sleep` |
| (3) mô hình | `sleep` | `2026-11-14_164909` | [`3_models/sleep/2026-11-14_164909/manifest.json`](3_models/sleep/2026-11-14_164909/manifest.json) |  | 6115 | `dbf172cbdc44` | `sky-ml train sleep` |
| (3) mô hình | `sleep` | `2026-11-14_164909` | [`3_models/sleep/2026-11-14_164909/majority/final.joblib`](3_models/sleep/2026-11-14_164909/majority/final.joblib) |  | 774 | `7e09f44da901` | `sky-ml train sleep` |
| (3) mô hình | `sleep` | `2026-11-14_164909` | [`3_models/sleep/2026-11-14_164909/logistic/final.joblib`](3_models/sleep/2026-11-14_164909/logistic/final.joblib) |  | 4635 | `dffab79dd4b1` | `sky-ml train sleep` |
| (3) mô hình | `sleep` | `2026-11-14_164909` | [`3_models/sleep/2026-11-14_164909/lightgbm/final.joblib`](3_models/sleep/2026-11-14_164909/lightgbm/final.joblib) |  | 983062 | `4ee383592bbf` | `sky-ml train sleep` |
| (3) mô hình | `sleep` | `2026-11-14_164909` | [`3_models/sleep/2026-11-14_164909/folds.json`](3_models/sleep/2026-11-14_164909/folds.json) |  | 807 | `d4a9740a6950` | `sky-ml train sleep` |
| (1) đã xử lý | `sleep` | `2026-11-14_164909` | [`2_features/sleep/2026-11-14_164909/table.csv.gz`](2_features/sleep/2026-11-14_164909/table.csv.gz) | 9913 | 2616647 | `3e5eb79e694d` | `sky-ml build-features sleep` |
| (1) đã xử lý | `sleep` | `2026-11-14_164909` | [`2_features/sleep/2026-11-14_164909/snapshot.json`](2_features/sleep/2026-11-14_164909/snapshot.json) |  | 2862 | `b08dab5eca0c` | `sky-ml build-features sleep` |
| (1) đã xử lý | `sleep` | `2026-11-14_164909` | [`2_features/sleep/2026-11-14_164909/features.json`](2_features/sleep/2026-11-14_164909/features.json) |  | 974 | `49927d10703c` | `sky-ml build-features sleep` |
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
| (2) dự đoán | `dose` | `2026-11-14_164606` | [`4_predictions/dose/2026-11-14_164606/2022-05-01_2023-01-01_latest_lightgbm_20261114_164835.json`](4_predictions/dose/2026-11-14_164606/2022-05-01_2023-01-01_latest_lightgbm_20261114_164835.json) |  | 271 | `7a120e21c3a6` | `sky-ml predict dose --input 2022-05-01_2023-01-01.csv --mode latest` |
| (2) dự đoán | `dose` | `2026-11-14_164606` | [`4_predictions/dose/2026-11-14_164606/2022-05-01_2023-01-01_latest_lightgbm_20261114_164835.csv`](4_predictions/dose/2026-11-14_164606/2022-05-01_2023-01-01_latest_lightgbm_20261114_164835.csv) | 1 | 198 | `b83333431afc` | `sky-ml predict dose --input 2022-05-01_2023-01-01.csv --mode latest` |
| (3) mô hình | `dose` | `2026-11-14_164606` | [`3_models/dose/2026-11-14_164606/summary.json`](3_models/dose/2026-11-14_164606/summary.json) |  | 1128 | `0f9b5b1b2aa7` | `sky-ml evaluate dose` |
| (3) mô hình | `dose` | `2026-11-14_164606` | [`3_models/dose/2026-11-14_164606/ridge/final.joblib`](3_models/dose/2026-11-14_164606/ridge/final.joblib) |  | 1034 | `012e0fb07dc1` | `sky-ml train dose` |
| (3) mô hình | `dose` | `2026-11-14_164606` | [`3_models/dose/2026-11-14_164606/oof.csv.gz`](3_models/dose/2026-11-14_164606/oof.csv.gz) | 18771 | 405616 | `37ed4b8730db` | `sky-ml train dose` |
| (3) mô hình | `dose` | `2026-11-14_164606` | [`3_models/dose/2026-11-14_164606/metrics.csv`](3_models/dose/2026-11-14_164606/metrics.csv) |  | 471 | `a97131fc83a9` | `sky-ml evaluate dose` |
| (3) mô hình | `dose` | `2026-11-14_164606` | [`3_models/dose/2026-11-14_164606/manifest.json`](3_models/dose/2026-11-14_164606/manifest.json) |  | 2861 | `49249df6e1f0` | `sky-ml train dose` |
| (3) mô hình | `dose` | `2026-11-14_164606` | [`3_models/dose/2026-11-14_164606/lightgbm/final.joblib`](3_models/dose/2026-11-14_164606/lightgbm/final.joblib) |  | 130688 | `b6b38cd9497c` | `sky-ml train dose` |
| (3) mô hình | `dose` | `2026-11-14_164606` | [`3_models/dose/2026-11-14_164606/last_value/final.joblib`](3_models/dose/2026-11-14_164606/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train dose` |
| (3) mô hình | `dose` | `2026-11-14_164606` | [`3_models/dose/2026-11-14_164606/folds.json`](3_models/dose/2026-11-14_164606/folds.json) |  | 650 | `1d7bbc77a889` | `sky-ml train dose` |
| (1) đã xử lý | `dose` | `2026-11-14_164606` | [`2_features/dose/2026-11-14_164606/table.csv.gz`](2_features/dose/2026-11-14_164606/table.csv.gz) | 8366 | 543695 | `3305a2ad5965` | `sky-ml build-features dose` |
| (1) đã xử lý | `dose` | `2026-11-14_164606` | [`2_features/dose/2026-11-14_164606/snapshot.json`](2_features/dose/2026-11-14_164606/snapshot.json) |  | 632 | `4c4088fd10df` | `sky-ml build-features dose` |
| (1) đã xử lý | `dose` | `2026-11-14_164606` | [`2_features/dose/2026-11-14_164606/features.json`](2_features/dose/2026-11-14_164606/features.json) |  | 108 | `2402f472bd7b` | `sky-ml build-features dose` |
| (3) mô hình | `cpet_physio` | `2026-11-14_164654` | [`3_models/cpet_physio/2026-11-14_164654/summary.json`](3_models/cpet_physio/2026-11-14_164654/summary.json) |  | 1605 | `7842c2c1a11a` | `sky-ml evaluate cpet_physio` |
| (3) mô hình | `cpet_physio` | `2026-11-14_164654` | [`3_models/cpet_physio/2026-11-14_164654/ridge/final.joblib`](3_models/cpet_physio/2026-11-14_164654/ridge/final.joblib) |  | 807 | `44c099d90cca` | `sky-ml train cpet_physio` |
| (3) mô hình | `cpet_physio` | `2026-11-14_164654` | [`3_models/cpet_physio/2026-11-14_164654/persistence/final.joblib`](3_models/cpet_physio/2026-11-14_164654/persistence/final.joblib) |  | 436 | `1d03134d6b7d` | `sky-ml train cpet_physio` |
| (3) mô hình | `cpet_physio` | `2026-11-14_164654` | [`3_models/cpet_physio/2026-11-14_164654/oof.csv.gz`](3_models/cpet_physio/2026-11-14_164654/oof.csv.gz) | 132 | 2177 | `4a466bebb5a9` | `sky-ml train cpet_physio` |
| (3) mô hình | `cpet_physio` | `2026-11-14_164654` | [`3_models/cpet_physio/2026-11-14_164654/metrics.csv`](3_models/cpet_physio/2026-11-14_164654/metrics.csv) |  | 614 | `1e7545eafc79` | `sky-ml evaluate cpet_physio` |
| (3) mô hình | `cpet_physio` | `2026-11-14_164654` | [`3_models/cpet_physio/2026-11-14_164654/mean_delta/final.joblib`](3_models/cpet_physio/2026-11-14_164654/mean_delta/final.joblib) |  | 446 | `6ec07e805b04` | `sky-ml train cpet_physio` |
| (3) mô hình | `cpet_physio` | `2026-11-14_164654` | [`3_models/cpet_physio/2026-11-14_164654/manifest.json`](3_models/cpet_physio/2026-11-14_164654/manifest.json) |  | 3167 | `0d488157004a` | `sky-ml train cpet_physio` |
| (3) mô hình | `cpet_physio` | `2026-11-14_164654` | [`3_models/cpet_physio/2026-11-14_164654/lightgbm/final.joblib`](3_models/cpet_physio/2026-11-14_164654/lightgbm/final.joblib) |  | 14445 | `8e7e5682c6e2` | `sky-ml train cpet_physio` |
| (3) mô hình | `cpet_physio` | `2026-11-14_164654` | [`3_models/cpet_physio/2026-11-14_164654/folds.json`](3_models/cpet_physio/2026-11-14_164654/folds.json) |  | 2477 | `ca0953998180` | `sky-ml train cpet_physio` |
| (1) đã xử lý | `cpet_physio` | `2026-11-14_164654` | [`2_features/cpet_physio/2026-11-14_164654/table.csv.gz`](2_features/cpet_physio/2026-11-14_164654/table.csv.gz) | 33 | 623 | `d4199aaab90c` | `sky-ml build-features cpet_physio` |
| (1) đã xử lý | `cpet_physio` | `2026-11-14_164654` | [`2_features/cpet_physio/2026-11-14_164654/snapshot.json`](2_features/cpet_physio/2026-11-14_164654/snapshot.json) |  | 637 | `65b686004c20` | `sky-ml build-features cpet_physio` |
| (1) đã xử lý | `cpet_physio` | `2026-11-14_164654` | [`2_features/cpet_physio/2026-11-14_164654/features.json`](2_features/cpet_physio/2026-11-14_164654/features.json) |  | 24 | `5243acdb1cc8` | `sky-ml build-features cpet_physio` |
| (3) mô hình | `cpet` | `2026-11-14_164613` | [`3_models/cpet/2026-11-14_164613/summary.json`](3_models/cpet/2026-11-14_164613/summary.json) |  | 1766 | `ffa3f19b5539` | `sky-ml evaluate cpet` |
| (3) mô hình | `cpet` | `2026-11-14_164613` | [`3_models/cpet/2026-11-14_164613/ridge/final.joblib`](3_models/cpet/2026-11-14_164613/ridge/final.joblib) |  | 941 | `767da7a728da` | `sky-ml train cpet` |
| (3) mô hình | `cpet` | `2026-11-14_164613` | [`3_models/cpet/2026-11-14_164613/persistence/final.joblib`](3_models/cpet/2026-11-14_164613/persistence/final.joblib) |  | 470 | `52114aa44915` | `sky-ml train cpet` |
| (3) mô hình | `cpet` | `2026-11-14_164613` | [`3_models/cpet/2026-11-14_164613/oof.csv.gz`](3_models/cpet/2026-11-14_164613/oof.csv.gz) | 132 | 2184 | `1ba164e1be12` | `sky-ml train cpet` |
| (3) mô hình | `cpet` | `2026-11-14_164613` | [`3_models/cpet/2026-11-14_164613/metrics.csv`](3_models/cpet/2026-11-14_164613/metrics.csv) |  | 617 | `1bd22e538792` | `sky-ml evaluate cpet` |
| (3) mô hình | `cpet` | `2026-11-14_164613` | [`3_models/cpet/2026-11-14_164613/mean_delta/final.joblib`](3_models/cpet/2026-11-14_164613/mean_delta/final.joblib) |  | 482 | `3114a83cee4e` | `sky-ml train cpet` |
| (3) mô hình | `cpet` | `2026-11-14_164613` | [`3_models/cpet/2026-11-14_164613/manifest.json`](3_models/cpet/2026-11-14_164613/manifest.json) |  | 3213 | `ebf3329c012b` | `sky-ml train cpet` |
| (3) mô hình | `cpet` | `2026-11-14_164613` | [`3_models/cpet/2026-11-14_164613/lightgbm/final.joblib`](3_models/cpet/2026-11-14_164613/lightgbm/final.joblib) |  | 14455 | `c4dee952136c` | `sky-ml train cpet` |
| (3) mô hình | `cpet` | `2026-11-14_164613` | [`3_models/cpet/2026-11-14_164613/folds.json`](3_models/cpet/2026-11-14_164613/folds.json) |  | 2477 | `ca0953998180` | `sky-ml train cpet` |
| (1) đã xử lý | `cpet` | `2026-11-14_164613` | [`2_features/cpet/2026-11-14_164613/table.csv.gz`](2_features/cpet/2026-11-14_164613/table.csv.gz) | 33 | 623 | `18e3ee5a14b3` | `sky-ml build-features cpet` |
| (1) đã xử lý | `cpet` | `2026-11-14_164613` | [`2_features/cpet/2026-11-14_164613/snapshot.json`](2_features/cpet/2026-11-14_164613/snapshot.json) |  | 637 | `65b686004c20` | `sky-ml build-features cpet` |
| (1) đã xử lý | `cpet` | `2026-11-14_164613` | [`2_features/cpet/2026-11-14_164613/features.json`](2_features/cpet/2026-11-14_164613/features.json) |  | 78 | `290e1a0fe52a` | `sky-ml build-features cpet` |

<!-- CATALOG:END -->
