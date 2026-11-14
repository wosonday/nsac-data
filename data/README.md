# data/ — dữ liệu của sky-ml (repo `nsac-data`)

Thư mục này chứa **dữ liệu đầu vào của mô hình, mô hình đã huấn luyện và dự đoán**, kèm danh mục (catalog) và hướng dẫn đọc cho agent của web nsac.
Phần **Danh mục dữ liệu** ở cuối file do `sky-ml` tự sinh từ `CATALOG.csv`; phần còn lại viết tay.

- Hướng dẫn chi tiết cho người: [`../docs/3_HUONG_DAN_DU_LIEU.md`](../docs/3_HUONG_DAN_DU_LIEU.md)
- Báo cáo tổng hợp: [`../docs/BAO_CAO_DU_LIEU_VA_MO_HINH_2026-11-14.md`](../docs/BAO_CAO_DU_LIEU_VA_MO_HINH_2026-11-14.md)
- Nguồn dữ liệu và trích dẫn: [`../docs/Tong_hop_du_lieu_mo_hinh.xlsx`](../docs/Tong_hop_du_lieu_mo_hinh.xlsx)
- Logic ra quyết định: [`../docs/LOGIC_RA_QUYET_DINH_SKY_2026-11-14.md`](../docs/LOGIC_RA_QUYET_DINH_SKY_2026-11-14.md)

## 1. Cấu trúc

| Thư mục | Nhóm | Bước tạo | Nội dung |
|---|---|---|---|
| `1_source/` | Bản copy nguồn (chỉ đọc) | 1 `load-data` | Đẩy lên git mọi file các mô hình dùng: MMASH `processed/sample-v2/` (hr), `raw/radlab/instruments/Lidal/` (dose), `raw/nlsp/{MR080G,MR079G,BRSMImmune}.zip` + `download_manifest.csv` (cpet), `raw/nlsp/BRSMAct.zip` (sleep_act), `raw/nlsp/CRF.zip` (vitals_*), `raw/nlsp/NNX10AP86G.zip` (mood, glucose), giấy phép/manifest Sleep-EDF, `COPY_MANIFEST.csv`. **Không đẩy** 20 file EDF Sleep-EDF (~480 MB) — tạo lại bằng `sky-ml load-data`. |
| `1_synthetic/` | ⚠️ **DỮ LIỆU GIẢ ĐỊNH** (không phải số đo thật) | `make-synthetic` | 3 bộ cho persona thiếu dữ liệu thật; README riêng, `*.params.json` (tham số ước lượng từ dữ liệu thật), `*.validation.csv` (so với dữ liệu thật), `SYNTHETIC_MANIFEST.csv`. KHÔNG dùng để train/đánh giá. |
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

### 2.3b Dữ liệu giả định (bắt buộc đọc)

- Nguồn: `data/1_synthetic/*.csv` và mọi file dự đoán có `_SYNTHETIC-INPUT` trong tên / cột `input_synthetic = True`.
- **Luôn hiển thị nhãn "Dữ liệu giả định"** cạnh giá trị; không trộn chung một đường biểu đồ với dữ liệu thật mà không phân biệt (màu/kiểu nét khác).
- Trong `glucose_daily_personas.csv`, hàng `is_synthetic = False` là giá trị OGTT THẬT (điểm neo) — hiển thị khác biệt.
- Bảng nguồn theo persona × chỉ số: `configs/crew_map.yaml` (real / synthetic / none).

### 2.4 Những điều không làm

- **Không nạp `.joblib` trong web.** Đây là pickle của Python (có thể chạy mã khi nạp, TS không đọc được). Web chỉ đọc CSV/JSON. Dự báo mới phải chạy bằng `sky-ml predict`.
- **Không gán `mmash:user_N` cho 6 phi hành gia hư cấu.** Persona chỉ được ánh xạ tới người analog UTMB theo `configs/crew_map.yaml`. Bundle `export-nsac` v2 **chưa xây**.
- Không gộp các cohort (MMASH, UTMB, Sleep-EDF, RadLab) theo ID hay thời gian; mỗi task là một nguồn riêng.
- Không sửa file trong `data/` bằng tay, kể cả phần Danh mục bên dưới (sẽ bị ghi đè).

### 2.5 Đọc theo từng task

