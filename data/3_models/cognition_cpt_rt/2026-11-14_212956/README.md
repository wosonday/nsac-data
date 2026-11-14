# (3) Mô hình đã huấn luyện — `cognition_cpt_rt` / run `2026-11-14_212956`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate cognition_cpt_rt`
- **README cập nhật (UTC):** 2026-11-14T14:30:25+00:00
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
| mae – ridge | 26.2325 (CI95 21.079–31.855); so baseline -1.189 |
| mae – lightgbm | 27.3022 (CI95 22.349–32.879); so baseline -0.119 |
| mae – last_value | 27.4212 (CI95 20.437–35.393); so baseline +0.000 |
| mae – personal_mean | 30.9685 (CI95 24.721–37.769); so baseline +3.547 |
| Mô hình triển khai (chốt trước) | personal_mean |
| Độ bao phủ khoảng 90% – ridge | 0.9077 (nửa độ rộng 58.616) |
| Độ bao phủ khoảng 90% (deploy) – personal_mean | 0.8974 (nửa độ rộng 83.667) |
| Đơn vị độc lập | 25 |
| NGOÀI cohort – last_value | MAE 43.571 (CI95 36.857–48.143), 3 người |
| NGOÀI cohort – personal_mean | MAE 59.111 (CI95 44.619–77.143), 3 người |
| NGOÀI cohort – ridge | MAE 42.109 (CI95 33.372–50.549), 3 người |
| NGOÀI cohort – lightgbm | MAE 35.978 (CI95 30.105–39.454), 3 người |
| NGOÀI cohort – bao phủ khoảng 90% (deploy) | 0.800 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | ms | Giá trị thật của target. |
| `y_pred` | ms | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/cognition_cpt_rt/2026-11-14_212956/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/cognition_cpt_rt/2026-11-14_212956`

## Giới hạn cần nhớ

- WinSCAT = Spaceflight Cognitive Assessment Tool for Windows (NASA); có hiệu ứng học (luyện tập) giữa các lần test.
- Chuỗi theo thứ tự lần test, khoảng cách giữa các lần không đều.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
