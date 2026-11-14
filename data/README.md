# data/ — dữ liệu của sky-ml (repo `nsac-data`)

> Cập nhật 14/11/2026 21:15 · 21 task · 6 chỉ số web × 6 persona · có ⚠️ **dữ liệu giả định** (mục 1, 2.4).
> Phần **4. Danh mục dữ liệu** do `sky-ml` tự sinh từ `CATALOG.csv`; phần còn lại viết tay. Mỗi thư mục run có `README.md` riêng (data card) — viết lại bằng `uv run sky-ml refresh-docs`.

| Tài liệu | Nội dung |
|---|---|
| [`../docs/BAO_CAO_DU_LIEU_VA_MO_HINH_2026-11-14.md`](../docs/BAO_CAO_DU_LIEU_VA_MO_HINH_2026-11-14.md) | Báo cáo tổng hợp: dữ liệu, kết quả, dữ liệu giả định, đề xuất |
| [`../docs/Tong_hop_du_lieu_mo_hinh.xlsx`](../docs/Tong_hop_du_lieu_mo_hinh.xlsx) | Bảng: nguồn gốc, lý do, mục tiêu, kết quả, persona × chỉ số, trích dẫn |
| [`../docs/3_HUONG_DAN_DU_LIEU.md`](../docs/3_HUONG_DAN_DU_LIEU.md) | Hướng dẫn cấu trúc dữ liệu cho người |
| [`../docs/LOGIC_RA_QUYET_DINH_SKY_2026-11-14.md`](../docs/LOGIC_RA_QUYET_DINH_SKY_2026-11-14.md) | Logic ra quyết định / ngưỡng có nhãn bằng chứng |
| [`../configs/crew_map.yaml`](../configs/crew_map.yaml) | Persona ↔ người analog; nguồn THẬT / GIẢ ĐỊNH cho từng chỉ số |
| [`1_synthetic/README.md`](1_synthetic/README.md) | ⚠️ Chi tiết dữ liệu giả định: phương pháp, tham số, kiểm tra |

## 1. Cấu trúc

| Thư mục | Nhóm | Bước tạo | Nội dung |
|---|---|---|---|
| `1_source/` | Bản copy nguồn THẬT (chỉ đọc) | 1 `load-data` | Copy từ NASA-cl, kiểm SHA-256, ghi `COPY_MANIFEST.csv`. Trên git: MMASH `processed/sample-v2/`, Lidal, `raw/nlsp/{MR080G, MR079G, BRSMImmune, BRSMAct, CRF, NNX10AP86G, BRSMCF}.zip` + `download_manifest.csv`, giấy phép. **Không đẩy** 20 file EDF Sleep-EDF (~480 MB). |
| `1_synthetic/` | ⚠️ **DỮ LIỆU GIẢ ĐỊNH** | `make-synthetic` | 3 bộ cho persona thiếu dữ liệu thật + `*.params.json` (tham số ước lượng từ dữ liệu thật) + `*.validation.csv` + `SYNTHETIC_MANIFEST.csv` + `README.md`. **Không dùng để train/đánh giá.** |
| `2_features/<task>/<run>/` | **(1) Dữ liệu đã xử lý = đầu vào mô hình** | 2 `build-features` | `table.csv.gz` (bảng train), `features.json`, `snapshot.json`; với `vitals_*` thêm `external.csv.gz` (6 persona, không train) |
| `3_models/<task>/<run>/` | **(3) Mô hình đã huấn luyện** | 3 `train`, 4 `evaluate` | `<model>/final.joblib`, `manifest.json`, `oof.csv.gz`, `folds.json`, `metrics.csv`, `summary.json`; tùy task: `confusion.csv` (sleep), `external_metrics.csv` (vitals_*) |
| `4_predictions/<task>/<run>/` | **(2) Dữ liệu dự đoán** | 5 `predict` (+ 4 với vitals) | `<input>_<mode>_<model>[_SYNTHETIC-INPUT]_<thời điểm>.csv/.json`; `external_backtest.csv` (vitals_*: 6 persona, có đáp án) |
| `CATALOG.csv` | Sổ cái | mọi bước | Mỗi file một dòng: `created_at_utc, kind, task, run_id, path, rows, bytes, sha256, produced_by` (`kind` = features / models / predictions / synthetic) |

Cùng `run_id` ở 2 – 3 – 4 = cùng một chuỗi xử lý (truy vết: dự đoán → mô hình → bảng đặc trưng → file nguồn).

## 2. Hướng dẫn cho agent của web (nsac)

> Dành cho agent xây/duy trì web nsac (TypeScript + Bun + Drizzle SQLite). Đọc hết mục này trước khi dùng bất kỳ file nào trong `data/`.

### 2.1 Bắt đầu nhanh: persona → file cần đọc

Persona chỉ lấy dữ liệu của ĐÚNG một người analog (`configs/crew_map.yaml`). `<run>` = run mới nhất của task trong mục 4.

| Chỉ số web | ayla-reyes · dae-jung-park · lena-fischer (`utmb_cft70:5160/8072/8936`) | tomas-ortega · yuki-tanaka · noor-abbasi (`utmb_c1:C1G0001/2/3`) |
|---|---|---|
| Nhịp tim | Thật · `4_predictions/vitals_pulse/<run>/external_backtest.csv` | Thật · như bên trái |
| Huyết áp | Thật · `4_predictions/vitals_sbp\|vitals_dbp/<run>/external_backtest.csv` | Thật · như bên trái |
| Nhiệt độ cơ thể | Thật · `4_predictions/vitals_temp/<run>/external_backtest.csv` | Thật nhưng thiếu ngày (C1G0001 không có chuỗi đủ dài) → UNKNOWN khi thiếu |
| Tâm trạng | Thật · `3_models/mood/<run>/oof.csv.gz` (lọc `model = personal_mean`) | ⚠️ Giả định · `4_predictions/mood/<run>/*SYNTHETIC-INPUT*.csv`; chuỗi: `1_synthetic/mood_c1_poms.csv` |
| Hoạt động và giấc ngủ | ⚠️ Giả định · `4_predictions/sleep_act/<run>/*SYNTHETIC-INPUT*.csv`; chuỗi: `1_synthetic/sleep_cft70_actigraphy.csv` | Thật · `3_models/sleep_act/<run>/oof.csv.gz` (lọc `personal_mean`) |
| Nhịp thở | Thật · `4_predictions/vitals_resp/<run>/external_backtest.csv` | Thật · như bên trái |
| Cân nặng | Thật · `4_predictions/vitals_weight/<run>/external_backtest.csv` | Thật · như bên trái |
| Thời lượng ngủ (giờ) | ⚠️ Giả định · `4_predictions/sleep_act_duration/<run>/*SYNTHETIC-INPUT*.csv` | Thật · `3_models/sleep_act_duration/<run>/oof.csv.gz` |
| Mệt mỏi (MFSI-SF) | Thật · `3_models/fatigue/<run>/oof.csv.gz` (lọc `personal_mean`) | Không có → UNKNOWN |
| Khối nạc chân, khoáng xương | Thật · `3_models/lean_mass_legs\|bone_mineral/<run>/oof.csv.gz` + `2_features/…/table.csv.gz` (% thay đổi PRE → ngày 70) | Không có → UNKNOWN |
| Tim: khối lượng / thể tích thất trái | Thật · `3_models/lv_mass\|lv_diastolic_volume/<run>/oof.csv.gz` (% thay đổi PRE → ngày 70, siêu âm 3D) | Không có → UNKNOWN |
| Đường huyết | Thật ở 5–6 mốc OGTT + ⚠️ giả định giữa các mốc · `1_synthetic/glucose_daily_personas.csv`; thay đổi PRE → ngày 66: `3_models/glucose/<run>/oof.csv.gz` | ⚠️ Giả định · `1_synthetic/glucose_daily_personas.csv` |

