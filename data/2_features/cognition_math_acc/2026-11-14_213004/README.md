# (1) Dữ liệu đã xử lý — đầu vào mô hình — `cognition_math_acc` / run `2026-11-14_213004`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features cognition_math_acc`
- **README cập nhật (UTC):** 2026-11-14T14:30:25+00:00
- **Cohort:** UTMB MR085G WinSCAT — TRAIN: Campaign 3 (25 người); NGOÀI cohort: Campaign 1 C1G0001–3 (= tomas, yuki, noor), 10 lần test/người
- **Nguồn:** data/1_source/raw/nlsp/MR085G.zip › MR085G_Campaign_3_WinSCAT_*.csv, MR085G_Campaign_1_WinSCAT_All.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |
| `external.csv.gz` | Bảng NGOÀI cohort (cùng quy tắc, KHÔNG dùng để train) — cohort campaign_1; chấm điểm ở bước evaluate |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 195 |
| Số người/chuỗi độc lập | 25 |
| Số đặc trưng | 5 |
| Target | `math_acc_next` (%) |
| Cửa sổ | {'past': 3, 'future': 1, 'step': 1} |
| Ngoài cohort | 21 hàng, 3 người (utmb_c1:C1G0001, utmb_c1:C1G0002, utmb_c1:C1G0003) |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `cutoff_time` | thời điểm test | Ngày giờ của lần test cuối trong cửa sổ (ngày gốc — KHÔNG hiển thị, chỉ dùng thứ tự tương đối). |
| `last_value` | % | Giá trị đo cuối trong cửa sổ quá khứ. |
| `mean_all` | % | Trung bình cả cửa sổ quá khứ. |
| `std_all` | % | Độ lệch chuẩn trong cửa sổ quá khứ (độ dao động). |
| `min_all` | % | Nhỏ nhất trong cửa sổ quá khứ. |
| `max_all` | % | Lớn nhất trong cửa sổ quá khứ. |
| `math_acc_next` | % | TARGET: độ chính xác test toán lần tới. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/MR085G.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/cognition_math_acc/2026-11-14_213004`

## Giới hạn cần nhớ

- WinSCAT = Spaceflight Cognitive Assessment Tool for Windows (NASA); có hiệu ứng học (luyện tập) giữa các lần test.
- Chuỗi theo thứ tự lần test, khoảng cách giữa các lần không đều.
