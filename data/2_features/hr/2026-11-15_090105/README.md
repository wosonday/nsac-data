# (1) Dữ liệu đã xử lý — đầu vào mô hình — `hr` / run `2026-11-15_090105`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features hr`
- **README cập nhật (UTC):** 2026-11-15T02:01:06+00:00
- **Cohort:** MMASH 1.0.0 (PhysioNet, ODbL 1.0) — 22 nam khỏe mạnh, mặt đất, ~24 giờ/người
- **Nguồn:** data/1_source/processed/sample-v2/mmash_minutes.csv.gz (bảng phút đã QA của NASA-cl)

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 5301 |
| Số người/chuỗi độc lập | 22 |
| Số đặc trưng | 7 |
| Target | `hr_next_5min` (bpm) |
| Cửa sổ | {'past': 30, 'future': 5, 'step': 5} |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `cutoff_time` | phút (tương đối) | Điểm cuối của cửa sổ quá khứ. Không phải UTC. |
| `last_value` | bpm | Giá trị đo cuối trong cửa sổ quá khứ. |
| `mean_last_5` | bpm | Trung bình 5 điểm cuối. |
| `mean_all` | bpm | Trung bình cả cửa sổ quá khứ. |
| `std_all` | bpm | Độ lệch chuẩn trong cửa sổ quá khứ (độ dao động). |
| `change_last_10` | bpm | Giá trị cuối − giá trị 10 điểm trước. |
| `min_all` | bpm | Nhỏ nhất trong cửa sổ quá khứ. |
| `max_all` | bpm | Lớn nhất trong cửa sổ quá khứ. |
| `hr_next_5min` | bpm | TARGET: HR trung bình 5 phút ngay sau cutoff_time. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/processed/sample-v2/mmash_minutes.csv.gz`
- **Mô hình dùng bảng này:** `data/3_models/hr/2026-11-15_090105`

## Giới hạn cần nhớ

- Proxy mặt đất, không phải dữ liệu phi hành gia.
- HR ngoài 30–220 bpm coi là thiếu (ngưỡng kỹ thuật, không phải lâm sàng); chưa lọc artifact sinh lý.
- Cửa sổ chồng lấn: số hàng ≠ số người độc lập (22).
- Thời gian là phút tương đối trong nghiên cứu, không phải UTC.