Ngoài 6 chỉ số (dùng nếu web có thẻ môi trường/thể lực): `dose`, `dose_orbit` (bức xạ ISS), `cpet`, `cpet_physio` (VO2peak), `hr` (MMASH), `sleep` (giai đoạn ngủ EEG) — không gắn với persona.

### 2.2 Thứ tự đọc

1. Mục **4. Danh mục dữ liệu** → `Run mới nhất` của task (run_id lớn nhất theo chuỗi `YYYY-MM-DD_HHMMSS`).
2. File dự đoán / OOF theo bảng 2.1 + file `.json` cùng tên (thông tin lần chạy).
3. `3_models/<task>/<run>/summary.json` → độ chính xác để hiển thị kèm.
4. `README.md` trong từng thư mục khi cần nghĩa của cột. Kiểm toàn vẹn bằng `sha256` trong `CATALOG.csv`.

### 2.3 Hợp đồng dữ liệu — file dự đoán `.csv`

| Cột | Kiểu | Ý nghĩa / cách dùng |
|---|---|---|
| `subject_id` | string | Mã có namespace nguồn: `utmb_cft70:5160`, `utmb_c1:C1G0001`, `utmb_c3:…`, `mmash:user_1`, `radlab:Lidal`. Map sang persona bằng `crew_map.yaml`. |
| `cutoff_time` | số hoặc ngày | Điểm cuối dữ liệu đã dùng. Phút (hr), ngày nghiên cứu (mood), ngày gốc của nghiên cứu (vitals, sleep_act), thời điểm nguồn (dose). **Không hiển thị ngày gốc** — đổi sang ngày tương đối. |
| `model`, `unit` | string | Mô hình đã dùng (= `deploy_model`), đơn vị của `prediction`. |
| `prediction` | float \| nhãn \| rỗng | Giá trị dự báo; nhãn với task phân loại; rỗng khi `abstain = True`. |
| `low90`, `high90` | float \| rỗng | Khoảng dự đoán 90% (split-conformal từ sai số OOF). Không có ở task phân loại. |
| `p_<lớp>` | float | Chỉ task phân loại (sleep): xác suất từng lớp. |
| `abstain`, `reasons` | bool, string | Từ chối dự báo + lý do (phân cách `;`): `missing_features`, `out_of_training_range`, `insufficient_calibration_data`. |
| `in_sample` | bool | `True` = người/chuỗi đã có trong dữ liệu huấn luyện. |
| `input_synthetic` | bool | `True` = đầu vào là ⚠️ **dữ liệu giả định**. |
| `y_true`, `abs_error` / `correct` | | Chỉ khi có đáp án (backtest, `external_backtest.csv`). |

File `.json` cùng tên: `task, run_id, model, mode, input, half_width_90, n_rows, n_abstain, n_in_sample, n_input_synthetic` (+ `mae_backtest`).

### 2.4 Quy tắc hiển thị (bắt buộc)

- `abstain = True` → **không hiển thị số**; trạng thái `UNKNOWN` kèm `reasons`. Không nội suy, không thay bằng giá trị trước.
- Luôn hiển thị `prediction` **kèm khoảng** `low90–high90` và đơn vị.
- `in_sample = True` → nhãn "minh họa trên dữ liệu huấn luyện"; không dùng làm bằng chứng độ chính xác.
- ⚠️ **Dữ liệu giả định** (`input_synthetic = True`, `is_synthetic = True`, mọi file trong `1_synthetic/`): luôn gắn nhãn **"Dữ liệu giả định"**, màu/kiểu nét khác dữ liệu thật; trong `glucose_daily_personas.csv` hàng `is_synthetic = False` là giá trị OGTT THẬT → hiển thị khác biệt.
- Độ chính xác lấy từ `summary.json` (`metrics`, `interval_coverage*`, `external` cho vitals) — không tự tính lại.
- Không tự đặt ngưỡng cảnh báo; theo `docs/LOGIC_RA_QUYET_DINH_SKY_2026-11-14.md`. Các ngưỡng trong dữ liệu chỉ là ngưỡng KỸ THUẬT để loại số ghi hỏng.
- Ghi nguồn (đầy đủ ở sheet `Trich_dan`): UTMB bed rest — NASA NLSP; MMASH — Rossi et al. 2020 (ODbL); Sleep-EDF — Kemp et al. 2000 (ODC-By); RadLab — NASA OSDR.

### 2.5 Những điều không làm

- **Không nạp `.joblib` trong web** (pickle Python, có thể chạy mã). Web chỉ đọc CSV/JSON; dự báo mới chạy bằng `sky-ml predict`.
- Không gán người analog khác cho persona ngoài `crew_map.yaml`; không gán `mmash:*`, `utmb_c3:*` cho persona.
- Không gộp cohort (MMASH, UTMB C1/C3/CFT70, Sleep-EDF, RadLab) theo ID hay thời gian.
- Không sửa tay file trong `data/`, kể cả mục 4 (sẽ bị ghi đè). Bundle `export-nsac` **chưa xây**.

### 2.6 Đọc theo từng task

