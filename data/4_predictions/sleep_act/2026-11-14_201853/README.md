# (2) Dữ liệu dự đoán — `sleep_act` / run `2026-11-14_201853`

Kết quả dự báo của mô hình đã lưu (bước 5) cho một file đầu vào mới, kèm khoảng 90%, cờ từ chối dự báo (abstain) và cờ in_sample.

- **Tạo bởi:** `sky-ml predict`
- **Thời điểm (UTC):** 2026-11-14T13:45:37+00:00
- **Cohort:** UTMB Bed Rest Campaign 1 (NASA NLSP, BRSMAct) — 3 người C1G0001–3, 2 đêm trước, ~60 đêm nằm giường, 7 đêm sau
- **Nguồn:** data/1_source/raw/nlsp/BRSMAct.zip › BRSMACT_Campagin_1_Actigraphy.csv (kiểm SHA-256 + MD5 theo download_manifest.csv)

## File trong thư mục

| File | Nội dung |
|---|---|
| `sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_204537.csv` | Dự đoán (mỗi lần chạy predict một file; .json cùng tên = thông tin lần chạy) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Lần chạy mới nhất | sleep_cft70_actigraphy_latest_personal_mean_SYNTHETIC-INPUT_20261114_204537 |
| Mô hình | personal_mean |
| Chế độ | latest |
| Số hàng | 3 |
| Từ chối (abstain) | 1 |
| Trong dữ liệu huấn luyện (in_sample) | 0 |
| Nửa độ rộng khoảng 90% | 12.714 % |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | utmb_c1:C1G000x — tương ứng persona tomas-ortega / yuki-tanaka / noor-abbasi. |
| `cutoff_time` | ngày | Đêm cuối của cửa sổ 7 đêm quá khứ (ngày gốc của nghiên cứu 2004 — KHÔNG đưa lên web, chỉ dùng ngày tương đối). |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `unit` |  | Đơn vị của prediction. |
| `prediction` | % | Dự báo của mô hình đã lưu. |
| `low90` | % | Cận dưới khoảng 90% (split-conformal từ sai số OOF). |
| `high90` | % | Cận trên khoảng 90%. |
| `abstain` | bool | True = từ chối dự báo; lý do ở cột reasons. |
| `reasons` |  | missing_features | out_of_training_range | insufficient_calibration_data (phân cách ;). |
| `in_sample` | bool | True = người này nằm trong dữ liệu huấn luyện → KHÔNG phải đánh giá trên người mới. |
| `input_synthetic` | bool | True = đầu vào là DỮ LIỆU GIẢ ĐỊNH (data/1_synthetic) — dự đoán chỉ để minh họa. |

## Truy vết (lineage)

- **Mô hình:** `data/3_models/sleep_act/2026-11-14_201853/personal_mean/final.joblib`
- **Bảng đặc trưng của run:** `data/2_features/sleep_act/2026-11-14_201853/table.csv.gz`

## Giới hạn cần nhớ

- Chỉ 3 người → CI95 theo người gần như vô nghĩa; đây là pilot minh họa, không phải bằng chứng hiệu năng.
- Một số đêm có dùng thuốc ngủ (Ambien) — chưa loại, ghi nhận như yếu tố gây nhiễu.
- Actigraphy đo ngủ/thức theo cử động, không phải giai đoạn ngủ EEG (khác task sleep).
- Analog nằm giường mặt đất, không phải dữ liệu chuyến bay.
