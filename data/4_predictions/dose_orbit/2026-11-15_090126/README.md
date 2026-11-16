# (2) Dữ liệu dự đoán — `dose_orbit` / run `2026-11-15_090126`

Kết quả dự báo của mô hình đã lưu (bước 5) cho một file đầu vào mới, kèm khoảng 90%, cờ từ chối dự báo (abstain) và cờ in_sample.

- **Tạo bởi:** `sky-ml predict / evaluate dose_orbit`
- **README cập nhật (UTC):** 2026-11-15T02:07:43+00:00
- **Cohort:** Như task dose (RadLab Lidal, ISS Columbus, 2022)
- **Nguồn:** data/1_source/raw/radlab/instruments/Lidal/*.csv — thêm cột latitude, longitude, altitude của chính file

## File trong thư mục

| File | Nội dung |
|---|---|
| `2022-05-01_2023-01-01_latest_lightgbm_20261115_090743.csv` | Dự đoán (.json cùng tên = thông tin lần chạy) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| 2022-05-01_2023-01-01_latest_lightgbm_20261115_090743 | mô hình lightgbm, chế độ latest, 1 hàng, từ chối 0, in_sample 1, đầu vào giả định 0, nửa độ rộng 90% 1.484 uGy/h |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Luôn là radlab:Lidal (một chuỗi thiết bị). |
| `cutoff_time` | thời điểm nguồn | Điểm cuối cửa sổ 6 giờ; chưa xác minh là UTC. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `unit` |  | Đơn vị của prediction. |
| `prediction` | uGy/h | Dự báo của mô hình đã lưu. |
| `low90` | uGy/h | Cận dưới khoảng 90% (split-conformal từ sai số OOF). |
| `high90` | uGy/h | Cận trên khoảng 90%. |
| `abstain` | bool | True = từ chối dự báo; lý do ở cột reasons. |
| `reasons` |  | Lý do từ chối, phân cách bằng dấu chấm phẩy: missing_features, out_of_training_range, insufficient_calibration_data. |
| `in_sample` | bool | True = người này nằm trong dữ liệu huấn luyện → KHÔNG phải đánh giá trên người mới. |
| `input_synthetic` | bool | True = đầu vào là DỮ LIỆU GIẢ ĐỊNH (data/1_synthetic) — dự đoán chỉ để minh họa. |

## Truy vết (lineage)

- **Mô hình:** `data/3_models/dose_orbit/2026-11-15_090126/lightgbm/final.joblib`
- **Bảng đặc trưng của run:** `data/2_features/dose_orbit/2026-11-15_090126/table.csv.gz`

## Giới hạn cần nhớ

- Chỉ dùng vị trí TẠI cutoff, không dùng vị trí 1 giờ tới (chưa có quỹ đạo dự báo).
- Cấu hình chốt sau một thí nghiệm thăm dò trên cùng các tháng test (14/11) → kết quả có thể hơi lạc quan; cần kiểm lại trên năm khác.
- 9 đơn vị độc lập (tháng).
