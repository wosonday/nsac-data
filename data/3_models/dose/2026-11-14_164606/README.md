# (3) Mô hình đã huấn luyện — `dose` / run `2026-11-14_164606`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate dose`
- **README cập nhật (UTC):** 2026-11-14T14:15:08+00:00
- **Cohort:** NASA OSDR RadLab — thiết bị Lidal, mô-đun Columbus, ISS, năm 2022 (một chuỗi thiết bị, không phải người)
- **Nguồn:** data/1_source/raw/radlab/instruments/Lidal/*.csv (3 file, lưới 5 phút)

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
| Số fold | 9 |
| Mô hình | last_value, ridge, lightgbm |
| Số file mô hình | 3 |
| mae – lightgbm | 0.7691 (CI95 0.686–0.871); so baseline -1.368 |
| mae – ridge | 0.9778 (CI95 0.901–1.068); so baseline -1.159 |
| mae – last_value | 2.1367 (CI95 1.850–2.436); so baseline +0.000 |
| Mô hình triển khai (chốt trước) | lightgbm |
| Độ bao phủ khoảng 90% – lightgbm | 0.8976 (nửa độ rộng 1.714) |
| Đơn vị độc lập | 9 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tháng được giữ làm test (by_month; train = các tháng trước, chừa 1 ngày). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Luôn là radlab:Lidal (một chuỗi thiết bị). |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | uGy/h | Giá trị thật của target. |
| `y_pred` | uGy/h | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/dose/2026-11-14_164606/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/dose/2026-11-14_164606`

## Giới hạn cần nhớ

- Đánh giá theo 9 tháng (4–12/2022): CI95 rất rộng về mặt lý thuyết, chỉ 9 đơn vị độc lập.
- Mốc thời gian lặp với giá trị khác nhau bị bỏ cả mốc; không nội suy điểm thiếu.
- Liều môi trường trong module, không phải liều cá nhân của phi hành gia.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
