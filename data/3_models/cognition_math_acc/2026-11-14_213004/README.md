# (3) Mô hình đã huấn luyện — `cognition_math_acc` / run `2026-11-14_213004`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate cognition_math_acc`
- **README cập nhật (UTC):** 2026-11-14T14:30:26+00:00
- **Cohort:** UTMB MR085G WinSCAT — TRAIN: Campaign 3 (25 người); NGOÀI cohort: Campaign 1 C1G0001–3 (= tomas, yuki, noor), 10 lần test/người
- **Nguồn:** data/1_source/raw/nlsp/MR085G.zip › MR085G_Campaign_3_WinSCAT_*.csv, MR085G_Campaign_1_WinSCAT_All.csv

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
| Số fold | 25 |
| Mô hình | last_value, personal_mean, ridge, lightgbm |
| Số file mô hình | 4 |
| mae – ridge | 7.7238 (CI95 6.374–9.333); so baseline -0.617 |
| mae – personal_mean | 7.9016 (CI95 6.399–9.668); so baseline -0.439 |
| mae – lightgbm | 8.0024 (CI95 6.575–9.734); so baseline -0.338 |
| mae – last_value | 8.3407 (CI95 6.731–10.482); so baseline +0.000 |
| Mô hình triển khai (chốt trước) | personal_mean |
| Độ bao phủ khoảng 90% – ridge | 0.9026 (nửa độ rộng 17.088) |
| Độ bao phủ khoảng 90% (deploy) – personal_mean | 0.8974 (nửa độ rộng 18.333) |
| Đơn vị độc lập | 25 |
| NGOÀI cohort – last_value | MAE 8.571 (CI95 4.286–12.857), 3 người |
| NGOÀI cohort – personal_mean | MAE 6.825 (CI95 3.095–10.238), 3 người |
| NGOÀI cohort – ridge | MAE 6.779 (CI95 3.599–9.694), 3 người |
| NGOÀI cohort – lightgbm | MAE 7.046 (CI95 3.997–9.782), 3 người |
| NGOÀI cohort – bao phủ khoảng 90% (deploy) | 0.952 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | % | Giá trị thật của target. |
| `y_pred` | % | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/cognition_math_acc/2026-11-14_213004/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/cognition_math_acc/2026-11-14_213004`

## Giới hạn cần nhớ

- WinSCAT = Spaceflight Cognitive Assessment Tool for Windows (NASA); có hiệu ứng học (luyện tập) giữa các lần test.
- Chuỗi theo thứ tự lần test, khoảng cách giữa các lần không đều.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
