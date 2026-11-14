# (1) Dữ liệu đã xử lý — đầu vào mô hình — `muscle_quadriceps` / run `2026-11-14_212853`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features muscle_quadriceps`
- **README cập nhật (UTC):** 2026-11-14T14:30:24+00:00
- **Cohort:** UTMB CFT70 iRATS — MRI thể tích cơ, 27 người (gồm persona dae-jung 8072, lena 8936; KHÔNG có ayla 5160)
- **Nguồn:** data/1_source/raw/nlsp/BEDREST_iRATS.zip › BEDREST_IRATS_MRI_ULTRASOUND_CFT70_MRI_<cơ>.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 27 |
| Số người/chuỗi độc lập | 27 |
| Số đặc trưng | 1 |
| Target | `pct_change_day69` (% so với PRE) |
| Cửa sổ | — (một hàng / người) |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `baseline` | đơn vị nguồn (thể tích MRI) | Giá trị PRE (ngày −6). |
| `pct_change_day69` | % so với PRE | TARGET: (thể tích ngày nằm giường 69 / PRE − 1) × 100. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/BEDREST_iRATS.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/muscle_quadriceps/2026-11-14_212853`

## Giới hạn cần nhớ

- Một hàng / người — pilot; nhóm tập luyện (iRATS) ảnh hưởng mạnh nhưng không dùng làm đặc trưng.
- Persona ayla (5160) và 3 persona Campaign 1 không có MRI → UNKNOWN.
