# (3) Mô hình đã huấn luyện — `dose_orbit` / run `2026-11-14_201827`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate dose_orbit`
- **Thời điểm (UTC):** 2026-11-14T13:18:32+00:00
- **Cohort:** Như task dose (RadLab Lidal, ISS Columbus, 2022)
- **Nguồn:** data/1_source/raw/radlab/instruments/Lidal/*.csv — thêm cột latitude, longitude, altitude của chính file

## File trong thư mục

| File | Nội dung |
|---|---|
| `oof.csv.gz` | Dự đoán ngoài tập huấn luyện (OOF) của mọi mô hình — nguồn của mọi điểm đánh giá |
| `folds.json` | Danh sách fold và số mẫu train/test |
| `manifest.json` | SHA-256 + phiên bản + tham số |
| `<model>/final.joblib` | Mô hình fit trên toàn bộ người → chỉ dùng cho NGƯỜI MỚI |
| `metrics.csv` | Metric theo người, CI95, so baseline |
| `summary.json` | Tóm tắt + độ bao phủ khoảng 90% |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| mae – lightgbm | 0.6373 (CI95 0.559–0.731); so baseline -1.499 |
| mae – ridge | 0.9745 (CI95 0.901–1.060); so baseline -1.162 |
| mae – last_value | 2.1367 (CI95 1.850–2.436); so baseline +0.000 |
| Độ bao phủ khoảng 90% | 0.8974 (nửa độ rộng 1.501) |
| Đơn vị độc lập | 9 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tháng được giữ làm test. |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Luôn là radlab:Lidal (một chuỗi thiết bị). |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | uGy/h | Giá trị thật của target. |
| `y_pred` | uGy/h | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/dose_orbit/2026-11-14_201827/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/dose_orbit/2026-11-14_201827`

## Giới hạn cần nhớ

- Chỉ dùng vị trí TẠI cutoff, không dùng vị trí 1 giờ tới (chưa có quỹ đạo dự báo).
- Cấu hình chốt sau một thí nghiệm thăm dò trên cùng các tháng test (14/11) → kết quả có thể hơi lạc quan; cần kiểm lại trên năm khác.
- 9 đơn vị độc lập (tháng).

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