| Task | Loại | Đơn vị | Lưu ý riêng |
|---|---|---|---|
| `vitals_sbp/dbp/temp/pulse/resp/weight` | hồi quy, ngày tới | mmHg · °C · bpm · lần/phút · kg | Train 23 người Campaign 3; 6 persona là test NGOÀI cohort (`in_sample = False`) |
| `mood` | hồi quy, lần đo tới (~1 tuần) | điểm TMD (cao = rối loạn nhiều) | C1 là dự đoán trên dữ liệu giả định |
| `fatigue` | hồi quy, lần đo tới (~1 tuần) | điểm MFSI-SF (cao = mệt hơn) | Chỉ CFT70 |
| `sleep_act_duration` | hồi quy, đêm tới | giờ | Như `sleep_act` |
| `lean_mass_legs`, `bone_mineral`, `lv_mass`, `lv_diastolic_volume` | hồi quy, 1 hàng/người | % so với PRE | % thay đổi PRE → ngày nằm giường 70; hiển thị như ước lượng nhóm (`mean_delta`) kèm khoảng 90% |
| `glucose` | hồi quy, 1 hàng/người | mg/dL | Thay đổi lúc đói PRE → ngày nằm giường 66; chuỗi hằng ngày là giả định |
| `sleep_act` | hồi quy, đêm tới | % hiệu suất ngủ | Pilot 3 người; CFT70 là dự đoán trên dữ liệu giả định (lena bị từ chối: ngoài miền huấn luyện) |
| `hr` | hồi quy, 5 phút tới | bpm | Người MMASH, không phải persona |
| `dose`, `dose_orbit` | hồi quy, 1 giờ tới | uGy/h | Một chuỗi thiết bị → `in_sample` luôn True (chuỗi đã học, giờ dự báo chưa xảy ra) |
| `cpet`, `cpet_physio` | hồi quy, 1 hàng/người | REL VO2PK nguồn | Hiển thị như ước lượng nhóm (mean_delta) |
| `sleep` | phân loại 5 lớp / epoch 30 s | W, N1, N2, N3, REM | Chấm điểm hồi cứu, không phải dự báo |

### 2.7 Trạng thái kết quả (OOF; CI95 theo đơn vị độc lập)

| Task | Triển khai | Trong cohort | Ngoài cohort (6 persona) | Baseline |
|---|---|---|---|---|
| `vitals_sbp` | ridge | MAE 5,72 mmHg (5,39–6,08), 23 người | **6,14 (5,16–7,15)**, bao phủ 0,899 | 7,34 / 8,08 |
| `vitals_dbp` | ridge | 5,10 mmHg (4,80–5,42) | **5,11 (4,48–5,92)**, bao phủ 0,905 | 6,61 / 6,71 |
| `vitals_temp` | ridge | 0,198 °C (0,179–0,218) | **0,162 (0,141–0,180)**, 5 persona, bao phủ 0,933 | 0,246 / 0,231 |
| `vitals_pulse` | ridge | 5,51 bpm (5,15–5,86) | **4,96 (4,38–5,55)**, bao phủ 0,929 | 6,86 / 6,05 |
| `mood` | personal_mean | 5,24 điểm TMD (4,20–6,30), 24 người | — | 5,56 (chênh lệch CI chứa 0) |
| `glucose` | mean_delta | 3,33 mg/dL (2,16–4,69), 23 người; ridge 2,98, hoán vị p = 0,015 | — | 3,30 |
| `sleep_act` | personal_mean | 5,40 điểm % (4,65–5,86), 3 người — pilot | — | 5,63 |
| `vitals_resp` | ridge | 1,18 lần/phút (1,07–1,30) | 0,72 (0,56–0,89), bao phủ 0,97 — **last_value tốt hơn ngoài cohort (0,50)** | 1,28 / 0,50 |
| `vitals_weight` | ridge | 0,37 kg (0,32–0,43) | 0,42 (0,33–0,49), bao phủ 0,85 | **last_value tốt nhất** 0,35 / 0,43 |
| `sleep_act_duration` | personal_mean | 0,40 giờ (0,37–0,43), 3 người — pilot | — | 0,40 |
| `fatigue` | personal_mean | 4,57 điểm (3,77–5,38), 24 người; tốt hơn baseline (ΔMAE −1,04; CI −1,45…−0,68) | — | 5,62 |
| `lean_mass_legs` | mean_delta | 6,1 điểm % (4,3–7,9), 18 người; TB thay đổi −2,7 % | — | persistence 6,0 |
| `bone_mineral` | mean_delta | 0,67 điểm % (0,48–0,86), 18 người; TB +0,1 % | — | persistence 0,63 |
| `lv_mass` | mean_delta | 7,8 điểm % (6,2–9,5), 35 người; TB **−7,6 %** | — | persistence 9,7 |
| `lv_diastolic_volume` | mean_delta | 8,2 điểm % (6,4–10,2), 35 người; TB **−7,8 %** | — | persistence 10,2 |
| `hr` | ridge | 3,92 bpm (3,61–4,24), 22 người; bao phủ 0,900 | — | 4,47 |
| `dose` / `dose_orbit` | lightgbm | 0,769 / 0,637 uGy/h, 9 tháng | — | 2,14 |
| `cpet` / `cpet_physio` | mean_delta | ridge 2,84 (p = 0,005) / mean_delta 3,62 (p = 0,51) | — | 4,13 |
| `sleep` | lightgbm | macro-F1 0,784 (0,760–0,807); kappa 0,777 | — | 0,119 |

`hr`, `dose`, `cpet`, `sleep` tái lập đúng run NASA-cl 11/11 (sai lệch ≤ 1e-15).

## 3. Tạo lại dữ liệu

```powershell
uv run sky-ml load-data
foreach ($t in "hr","dose","dose_orbit","cpet","cpet_physio","sleep","sleep_act","sleep_act_duration",
               "vitals_sbp","vitals_dbp","vitals_temp","vitals_pulse","vitals_resp","vitals_weight",
               "mood","fatigue","glucose","lean_mass_legs","bone_mineral","lv_mass","lv_diastolic_volume") {
  uv run sky-ml build-features $t; uv run sky-ml train $t; uv run sky-ml evaluate $t
}
uv run sky-ml make-synthetic                     # ⚠️ DỮ LIỆU GIẢ ĐỊNH → data/1_synthetic
uv run sky-ml predict mood       --input data/1_synthetic/mood_c1_poms.csv
uv run sky-ml predict sleep_act  --input data/1_synthetic/sleep_cft70_actigraphy.csv
uv run sky-ml predict sleep_act_duration --input data/1_synthetic/sleep_cft70_actigraphy.csv
uv run sky-ml predict hr         --input data/1_source/processed/sample-v2/mmash_minutes.csv.gz
uv run sky-ml predict dose       --input data/1_source/raw/radlab/instruments/Lidal/2022-05-01_2023-01-01.csv
uv run sky-ml predict dose_orbit --input data/1_source/raw/radlab/instruments/Lidal/2022-05-01_2023-01-01.csv
uv run sky-ml refresh-docs                       # viết lại mọi README + mục 4
```

## 4. Danh mục dữ liệu

<!-- CATALOG:START -->

_Tự sinh bởi `sky-ml` từ `CATALOG.csv` — không sửa tay phần này._

