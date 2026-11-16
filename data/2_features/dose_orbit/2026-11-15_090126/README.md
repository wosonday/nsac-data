# (1) Dữ liệu đã xử lý — đầu vào mô hình — `dose_orbit` / run `2026-11-15_090126`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features dose_orbit`
- **README cập nhật (UTC):** 2026-11-15T02:01:26+00:00
- **Cohort:** Như task dose (RadLab Lidal, ISS Columbus, 2022)
- **Nguồn:** data/1_source/raw/radlab/instruments/Lidal/*.csv — thêm cột latitude, longitude, altitude của chính file

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
| Số đặc trưng | 10 |
| Target | `dose_rate_next_1h` (uGy/h) |
| Cửa sổ | {'past': 72, 'future': 12, 'step': 12} |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Luôn là radlab:Lidal (một chuỗi thiết bị). |
| `cutoff_time` | thời điểm nguồn | Điểm cuối cửa sổ 6 giờ; chưa xác minh là UTC. |
| `last_value` | uGy/h | Giá trị đo cuối trong cửa sổ quá khứ. |
| `mean_last_5` | uGy/h | Trung bình 5 điểm cuối. |
| `mean_all` | uGy/h | Trung bình cả cửa sổ quá khứ. |
| `std_all` | uGy/h | Độ lệch chuẩn trong cửa sổ quá khứ (độ dao động). |
| `change_last_10` | uGy/h | Giá trị cuối − giá trị 10 điểm trước. |
| `min_all` | uGy/h | Nhỏ nhất trong cửa sổ quá khứ. |
| `max_all` | uGy/h | Lớn nhất trong cửa sổ quá khứ. |
| `dose_rate_next_1h` | uGy/h | TARGET: tốc độ liều hấp thụ trung bình 1 giờ sau cutoff_time. |
| `latitude_now` | độ | Vĩ độ ISS tại cutoff (biết được lúc dự báo). |
| `longitude_now` | độ | Kinh độ ISS tại cutoff. |
| `altitude_now` | km | Độ cao ISS tại cutoff. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/radlab/instruments/Lidal/*.csv`
- **Mô hình dùng bảng này:** `data/3_models/dose_orbit/2026-11-15_090126`

## Giới hạn cần nhớ

- Chỉ dùng vị trí TẠI cutoff, không dùng vị trí 1 giờ tới (chưa có quỹ đạo dự báo).
- Cấu hình chốt sau một thí nghiệm thăm dò trên cùng các tháng test (14/11) → kết quả có thể hơi lạc quan; cần kiểm lại trên năm khác.
- 9 đơn vị độc lập (tháng).
