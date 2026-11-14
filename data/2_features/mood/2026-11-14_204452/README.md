# (1) Dữ liệu đã xử lý — đầu vào mô hình — `mood` / run `2026-11-14_204452`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features mood`
- **Thời điểm (UTC):** 2026-11-14T13:44:52+00:00
- **Cohort:** UTMB CFT70 — NNX10AP86G POMS, 24 người, 13–16 lần đo/người (~hằng tuần)
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip › NNX10AP86G_CFT70_POMS_TMD.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 292 |
| Số người/chuỗi độc lập | 24 |
| Số đặc trưng | 5 |
| Target | `tmd_next` (điểm TMD) |
| Cửa sổ | {'past': 3, 'future': 1, 'step': 1} |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `cutoff_time` | ngày nghiên cứu | PRE = −BR_Day, IN = +BR_Day, POST = 70 + BR_Day. |
| `last_value` | điểm TMD | Giá trị đo cuối trong cửa sổ quá khứ. |
| `mean_all` | điểm TMD | Trung bình cả cửa sổ quá khứ. |
| `std_all` | điểm TMD | Độ lệch chuẩn trong cửa sổ quá khứ (độ dao động). |
| `min_all` | điểm TMD | Nhỏ nhất trong cửa sổ quá khứ. |
| `max_all` | điểm TMD | Lớn nhất trong cửa sổ quá khứ. |
| `tmd_next` | điểm TMD | TARGET: POMS Total Mood Disturbance của lần đo tới (cao hơn = rối loạn tâm trạng nhiều hơn). |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/NNX10AP86G.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/mood/2026-11-14_204452`

## Giới hạn cần nhớ

- Thang tự đánh giá; khoảng cách giữa các lần đo không đều (PRE 7–12 ngày, IN 7 ngày).
- Có nhóm can thiệp (Treatment) — không dùng làm đặc trưng.
- 3 persona Campaign 1 KHÔNG có POMS thật → dữ liệu giả định data/1_synthetic/mood_c1_poms.csv (chỉ để minh họa).
