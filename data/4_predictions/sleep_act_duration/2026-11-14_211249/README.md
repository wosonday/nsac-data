# (2) Dữ liệu dự đoán — `sleep_act_duration` / run `2026-11-14_211249`

Kết quả dự báo của mô hình đã lưu (bước 5) cho một file đầu vào mới, kèm khoảng 90%, cờ từ chối dự báo (abstain) và cờ in_sample.

- **Tạo bởi:** `sky-ml predict / evaluate sleep_act_duration`
- **README cập nhật (UTC):** 2026-11-14T14:30:23+00:00
- **Cohort:** UTMB Bed Rest Campaign 1 (BRSMAct) — 3 người C1G0001–3 (= tomas, yuki, noor)
- **Nguồn:** data/1_source/raw/nlsp/BRSMAct.zip › BRSMACT_Campagin_1_Actigraphy.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_211431.csv` | ⚠️ Dự đoán trên DỮ LIỆU GIẢ ĐỊNH (.json cùng tên = thông tin lần chạy) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_211431 | mô hình personal_mean, chế độ latest, 3 hàng, từ chối 1, in_sample 0, đầu vào giả định 3, nửa độ rộng 90% 1.071 giờ |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `cutoff_time` | phút (tương đối) | Điểm cuối của cửa sổ quá khứ. Không phải UTC. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `unit` |  | Đơn vị của prediction. |
| `prediction` | giờ | Dự báo của mô hình đã lưu. |
| `low90` | giờ | Cận dưới khoảng 90% (split-conformal từ sai số OOF). |
| `high90` | giờ | Cận trên khoảng 90%. |
| `abstain` | bool | True = từ chối dự báo; lý do ở cột reasons. |
| `reasons` |  | Lý do từ chối, phân cách bằng dấu chấm phẩy: missing_features, out_of_training_range, insufficient_calibration_data. |
| `in_sample` | bool | True = người này nằm trong dữ liệu huấn luyện → KHÔNG phải đánh giá trên người mới. |
| `input_synthetic` | bool | True = đầu vào là DỮ LIỆU GIẢ ĐỊNH (data/1_synthetic) — dự đoán chỉ để minh họa. |

## Truy vết (lineage)

- **Mô hình:** `data/3_models/sleep_act_duration/2026-11-14_211249/personal_mean/final.joblib`
- **Bảng đặc trưng của run:** `data/2_features/sleep_act_duration/2026-11-14_211249/table.csv.gz`

## Giới hạn cần nhớ

- Chỉ 3 người → pilot; có đêm dùng thuốc ngủ (Ambien).
- 3 persona CFT70 dùng dữ liệu GIẢ ĐỊNH data/1_synthetic/sleep_cft70_actigraphy.csv (cột duration).

## ⚠️ DỮ LIỆU GIẢ ĐỊNH

Thư mục này có dự đoán chạy trên **dữ liệu giả định** (`data/1_synthetic`, tên file chứa `_SYNTHETIC-INPUT`, cột `input_synthetic = True`). Kết quả chỉ để MINH HỌA; web phải gắn nhãn "Dữ liệu giả định". Mô hình vẫn được train trên dữ liệu thật.
Với đầu vào giả định: `subject_id` là persona analog theo `configs/crew_map.yaml`; `cutoff_time` có thể là lịch nhân tạo (2000-01-01 + ngày nghiên cứu), không phải ngày thật.
