# (3) Mô hình đã huấn luyện — `lv_diastolic_volume` / run `2026-11-14_211412`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate lv_diastolic_volume`
- **README cập nhật (UTC):** 2026-11-14T14:15:13+00:00
- **Cohort:** UTMB CFT70 (nằm giường 70 ngày) — người có đo PRE và ngày 70
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip (iDXA) hoặc BRSMCF.zip (siêu âm tim 3D) — xem tasks.yaml › member, value_column

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
| Số fold | 35 |
| Mô hình | persistence, mean_delta, ridge |
| Số file mô hình | 3 |
| mae – mean_delta | 8.2450 (CI95 6.357–10.231); so baseline -1.939 |
| mae – ridge | 8.4576 (CI95 6.560–10.452); so baseline -1.727 |
| mae – persistence | 10.1843 (CI95 7.880–12.782); so baseline +0.000 |
| Mô hình triển khai (chốt trước) | mean_delta |
| Kiểm định hoán vị | mean_delta: p = 0.6368 (200 lần) |
| Độ bao phủ khoảng 90% – mean_delta | 0.9143 (nửa độ rộng 16.876) |
| Đơn vị độc lập | 35 |

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

- **Bảng đặc trưng (đầu vào):** `data/2_features/lv_diastolic_volume/2026-11-14_211412/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/lv_diastolic_volume/2026-11-14_211412`

## Giới hạn cần nhớ

- Một hàng / người — pilot; đánh giá LOSO + kiểm định hoán vị 200 lần.
- Nhóm can thiệp (tập luyện, testosterone…) ảnh hưởng mạnh nhưng KHÔNG dùng làm đặc trưng (phi hành gia thật không có nhãn này).
- Chỉ có ở 3 persona CFT70; persona Campaign 1 → UNKNOWN.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
