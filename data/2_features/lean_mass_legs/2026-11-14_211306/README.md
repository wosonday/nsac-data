# (1) Dữ liệu đã xử lý — đầu vào mô hình — `lean_mass_legs` / run `2026-11-14_211306`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features lean_mass_legs`
- **README cập nhật (UTC):** 2026-11-14T14:15:12+00:00
- **Cohort:** UTMB CFT70 (nằm giường 70 ngày) — người có đo PRE và ngày 70
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip (iDXA) hoặc BRSMCF.zip (siêu âm tim 3D) — xem tasks.yaml › member, value_column

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 18 |
| Số người/chuỗi độc lập | 18 |
| Số đặc trưng | 1 |
| Target | `pct_change_day70` (% so với PRE) |
| Cửa sổ | — (một hàng / người) |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `baseline` | đơn vị nguồn | Trung bình mọi lần đo PRE của người đó (g với iDXA, g với LV mass, mL với LVDV). |
| `pct_change_day70` | % so với PRE | TARGET: (giá trị ngày nằm giường 70 / baseline − 1) × 100. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/NNX10AP86G.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/lean_mass_legs/2026-11-14_211306`

## Giới hạn cần nhớ

- Một hàng / người — pilot; đánh giá LOSO + kiểm định hoán vị 200 lần.
- Nhóm can thiệp (tập luyện, testosterone…) ảnh hưởng mạnh nhưng KHÔNG dùng làm đặc trưng (phi hành gia thật không có nhãn này).
- Chỉ có ở 3 persona CFT70; persona Campaign 1 → UNKNOWN.
