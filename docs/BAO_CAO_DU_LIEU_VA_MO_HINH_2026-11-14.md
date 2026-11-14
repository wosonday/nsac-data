# Báo cáo dữ liệu và mô hình sky-ml × nsac

> Cập nhật 14/11/2026, 20:50 · Thư mục: `D:\Project\nasa-hackathon` · Bảng chi tiết: [`docs/Tong_hop_du_lieu_mo_hinh.xlsx`](Tong_hop_du_lieu_mo_hinh.xlsx)
>
> ⚠️ Báo cáo có dùng **DỮ LIỆU GIẢ ĐỊNH** (mục 5) cho phần persona không có dữ liệu thật. BTC cho phép việc này; mọi chỗ dùng đều được ghi rõ.

## 1. Tóm tắt

- **13 task đã chạy**, mỗi task có đủ (1) đặc trưng, (3) mô hình, (2) dự đoán hoặc OOF:
  - nhóm cũ: `hr`, `dose`, `dose_orbit`, `cpet`, `cpet_physio`, `sleep`, `sleep_act`;
  - nhóm mới: `vitals_sbp`, `vitals_dbp`, `vitals_temp`, `vitals_pulse`, `mood`, `glucose`.
- **Đủ 6 chỉ số web × 6 persona.** Phần lớn là dữ liệu thật; ba khoảng trống được lấp bằng dữ liệu giả định:
  - tâm trạng của 3 persona Campaign 1;
  - giấc ngủ theo đêm của 3 persona CFT70;
  - đường huyết hằng ngày của cả 6 persona.
- **Bằng chứng mạnh nhất mới có: các chỉ số sinh tồn (`vitals_*`).** Mô hình train trên 23 người Campaign 3 được kiểm tra trên **đúng 6 persona chưa từng thấy**:
  - sai số tương đương trong cohort;
  - khoảng 90% bao phủ 0,90–0,93.
- **Tái lập:** 5 task gốc vẫn trùng run NASA-cl ngày 11/11.

## 2. Dữ liệu thật: nguồn gốc, lý do, mục tiêu

| Task | Chỉ số web | Dữ liệu · nguồn | Lý do sử dụng | Mục tiêu dự báo |
|---|---|---|---|---|
| `hr` | Nhịp tim | MMASH · PhysioNet (ODbL) | Chuỗi nhịp tim theo phút đã QA | Nhịp tim 5 phút tới |
| `vitals_pulse` | Nhịp tim | UTMB CRF · NASA NLSP | Nhịp tim buổi sáng của **chính 6 persona** | Nhịp tim sáng ngày tới |
| `vitals_sbp`, `vitals_dbp` | Huyết áp | UTMB CRF · NASA NLSP | Nguồn duy nhất có huyết áp hằng ngày của các persona | Huyết áp tâm thu / tâm trương ngày tới |
| `vitals_temp` | Nhiệt độ | UTMB CRF · NASA NLSP | Nhiệt độ buổi sáng hằng ngày | Nhiệt độ ngày tới |
| `mood` | Tâm trạng | UTMB CFT70 POMS (NNX10AP86G) · NASA NLSP | Thang POMS chuẩn hóa, đo hằng tuần | Điểm rối loạn tâm trạng (TMD) lần đo tới |
| `sleep` | Giấc ngủ | Sleep-EDF · PhysioNet (ODC-By) | EEG/EOG có nhãn chuyên gia | Giai đoạn ngủ từng epoch 30 s |
| `sleep_act` | Giấc ngủ | UTMB Campaign 1 BRSMAct · NASA NLSP | Đúng 3 persona C1 | Hiệu suất ngủ đêm tới |
| `glucose` | Đường huyết | UTMB CFT70 OGTT (NNX10AP86G) · NASA NLSP | Đường huyết đo thật trong nằm giường | Thay đổi đường huyết lúc đói từ trước nằm giường đến ngày 66 |
| `dose`, `dose_orbit` | Bức xạ (ngoài 6 chỉ số) | RadLab Lidal · NASA OSDR | Liều đo thật trên ISS | Liều 1 giờ tới |
| `cpet`, `cpet_physio` | Thể lực (ngoài 6 chỉ số) | UTMB CFT70 MR080G · NASA NLSP | Analog của mất thể lực khi bay | Thay đổi VO2peak sau 70 ngày |

