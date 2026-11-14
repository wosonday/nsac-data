# (1) Dữ liệu đã xử lý — đầu vào mô hình — `fatigue` / run `2026-11-14_211255`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features fatigue`
- **README cập nhật (UTC):** 2026-11-14T14:15:12+00:00
- **Cohort:** UTMB CFT70 — NNX10AP86G MFSI-SF (Multidimensional Fatigue Symptom Inventory – Short Form), 24 người, ~16 lần đo/người
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip › NNX10AP86G_CFT70_MFSI-SF_Total_Scale.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 286 |
| Số người/chuỗi độc lập | 24 |
| Số đặc trưng | 5 |
| Target | `mfsi_total_next` (điểm MFSI-SF) |
| Cửa sổ | {'past': 3, 'future': 1, 'step': 1} |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `cutoff_time` | ngày nghiên cứu | PRE = −BR_Day, IN = +BR_Day, POST = 70 + BR_Day. |
| `last_value` | điểm MFSI-SF | Giá trị đo cuối trong cửa sổ quá khứ. |
| `mean_all` | điểm MFSI-SF | Trung bình cả cửa sổ quá khứ. |
| `std_all` | điểm MFSI-SF | Độ lệch chuẩn trong cửa sổ quá khứ (độ dao động). |
| `min_all` | điểm MFSI-SF | Nhỏ nhất trong cửa sổ quá khứ. |
| `max_all` | điểm MFSI-SF | Lớn nhất trong cửa sổ quá khứ. |
| `mfsi_total_next` | điểm | TARGET: tổng điểm mệt mỏi MFSI-SF lần đo tới (cao hơn = mệt hơn; có thể âm vì trừ thang sức sống). |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/NNX10AP86G.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/fatigue/2026-11-14_211255`

## Giới hạn cần nhớ

- Thang tự đánh giá; 3 persona Campaign 1 không có MFSI-SF.
