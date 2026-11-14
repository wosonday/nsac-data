# (3) Mô hình đã huấn luyện — `fatigue` / run `2026-11-14_211255`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate fatigue`
- **README cập nhật (UTC):** 2026-11-14T14:15:12+00:00
- **Cohort:** UTMB CFT70 — NNX10AP86G MFSI-SF (Multidimensional Fatigue Symptom Inventory – Short Form), 24 người, ~16 lần đo/người
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip › NNX10AP86G_CFT70_MFSI-SF_Total_Scale.csv

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
| Số fold | 24 |
| Mô hình | last_value, personal_mean, ridge, lightgbm |
| Số file mô hình | 4 |
| mae – personal_mean | 4.5749 (CI95 3.769–5.378); so baseline -1.041 |
| mae – ridge | 4.7568 (CI95 4.095–5.453); so baseline -0.859 |
| mae – lightgbm | 5.1238 (CI95 4.353–6.011); so baseline -0.492 |
| mae – last_value | 5.6159 (CI95 4.555–6.676); so baseline +0.000 |
| Mô hình triển khai (chốt trước) | personal_mean |
| Độ bao phủ khoảng 90% – personal_mean | 0.8986 (nửa độ rộng 10.667) |
| Đơn vị độc lập | 24 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | điểm MFSI-SF | Giá trị thật của target. |
| `y_pred` | điểm MFSI-SF | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/fatigue/2026-11-14_211255/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/fatigue/2026-11-14_211255`

## Giới hạn cần nhớ

- Thang tự đánh giá; 3 persona Campaign 1 không có MFSI-SF.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
