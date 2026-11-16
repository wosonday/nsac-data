# (2) Dữ liệu dự đoán — `mood` / run `2026-11-15_090458`

Kết quả dự báo của mô hình đã lưu (bước 5) cho một file đầu vào mới, kèm khoảng 90%, cờ từ chối dự báo (abstain) và cờ in_sample.

- **Tạo bởi:** `sky-ml predict / evaluate mood`
- **README cập nhật (UTC):** 2026-11-15T02:07:29+00:00
- **Cohort:** UTMB CFT70 — NNX10AP86G POMS, 24 người, 13–16 lần đo/người (~hằng tuần)
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip › NNX10AP86G_CFT70_POMS_TMD.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `mood_c1_poms_latest_personal_mean_SYNTHETIC-INPUT_20261115_090729.csv` | ⚠️ Dự đoán trên DỮ LIỆU GIẢ ĐỊNH (.json cùng tên = thông tin lần chạy) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| mood_c1_poms_latest_personal_mean_SYNTHETIC-INPUT_20261115_090729 | mô hình personal_mean, chế độ latest, 3 hàng, từ chối 0, in_sample 0, đầu vào giả định 3, nửa độ rộng 90% 13.333 điểm TMD |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `cutoff_time` | ngày nghiên cứu | PRE = −BR_Day, IN = +BR_Day, POST = 70 + BR_Day. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `unit` |  | Đơn vị của prediction. |
| `prediction` | điểm TMD | Dự báo của mô hình đã lưu. |
| `low90` | điểm TMD | Cận dưới khoảng 90% (split-conformal từ sai số OOF). |
| `high90` | điểm TMD | Cận trên khoảng 90%. |
| `abstain` | bool | True = từ chối dự báo; lý do ở cột reasons. |
| `reasons` |  | Lý do từ chối, phân cách bằng dấu chấm phẩy: missing_features, out_of_training_range, insufficient_calibration_data. |
| `in_sample` | bool | True = người này nằm trong dữ liệu huấn luyện → KHÔNG phải đánh giá trên người mới. |
| `input_synthetic` | bool | True = đầu vào là DỮ LIỆU GIẢ ĐỊNH (data/1_synthetic) — dự đoán chỉ để minh họa. |

## Truy vết (lineage)

- **Mô hình:** `data/3_models/mood/2026-11-15_090458/personal_mean/final.joblib`
- **Bảng đặc trưng của run:** `data/2_features/mood/2026-11-15_090458/table.csv.gz`

## Giới hạn cần nhớ

- Thang tự đánh giá; khoảng cách giữa các lần đo không đều (PRE 7–12 ngày, IN 7 ngày).
- Có nhóm can thiệp (Treatment) — không dùng làm đặc trưng.
- 3 persona Campaign 1 KHÔNG có POMS thật → dữ liệu giả định data/1_synthetic/mood_c1_poms.csv (chỉ để minh họa).

## ⚠️ DỮ LIỆU GIẢ ĐỊNH

Thư mục này có dự đoán chạy trên **dữ liệu giả định** (`data/1_synthetic`, tên file chứa `_SYNTHETIC-INPUT`, cột `input_synthetic = True`). Kết quả chỉ để MINH HỌA; web phải gắn nhãn "Dữ liệu giả định". Mô hình vẫn được train trên dữ liệu thật.
Với đầu vào giả định: `subject_id` là persona analog theo `configs/crew_map.yaml`; `cutoff_time` có thể là lịch nhân tạo (2000-01-01 + ngày nghiên cứu), không phải ngày thật.
