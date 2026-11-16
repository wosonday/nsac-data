# (1) Dữ liệu đã xử lý — đầu vào mô hình — `dose` / run `2026-11-15_090116`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features dose`
- **README cập nhật (UTC):** 2026-11-15T02:01:16+00:00
- **Cohort:** NASA OSDR RadLab — thiết bị Lidal, mô-đun Columbus, ISS, năm 2022 (một chuỗi thiết bị, không phải người)
- **Nguồn:** data/1_source/raw/radlab/instruments/Lidal/*.csv (3 file, lưới 5 phút)

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 8366 |
| Số người/chuỗi độc lập | 1 |
| Số đặc trưng | 7 |
| Target | `dose_rate_next_1h` (uGy/h) |
| Cửa sổ | {'past': 72, 'future': 12, 'step': 12} |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Luôn là radlab:Lidal (một chuỗi thiết bị). |
| `cutoff_time` | thời điểm nguồn | Điểm cuối cửa sổ 6 giờ quá khứ; giữ như nguồn, CHƯA xác minh là UTC. |
| `last_value` | uGy/h | Giá trị đo cuối trong cửa sổ quá khứ. |
| `mean_last_5` | uGy/h | Trung bình 5 điểm cuối. |
| `mean_all` | uGy/h | Trung bình cả cửa sổ quá khứ. |
| `std_all` | uGy/h | Độ lệch chuẩn trong cửa sổ quá khứ (độ dao động). |
| `change_last_10` | uGy/h | Giá trị cuối − giá trị 10 điểm trước. |
| `min_all` | uGy/h | Nhỏ nhất trong cửa sổ quá khứ. |
| `max_all` | uGy/h | Lớn nhất trong cửa sổ quá khứ. |
| `dose_rate_next_1h` | uGy/h | TARGET: tốc độ liều hấp thụ trung bình 1 giờ sau cutoff_time. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/radlab/instruments/Lidal/*.csv`
- **Mô hình dùng bảng này:** `data/3_models/dose/2026-11-15_090116`

## Giới hạn cần nhớ

- Đánh giá theo 9 tháng (4–12/2022): CI95 rất rộng về mặt lý thuyết, chỉ 9 đơn vị độc lập.
- Mốc thời gian lặp với giá trị khác nhau bị bỏ cả mốc; không nội suy điểm thiếu.
- Liều môi trường trong module, không phải liều cá nhân của phi hành gia.