| Task | Run mới nhất | Dự đoán mới nhất |
|---|---|---|
| `bone_mineral` | `2026-11-14_211319` | — |
| `cpet` | `2026-11-14_164613` | — |
| `cpet_physio` | `2026-11-14_164654` | — |
| `dose` | `2026-11-14_164606` | [`4_predictions/dose/2026-11-14_164606/2022-05-01_2023-01-01_latest_lightgbm_20261114_164835.csv`](4_predictions/dose/2026-11-14_164606/2022-05-01_2023-01-01_latest_lightgbm_20261114_164835.csv) |
| `dose_orbit` | `2026-11-14_201827` | [`4_predictions/dose_orbit/2026-11-14_201827/2022-05-01_2023-01-01_latest_lightgbm_20261114_201912.csv`](4_predictions/dose_orbit/2026-11-14_201827/2022-05-01_2023-01-01_latest_lightgbm_20261114_201912.csv) |
| `fatigue` | `2026-11-14_211255` | — |
| `glucose` | `2026-11-14_204458` | — |
| `hr` | `2026-11-14_145321` | [`4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.csv`](4_predictions/hr/2026-11-14_145321/mmash_minutes_latest_ridge_20261114_145412.csv) |
| `lean_mass_legs` | `2026-11-14_211306` | — |
| `lv_diastolic_volume` | `2026-11-14_211412` | — |
| `lv_mass` | `2026-11-14_211332` | — |
| `mood` | `2026-11-14_204452` | [`4_predictions/mood/2026-11-14_204452/mood_c1_poms_latest_personal_mean_SYNTHETIC-INPUT_20261114_204535.csv`](4_predictions/mood/2026-11-14_204452/mood_c1_poms_latest_personal_mean_SYNTHETIC-INPUT_20261114_204535.csv) |
| `sleep` | `2026-11-14_164909` | — |
| `sleep_act` | `2026-11-14_201853` | [`4_predictions/sleep_act/2026-11-14_201853/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_204537.csv`](4_predictions/sleep_act/2026-11-14_201853/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_204537.csv) |
| `sleep_act_duration` | `2026-11-14_211249` | [`4_predictions/sleep_act_duration/2026-11-14_211249/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_211431.csv`](4_predictions/sleep_act_duration/2026-11-14_211249/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_211431.csv) |
| `vitals_dbp` | `2026-11-14_204424` | [`4_predictions/vitals_dbp/2026-11-14_204424/external_backtest.csv`](4_predictions/vitals_dbp/2026-11-14_204424/external_backtest.csv) |
| `vitals_pulse` | `2026-11-14_204445` | [`4_predictions/vitals_pulse/2026-11-14_204445/external_backtest.csv`](4_predictions/vitals_pulse/2026-11-14_204445/external_backtest.csv) |
| `vitals_resp` | `2026-11-14_211232` | [`4_predictions/vitals_resp/2026-11-14_211232/external_backtest.csv`](4_predictions/vitals_resp/2026-11-14_211232/external_backtest.csv) |
| `vitals_sbp` | `2026-11-14_204416` | [`4_predictions/vitals_sbp/2026-11-14_204416/external_backtest.csv`](4_predictions/vitals_sbp/2026-11-14_204416/external_backtest.csv) |
| `vitals_temp` | `2026-11-14_204437` | [`4_predictions/vitals_temp/2026-11-14_204437/external_backtest.csv`](4_predictions/vitals_temp/2026-11-14_204437/external_backtest.csv) |
| `vitals_weight` | `2026-11-14_211241` | [`4_predictions/vitals_weight/2026-11-14_211241/external_backtest.csv`](4_predictions/vitals_weight/2026-11-14_211241/external_backtest.csv) |
| ⚠️ dữ liệu giả định | `1_synthetic` | [`1_synthetic/README.md`](1_synthetic/README.md) |

