# (1) Dữ liệu đã xử lý — đầu vào mô hình — `glucose` / run `2026-11-15_090515`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features glucose`
- **README cập nhật (UTC):** 2026-11-15T02:05:15+00:00
- **Cohort:** UTMB CFT70 — NNX10AP86G OGTT, 23 người đủ dữ liệu PRE + ngày nằm giường 66
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip › NNX10AP86G_CFT70_OGTT.csv (phút 0 = lúc đói; 30–120 = sau uống glucose)

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 23 |
| Số người/chuỗi độc lập | 23 |
| Số đặc trưng | 3 |
| Target | `delta_glucose_0` (mg/dL) |
| Cửa sổ | — (một hàng / người) |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `pre_glucose_0` | mg/dL | Trung bình đường huyết lúc đói các lần PRE. |
| `pre_glucose_120` | mg/dL | Trung bình đường huyết 2 giờ sau uống glucose, các lần PRE. |
| `pre_insulin_0` | uU/mL | Trung bình insulin lúc đói các lần PRE. |
| `delta_glucose_0` | mg/dL | TARGET: đường huyết lúc đói ngày nằm giường 66 − trung bình PRE. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/NNX10AP86G.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/glucose/2026-11-15_090515`

## Giới hạn cần nhớ

- Một hàng / người (23 hàng) — pilot. OGTT là nghiệm pháp tại phòng thí nghiệm, không phải CGM.
- Đường huyết hằng ngày của persona trên web là DỮ LIỆU GIẢ ĐỊNH (data/1_synthetic/glucose_daily_personas.csv), neo vào giá trị OGTT thật với CFT70.
