# (1) Dữ liệu đã xử lý — đầu vào mô hình — `dxa_regional` / run `2026-11-14_213012`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features dxa_regional`
- **README cập nhật (UTC):** 2026-11-14T14:30:26+00:00
- **Cohort:** UTMB CFT70 BRSMiDXA — 5 người (5297, 6187, 6464, 8179, 9023), KHÔNG có persona
- **Nguồn:** data/1_source/raw/nlsp/BRSMiDXA.zip › *_L_Hip_*, *_R_Hip_*, *_S_bone_*.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng MÔ TẢ dữ liệu thật (không có mô hình) — dùng hiển thị trực tiếp |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng | 90 |
| Số người | 5 |
| Loại | MÔ TẢ — không train/evaluate |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `region` |  | L_Hip / R_Hip (BMD toàn bộ hông) · S_bone (BMD cột sống L1–L4). |
| `bmd` | g/cm² | Mật độ khoáng xương (trung bình các lần quét cùng ngày). |
| `days_since_first_scan` | ngày | Số ngày kể từ lần quét đầu (nguồn không ghi pha PRE/IN/POST). |
| `pct_vs_first_scan` | % | % thay đổi BMD so với lần quét đầu. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/BRSMiDXA.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/dxa_regional/2026-11-14_213012`

## Giới hạn cần nhớ

- Bảng MÔ TẢ — 5 người quá ít để train/đánh giá mô hình.