**Nguyên tắc chung khi xử lý:**
- kiểm hash SHA-256 + MD5 cho từng file trong ZIP;
- ngưỡng chỉ dùng để loại số ghi hỏng (ngưỡng kỹ thuật), không phải ngưỡng lâm sàng;
- không nội suy dữ liệu thiếu;
- không gộp người giữa các cohort.

## 3. Kết quả

Kết quả là dự đoán ngoài tập huấn luyện (OOF), CI95 tính bằng bootstrap theo đơn vị độc lập (người hoặc tháng). "Ngoài cohort" là đánh giá trên 6 persona khi mô hình chưa từng thấy họ.

| Task | Mô hình triển khai | Trong cohort | **Ngoài cohort (6 persona)** | Baseline |
|---|---|---|---|---|
| `vitals_sbp` | ridge | MAE 5,72 mmHg (5,39–6,08), 23 người | **6,14 (5,16–7,15)**, bao phủ 0,899 | last_value 7,34 / 8,08 |
| `vitals_dbp` | ridge | 5,10 mmHg (4,80–5,42) | **5,11 (4,48–5,92)**, bao phủ 0,905 | 6,61 / 6,71 |
| `vitals_temp` | ridge | 0,198 °C (0,179–0,218) | **0,162 (0,141–0,180)**, 5 persona, bao phủ 0,933 | 0,246 / 0,231 |
| `vitals_pulse` | ridge | 5,51 bpm (5,15–5,86) | **4,96 (4,38–5,55)**, bao phủ 0,929 | 6,86 / 6,05 |
| `mood` | personal_mean | 5,24 điểm TMD (4,20–6,30), 24 người | — | 5,56 (chênh lệch có CI chứa 0) |
| `glucose` | mean_delta | 3,33 mg/dL (2,16–4,69), 23 người; ridge 2,98, hoán vị p = 0,015 | — | 3,30 |
| `hr` | ridge | 3,92 bpm (3,61–4,24), 22 người | — | 4,47 |
| `dose` / `dose_orbit` | lightgbm | 0,769 / **0,637** uGy/h (9 tháng) | — | 2,14 |
| `cpet` / `cpet_physio` | mean_delta | ridge 2,84 (p = 0,005) / 3,62 (p = 0,51) | — | 4,13 |
| `sleep` | lightgbm | macro-F1 0,784 (0,760–0,807) | — | 0,119 |
| `sleep_act` | personal_mean | 5,40 điểm % (3 người, pilot) | — | 5,63 |

### Cách hiểu

1. **Sinh tồn hằng ngày:** dự báo ngày tới tốt hơn "giữ nguyên hôm nay" khoảng 20%. Kết quả giữ được khi chuyển sang người mới, nên đây là bằng chứng trung thực nhất trên persona.
2. **Tâm trạng:** trung bình cá nhân là đủ. Không mô hình nào chắc chắn tốt hơn baseline vì CI của chênh lệch chứa 0.
3. **Đường huyết lúc đói:** gần như không đổi khi nằm giường (trung bình +0,8 mg/dL). Ridge có tín hiệu yếu (p = 0,015) nhưng CI của chênh lệch chứa 0, nên vẫn giữ `mean_delta` như đã chốt trước khi chạy.
4. **Một số task không có mô hình vượt baseline rõ ràng** (`mood`, `glucose`, `sleep_act`, `cpet_physio`). Web nên hiển thị ước lượng kèm khoảng 90%, không nên trình bày như dự báo cá nhân hóa chính xác.

## 4. Persona × chỉ số

| Chỉ số | ayla · dae-jung · lena (CFT70) | tomas · yuki · noor (Campaign 1) |
|---|---|---|
| Nhịp tim | Thật | Thật |
| Huyết áp | Thật | Thật |
| Nhiệt độ | Thật | Thật, có đo 112/252 ngày; ngày không đo để trống |
| Tâm trạng | Thật | ⚠️ **Giả định** |
| Hoạt động và giấc ngủ | ⚠️ **Giả định** | Thật |
| Đường huyết | Thật ở 5–6 mốc OGTT + ⚠️ **giả định** giữa các mốc | ⚠️ **Giả định** |

