# (2) Dữ liệu dự đoán — `dose` / run `2026-11-14_164606`

Kết quả dự báo của mô hình đã lưu (bước 5) cho một file đầu vào mới, kèm khoảng 90%, cờ từ chối dự báo (abstain) và cờ in_sample.

- **Tạo bởi:** `sky-ml predict`
- **Thời điểm (UTC):** 2026-11-14T09:48:35+00:00
- **Cohort:** NASA OSDR RadLab — thiết bị Lidal, mô-đun Columbus, ISS, năm 2022 (một chuỗi thiết bị, không phải người)
- **Nguồn:** data/1_source/raw/radlab/instruments/Lidal/*.csv (3 file, lưới 5 phút)

## File trong thư mục

| File | Nội dung |
|---|---|
| `2022-05-01_2023-01-01_latest_lightgbm_20261114_164835.csv` | Dự đoán (mỗi lần chạy predict một file; .json cùng tên = thông tin lần chạy) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Lần chạy mới nhất | 2022-05-01_2023-01-01_latest_lightgbm_20261114_164835 |
| Mô hình | lightgbm |
| Chế độ | latest |
| Số hàng | 1 |
| Từ chối (abstain) | 0 |
| Trong dữ liệu huấn luyện (in_sample) | 1 |
| Nửa độ rộng khoảng 90% | 1.696 uGy/h |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Luôn là radlab:Lidal (một chuỗi thiết bị). |
| `cutoff_time` | thời điểm nguồn | Điểm cuối cửa sổ 6 giờ quá khứ; giữ như nguồn, CHƯA xác minh là UTC. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `unit` |  | Đơn vị của prediction. |
| `prediction` | uGy/h | Dự báo của mô hình đã lưu. |
| `low90` | uGy/h | Cận dưới khoảng 90% (split-conformal từ sai số OOF). |
| `high90` | uGy/h | Cận trên khoảng 90%. |
| `abstain` | bool | True = từ chối dự báo; lý do ở cột reasons. |
| `reasons` |  | missing_features | out_of_training_range | insufficient_calibration_data (phân cách ;). |
| `in_sample` | bool | True = người này nằm trong dữ liệu huấn luyện → KHÔNG phải đánh giá trên người mới. |

## Truy vết (lineage)

- **Mô hình:** `data/3_models/dose/2026-11-14_164606/lightgbm/final.joblib`
- **Bảng đặc trưng của run:** `data/2_features/dose/2026-11-14_164606/table.csv.gz`

## Giới hạn cần nhớ

- Đánh giá theo 9 tháng (4–12/2022): CI95 rất rộng về mặt lý thuyết, chỉ 9 đơn vị độc lập.
- Mốc thời gian lặp với giá trị khác nhau bị bỏ cả mốc; không nội suy điểm thiếu.
- Liều môi trường trong module, không phải liều cá nhân của phi hành gia.
