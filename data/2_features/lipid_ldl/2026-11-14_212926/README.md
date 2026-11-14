# (1) Dữ liệu đã xử lý — đầu vào mô hình — `lipid_ldl` / run `2026-11-14_212926`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features lipid_ldl`
- **README cập nhật (UTC):** 2026-11-14T14:30:25+00:00
- **Cohort:** UTMB CFT70 NNX10AP86G lipid, 24 người, đo ngày nằm giường 14, 42, 70 (không có PRE)
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip › NNX10AP86G_CFT70_LIPIDS.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 24 |
| Số người/chuỗi độc lập | 24 |
| Số đặc trưng | 1 |
| Target | `pct_change_day70` (% so với PRE) |
| Cửa sổ | — (một hàng / người) |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `baseline` | mg/dL | LDL-cholesterol ngày nằm giường 14 (mốc sớm nhất có đo). |
| `pct_change_day70` | % so với ngày 14 | TARGET: (LDL ngày 70 / ngày 14 − 1) × 100. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/NNX10AP86G.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/lipid_ldl/2026-11-14_212926`

## Giới hạn cần nhớ

- Baseline là ngày 14 TRONG nằm giường, không phải trước nằm giường.
