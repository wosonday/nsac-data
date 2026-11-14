# (1) Dữ liệu đã xử lý — đầu vào mô hình — `cortisol` / run `2026-11-14_213014`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features cortisol`
- **README cập nhật (UTC):** 2026-11-14T14:30:26+00:00
- **Cohort:** UTMB Campaign 3 BRSMLVR — cortisol nước bọt, 14 người
- **Nguồn:** data/1_source/raw/nlsp/BRSMLVR.zip › *Salivary_Cortisol.csv, *Saliva_Cortisol.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng MÔ TẢ dữ liệu thật (không có mô hình) — dùng hiển thị trực tiếp |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng | 399 |
| Số người | 14 |
| Loại | MÔ TẢ — không train/evaluate |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `study_day` | ngày nghiên cứu | Ngày theo nguồn (âm = trước nằm giường). |
| `cortisol_mean` | theo nguồn | Trung bình cortisol nước bọt các mẫu trong ngày (đơn vị nguồn chưa có codebook). |
| `n_samples` |  | Số mẫu trong ngày. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/BRSMLVR.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/cortisol/2026-11-14_213014`

## Giới hạn cần nhớ

- Bảng MÔ TẢ. Cortisol thay đổi theo giờ trong ngày nhưng nguồn không ghi giờ lấy mẫu → chỉ dùng trung bình ngày.
- File C3F 'Saliva_Cortisol' của nguồn thực chứa cột VZV → bị bỏ qua.
