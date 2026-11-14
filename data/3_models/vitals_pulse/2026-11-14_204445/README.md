# (3) Mô hình đã huấn luyện — `vitals_pulse` / run `2026-11-14_204445`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate vitals_pulse`
- **README cập nhật (UTC):** 2026-11-14T14:30:22+00:00
- **Cohort:** UTMB bed rest CRF Daily Vitals — TRAIN: Campaign 3 (23 người); NGOÀI cohort: CFT70 (5160, 8072, 8936) + Campaign 1 (C1G0001–3) = 6 persona
- **Nguồn:** data/1_source/raw/nlsp/CRF.zip › */Daily_Vitals/*.csv, CFT70_VITALS/*.csv (kiểm SHA-256 + MD5)

## File trong thư mục

| File | Nội dung |
|---|---|
| `oof.csv.gz` | Dự đoán ngoài tập huấn luyện (OOF) của mọi mô hình — nguồn của mọi điểm đánh giá |
| `folds.json` | Danh sách fold và số mẫu train/test |
| `manifest.json` | SHA-256 + phiên bản + tham số |
| `<model>/final.joblib` | Mô hình fit trên toàn bộ người → chỉ dùng cho NGƯỜI MỚI |
| `metrics.csv` | Metric theo đơn vị độc lập, CI95, so baseline |
| `summary.json` | Tóm tắt: metric, độ bao phủ khoảng 90%, kiểm định hoán vị, kết quả ngoài cohort |
| `external_metrics.csv` | MAE + CI95 trên người NGOÀI cohort (chưa từng thấy) cho mọi mô hình |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số fold | 23 |
| Mô hình | last_value, personal_mean, ridge, lightgbm |
| Số file mô hình | 4 |
| mae – ridge | 5.5139 (CI95 5.152–5.864); so baseline -1.346 |
| mae – personal_mean | 5.5354 (CI95 5.144–5.920); so baseline -1.325 |
| mae – lightgbm | 5.8414 (CI95 5.357–6.363); so baseline -1.019 |
| mae – last_value | 6.8602 (CI95 6.310–7.393); so baseline +0.000 |
| Mô hình triển khai (chốt trước) | ridge |
| Độ bao phủ khoảng 90% – ridge | 0.8991 (nửa độ rộng 11.580) |
| Đơn vị độc lập | 23 |
| NGOÀI cohort – last_value | MAE 6.048 (CI95 5.273–6.853), 6 người |
| NGOÀI cohort – personal_mean | MAE 4.917 (CI95 4.163–5.627), 6 người |
| NGOÀI cohort – ridge | MAE 4.965 (CI95 4.376–5.545), 6 người |
| NGOÀI cohort – lightgbm | MAE 5.094 (CI95 4.449–5.691), 6 người |
| NGOÀI cohort – bao phủ khoảng 90% (deploy) | 0.929 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | utmb_c3:<id> (train) · utmb_cft70:<id> · utmb_c1:<id> (ngoài cohort). |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | bpm | Giá trị thật của target. |
| `y_pred` | bpm | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/vitals_pulse/2026-11-14_204445/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/vitals_pulse/2026-11-14_204445`

## Giới hạn cần nhớ

- Một lần đo/ngày (thường ~6:00), tư thế nằm đầu thấp 6° trong giai đoạn nằm giường.
- Ngưỡng kỹ thuật loại số ghi hỏng: HA tâm thu 60–250, tâm trương 30–150 mmHg, nhiệt độ 34–42 °C, mạch 30–220 bpm — KHÔNG phải ngưỡng lâm sàng.
- Campaign 1 chỉ có nhiệt độ 112/252 ngày — ngày không đo để trống, không nội suy.
- external.csv.gz + external_metrics.csv = đánh giá trên người CHƯA TỪNG THẤY (đúng 6 persona).

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
