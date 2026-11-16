# (3) Mô hình đã huấn luyện — `cpet_physio` / run `2026-11-15_090220`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate cpet_physio`
- **README cập nhật (UTC):** 2026-11-15T02:02:39+00:00
- **Cohort:** UTMB CFT70 — như task cpet, 33 người
- **Nguồn:** Như task cpet; chỉ dùng pre_vo2 và age

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
| Số fold | 33 |
| Mô hình | persistence, mean_delta, ridge, lightgbm |
| Số file mô hình | 4 |
| mae – mean_delta | 3.6169 (CI95 2.656–4.754); so baseline -0.508 |
| mae – ridge | 3.6679 (CI95 2.723–4.719); so baseline -0.457 |
| mae – lightgbm | 3.8111 (CI95 2.859–4.894); so baseline -0.314 |
| mae – persistence | 4.1253 (CI95 2.974–5.493); so baseline +0.000 |
| Mô hình triển khai (chốt trước) | mean_delta |
| Kiểm định hoán vị | mean_delta: p = 0.5124 (200 lần) |
| Độ bao phủ khoảng 90% – mean_delta | 0.9091 (nửa độ rộng 6.998) |
| Đơn vị độc lập | 33 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | source_REL_VO2PK | Giá trị thật của target. |
| `y_pred` | source_REL_VO2PK | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/cpet_physio/2026-11-15_090220/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/cpet_physio/2026-11-15_090220`

## Giới hạn cần nhớ

- Contract đầu vào áp dụng được cho phi hành gia (không cần nhóm can thiệp).
- Một hàng / người (33 hàng): mẫu rất nhỏ; kết quả là pilot kỹ thuật.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
