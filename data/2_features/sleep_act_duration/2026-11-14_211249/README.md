# (1) Dữ liệu đã xử lý — đầu vào mô hình — `sleep_act_duration` / run `2026-11-14_211249`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features sleep_act_duration`
- **README cập nhật (UTC):** 2026-11-14T14:30:23+00:00
- **Cohort:** UTMB Bed Rest Campaign 1 (BRSMAct) — 3 người C1G0001–3 (= tomas, yuki, noor)
- **Nguồn:** data/1_source/raw/nlsp/BRSMAct.zip › BRSMACT_Campagin_1_Actigraphy.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 162 |
| Số người/chuỗi độc lập | 3 |
| Số đặc trưng | 6 |
| Target | `sleep_hours_next_night` (giờ) |
| Cửa sổ | {'past': 7, 'future': 1, 'step': 1} |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `cutoff_time` | phút (tương đối) | Điểm cuối của cửa sổ quá khứ. Không phải UTC. |
| `last_value` | giờ | Giá trị đo cuối trong cửa sổ quá khứ. |
| `mean_last_5` | giờ | Trung bình 5 điểm cuối. |
| `mean_all` | giờ | Trung bình cả cửa sổ quá khứ. |
| `std_all` | giờ | Độ lệch chuẩn trong cửa sổ quá khứ (độ dao động). |
| `min_all` | giờ | Nhỏ nhất trong cửa sổ quá khứ. |
| `max_all` | giờ | Lớn nhất trong cửa sổ quá khứ. |
| `sleep_hours_next_night` | giờ | TARGET: thời lượng ngủ (actigraphy) đêm tới. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/BRSMAct.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/sleep_act_duration/2026-11-14_211249`

## Giới hạn cần nhớ

- Chỉ 3 người → pilot; có đêm dùng thuốc ngủ (Ambien).
- 3 persona CFT70 dùng dữ liệu GIẢ ĐỊNH data/1_synthetic/sleep_cft70_actigraphy.csv (cột duration).