| Task | Loại | Đơn vị / nhãn | Hiển thị gì | Lưu ý riêng |
|---|---|---|---|---|
| `hr` | hồi quy, dự báo 5 phút | bpm | `4_predictions` (latest) | `subject_id` = người MMASH, không phải phi hành gia |
| `dose` | hồi quy, dự báo 1 giờ | uGy/h | `4_predictions` (latest): liều 1 giờ tới sau điểm đo cuối | Một chuỗi thiết bị (`radlab:Lidal`) nên `in_sample` luôn True — nghĩa là chuỗi đã được học, KHÔNG có nghĩa giờ dự báo đã được thấy. `cutoff_time` giữ như nguồn, chưa xác minh UTC. |
| `cpet` | hồi quy, 1 hàng/người | `source_REL_VO2PK` (≈ mL/kg/min) | `3_models/cpet/<run>/oof.csv.gz`, lọc `model == deploy_model` | Chưa có dự đoán cho người mới; OOF = dự đoán khi người đó bị giữ ra. Có đặc trưng nhóm can thiệp (GROUP) — phi hành gia không có. |
| `cpet_physio` | như cpet, chỉ `pre_vo2` + `age` | như cpet | như cpet | Contract dùng được cho phi hành gia. Ridge không tốt hơn `mean_delta` khi bỏ GROUP. |
| `dose_orbit` | như dose + vị trí ISS lúc dự báo | uGy/h | `4_predictions/dose_orbit` (latest) | Khoảng 90% hẹp hơn dose. Chỉ dùng vị trí hiện tại, không dùng quỹ đạo tương lai. |
| `sleep_act` | hồi quy, đêm tới | % hiệu suất ngủ | `3_models/sleep_act/<run>/oof.csv.gz`, lọc `model == personal_mean` | 3 người `utmb_c1:C1G000x` = persona tomas-ortega / yuki-tanaka / noor-abbasi. `cutoff_time` là ngày thật năm 2004 → chỉ hiển thị ngày tương đối. |
| `vitals_sbp/dbp/temp/pulse` | hồi quy, ngày tới | mmHg · °C · bpm | `4_predictions/<task>/<run>/external_backtest.csv` — dự đoán cho **đúng 6 persona** (người chưa từng thấy), có `y_true` | Train Campaign 3; persona là test NGOÀI cohort (`in_sample = False`). `cutoff_time` là ngày thật nghiên cứu → chỉ hiển thị ngày tương đối. |
| `mood` | hồi quy, lần đo tới (~1 tuần) | điểm TMD | CFT70: `3_models/mood/<run>/oof.csv.gz` (lọc `personal_mean`); C1: `4_predictions/mood/…SYNTHETIC-INPUT…csv` | C1 là dự đoán trên **dữ liệu giả định**. |
| `glucose` | hồi quy, 1 hàng/người | mg/dL | `3_models/glucose/<run>/oof.csv.gz` (lọc `mean_delta`) + chuỗi ngày `1_synthetic/glucose_daily_personas.csv` | Thay đổi lúc đói PRE → ngày 66; chuỗi ngày là giả định neo vào OGTT thật. |
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
| `dose_orbit` | lightgbm | MAE 0,637 uGy/h (0,559–0,731), 9 tháng; bao phủ 90% = 0,897 | last_value 2,14 |
| `sleep_act` | personal_mean | MAE 5,40 điểm % (4,65–5,86), 3 người — pilot | last_value 5,63 |
| `vitals_sbp` | ridge | MAE 5,72 mmHg (5,39–6,08), 23 người; **ngoài cohort 6 persona 6,14 (5,16–7,15)**, bao phủ 0,899 | last_value 7,34 / 8,08 |
| `vitals_dbp` | ridge | MAE 5,10 mmHg (4,80–5,42); **ngoài cohort 5,11 (4,48–5,92)**, bao phủ 0,905 | last_value 6,61 / 6,71 |
| `vitals_temp` | ridge | MAE 0,198 °C (0,179–0,218); **ngoài cohort 0,162 (0,141–0,180)**, 5 persona, bao phủ 0,933 | last_value 0,246 / 0,231 |
| `vitals_pulse` | ridge | MAE 5,51 bpm (5,15–5,86); **ngoài cohort 4,96 (4,38–5,55)**, bao phủ 0,929 | last_value 6,86 / 6,05 |
| `mood` | personal_mean | MAE 5,24 điểm TMD (4,20–6,30), 24 người; bao phủ 0,897 | last_value 5,56 (chênh lệch CI chứa 0) |
| `glucose` | mean_delta | MAE 3,33 mg/dL (2,16–4,69), 23 người; ridge 2,98, hoán vị p = 0,015 | persistence 3,30 |

| Chỉ số nsac | Task sky-ml | Có dữ liệu? |
|---|---|---|
| Nhịp tim | `hr` (MMASH) + `vitals_pulse` (6 persona, thật) | Có |
| Hoạt động và giấc ngủ | `sleep` (giai đoạn ngủ), `sleep_act` (hiệu suất ngủ theo đêm, 3 persona) | Có — `sleep_act` là pilot 3 người; chưa có số bước/hoạt động |
| Huyết áp, nhiệt độ cơ thể | `vitals_sbp`, `vitals_dbp`, `vitals_temp` (UTMB CRF) | **Có — dữ liệu thật của đúng 6 persona** |
| Tâm trạng | `mood` (POMS) | Có — thật cho 3 persona CFT70; **giả định** cho 3 persona C1 |
| Đường huyết | `glucose` (OGTT) + `1_synthetic/glucose_daily_personas.csv` | Có — thay đổi thật (CFT70, 5–6 mốc); chuỗi hằng ngày là **giả định** |
| (ngoài 6 chỉ số) Thể lực hiếu khí, liều bức xạ | `cpet`, `cpet_physio`, `dose` | Có — dùng cho thẻ thể lực / môi trường nếu web có |

## 3. Tạo lại dữ liệu