Nguồn của bảng này: `configs/crew_map.yaml`. Mỗi persona chỉ lấy dữ liệu của đúng một người analog.

## 5. ⚠️ Dữ liệu giả định (`data/1_synthetic/`)

### 5.1 Quy tắc

1. **Tham số lấy từ dữ liệu thật:** mọi tham số được ước lượng từ dữ liệu thật trong `data/1_source` và ghi vào `<tên>.params.json`. Không có số nào lấy từ trí nhớ.
2. **Mô hình sinh:** `y_it = μ(t) + b_i + e_it`, trong đó:
   - `μ(t)`: trung bình quần thể theo ngày nghiên cứu;
   - `b_i ~ N(0, σ_b)`: chênh lệch riêng của từng người, với σ_b là biến thiên giữa người;
   - `e_it`: dao động ngày qua ngày trong người, theo AR(1) với hệ số tự tương quan ρ và độ lệch σ_e.

   Cách tách "giữa người / trong người" này theo khái niệm biến thiên sinh học được EFLM chuẩn hóa: biến thiên trong người (CVI) là dao động quanh điểm cân bằng của một người ở trạng thái ổn định; biến thiên giữa người (CVG) là khác biệt giữa điểm cân bằng của các người với nhau.
3. **Không train, không đánh giá:** dữ liệu giả định chỉ dùng làm đầu vào hiển thị hoặc dự đoán minh họa.
   - Dự đoán từ dữ liệu giả định có cột `input_synthetic = True` và tên file chứa `_SYNTHETIC-INPUT`.
   - Có test đảm bảo không task nào lấy `1_synthetic` làm đầu vào train.
4. **Tái lập được:** seed 17 cố định, `SYNTHETIC_MANIFEST.csv` lưu SHA-256, `*.validation.csv` so sánh với dữ liệu thật.

### 5.2 Ba bộ dữ liệu

| File | Persona | Tham số (từ dữ liệu thật) | Kiểm tra: thật → giả định |
|---|---|---|---|
| `mood_c1_poms.csv` (45 hàng) | 3 persona C1 | POMS CFT70, 24 người: σ_b 9,56 · σ_e 7,22 · ρ 0,31 | TB −11,1 → −16,1; SD 12,1 → 10,6 |
| `sleep_cft70_actigraphy.csv` (237 hàng) | 3 persona CFT70 | Actigraphy C1, **chỉ 3 người**: hiệu suất σ_e 6,3 · ρ 0,30 | Hiệu suất 82,0 ± 8,3 → 84,1 ± 9,2; thời lượng 7,23 → 7,26 giờ |
| `glucose_daily_personas.csv` (498 hàng, 10 hàng thật) | 6 persona | OGTT lúc đói: σ trong người 4,81 · σ giữa người 6,72 · TB 89,6 mg/dL | TB 89,8 → 90,4; SD 6,35 → 6,37 |

### 5.3 Giới hạn của dữ liệu giả định

- Chuỗi giả định phản ánh phân bố của nhóm người analog, không phản ánh người cụ thể (trừ các điểm neo thật).
- Không mô phỏng sự kiện bất thường như bệnh hay dùng thuốc.
- Bộ giấc ngủ cho CFT70 học từ chỉ 3 người nên độ tin cậy thấp nhất.
- Khi dự đoán trên bộ này, mô hình `sleep_act` đã từ chối dự đoán cho lena vì giá trị nằm ngoài miền huấn luyện; cơ chế an toàn hoạt động đúng.

**Web bắt buộc:** gắn nhãn "Dữ liệu giả định" và tách biệt về hình thức (màu hoặc kiểu nét) với dữ liệu thật.

## 6. Dữ liệu cho web

