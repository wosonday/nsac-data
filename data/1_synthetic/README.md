# data/1_synthetic — DỮ LIỆU GIẢ ĐỊNH (synthetic)

> ⚠️ **DỮ LIỆU GIẢ ĐỊNH — KHÔNG PHẢI SỐ ĐO THẬT.** Sinh bằng `sky-ml make-synthetic` để lấp chỗ persona không có dữ liệu thật (BTC cho phép, phải ghi rõ). Không dùng để train hay đánh giá mô hình. Web PHẢI gắn nhãn "Dữ liệu giả định" khi hiển thị.

- Bộ sinh: `sky-ml-synthetic-1.0` (src/sky_ml/_synthetic.py) · seed 17 · ánh xạ persona: `configs/crew_map.yaml`
- Mô hình sinh chung: `y_it = μ(t) + b_i + e_it`; `b_i ~ N(0, σ_b)`; `e_it` AR(1) với hệ số ρ, SD σ_e. Mọi tham số ước lượng từ dữ liệu THẬT trong `data/1_source` và ghi ở `<tên>.params.json`.
- Cột `is_synthetic`: True = giá trị sinh ra; False = giá trị thật giữ làm điểm neo.

## `mood_c1_poms.csv`

**Điểm POMS-TMD hằng tuần cho 3 persona Campaign 1 (không có POMS thật)**

- Nguồn tham số: NNX10AP86G_CFT70_POMS_TMD.csv (24 người CFT70)
- Persona: noor-abbasi, tomas-ortega, yuki-tanaka · 45 hàng · giả định 45 / thật (neo) 0
- Cột: `persona`, `subject_id`, `study_day`, `tmd`, `is_synthetic`, `generator`

Kiểm tra: thống kê giả định so với dữ liệu thật dùng để sinh

| dataset | variable | people | rows | mean | sd | min | max | lag1_autocorr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| THẬT – POMS CFT70 | tmd | 24 | 367 | -11.079 | 12.087 | -32.0 | 27.0 | 0.742 |
| GIẢ ĐỊNH – C1 | tmd | 3 | 45 | -16.089 | 10.58 | -32.0 | 6.0 | 0.521 |

## `glucose_daily_personas.csv`

**Đường huyết lúc đói hằng ngày cho 6 persona (CFT70 neo vào OGTT thật)**

- Nguồn tham số: NNX10AP86G_CFT70_OGTT.csv, phút 0 (24 người)
- Persona: ayla-reyes, dae-jung-park, lena-fischer, noor-abbasi, tomas-ortega, yuki-tanaka · 498 hàng · giả định 488 / thật (neo) 10
- Cột: `persona`, `subject_id`, `study_day`, `glucose_fasting`, `is_synthetic`, `generator`

Kiểm tra: thống kê giả định so với dữ liệu thật dùng để sinh

| dataset | variable | people | rows | mean | sd | min | max | lag1_autocorr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| THẬT – OGTT phút 0 | glucose_fasting | 24 | 120 | 89.798 | 6.35 | 70.8 | 104.5 | 0.624 |
| GIẢ ĐỊNH – hằng ngày | glucose_fasting | 6 | 488 | 90.384 | 6.371 | 73.7 | 104.5 | 0.411 |

## `sleep_cft70_actigraphy.csv`

**Hiệu suất/thời lượng ngủ theo đêm cho 3 persona CFT70 (không có actigraphy thật)**

- Nguồn tham số: BRSMACT_Campagin_1_Actigraphy.csv (3 người C1 — rất ít)
- Persona: ayla-reyes, dae-jung-park, lena-fischer · 237 hàng · giả định 237 / thật (neo) 0
- Cột: `persona`, `subject_id`, `study_day`, `date`, `efficiency`, `duration`, `is_synthetic`, `generator`

Kiểm tra: thống kê giả định so với dữ liệu thật dùng để sinh

| dataset | variable | people | rows | mean | sd | min | max | lag1_autocorr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| THẬT – actigraphy C1 (efficiency) | efficiency | 3 | 190 | 81.959 | 8.269 | 52.5 | 96.7 | 0.59 |
| THẬT – actigraphy C1 (duration) | duration | 3 | 190 | 7.226 | 0.518 | 5.033 | 7.967 | 0.468 |
| GIẢ ĐỊNH – CFT70 (efficiency) | efficiency | 3 | 237 | 84.093 | 9.21 | 63.7 | 96.7 | 0.702 |
| GIẢ ĐỊNH – CFT70 (duration) | duration | 3 | 237 | 7.263 | 0.46 | 6.02 | 7.97 | 0.432 |

## Giới hạn

1. Giá trị sinh ra phản ánh phân bố QUẦN THỂ analog, không phản ánh người analog cụ thể (trừ điểm neo thật).
2. Không mô phỏng sự kiện bất thường (bệnh, thuốc, sự cố) — chuỗi "bình thường" theo thống kê.
3. `sleep_cft70_actigraphy` học từ CHỈ 3 người Campaign 1 → độ tin cậy thấp nhất.
4. `mood_c1_poms` dùng lịch đo và xu hướng của CFT70 (70 ngày) cắt ở 60 ngày.
5. Cột `date` (nếu có) là lịch nhân tạo 2000-01-01 + study_day.