```powershell
uv run sky-ml load-data
foreach ($t in "hr","dose","dose_orbit","cpet","cpet_physio","sleep","sleep_act","vitals_sbp","vitals_dbp","vitals_temp","vitals_pulse","mood","glucose") {
  uv run sky-ml build-features $t; uv run sky-ml train $t; uv run sky-ml evaluate $t
}
uv run sky-ml make-synthetic   # DỮ LIỆU GIẢ ĐỊNH → data/1_synthetic
uv run sky-ml predict mood --input data/1_synthetic/mood_c1_poms.csv
uv run sky-ml predict sleep_act --input data/1_synthetic/sleep_cft70_actigraphy.csv
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
| `dose_orbit` | `2026-11-14_201827` | [`4_predictions/dose_orbit/2026-11-14_201827/2022-05-01_2023-01-01_latest_lightgbm_20261114_201912.csv`](4_predictions/dose_orbit/2026-11-14_201827/2022-05-01_2023-01-01_latest_lightgbm_20261114_201912.csv) |
| `glucose` | `2026-11-14_204458` | — |
| `hr` | `2026-11-14_145321` | [`4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.csv`](4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.csv) |
| `mood` | `2026-11-14_204452` | [`4_predictions/mood/2026-11-14_204452/mood_c1_poms_latest_personal_mean_SYNTHETIC-INPUT_20261114_204535.csv`](4_predictions/mood/2026-11-14_204452/mood_c1_poms_latest_personal_mean_SYNTHETIC-INPUT_20261114_204535.csv) |
| `persona` | `seed17` | — |
| `sleep` | `2026-11-14_164909` | — |
| `sleep_act` | `2026-11-14_201853` | [`4_predictions/sleep_act/2026-11-14_201853/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_204537.csv`](4_predictions/sleep_act/2026-11-14_201853/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_204537.csv) |
| `vitals_dbp` | `2026-11-14_204424` | [`4_predictions/vitals_dbp/2026-11-14_204424/external_backtest.csv`](4_predictions/vitals_dbp/2026-11-14_204424/external_backtest.csv) |
| `vitals_pulse` | `2026-11-14_204445` | [`4_predictions/vitals_pulse/2026-11-14_204445/external_backtest.csv`](4_predictions/vitals_pulse/2026-11-14_204445/external_backtest.csv) |
| `vitals_sbp` | `2026-11-14_204416` | [`4_predictions/vitals_sbp/2026-11-14_204416/external_backtest.csv`](4_predictions/vitals_sbp/2026-11-14_204416/external_backtest.csv) |
| `vitals_temp` | `2026-11-14_204437` | [`4_predictions/vitals_temp/2026-11-14_204437/external_backtest.csv`](4_predictions/vitals_temp/2026-11-14_204437/external_backtest.csv) |

| Nhóm | Task | Run | File | Số hàng | Byte | SHA-256 (12 ký tự đầu) | Lệnh tạo |
|---|---|---|---|---|---|---|---|
| (2) dự đoán | `vitals_temp` | `2026-11-14_204437` | [`4_predictions/vitals_temp/2026-11-14_204437/external_backtest.csv`](4_predictions/vitals_temp/2026-11-14_204437/external_backtest.csv) | 223 | 29015 | `b1591dcb5460` | `sky-ml evaluate vitals_temp` |
| (3) mô hình | `vitals_temp` | `2026-11-14_204437` | [`3_models/vitals_temp/2026-11-14_204437/summary.json`](3_models/vitals_temp/2026-11-14_204437/summary.json) |  | 2487 | `744805a9f26c` | `sky-ml evaluate vitals_temp` |
| (3) mô hình | `vitals_temp` | `2026-11-14_204437` | [`3_models/vitals_temp/2026-11-14_204437/ridge/final.joblib`](3_models/vitals_temp/2026-11-14_204437/ridge/final.joblib) |  | 987 | `f90ddd862e75` | `sky-ml train vitals_temp` |
| (3) mô hình | `vitals_temp` | `2026-11-14_204437` | [`3_models/vitals_temp/2026-11-14_204437/personal_mean/final.joblib`](3_models/vitals_temp/2026-11-14_204437/personal_mean/final.joblib) |  | 74 | `bb15f831b326` | `sky-ml train vitals_temp` |
| (3) mô hình | `vitals_temp` | `2026-11-14_204437` | [`3_models/vitals_temp/2026-11-14_204437/oof.csv.gz`](3_models/vitals_temp/2026-11-14_204437/oof.csv.gz) | 9088 | 81254 | `71c080e7ba58` | `sky-ml train vitals_temp` |
| (3) mô hình | `vitals_temp` | `2026-11-14_204437` | [`3_models/vitals_temp/2026-11-14_204437/metrics.csv`](3_models/vitals_temp/2026-11-14_204437/metrics.csv) |  | 657 | `3e09006153a9` | `sky-ml evaluate vitals_temp` |
| (3) mô hình | `vitals_temp` | `2026-11-14_204437` | [`3_models/vitals_temp/2026-11-14_204437/manifest.json`](3_models/vitals_temp/2026-11-14_204437/manifest.json) |  | 2966 | `5c29a3da97c5` | `sky-ml train vitals_temp` |
| (3) mô hình | `vitals_temp` | `2026-11-14_204437` | [`3_models/vitals_temp/2026-11-14_204437/lightgbm/final.joblib`](3_models/vitals_temp/2026-11-14_204437/lightgbm/final.joblib) |  | 41106 | `dc13799f0ece` | `sky-ml train vitals_temp` |
| (3) mô hình | `vitals_temp` | `2026-11-14_204437` | [`3_models/vitals_temp/2026-11-14_204437/last_value/final.joblib`](3_models/vitals_temp/2026-11-14_204437/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train vitals_temp` |
| (3) mô hình | `vitals_temp` | `2026-11-14_204437` | [`3_models/vitals_temp/2026-11-14_204437/folds.json`](3_models/vitals_temp/2026-11-14_204437/folds.json) |  | 1739 | `630362a31cfe` | `sky-ml train vitals_temp` |
| (1) đã xử lý | `vitals_temp` | `2026-11-14_204437` | [`2_features/vitals_temp/2026-11-14_204437/table.csv.gz`](2_features/vitals_temp/2026-11-14_204437/table.csv.gz) | 2272 | 32994 | `cf7fd5434a52` | `sky-ml build-features vitals_temp` |
| (1) đã xử lý | `vitals_temp` | `2026-11-14_204437` | [`2_features/vitals_temp/2026-11-14_204437/snapshot.json`](2_features/vitals_temp/2026-11-14_204437/snapshot.json) |  | 440 | `2c76ed858a4c` | `sky-ml build-features vitals_temp` |
| (1) đã xử lý | `vitals_temp` | `2026-11-14_204437` | [`2_features/vitals_temp/2026-11-14_204437/features.json`](2_features/vitals_temp/2026-11-14_204437/features.json) |  | 88 | `c8c920d3a47e` | `sky-ml build-features vitals_temp` |
| (1) đã xử lý | `vitals_temp` | `2026-11-14_204437` | [`2_features/vitals_temp/2026-11-14_204437/external.csv.gz`](2_features/vitals_temp/2026-11-14_204437/external.csv.gz) | 223 | 3750 | `ade61a507fa0` | `sky-ml build-features vitals_temp` |
| (2) dự đoán | `vitals_sbp` | `2026-11-14_204416` | [`4_predictions/vitals_sbp/2026-11-14_204416/external_backtest.csv`](4_predictions/vitals_sbp/2026-11-14_204416/external_backtest.csv) | 431 | 56519 | `5ffb3957ee40` | `sky-ml evaluate vitals_sbp` |
| (3) mô hình | `vitals_sbp` | `2026-11-14_204416` | [`3_models/vitals_sbp/2026-11-14_204416/summary.json`](3_models/vitals_sbp/2026-11-14_204416/summary.json) |  | 2487 | `8866f1b7f442` | `sky-ml evaluate vitals_sbp` |
| (3) mô hình | `vitals_sbp` | `2026-11-14_204416` | [`3_models/vitals_sbp/2026-11-14_204416/ridge/final.joblib`](3_models/vitals_sbp/2026-11-14_204416/ridge/final.joblib) |  | 988 | `439baf132763` | `sky-ml train vitals_sbp` |
| (3) mô hình | `vitals_sbp` | `2026-11-14_204416` | [`3_models/vitals_sbp/2026-11-14_204416/personal_mean/final.joblib`](3_models/vitals_sbp/2026-11-14_204416/personal_mean/final.joblib) |  | 74 | `bb15f831b326` | `sky-ml train vitals_sbp` |
| (3) mô hình | `vitals_sbp` | `2026-11-14_204416` | [`3_models/vitals_sbp/2026-11-14_204416/oof.csv.gz`](3_models/vitals_sbp/2026-11-14_204416/oof.csv.gz) | 9120 | 94292 | `893ce60b23b0` | `sky-ml train vitals_sbp` |
| (3) mô hình | `vitals_sbp` | `2026-11-14_204416` | [`3_models/vitals_sbp/2026-11-14_204416/metrics.csv`](3_models/vitals_sbp/2026-11-14_204416/metrics.csv) |  | 616 | `1766689dcff0` | `sky-ml evaluate vitals_sbp` |
| (3) mô hình | `vitals_sbp` | `2026-11-14_204416` | [`3_models/vitals_sbp/2026-11-14_204416/manifest.json`](3_models/vitals_sbp/2026-11-14_204416/manifest.json) |  | 2963 | `1b9f723f1405` | `sky-ml train vitals_sbp` |
| (3) mô hình | `vitals_sbp` | `2026-11-14_204416` | [`3_models/vitals_sbp/2026-11-14_204416/lightgbm/final.joblib`](3_models/vitals_sbp/2026-11-14_204416/lightgbm/final.joblib) |  | 41946 | `d83b052361a2` | `sky-ml train vitals_sbp` |
| (3) mô hình | `vitals_sbp` | `2026-11-14_204416` | [`3_models/vitals_sbp/2026-11-14_204416/last_value/final.joblib`](3_models/vitals_sbp/2026-11-14_204416/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train vitals_sbp` |
| (3) mô hình | `vitals_sbp` | `2026-11-14_204416` | [`3_models/vitals_sbp/2026-11-14_204416/folds.json`](3_models/vitals_sbp/2026-11-14_204416/folds.json) |  | 1739 | `d4c9b3b9ada2` | `sky-ml train vitals_sbp` |
| (1) đã xử lý | `vitals_sbp` | `2026-11-14_204416` | [`2_features/vitals_sbp/2026-11-14_204416/table.csv.gz`](2_features/vitals_sbp/2026-11-14_204416/table.csv.gz) | 2280 | 45322 | `4d582804d8de` | `sky-ml build-features vitals_sbp` |
| (1) đã xử lý | `vitals_sbp` | `2026-11-14_204416` | [`2_features/vitals_sbp/2026-11-14_204416/snapshot.json`](2_features/vitals_sbp/2026-11-14_204416/snapshot.json) |  | 440 | `2c76ed858a4c` | `sky-ml build-features vitals_sbp` |
| (1) đã xử lý | `vitals_sbp` | `2026-11-14_204416` | [`2_features/vitals_sbp/2026-11-14_204416/features.json`](2_features/vitals_sbp/2026-11-14_204416/features.json) |  | 88 | `c8c920d3a47e` | `sky-ml build-features vitals_sbp` |
| (1) đã xử lý | `vitals_sbp` | `2026-11-14_204416` | [`2_features/vitals_sbp/2026-11-14_204416/external.csv.gz`](2_features/vitals_sbp/2026-11-14_204416/external.csv.gz) | 431 | 9194 | `f588f58a53e9` | `sky-ml build-features vitals_sbp` |
| (2) dự đoán | `vitals_pulse` | `2026-11-14_204445` | [`4_predictions/vitals_pulse/2026-11-14_204445/external_backtest.csv`](4_predictions/vitals_pulse/2026-11-14_204445/external_backtest.csv) | 423 | 53970 | `39d4445bea58` | `sky-ml evaluate vitals_pulse` |
| (3) mô hình | `vitals_pulse` | `2026-11-14_204445` | [`3_models/vitals_pulse/2026-11-14_204445/summary.json`](3_models/vitals_pulse/2026-11-14_204445/summary.json) |  | 2491 | `06d74f6bc3af` | `sky-ml evaluate vitals_pulse` |
| (3) mô hình | `vitals_pulse` | `2026-11-14_204445` | [`3_models/vitals_pulse/2026-11-14_204445/ridge/final.joblib`](3_models/vitals_pulse/2026-11-14_204445/ridge/final.joblib) |  | 983 | `3513a353daf7` | `sky-ml train vitals_pulse` |
| (3) mô hình | `vitals_pulse` | `2026-11-14_204445` | [`3_models/vitals_pulse/2026-11-14_204445/personal_mean/final.joblib`](3_models/vitals_pulse/2026-11-14_204445/personal_mean/final.joblib) |  | 74 | `bb15f831b326` | `sky-ml train vitals_pulse` |
| (3) mô hình | `vitals_pulse` | `2026-11-14_204445` | [`3_models/vitals_pulse/2026-11-14_204445/oof.csv.gz`](3_models/vitals_pulse/2026-11-14_204445/oof.csv.gz) | 8876 | 89717 | `4be06243e089` | `sky-ml train vitals_pulse` |
| (3) mô hình | `vitals_pulse` | `2026-11-14_204445` | [`3_models/vitals_pulse/2026-11-14_204445/metrics.csv`](3_models/vitals_pulse/2026-11-14_204445/metrics.csv) |  | 618 | `4dde922b9c7a` | `sky-ml evaluate vitals_pulse` |
| (3) mô hình | `vitals_pulse` | `2026-11-14_204445` | [`3_models/vitals_pulse/2026-11-14_204445/manifest.json`](3_models/vitals_pulse/2026-11-14_204445/manifest.json) |  | 2969 | `589be152015f` | `sky-ml train vitals_pulse` |
| (3) mô hình | `vitals_pulse` | `2026-11-14_204445` | [`3_models/vitals_pulse/2026-11-14_204445/lightgbm/final.joblib`](3_models/vitals_pulse/2026-11-14_204445/lightgbm/final.joblib) |  | 37561 | `f6935104e614` | `sky-ml train vitals_pulse` |
| (3) mô hình | `vitals_pulse` | `2026-11-14_204445` | [`3_models/vitals_pulse/2026-11-14_204445/last_value/final.joblib`](3_models/vitals_pulse/2026-11-14_204445/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train vitals_pulse` |
| (3) mô hình | `vitals_pulse` | `2026-11-14_204445` | [`3_models/vitals_pulse/2026-11-14_204445/folds.json`](3_models/vitals_pulse/2026-11-14_204445/folds.json) |  | 1738 | `8bbcfea90bb3` | `sky-ml train vitals_pulse` |
| (1) đã xử lý | `vitals_pulse` | `2026-11-14_204445` | [`2_features/vitals_pulse/2026-11-14_204445/table.csv.gz`](2_features/vitals_pulse/2026-11-14_204445/table.csv.gz) | 2219 | 42937 | `e11d77a39b45` | `sky-ml build-features vitals_pulse` |
| (1) đã xử lý | `vitals_pulse` | `2026-11-14_204445` | [`2_features/vitals_pulse/2026-11-14_204445/snapshot.json`](2_features/vitals_pulse/2026-11-14_204445/snapshot.json) |  | 440 | `2c76ed858a4c` | `sky-ml build-features vitals_pulse` |
| (1) đã xử lý | `vitals_pulse` | `2026-11-14_204445` | [`2_features/vitals_pulse/2026-11-14_204445/features.json`](2_features/vitals_pulse/2026-11-14_204445/features.json) |  | 88 | `c8c920d3a47e` | `sky-ml build-features vitals_pulse` |
| (1) đã xử lý | `vitals_pulse` | `2026-11-14_204445` | [`2_features/vitals_pulse/2026-11-14_204445/external.csv.gz`](2_features/vitals_pulse/2026-11-14_204445/external.csv.gz) | 423 | 8665 | `34724dad5a55` | `sky-ml build-features vitals_pulse` |
| (2) dự đoán | `vitals_dbp` | `2026-11-14_204424` | [`4_predictions/vitals_dbp/2026-11-14_204424/external_backtest.csv`](4_predictions/vitals_dbp/2026-11-14_204424/external_backtest.csv) | 431 | 54848 | `91593ef6f1e4` | `sky-ml evaluate vitals_dbp` |
| (3) mô hình | `vitals_dbp` | `2026-11-14_204424` | [`3_models/vitals_dbp/2026-11-14_204424/summary.json`](3_models/vitals_dbp/2026-11-14_204424/summary.json) |  | 2490 | `b970c8492188` | `sky-ml evaluate vitals_dbp` |
| (3) mô hình | `vitals_dbp` | `2026-11-14_204424` | [`3_models/vitals_dbp/2026-11-14_204424/ridge/final.joblib`](3_models/vitals_dbp/2026-11-14_204424/ridge/final.joblib) |  | 988 | `61f8e859c298` | `sky-ml train vitals_dbp` |
| (3) mô hình | `vitals_dbp` | `2026-11-14_204424` | [`3_models/vitals_dbp/2026-11-14_204424/personal_mean/final.joblib`](3_models/vitals_dbp/2026-11-14_204424/personal_mean/final.joblib) |  | 74 | `bb15f831b326` | `sky-ml train vitals_dbp` |
| (3) mô hình | `vitals_dbp` | `2026-11-14_204424` | [`3_models/vitals_dbp/2026-11-14_204424/oof.csv.gz`](3_models/vitals_dbp/2026-11-14_204424/oof.csv.gz) | 9120 | 92801 | `3c2cd2fb9d6f` | `sky-ml train vitals_dbp` |
| (3) mô hình | `vitals_dbp` | `2026-11-14_204424` | [`3_models/vitals_dbp/2026-11-14_204424/metrics.csv`](3_models/vitals_dbp/2026-11-14_204424/metrics.csv) |  | 617 | `608058894249` | `sky-ml evaluate vitals_dbp` |
| (3) mô hình | `vitals_dbp` | `2026-11-14_204424` | [`3_models/vitals_dbp/2026-11-14_204424/manifest.json`](3_models/vitals_dbp/2026-11-14_204424/manifest.json) |  | 2963 | `1e611f6fa86b` | `sky-ml train vitals_dbp` |
| (3) mô hình | `vitals_dbp` | `2026-11-14_204424` | [`3_models/vitals_dbp/2026-11-14_204424/lightgbm/final.joblib`](3_models/vitals_dbp/2026-11-14_204424/lightgbm/final.joblib) |  | 39746 | `b9f10649f807` | `sky-ml train vitals_dbp` |
| (3) mô hình | `vitals_dbp` | `2026-11-14_204424` | [`3_models/vitals_dbp/2026-11-14_204424/last_value/final.joblib`](3_models/vitals_dbp/2026-11-14_204424/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train vitals_dbp` |
| (3) mô hình | `vitals_dbp` | `2026-11-14_204424` | [`3_models/vitals_dbp/2026-11-14_204424/folds.json`](3_models/vitals_dbp/2026-11-14_204424/folds.json) |  | 1739 | `d4c9b3b9ada2` | `sky-ml train vitals_dbp` |
| (1) đã xử lý | `vitals_dbp` | `2026-11-14_204424` | [`2_features/vitals_dbp/2026-11-14_204424/table.csv.gz`](2_features/vitals_dbp/2026-11-14_204424/table.csv.gz) | 2280 | 42443 | `d0e8fe499978` | `sky-ml build-features vitals_dbp` |
| (1) đã xử lý | `vitals_dbp` | `2026-11-14_204424` | [`2_features/vitals_dbp/2026-11-14_204424/snapshot.json`](2_features/vitals_dbp/2026-11-14_204424/snapshot.json) |  | 440 | `2c76ed858a4c` | `sky-ml build-features vitals_dbp` |
| (1) đã xử lý | `vitals_dbp` | `2026-11-14_204424` | [`2_features/vitals_dbp/2026-11-14_204424/features.json`](2_features/vitals_dbp/2026-11-14_204424/features.json) |  | 88 | `c8c920d3a47e` | `sky-ml build-features vitals_dbp` |
| (1) đã xử lý | `vitals_dbp` | `2026-11-14_204424` | [`2_features/vitals_dbp/2026-11-14_204424/external.csv.gz`](2_features/vitals_dbp/2026-11-14_204424/external.csv.gz) | 431 | 8767 | `887b139a0aad` | `sky-ml build-features vitals_dbp` |
| (2) dự đoán | `sleep_act` | `2026-11-14_201853` | [`4_predictions/sleep_act/2026-11-14_201853/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_204537.json`](4_predictions/sleep_act/2026-11-14_201853/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_204537.json) |  | 282 | `590e8d2b39ba` | `sky-ml predict sleep_act --input sleep_cft70_actigraphy.csv --mode latest` |
| (2) dự đoán | `sleep_act` | `2026-11-14_201853` | [`4_predictions/sleep_act/2026-11-14_201853/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_204537.csv`](4_predictions/sleep_act/2026-11-14_201853/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_204537.csv) | 3 | 401 | `b4acf9917572` | `sky-ml predict sleep_act --input sleep_cft70_actigraphy.csv --mode latest` |
| (3) mô hình | `sleep_act` | `2026-11-14_201853` | [`3_models/sleep_act/2026-11-14_201853/summary.json`](3_models/sleep_act/2026-11-14_201853/summary.json) |  | 1411 | `ac6d379c88ee` | `sky-ml evaluate sleep_act` |
| (3) mô hình | `sleep_act` | `2026-11-14_201853` | [`3_models/sleep_act/2026-11-14_201853/ridge/final.joblib`](3_models/sleep_act/2026-11-14_201853/ridge/final.joblib) |  | 984 | `79b7e1248d46` | `sky-ml train sleep_act` |
| (3) mô hình | `sleep_act` | `2026-11-14_201853` | [`3_models/sleep_act/2026-11-14_201853/personal_mean/final.joblib`](3_models/sleep_act/2026-11-14_201853/personal_mean/final.joblib) |  | 74 | `bb15f831b326` | `sky-ml train sleep_act` |
| (3) mô hình | `sleep_act` | `2026-11-14_201853` | [`3_models/sleep_act/2026-11-14_201853/oof.csv.gz`](3_models/sleep_act/2026-11-14_201853/oof.csv.gz) | 648 | 6885 | `889f3dbe4ea3` | `sky-ml train sleep_act` |
| (3) mô hình | `sleep_act` | `2026-11-14_201853` | [`3_models/sleep_act/2026-11-14_201853/metrics.csv`](3_models/sleep_act/2026-11-14_201853/metrics.csv) |  | 606 | `c484a440294e` | `sky-ml evaluate sleep_act` |
| (3) mô hình | `sleep_act` | `2026-11-14_201853` | [`3_models/sleep_act/2026-11-14_201853/manifest.json`](3_models/sleep_act/2026-11-14_201853/manifest.json) |  | 2972 | `9d23d4369ba8` | `sky-ml train sleep_act` |
| (3) mô hình | `sleep_act` | `2026-11-14_201853` | [`3_models/sleep_act/2026-11-14_201853/lightgbm/final.joblib`](3_models/sleep_act/2026-11-14_201853/lightgbm/final.joblib) |  | 12667 | `d02e47d7e837` | `sky-ml train sleep_act` |
| (3) mô hình | `sleep_act` | `2026-11-14_201853` | [`3_models/sleep_act/2026-11-14_201853/last_value/final.joblib`](3_models/sleep_act/2026-11-14_201853/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train sleep_act` |
| (3) mô hình | `sleep_act` | `2026-11-14_201853` | [`3_models/sleep_act/2026-11-14_201853/folds.json`](3_models/sleep_act/2026-11-14_201853/folds.json) |  | 233 | `da8937441667` | `sky-ml train sleep_act` |
| (1) đã xử lý | `sleep_act` | `2026-11-14_201853` | [`2_features/sleep_act/2026-11-14_201853/table.csv.gz`](2_features/sleep_act/2026-11-14_201853/table.csv.gz) | 162 | 4290 | `3d4113b2ec1b` | `sky-ml build-features sleep_act` |
| (1) đã xử lý | `sleep_act` | `2026-11-14_201853` | [`2_features/sleep_act/2026-11-14_201853/snapshot.json`](2_features/sleep_act/2026-11-14_201853/snapshot.json) |  | 444 | `b3eba27d31a1` | `sky-ml build-features sleep_act` |
| (1) đã xử lý | `sleep_act` | `2026-11-14_201853` | [`2_features/sleep_act/2026-11-14_201853/features.json`](2_features/sleep_act/2026-11-14_201853/features.json) |  | 88 | `c8c920d3a47e` | `sky-ml build-features sleep_act` |
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
| ⚠️ GIẢ ĐỊNH | `persona` | `seed17` | [`1_synthetic/sleep_cft70_actigraphy.validation.csv`](1_synthetic/sleep_cft70_actigraphy.validation.csv) |  | 558 | `65c37ee2921d` | `sky-ml make-synthetic` |
| ⚠️ GIẢ ĐỊNH | `persona` | `seed17` | [`1_synthetic/sleep_cft70_actigraphy.params.json`](1_synthetic/sleep_cft70_actigraphy.params.json) |  | 1598 | `0a87d65fd782` | `sky-ml make-synthetic` |
| ⚠️ GIẢ ĐỊNH | `persona` | `seed17` | [`1_synthetic/sleep_cft70_actigraphy.csv`](1_synthetic/sleep_cft70_actigraphy.csv) |  | 18662 | `88d947c8f9d1` | `sky-ml make-synthetic` |
| ⚠️ GIẢ ĐỊNH | `persona` | `seed17` | [`1_synthetic/mood_c1_poms.validation.csv`](1_synthetic/mood_c1_poms.validation.csv) |  | 258 | `dca34a8662b0` | `sky-ml make-synthetic` |
| ⚠️ GIẢ ĐỊNH | `persona` | `seed17` | [`1_synthetic/mood_c1_poms.params.json`](1_synthetic/mood_c1_poms.params.json) |  | 838 | `eeb4ab568e86` | `sky-ml make-synthetic` |
| ⚠️ GIẢ ĐỊNH | `persona` | `seed17` | [`1_synthetic/mood_c1_poms.csv`](1_synthetic/mood_c1_poms.csv) |  | 2981 | `9219203b8e41` | `sky-ml make-synthetic` |
| ⚠️ GIẢ ĐỊNH | `persona` | `seed17` | [`1_synthetic/glucose_daily_personas.validation.csv`](1_synthetic/glucose_daily_personas.validation.csv) |  | 278 | `524f2088c02e` | `sky-ml make-synthetic` |
| ⚠️ GIẢ ĐỊNH | `persona` | `seed17` | [`1_synthetic/glucose_daily_personas.params.json`](1_synthetic/glucose_daily_personas.params.json) |  | 637 | `a3a240f4bbcc` | `sky-ml make-synthetic` |
| ⚠️ GIẢ ĐỊNH | `persona` | `seed17` | [`1_synthetic/glucose_daily_personas.csv`](1_synthetic/glucose_daily_personas.csv) |  | 31201 | `35a6e9b055fb` | `sky-ml make-synthetic` |
| ⚠️ GIẢ ĐỊNH | `persona` | `seed17` | [`1_synthetic/README.md`](1_synthetic/README.md) |  | 4040 | `9cce9453ad2e` | `sky-ml make-synthetic` |
| (2) dự đoán | `mood` | `2026-11-14_204452` | [`4_predictions/mood/2026-11-14_204452/mood_c1_poms_latest_personal_mean_SYNTHETIC-INPUT_20261114_204535.json`](4_predictions/mood/2026-11-14_204452/mood_c1_poms_latest_personal_mean_SYNTHETIC-INPUT_20261114_204535.json) |  | 267 | `406f23dc347c` | `sky-ml predict mood --input mood_c1_poms.csv --mode latest` |
| (2) dự đoán | `mood` | `2026-11-14_204452` | [`4_predictions/mood/2026-11-14_204452/mood_c1_poms_latest_personal_mean_SYNTHETIC-INPUT_20261114_204535.csv`](4_predictions/mood/2026-11-14_204452/mood_c1_poms_latest_personal_mean_SYNTHETIC-INPUT_20261114_204535.csv) | 3 | 429 | `53213cd3497e` | `sky-ml predict mood --input mood_c1_poms.csv --mode latest` |
| (3) mô hình | `mood` | `2026-11-14_204452` | [`3_models/mood/2026-11-14_204452/summary.json`](3_models/mood/2026-11-14_204452/summary.json) |  | 1584 | `700c065d4ab0` | `sky-ml evaluate mood` |
| (3) mô hình | `mood` | `2026-11-14_204452` | [`3_models/mood/2026-11-14_204452/ridge/final.joblib`](3_models/mood/2026-11-14_204452/ridge/final.joblib) |  | 938 | `362e9d0e6a62` | `sky-ml train mood` |
| (3) mô hình | `mood` | `2026-11-14_204452` | [`3_models/mood/2026-11-14_204452/personal_mean/final.joblib`](3_models/mood/2026-11-14_204452/personal_mean/final.joblib) |  | 74 | `bb15f831b326` | `sky-ml train mood` |
| (3) mô hình | `mood` | `2026-11-14_204452` | [`3_models/mood/2026-11-14_204452/oof.csv.gz`](3_models/mood/2026-11-14_204452/oof.csv.gz) | 1168 | 12105 | `162381441758` | `sky-ml train mood` |
| (3) mô hình | `mood` | `2026-11-14_204452` | [`3_models/mood/2026-11-14_204452/metrics.csv`](3_models/mood/2026-11-14_204452/metrics.csv) |  | 618 | `128d2adb6bd2` | `sky-ml evaluate mood` |
| (3) mô hình | `mood` | `2026-11-14_204452` | [`3_models/mood/2026-11-14_204452/manifest.json`](3_models/mood/2026-11-14_204452/manifest.json) |  | 2931 | `48d1e550ba04` | `sky-ml train mood` |
| (3) mô hình | `mood` | `2026-11-14_204452` | [`3_models/mood/2026-11-14_204452/lightgbm/final.joblib`](3_models/mood/2026-11-14_204452/lightgbm/final.joblib) |  | 13647 | `f350a79024eb` | `sky-ml train mood` |
| (3) mô hình | `mood` | `2026-11-14_204452` | [`3_models/mood/2026-11-14_204452/last_value/final.joblib`](3_models/mood/2026-11-14_204452/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train mood` |
| (3) mô hình | `mood` | `2026-11-14_204452` | [`3_models/mood/2026-11-14_204452/folds.json`](3_models/mood/2026-11-14_204452/folds.json) |  | 1849 | `344f6330f0e7` | `sky-ml train mood` |
| (1) đã xử lý | `mood` | `2026-11-14_204452` | [`2_features/mood/2026-11-14_204452/table.csv.gz`](2_features/mood/2026-11-14_204452/table.csv.gz) | 292 | 4292 | `22312504a596` | `sky-ml build-features mood` |
| (1) đã xử lý | `mood` | `2026-11-14_204452` | [`2_features/mood/2026-11-14_204452/snapshot.json`](2_features/mood/2026-11-14_204452/snapshot.json) |  | 447 | `9f2f000cba4c` | `sky-ml build-features mood` |
| (1) đã xử lý | `mood` | `2026-11-14_204452` | [`2_features/mood/2026-11-14_204452/features.json`](2_features/mood/2026-11-14_204452/features.json) |  | 71 | `da8d2b3f7a97` | `sky-ml build-features mood` |
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
| (3) mô hình | `glucose` | `2026-11-14_204458` | [`3_models/glucose/2026-11-14_204458/summary.json`](3_models/glucose/2026-11-14_204458/summary.json) |  | 1501 | `42c38f3b3400` | `sky-ml evaluate glucose` |
| (3) mô hình | `glucose` | `2026-11-14_204458` | [`3_models/glucose/2026-11-14_204458/ridge/final.joblib`](3_models/glucose/2026-11-14_204458/ridge/final.joblib) |  | 869 | `69b7264fad39` | `sky-ml train glucose` |
| (3) mô hình | `glucose` | `2026-11-14_204458` | [`3_models/glucose/2026-11-14_204458/persistence/final.joblib`](3_models/glucose/2026-11-14_204458/persistence/final.joblib) |  | 451 | `21d32c907c40` | `sky-ml train glucose` |
| (3) mô hình | `glucose` | `2026-11-14_204458` | [`3_models/glucose/2026-11-14_204458/oof.csv.gz`](3_models/glucose/2026-11-14_204458/oof.csv.gz) | 69 | 1167 | `4c7d6416c060` | `sky-ml train glucose` |
| (3) mô hình | `glucose` | `2026-11-14_204458` | [`3_models/glucose/2026-11-14_204458/metrics.csv`](3_models/glucose/2026-11-14_204458/metrics.csv) |  | 475 | `cb6368d9c9fa` | `sky-ml evaluate glucose` |
| (3) mô hình | `glucose` | `2026-11-14_204458` | [`3_models/glucose/2026-11-14_204458/mean_delta/final.joblib`](3_models/glucose/2026-11-14_204458/mean_delta/final.joblib) |  | 464 | `beba2a2d8d78` | `sky-ml train glucose` |
| (3) mô hình | `glucose` | `2026-11-14_204458` | [`3_models/glucose/2026-11-14_204458/manifest.json`](3_models/glucose/2026-11-14_204458/manifest.json) |  | 2417 | `515ec539f9d1` | `sky-ml train glucose` |
| (3) mô hình | `glucose` | `2026-11-14_204458` | [`3_models/glucose/2026-11-14_204458/folds.json`](3_models/glucose/2026-11-14_204458/folds.json) |  | 1727 | `99d2c81c1d62` | `sky-ml train glucose` |
| (1) đã xử lý | `glucose` | `2026-11-14_204458` | [`2_features/glucose/2026-11-14_204458/table.csv.gz`](2_features/glucose/2026-11-14_204458/table.csv.gz) | 23 | 538 | `8e5eea772208` | `sky-ml build-features glucose` |
| (1) đã xử lý | `glucose` | `2026-11-14_204458` | [`2_features/glucose/2026-11-14_204458/snapshot.json`](2_features/glucose/2026-11-14_204458/snapshot.json) |  | 447 | `9f2f000cba4c` | `sky-ml build-features glucose` |
| (1) đã xử lý | `glucose` | `2026-11-14_204458` | [`2_features/glucose/2026-11-14_204458/features.json`](2_features/glucose/2026-11-14_204458/features.json) |  | 61 | `43baffb54f07` | `sky-ml build-features glucose` |
| (2) dự đoán | `dose_orbit` | `2026-11-14_201827` | [`4_predictions/dose_orbit/2026-11-14_201827/2022-05-01_2023-01-01_latest_lightgbm_20261114_201912.json`](4_predictions/dose_orbit/2026-11-14_201827/2022-05-01_2023-01-01_latest_lightgbm_20261114_201912.json) |  | 277 | `a676d9af8f53` | `sky-ml predict dose_orbit --input 2022-05-01_2023-01-01.csv --mode latest` |
| (2) dự đoán | `dose_orbit` | `2026-11-14_201827` | [`4_predictions/dose_orbit/2026-11-14_201827/2022-05-01_2023-01-01_latest_lightgbm_20261114_201912.csv`](4_predictions/dose_orbit/2026-11-14_201827/2022-05-01_2023-01-01_latest_lightgbm_20261114_201912.csv) | 1 | 200 | `d5ca1df293d8` | `sky-ml predict dose_orbit --input 2022-05-01_2023-01-01.csv --mode latest` |
| (3) mô hình | `dose_orbit` | `2026-11-14_201827` | [`3_models/dose_orbit/2026-11-14_201827/summary.json`](3_models/dose_orbit/2026-11-14_201827/summary.json) |  | 1134 | `0fa7f3393974` | `sky-ml evaluate dose_orbit` |
| (3) mô hình | `dose_orbit` | `2026-11-14_201827` | [`3_models/dose_orbit/2026-11-14_201827/ridge/final.joblib`](3_models/dose_orbit/2026-11-14_201827/ridge/final.joblib) |  | 1167 | `ee8408062448` | `sky-ml train dose_orbit` |
| (3) mô hình | `dose_orbit` | `2026-11-14_201827` | [`3_models/dose_orbit/2026-11-14_201827/oof.csv.gz`](3_models/dose_orbit/2026-11-14_201827/oof.csv.gz) | 18771 | 405811 | `417ef8b87f30` | `sky-ml train dose_orbit` |
| (3) mô hình | `dose_orbit` | `2026-11-14_201827` | [`3_models/dose_orbit/2026-11-14_201827/metrics.csv`](3_models/dose_orbit/2026-11-14_201827/metrics.csv) |  | 474 | `3f21e0acf9a9` | `sky-ml evaluate dose_orbit` |
| (3) mô hình | `dose_orbit` | `2026-11-14_201827` | [`3_models/dose_orbit/2026-11-14_201827/manifest.json`](3_models/dose_orbit/2026-11-14_201827/manifest.json) |  | 2934 | `595dad11b904` | `sky-ml train dose_orbit` |
| (3) mô hình | `dose_orbit` | `2026-11-14_201827` | [`3_models/dose_orbit/2026-11-14_201827/lightgbm/final.joblib`](3_models/dose_orbit/2026-11-14_201827/lightgbm/final.joblib) |  | 133595 | `7d290e5dfb10` | `sky-ml train dose_orbit` |
| (3) mô hình | `dose_orbit` | `2026-11-14_201827` | [`3_models/dose_orbit/2026-11-14_201827/last_value/final.joblib`](3_models/dose_orbit/2026-11-14_201827/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train dose_orbit` |
| (3) mô hình | `dose_orbit` | `2026-11-14_201827` | [`3_models/dose_orbit/2026-11-14_201827/folds.json`](3_models/dose_orbit/2026-11-14_201827/folds.json) |  | 650 | `1d7bbc77a889` | `sky-ml train dose_orbit` |
| (1) đã xử lý | `dose_orbit` | `2026-11-14_201827` | [`2_features/dose_orbit/2026-11-14_201827/table.csv.gz`](2_features/dose_orbit/2026-11-14_201827/table.csv.gz) | 8366 | 679388 | `23220b09c681` | `sky-ml build-features dose_orbit` |
| (1) đã xử lý | `dose_orbit` | `2026-11-14_201827` | [`2_features/dose_orbit/2026-11-14_201827/snapshot.json`](2_features/dose_orbit/2026-11-14_201827/snapshot.json) |  | 632 | `4c4088fd10df` | `sky-ml build-features dose_orbit` |
| (1) đã xử lý | `dose_orbit` | `2026-11-14_201827` | [`2_features/dose_orbit/2026-11-14_201827/features.json`](2_features/dose_orbit/2026-11-14_201827/features.json) |  | 163 | `b4d8dfc63dca` | `sky-ml build-features dose_orbit` |
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
