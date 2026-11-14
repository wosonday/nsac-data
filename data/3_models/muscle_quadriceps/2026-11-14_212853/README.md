# (3) Mô hình đã huấn luyện — `muscle_quadriceps` / run `2026-11-14_212853`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate muscle_quadriceps`
- **README cập nhật (UTC):** 2026-11-14T14:30:25+00:00
- **Cohort:** UTMB CFT70 iRATS — MRI thể tích cơ, 27 người (gồm persona dae-jung 8072, lena 8936; KHÔNG có ayla 5160)
- **Nguồn:** data/1_source/raw/nlsp/BEDREST_iRATS.zip › BEDREST_IRATS_MRI_ULTRASOUND_CFT70_MRI_<cơ>.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `oof.csv.gz` | Dự đoán ngoài tập huấn luyện (OOF) của mọi mô hình — nguồn của mọi điểm đánh giá |
| `folds.json` | Danh sách fold và số mẫu train/test |
| `manifest.json` | SHA-256 + phiên bản + tham số |
| `<model>/final.joblib` | Mô hình fit trên toàn bộ người → chỉ dùng cho NGƯỜI MỚI |
| `metrics.csv` | Metric theo đơn vị độc lập, CI95, so baseline |
| `summary.json` | Tóm tắt: metric, độ bao phủ khoảng 90%, kiểm định hoán vị, kết quả ngoài cohort |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số fold | 27 |
| Mô hình | persistence, mean_delta, ridge |
| Số file mô hình | 3 |
| mae – persistence | 6.0866 (CI95 4.485–7.796); so baseline +0.000 |
| mae – mean_delta | 6.4083 (CI95 4.791–8.102); so baseline +0.322 |
| mae – ridge | 6.7246 (CI95 5.019–8.542); so baseline +0.638 |
| Mô hình triển khai (chốt trước) | mean_delta |
| Kiểm định hoán vị | persistence: p = 0.8308 (200 lần) |
| Độ bao phủ khoảng 90% – persistence | 0.9259 (nửa độ rộng 16.340) |
| Độ bao phủ khoảng 90% (deploy) – mean_delta | 0.9259 (nửa độ rộng 16.180) |
| Đơn vị độc lập | 27 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | % so với PRE | Giá trị thật của target. |
| `y_pred` | % so với PRE | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/muscle_quadriceps/2026-11-14_212853/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/muscle_quadriceps/2026-11-14_212853`

## Giới hạn cần nhớ

- Một hàng / người — pilot; nhóm tập luyện (iRATS) ảnh hưởng mạnh nhưng không dùng làm đặc trưng.
- Persona ayla (5160) và 3 persona Campaign 1 không có MRI → UNKNOWN.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
