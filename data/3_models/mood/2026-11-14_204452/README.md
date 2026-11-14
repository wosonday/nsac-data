# (3) Mô hình đã huấn luyện — `mood` / run `2026-11-14_204452`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate mood`
- **README cập nhật (UTC):** 2026-11-14T14:30:21+00:00
- **Cohort:** UTMB CFT70 — NNX10AP86G POMS, 24 người, 13–16 lần đo/người (~hằng tuần)
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip › NNX10AP86G_CFT70_POMS_TMD.csv

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
| mae – ridge | 5.2074 (CI95 4.172–6.252); so baseline -0.358 |
| mae – personal_mean | 5.2423 (CI95 4.204–6.300); so baseline -0.323 |
| mae – lightgbm | 5.3896 (CI95 4.388–6.401); so baseline -0.175 |
| mae – last_value | 5.5649 (CI95 4.423–6.689); so baseline +0.000 |
| Mô hình triển khai (chốt trước) | personal_mean |
| Độ bao phủ khoảng 90% – ridge | 0.8973 (nửa độ rộng 12.553) |
| Độ bao phủ khoảng 90% (deploy) – personal_mean | 0.8973 (nửa độ rộng 13.333) |
| Đơn vị độc lập | 24 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | điểm TMD | Giá trị thật của target. |
| `y_pred` | điểm TMD | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/mood/2026-11-14_204452/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/mood/2026-11-14_204452`

## Giới hạn cần nhớ

- Thang tự đánh giá; khoảng cách giữa các lần đo không đều (PRE 7–12 ngày, IN 7 ngày).
- Có nhóm can thiệp (Treatment) — không dùng làm đặc trưng.
- 3 persona Campaign 1 KHÔNG có POMS thật → dữ liệu giả định data/1_synthetic/mood_c1_poms.csv (chỉ để minh họa).

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
