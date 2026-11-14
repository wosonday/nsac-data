# (3) Mô hình đã huấn luyện — `vitals_resp` / run `2026-11-14_211232`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate vitals_resp`
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
| mae – personal_mean | 1.1526 (CI95 1.033–1.279); so baseline -0.130 |
| mae – ridge | 1.1764 (CI95 1.070–1.295); so baseline -0.107 |
| mae – lightgbm | 1.1856 (CI95 1.086–1.284); so baseline -0.097 |
| mae – last_value | 1.2829 (CI95 1.151–1.421); so baseline +0.000 |
| Mô hình triển khai (chốt trước) | ridge |
| Độ bao phủ khoảng 90% – personal_mean | 0.9025 (nửa độ rộng 2.286) |
| Độ bao phủ khoảng 90% (deploy) – ridge | 0.8998 (nửa độ rộng 2.429) |
| Đơn vị độc lập | 23 |
| NGOÀI cohort – last_value | MAE 0.503 (CI95 0.305–0.708), 6 người |
| NGOÀI cohort – personal_mean | MAE 0.569 (CI95 0.316–0.828), 6 người |
| NGOÀI cohort – ridge | MAE 0.721 (CI95 0.564–0.894), 6 người |
| NGOÀI cohort – lightgbm | MAE 0.701 (CI95 0.497–0.909), 6 người |
| NGOÀI cohort – bao phủ khoảng 90% (deploy) | 0.973 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | utmb_c3:<id> (train) · utmb_cft70:<id> · utmb_c1:<id> (ngoài cohort). |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | lần/phút | Giá trị thật của target. |
| `y_pred` | lần/phút | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/vitals_resp/2026-11-14_211232/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/vitals_resp/2026-11-14_211232`

## Giới hạn cần nhớ

- Một lần đo/ngày (thường ~6:00), tư thế nằm đầu thấp 6° trong giai đoạn nằm giường.
- Ngưỡng kỹ thuật loại số ghi hỏng: HA tâm thu 60–250, tâm trương 30–150 mmHg, nhiệt độ 34–42 °C, mạch 30–220 bpm — KHÔNG phải ngưỡng lâm sàng.
- Campaign 1 chỉ có nhiệt độ 112/252 ngày — ngày không đo để trống, không nội suy.
- external.csv.gz + external_metrics.csv = đánh giá trên người CHƯA TỪNG THẤY (đúng 6 persona).

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