| Task | File | Ghi chú |
|---|---|---|
| `vitals_*` | `4_predictions/vitals_*/<run>/external_backtest.csv` | 6 persona, `in_sample = False`, có `y_true` |
| `mood` | CFT70: `3_models/mood/<run>/oof.csv.gz`; C1: `4_predictions/mood/…SYNTHETIC-INPUT…csv` | C1 là giả định |
| `glucose` | `3_models/glucose/<run>/oof.csv.gz` + `1_synthetic/glucose_daily_personas.csv` | Hiển thị điểm thật khác với phần giả định |
| `sleep_act` | C1: OOF; CFT70: `4_predictions/sleep_act/…SYNTHETIC-INPUT…csv` | — |
| `hr`, `dose`, `dose_orbit` | `4_predictions/<task>/<run>/*_latest_*.csv` | — |
| `cpet`, `cpet_physio`, `sleep` | `3_models/<task>/<run>/oof.csv.gz` | — |

## 7. Giới hạn chung

1. Không có dữ liệu phi hành gia thật trong mô hình. Nguồn là analog nằm giường (UTMB), người mặt đất (MMASH, Sleep-EDF) hoặc dữ liệu thiết bị (RadLab).
2. Ngày gốc của các nghiên cứu (2004–2009) không được hiển thị lên web; chỉ dùng ngày tương đối.
3. Các ngưỡng dùng để loại số ghi hỏng là ngưỡng kỹ thuật, không phải ngưỡng lâm sàng hay ngưỡng cảnh báo.
4. Timestamp RadLab chưa xác minh múi giờ; cấu hình `dose_orbit` cần kiểm lại trên năm khác.

## 8. Đề xuất bổ sung

| Ưu tiên | Việc | Vì sao |
|---|---|---|
| Cao | `export-nsac` dùng `crew_map.yaml` | Đã đủ 6 × 6; web cần một file JSON duy nhất có cờ real/synthetic cho từng điểm |
| Cao | Nhãn "Dữ liệu giả định" trên web | Yêu cầu của BTC |
| Trung bình | Thay dữ liệu giả định bằng dữ liệu thật khi tìm được | POMS Campaign 1, actigraphy CFT70 trên NLSP |
| Trung bình | Thẻ đường huyết mô tả từ OSD-575 (Inspiration4) | Bằng chứng từ chuyến bay thật; có cờ nghi vấn ở mốc R+45 |
| Trung bình | Kiểm lại `dose_orbit` trên Lidal 2023; xác minh múi giờ RadLab | Tránh kết quả lạc quan |
| Thấp | Thêm MFSI-SF (mệt mỏi), các thang con của POMS; iRATS cho `cpet` | Dữ liệu đã có sẵn trong NASA-cl |

## 9. Tái lập

```powershell
uv run sky-ml load-data
foreach ($t in "hr","dose","dose_orbit","cpet","cpet_physio","sleep","sleep_act",
               "vitals_sbp","vitals_dbp","vitals_temp","vitals_pulse","mood","glucose") {
  uv run sky-ml build-features $t; uv run sky-ml train $t; uv run sky-ml evaluate $t
}
uv run sky-ml make-synthetic                     # DỮ LIỆU GIẢ ĐỊNH → data/1_synthetic
uv run sky-ml predict mood      --input data/1_synthetic/mood_c1_poms.csv
uv run sky-ml predict sleep_act --input data/1_synthetic/sleep_cft70_actigraphy.csv
```

## Nguồn

- NASA Life Sciences Portal — UTMB Bed Rest: CRF Daily Vitals, NNX10AP86G (POMS, OGTT), MR080G, BRSMAct — https://nlsp.nasa.gov/explore
- McNair DM, Lorr M, Droppleman LF. *Manual for the Profile of Mood States*. EdITS, 1971
- Fraser CG, Harris EK. Generation and application of data on biological variation in clinical chemistry. *Crit Rev Clin Lab Sci* 1989;27(5):409–437
- Coşkun A, Sandberg S, et al. Personalized reference intervals in laboratory medicine: a new model based on within-subject biological variation. *Clin Chem* 2021;67(2):374
- Rossi A, et al. MMASH 1.0.0. PhysioNet, 2020. doi:10.13026/cerq-fc86
- Kemp B, et al. *IEEE Trans Biomed Eng* 2000;47(9):1185–1194; Sleep-EDF Expanded doi:10.13026/C2X676
- NASA OSDR RadLab data API — https://visualization.osdr.nasa.gov/radlab/gui/data-api/
- Pollard T, et al. PhysioNet as a global platform for biomedical research. *Nature Health* 2026. doi:10.1038/s44360-026-00096-z