| Nhóm | Task | Run | File | Số hàng | Byte | SHA-256 (12 ký tự đầu) | Lệnh tạo |
|---|---|---|---|---|---|---|---|
| (2) dự đoán | `vitals_weight` | `2026-11-14_211241` | [`4_predictions/vitals_weight/2026-11-14_211241/external_backtest.csv`](4_predictions/vitals_weight/2026-11-14_211241/external_backtest.csv) | 407 | 52046 | `9928ea31fa04` | `sky-ml evaluate vitals_weight` |
| (3) mô hình | `vitals_weight` | `2026-11-14_211241` | [`3_models/vitals_weight/2026-11-14_211241/summary.json`](3_models/vitals_weight/2026-11-14_211241/summary.json) |  | 2684 | `3c9ca3ef92d9` | `sky-ml evaluate vitals_weight` |
| (3) mô hình | `vitals_weight` | `2026-11-14_211241` | [`3_models/vitals_weight/2026-11-14_211241/ridge/final.joblib`](3_models/vitals_weight/2026-11-14_211241/ridge/final.joblib) |  | 977 | `ee798b112f36` | `sky-ml train vitals_weight` |
| (3) mô hình | `vitals_weight` | `2026-11-14_211241` | [`3_models/vitals_weight/2026-11-14_211241/personal_mean/final.joblib`](3_models/vitals_weight/2026-11-14_211241/personal_mean/final.joblib) |  | 74 | `bb15f831b326` | `sky-ml train vitals_weight` |
| (3) mô hình | `vitals_weight` | `2026-11-14_211241` | [`3_models/vitals_weight/2026-11-14_211241/oof.csv.gz`](3_models/vitals_weight/2026-11-14_211241/oof.csv.gz) | 8756 | 83817 | `b62bd008f2d1` | `sky-ml train vitals_weight` |
| (3) mô hình | `vitals_weight` | `2026-11-14_211241` | [`3_models/vitals_weight/2026-11-14_211241/metrics.csv`](3_models/vitals_weight/2026-11-14_211241/metrics.csv) |  | 635 | `26432c988495` | `sky-ml evaluate vitals_weight` |
| (3) mô hình | `vitals_weight` | `2026-11-14_211241` | [`3_models/vitals_weight/2026-11-14_211241/manifest.json`](3_models/vitals_weight/2026-11-14_211241/manifest.json) |  | 2972 | `eb18b49ff10e` | `sky-ml train vitals_weight` |
| (3) mô hình | `vitals_weight` | `2026-11-14_211241` | [`3_models/vitals_weight/2026-11-14_211241/lightgbm/final.joblib`](3_models/vitals_weight/2026-11-14_211241/lightgbm/final.joblib) |  | 44414 | `78e1727b1ede` | `sky-ml train vitals_weight` |
| (3) mô hình | `vitals_weight` | `2026-11-14_211241` | [`3_models/vitals_weight/2026-11-14_211241/last_value/final.joblib`](3_models/vitals_weight/2026-11-14_211241/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train vitals_weight` |
| (3) mô hình | `vitals_weight` | `2026-11-14_211241` | [`3_models/vitals_weight/2026-11-14_211241/folds.json`](3_models/vitals_weight/2026-11-14_211241/folds.json) |  | 1734 | `982d6c38957d` | `sky-ml train vitals_weight` |
| (1) đã xử lý | `vitals_weight` | `2026-11-14_211241` | [`2_features/vitals_weight/2026-11-14_211241/table.csv.gz`](2_features/vitals_weight/2026-11-14_211241/table.csv.gz) | 2189 | 51126 | `6f976d5b6aa1` | `sky-ml build-features vitals_weight` |
| (1) đã xử lý | `vitals_weight` | `2026-11-14_211241` | [`2_features/vitals_weight/2026-11-14_211241/snapshot.json`](2_features/vitals_weight/2026-11-14_211241/snapshot.json) |  | 440 | `2c76ed858a4c` | `sky-ml build-features vitals_weight` |
| (1) đã xử lý | `vitals_weight` | `2026-11-14_211241` | [`2_features/vitals_weight/2026-11-14_211241/features.json`](2_features/vitals_weight/2026-11-14_211241/features.json) |  | 88 | `c8c920d3a47e` | `sky-ml build-features vitals_weight` |
| (1) đã xử lý | `vitals_weight` | `2026-11-14_211241` | [`2_features/vitals_weight/2026-11-14_211241/external.csv.gz`](2_features/vitals_weight/2026-11-14_211241/external.csv.gz) | 407 | 10225 | `0d97d1bec1c8` | `sky-ml build-features vitals_weight` |
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
| (2) dự đoán | `vitals_resp` | `2026-11-14_211232` | [`4_predictions/vitals_resp/2026-11-14_211232/external_backtest.csv`](4_predictions/vitals_resp/2026-11-14_211232/external_backtest.csv) | 411 | 56717 | `43c69d94f3b6` | `sky-ml evaluate vitals_resp` |
| (3) mô hình | `vitals_resp` | `2026-11-14_211232` | [`3_models/vitals_resp/2026-11-14_211232/summary.json`](3_models/vitals_resp/2026-11-14_211232/summary.json) |  | 2694 | `598ed31722c5` | `sky-ml evaluate vitals_resp` |
| (3) mô hình | `vitals_resp` | `2026-11-14_211232` | [`3_models/vitals_resp/2026-11-14_211232/ridge/final.joblib`](3_models/vitals_resp/2026-11-14_211232/ridge/final.joblib) |  | 991 | `002cff052150` | `sky-ml train vitals_resp` |
| (3) mô hình | `vitals_resp` | `2026-11-14_211232` | [`3_models/vitals_resp/2026-11-14_211232/personal_mean/final.joblib`](3_models/vitals_resp/2026-11-14_211232/personal_mean/final.joblib) |  | 74 | `bb15f831b326` | `sky-ml train vitals_resp` |
| (3) mô hình | `vitals_resp` | `2026-11-14_211232` | [`3_models/vitals_resp/2026-11-14_211232/oof.csv.gz`](3_models/vitals_resp/2026-11-14_211232/oof.csv.gz) | 9024 | 64392 | `8d0eaa0f42c7` | `sky-ml train vitals_resp` |
| (3) mô hình | `vitals_resp` | `2026-11-14_211232` | [`3_models/vitals_resp/2026-11-14_211232/metrics.csv`](3_models/vitals_resp/2026-11-14_211232/metrics.csv) |  | 640 | `07e2829970cb` | `sky-ml evaluate vitals_resp` |
| (3) mô hình | `vitals_resp` | `2026-11-14_211232` | [`3_models/vitals_resp/2026-11-14_211232/manifest.json`](3_models/vitals_resp/2026-11-14_211232/manifest.json) |  | 2966 | `eba9818318a1` | `sky-ml train vitals_resp` |
| (3) mô hình | `vitals_resp` | `2026-11-14_211232` | [`3_models/vitals_resp/2026-11-14_211232/lightgbm/final.joblib`](3_models/vitals_resp/2026-11-14_211232/lightgbm/final.joblib) |  | 39048 | `21135f7a10a0` | `sky-ml train vitals_resp` |
| (3) mô hình | `vitals_resp` | `2026-11-14_211232` | [`3_models/vitals_resp/2026-11-14_211232/last_value/final.joblib`](3_models/vitals_resp/2026-11-14_211232/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train vitals_resp` |
| (3) mô hình | `vitals_resp` | `2026-11-14_211232` | [`3_models/vitals_resp/2026-11-14_211232/folds.json`](3_models/vitals_resp/2026-11-14_211232/folds.json) |  | 1739 | `af1c097c285b` | `sky-ml train vitals_resp` |
| (1) đã xử lý | `vitals_resp` | `2026-11-14_211232` | [`2_features/vitals_resp/2026-11-14_211232/table.csv.gz`](2_features/vitals_resp/2026-11-14_211232/table.csv.gz) | 2256 | 15731 | `3afe8f133558` | `sky-ml build-features vitals_resp` |
| (1) đã xử lý | `vitals_resp` | `2026-11-14_211232` | [`2_features/vitals_resp/2026-11-14_211232/snapshot.json`](2_features/vitals_resp/2026-11-14_211232/snapshot.json) |  | 440 | `2c76ed858a4c` | `sky-ml build-features vitals_resp` |
| (1) đã xử lý | `vitals_resp` | `2026-11-14_211232` | [`2_features/vitals_resp/2026-11-14_211232/features.json`](2_features/vitals_resp/2026-11-14_211232/features.json) |  | 88 | `c8c920d3a47e` | `sky-ml build-features vitals_resp` |
| (1) đã xử lý | `vitals_resp` | `2026-11-14_211232` | [`2_features/vitals_resp/2026-11-14_211232/external.csv.gz`](2_features/vitals_resp/2026-11-14_211232/external.csv.gz) | 411 | 2217 | `936de27d47b7` | `sky-ml build-features vitals_resp` |
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
| (2) dự đoán | `sleep_act_duration` | `2026-11-14_211249` | [`4_predictions/sleep_act_duration/2026-11-14_211249/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_211431.json`](4_predictions/sleep_act_duration/2026-11-14_211249/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_211431.json) |  | 291 | `238e1d3c5404` | `sky-ml predict sleep_act_duration --input sleep_cft70_actigraphy.csv --mode latest` |
| (2) dự đoán | `sleep_act_duration` | `2026-11-14_211249` | [`4_predictions/sleep_act_duration/2026-11-14_211249/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_211431.csv`](4_predictions/sleep_act_duration/2026-11-14_211249/sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_211431.csv) | 3 | 426 | `fba317eef154` | `sky-ml predict sleep_act_duration --input sleep_cft70_actigraphy.csv --mode latest` |
| (3) mô hình | `sleep_act_duration` | `2026-11-14_211249` | [`3_models/sleep_act_duration/2026-11-14_211249/summary.json`](3_models/sleep_act_duration/2026-11-14_211249/summary.json) |  | 1590 | `e59d8cf83cc9` | `sky-ml evaluate sleep_act_duration` |
| (3) mô hình | `sleep_act_duration` | `2026-11-14_211249` | [`3_models/sleep_act_duration/2026-11-14_211249/ridge/final.joblib`](3_models/sleep_act_duration/2026-11-14_211249/ridge/final.joblib) |  | 992 | `2b4524cf9701` | `sky-ml train sleep_act_duration` |
| (3) mô hình | `sleep_act_duration` | `2026-11-14_211249` | [`3_models/sleep_act_duration/2026-11-14_211249/personal_mean/final.joblib`](3_models/sleep_act_duration/2026-11-14_211249/personal_mean/final.joblib) |  | 74 | `bb15f831b326` | `sky-ml train sleep_act_duration` |
| (3) mô hình | `sleep_act_duration` | `2026-11-14_211249` | [`3_models/sleep_act_duration/2026-11-14_211249/oof.csv.gz`](3_models/sleep_act_duration/2026-11-14_211249/oof.csv.gz) | 648 | 6817 | `4cb03863efb5` | `sky-ml train sleep_act_duration` |
| (3) mô hình | `sleep_act_duration` | `2026-11-14_211249` | [`3_models/sleep_act_duration/2026-11-14_211249/metrics.csv`](3_models/sleep_act_duration/2026-11-14_211249/metrics.csv) |  | 631 | `d840e1c365ff` | `sky-ml evaluate sleep_act_duration` |
| (3) mô hình | `sleep_act_duration` | `2026-11-14_211249` | [`3_models/sleep_act_duration/2026-11-14_211249/manifest.json`](3_models/sleep_act_duration/2026-11-14_211249/manifest.json) |  | 2985 | `4daf3d8f5b20` | `sky-ml train sleep_act_duration` |
| (3) mô hình | `sleep_act_duration` | `2026-11-14_211249` | [`3_models/sleep_act_duration/2026-11-14_211249/lightgbm/final.joblib`](3_models/sleep_act_duration/2026-11-14_211249/lightgbm/final.joblib) |  | 12642 | `9a3f9ba28a6c` | `sky-ml train sleep_act_duration` |
| (3) mô hình | `sleep_act_duration` | `2026-11-14_211249` | [`3_models/sleep_act_duration/2026-11-14_211249/last_value/final.joblib`](3_models/sleep_act_duration/2026-11-14_211249/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train sleep_act_duration` |
| (3) mô hình | `sleep_act_duration` | `2026-11-14_211249` | [`3_models/sleep_act_duration/2026-11-14_211249/folds.json`](3_models/sleep_act_duration/2026-11-14_211249/folds.json) |  | 233 | `da8937441667` | `sky-ml train sleep_act_duration` |
| (1) đã xử lý | `sleep_act_duration` | `2026-11-14_211249` | [`2_features/sleep_act_duration/2026-11-14_211249/table.csv.gz`](2_features/sleep_act_duration/2026-11-14_211249/table.csv.gz) | 162 | 4278 | `90d94d36787d` | `sky-ml build-features sleep_act_duration` |
| (1) đã xử lý | `sleep_act_duration` | `2026-11-14_211249` | [`2_features/sleep_act_duration/2026-11-14_211249/snapshot.json`](2_features/sleep_act_duration/2026-11-14_211249/snapshot.json) |  | 444 | `b3eba27d31a1` | `sky-ml build-features sleep_act_duration` |
| (1) đã xử lý | `sleep_act_duration` | `2026-11-14_211249` | [`2_features/sleep_act_duration/2026-11-14_211249/features.json`](2_features/sleep_act_duration/2026-11-14_211249/features.json) |  | 88 | `c8c920d3a47e` | `sky-ml build-features sleep_act_duration` |
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
| (3) mô hình | `lv_mass` | `2026-11-14_211332` | [`3_models/lv_mass/2026-11-14_211332/summary.json`](3_models/lv_mass/2026-11-14_211332/summary.json) |  | 1501 | `e73692feaee9` | `sky-ml evaluate lv_mass` |
| (3) mô hình | `lv_mass` | `2026-11-14_211332` | [`3_models/lv_mass/2026-11-14_211332/ridge/final.joblib`](3_models/lv_mass/2026-11-14_211332/ridge/final.joblib) |  | 750 | `5c078dca12ca` | `sky-ml train lv_mass` |
| (3) mô hình | `lv_mass` | `2026-11-14_211332` | [`3_models/lv_mass/2026-11-14_211332/persistence/final.joblib`](3_models/lv_mass/2026-11-14_211332/persistence/final.joblib) |  | 420 | `937d8f5c094f` | `sky-ml train lv_mass` |
| (3) mô hình | `lv_mass` | `2026-11-14_211332` | [`3_models/lv_mass/2026-11-14_211332/oof.csv.gz`](3_models/lv_mass/2026-11-14_211332/oof.csv.gz) | 105 | 2014 | `e0953db16fcd` | `sky-ml train lv_mass` |
| (3) mô hình | `lv_mass` | `2026-11-14_211332` | [`3_models/lv_mass/2026-11-14_211332/metrics.csv`](3_models/lv_mass/2026-11-14_211332/metrics.csv) |  | 469 | `f8feb2c0868e` | `sky-ml evaluate lv_mass` |
| (3) mô hình | `lv_mass` | `2026-11-14_211332` | [`3_models/lv_mass/2026-11-14_211332/mean_delta/final.joblib`](3_models/lv_mass/2026-11-14_211332/mean_delta/final.joblib) |  | 436 | `6c1a5fc7a1c0` | `sky-ml train lv_mass` |
| (3) mô hình | `lv_mass` | `2026-11-14_211332` | [`3_models/lv_mass/2026-11-14_211332/manifest.json`](3_models/lv_mass/2026-11-14_211332/manifest.json) |  | 2365 | `8adaba66ce3c` | `sky-ml train lv_mass` |
| (3) mô hình | `lv_mass` | `2026-11-14_211332` | [`3_models/lv_mass/2026-11-14_211332/folds.json`](3_models/lv_mass/2026-11-14_211332/folds.json) |  | 2627 | `108cc6d30b06` | `sky-ml train lv_mass` |
| (1) đã xử lý | `lv_mass` | `2026-11-14_211332` | [`2_features/lv_mass/2026-11-14_211332/table.csv.gz`](2_features/lv_mass/2026-11-14_211332/table.csv.gz) | 35 | 751 | `7225d9f3cb45` | `sky-ml build-features lv_mass` |
| (1) đã xử lý | `lv_mass` | `2026-11-14_211332` | [`2_features/lv_mass/2026-11-14_211332/snapshot.json`](2_features/lv_mass/2026-11-14_211332/snapshot.json) |  | 443 | `cd9040f0831b` | `sky-ml build-features lv_mass` |
| (1) đã xử lý | `lv_mass` | `2026-11-14_211332` | [`2_features/lv_mass/2026-11-14_211332/features.json`](2_features/lv_mass/2026-11-14_211332/features.json) |  | 16 | `aafb3fb6505e` | `sky-ml build-features lv_mass` |
| (3) mô hình | `lv_diastolic_volume` | `2026-11-14_211412` | [`3_models/lv_diastolic_volume/2026-11-14_211412/summary.json`](3_models/lv_diastolic_volume/2026-11-14_211412/summary.json) |  | 1355 | `f2058744ff23` | `sky-ml evaluate lv_diastolic_volume` |
| (3) mô hình | `lv_diastolic_volume` | `2026-11-14_211412` | [`3_models/lv_diastolic_volume/2026-11-14_211412/ridge/final.joblib`](3_models/lv_diastolic_volume/2026-11-14_211412/ridge/final.joblib) |  | 752 | `5e04a63254f1` | `sky-ml train lv_diastolic_volume` |
| (3) mô hình | `lv_diastolic_volume` | `2026-11-14_211412` | [`3_models/lv_diastolic_volume/2026-11-14_211412/persistence/final.joblib`](3_models/lv_diastolic_volume/2026-11-14_211412/persistence/final.joblib) |  | 420 | `937d8f5c094f` | `sky-ml train lv_diastolic_volume` |
| (3) mô hình | `lv_diastolic_volume` | `2026-11-14_211412` | [`3_models/lv_diastolic_volume/2026-11-14_211412/oof.csv.gz`](3_models/lv_diastolic_volume/2026-11-14_211412/oof.csv.gz) | 105 | 2004 | `95867c32cb81` | `sky-ml train lv_diastolic_volume` |
| (3) mô hình | `lv_diastolic_volume` | `2026-11-14_211412` | [`3_models/lv_diastolic_volume/2026-11-14_211412/metrics.csv`](3_models/lv_diastolic_volume/2026-11-14_211412/metrics.csv) |  | 472 | `c2d650641ebd` | `sky-ml evaluate lv_diastolic_volume` |
| (3) mô hình | `lv_diastolic_volume` | `2026-11-14_211412` | [`3_models/lv_diastolic_volume/2026-11-14_211412/mean_delta/final.joblib`](3_models/lv_diastolic_volume/2026-11-14_211412/mean_delta/final.joblib) |  | 437 | `783d78c2bc60` | `sky-ml train lv_diastolic_volume` |
| (3) mô hình | `lv_diastolic_volume` | `2026-11-14_211412` | [`3_models/lv_diastolic_volume/2026-11-14_211412/manifest.json`](3_models/lv_diastolic_volume/2026-11-14_211412/manifest.json) |  | 2389 | `44123e5b8ae9` | `sky-ml train lv_diastolic_volume` |
| (3) mô hình | `lv_diastolic_volume` | `2026-11-14_211412` | [`3_models/lv_diastolic_volume/2026-11-14_211412/folds.json`](3_models/lv_diastolic_volume/2026-11-14_211412/folds.json) |  | 2627 | `108cc6d30b06` | `sky-ml train lv_diastolic_volume` |
| (1) đã xử lý | `lv_diastolic_volume` | `2026-11-14_211412` | [`2_features/lv_diastolic_volume/2026-11-14_211412/table.csv.gz`](2_features/lv_diastolic_volume/2026-11-14_211412/table.csv.gz) | 35 | 747 | `2ba88965cef9` | `sky-ml build-features lv_diastolic_volume` |
| (1) đã xử lý | `lv_diastolic_volume` | `2026-11-14_211412` | [`2_features/lv_diastolic_volume/2026-11-14_211412/snapshot.json`](2_features/lv_diastolic_volume/2026-11-14_211412/snapshot.json) |  | 443 | `cd9040f0831b` | `sky-ml build-features lv_diastolic_volume` |
| (1) đã xử lý | `lv_diastolic_volume` | `2026-11-14_211412` | [`2_features/lv_diastolic_volume/2026-11-14_211412/features.json`](2_features/lv_diastolic_volume/2026-11-14_211412/features.json) |  | 16 | `aafb3fb6505e` | `sky-ml build-features lv_diastolic_volume` |
| (3) mô hình | `lean_mass_legs` | `2026-11-14_211306` | [`3_models/lean_mass_legs/2026-11-14_211306/summary.json`](3_models/lean_mass_legs/2026-11-14_211306/summary.json) |  | 1524 | `9c6fedee8c17` | `sky-ml evaluate lean_mass_legs` |
| (3) mô hình | `lean_mass_legs` | `2026-11-14_211306` | [`3_models/lean_mass_legs/2026-11-14_211306/ridge/final.joblib`](3_models/lean_mass_legs/2026-11-14_211306/ridge/final.joblib) |  | 751 | `63f84fd67173` | `sky-ml train lean_mass_legs` |
| (3) mô hình | `lean_mass_legs` | `2026-11-14_211306` | [`3_models/lean_mass_legs/2026-11-14_211306/persistence/final.joblib`](3_models/lean_mass_legs/2026-11-14_211306/persistence/final.joblib) |  | 420 | `937d8f5c094f` | `sky-ml train lean_mass_legs` |
| (3) mô hình | `lean_mass_legs` | `2026-11-14_211306` | [`3_models/lean_mass_legs/2026-11-14_211306/oof.csv.gz`](3_models/lean_mass_legs/2026-11-14_211306/oof.csv.gz) | 54 | 1080 | `307542504569` | `sky-ml train lean_mass_legs` |
| (3) mô hình | `lean_mass_legs` | `2026-11-14_211306` | [`3_models/lean_mass_legs/2026-11-14_211306/metrics.csv`](3_models/lean_mass_legs/2026-11-14_211306/metrics.csv) |  | 469 | `6b094dfa3855` | `sky-ml evaluate lean_mass_legs` |
| (3) mô hình | `lean_mass_legs` | `2026-11-14_211306` | [`3_models/lean_mass_legs/2026-11-14_211306/mean_delta/final.joblib`](3_models/lean_mass_legs/2026-11-14_211306/mean_delta/final.joblib) |  | 437 | `790147aa2a9d` | `sky-ml train lean_mass_legs` |
| (3) mô hình | `lean_mass_legs` | `2026-11-14_211306` | [`3_models/lean_mass_legs/2026-11-14_211306/manifest.json`](3_models/lean_mass_legs/2026-11-14_211306/manifest.json) |  | 2383 | `68f329780112` | `sky-ml train lean_mass_legs` |
| (3) mô hình | `lean_mass_legs` | `2026-11-14_211306` | [`3_models/lean_mass_legs/2026-11-14_211306/folds.json`](3_models/lean_mass_legs/2026-11-14_211306/folds.json) |  | 1352 | `b1ffc64fd51c` | `sky-ml train lean_mass_legs` |
| (1) đã xử lý | `lean_mass_legs` | `2026-11-14_211306` | [`2_features/lean_mass_legs/2026-11-14_211306/table.csv.gz`](2_features/lean_mass_legs/2026-11-14_211306/table.csv.gz) | 18 | 422 | `e652b7e2ecca` | `sky-ml build-features lean_mass_legs` |
| (1) đã xử lý | `lean_mass_legs` | `2026-11-14_211306` | [`2_features/lean_mass_legs/2026-11-14_211306/snapshot.json`](2_features/lean_mass_legs/2026-11-14_211306/snapshot.json) |  | 447 | `9f2f000cba4c` | `sky-ml build-features lean_mass_legs` |
| (1) đã xử lý | `lean_mass_legs` | `2026-11-14_211306` | [`2_features/lean_mass_legs/2026-11-14_211306/features.json`](2_features/lean_mass_legs/2026-11-14_211306/features.json) |  | 16 | `aafb3fb6505e` | `sky-ml build-features lean_mass_legs` |
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
| (3) mô hình | `fatigue` | `2026-11-14_211255` | [`3_models/fatigue/2026-11-14_211255/summary.json`](3_models/fatigue/2026-11-14_211255/summary.json) |  | 1420 | `2b315014889c` | `sky-ml evaluate fatigue` |
| (3) mô hình | `fatigue` | `2026-11-14_211255` | [`3_models/fatigue/2026-11-14_211255/ridge/final.joblib`](3_models/fatigue/2026-11-14_211255/ridge/final.joblib) |  | 945 | `48fb10dd2e6b` | `sky-ml train fatigue` |
| (3) mô hình | `fatigue` | `2026-11-14_211255` | [`3_models/fatigue/2026-11-14_211255/personal_mean/final.joblib`](3_models/fatigue/2026-11-14_211255/personal_mean/final.joblib) |  | 74 | `bb15f831b326` | `sky-ml train fatigue` |
| (3) mô hình | `fatigue` | `2026-11-14_211255` | [`3_models/fatigue/2026-11-14_211255/oof.csv.gz`](3_models/fatigue/2026-11-14_211255/oof.csv.gz) | 1144 | 11606 | `13be2d48b705` | `sky-ml train fatigue` |
| (3) mô hình | `fatigue` | `2026-11-14_211255` | [`3_models/fatigue/2026-11-14_211255/metrics.csv`](3_models/fatigue/2026-11-14_211255/metrics.csv) |  | 618 | `2c294053081e` | `sky-ml evaluate fatigue` |
| (3) mô hình | `fatigue` | `2026-11-14_211255` | [`3_models/fatigue/2026-11-14_211255/manifest.json`](3_models/fatigue/2026-11-14_211255/manifest.json) |  | 2944 | `271320c8613f` | `sky-ml train fatigue` |
| (3) mô hình | `fatigue` | `2026-11-14_211255` | [`3_models/fatigue/2026-11-14_211255/lightgbm/final.joblib`](3_models/fatigue/2026-11-14_211255/lightgbm/final.joblib) |  | 13568 | `1e2345651023` | `sky-ml train fatigue` |
| (3) mô hình | `fatigue` | `2026-11-14_211255` | [`3_models/fatigue/2026-11-14_211255/last_value/final.joblib`](3_models/fatigue/2026-11-14_211255/last_value/final.joblib) |  | 72 | `1bedcf00814c` | `sky-ml train fatigue` |
| (3) mô hình | `fatigue` | `2026-11-14_211255` | [`3_models/fatigue/2026-11-14_211255/folds.json`](3_models/fatigue/2026-11-14_211255/folds.json) |  | 1848 | `b41f97f9642b` | `sky-ml train fatigue` |
| (1) đã xử lý | `fatigue` | `2026-11-14_211255` | [`2_features/fatigue/2026-11-14_211255/table.csv.gz`](2_features/fatigue/2026-11-14_211255/table.csv.gz) | 286 | 3857 | `10a4f4fa113a` | `sky-ml build-features fatigue` |
| (1) đã xử lý | `fatigue` | `2026-11-14_211255` | [`2_features/fatigue/2026-11-14_211255/snapshot.json`](2_features/fatigue/2026-11-14_211255/snapshot.json) |  | 447 | `9f2f000cba4c` | `sky-ml build-features fatigue` |
| (1) đã xử lý | `fatigue` | `2026-11-14_211255` | [`2_features/fatigue/2026-11-14_211255/features.json`](2_features/fatigue/2026-11-14_211255/features.json) |  | 71 | `da8d2b3f7a97` | `sky-ml build-features fatigue` |
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
| (3) mô hình | `bone_mineral` | `2026-11-14_211319` | [`3_models/bone_mineral/2026-11-14_211319/summary.json`](3_models/bone_mineral/2026-11-14_211319/summary.json) |  | 1508 | `c13fe5286c50` | `sky-ml evaluate bone_mineral` |
| (3) mô hình | `bone_mineral` | `2026-11-14_211319` | [`3_models/bone_mineral/2026-11-14_211319/ridge/final.joblib`](3_models/bone_mineral/2026-11-14_211319/ridge/final.joblib) |  | 756 | `66873886a18b` | `sky-ml train bone_mineral` |
| (3) mô hình | `bone_mineral` | `2026-11-14_211319` | [`3_models/bone_mineral/2026-11-14_211319/persistence/final.joblib`](3_models/bone_mineral/2026-11-14_211319/persistence/final.joblib) |  | 420 | `937d8f5c094f` | `sky-ml train bone_mineral` |
| (3) mô hình | `bone_mineral` | `2026-11-14_211319` | [`3_models/bone_mineral/2026-11-14_211319/oof.csv.gz`](3_models/bone_mineral/2026-11-14_211319/oof.csv.gz) | 54 | 1065 | `13bab0370f55` | `sky-ml train bone_mineral` |
| (3) mô hình | `bone_mineral` | `2026-11-14_211319` | [`3_models/bone_mineral/2026-11-14_211319/metrics.csv`](3_models/bone_mineral/2026-11-14_211319/metrics.csv) |  | 485 | `b2edc7af3919` | `sky-ml evaluate bone_mineral` |
| (3) mô hình | `bone_mineral` | `2026-11-14_211319` | [`3_models/bone_mineral/2026-11-14_211319/mean_delta/final.joblib`](3_models/bone_mineral/2026-11-14_211319/mean_delta/final.joblib) |  | 438 | `a290fe94f758` | `sky-ml train bone_mineral` |
| (3) mô hình | `bone_mineral` | `2026-11-14_211319` | [`3_models/bone_mineral/2026-11-14_211319/manifest.json`](3_models/bone_mineral/2026-11-14_211319/manifest.json) |  | 2379 | `cff36a020d7d` | `sky-ml train bone_mineral` |
| (3) mô hình | `bone_mineral` | `2026-11-14_211319` | [`3_models/bone_mineral/2026-11-14_211319/folds.json`](3_models/bone_mineral/2026-11-14_211319/folds.json) |  | 1352 | `b1ffc64fd51c` | `sky-ml train bone_mineral` |
| (1) đã xử lý | `bone_mineral` | `2026-11-14_211319` | [`2_features/bone_mineral/2026-11-14_211319/table.csv.gz`](2_features/bone_mineral/2026-11-14_211319/table.csv.gz) | 18 | 413 | `d28ed3f9a04d` | `sky-ml build-features bone_mineral` |
| (1) đã xử lý | `bone_mineral` | `2026-11-14_211319` | [`2_features/bone_mineral/2026-11-14_211319/snapshot.json`](2_features/bone_mineral/2026-11-14_211319/snapshot.json) |  | 447 | `9f2f000cba4c` | `sky-ml build-features bone_mineral` |
| (1) đã xử lý | `bone_mineral` | `2026-11-14_211319` | [`2_features/bone_mineral/2026-11-14_211319/features.json`](2_features/bone_mineral/2026-11-14_211319/features.json) |  | 16 | `aafb3fb6505e` | `sky-ml build-features bone_mineral` |

<!-- CATALOG:END -->
