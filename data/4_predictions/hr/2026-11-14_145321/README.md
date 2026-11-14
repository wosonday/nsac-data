# (2) Dữ liệu dự đoán — `hr` / run `2026-11-14_145321`

Kết quả dự báo của mô hình đã lưu (bước 5) cho một file đầu vào mới, kèm khoảng 90%, cờ từ chối dự báo (abstain) và cờ in_sample.

- **Tạo bởi:** `sky-ml predict`
- **Thời điểm (UTC):** 2026-11-14T07:54:12+00:00
- **Cohort:** MMASH 1.0.0 (PhysioNet, ODbL 1.0) — 22 nam khỏe mạnh, mặt đất, ~24 giờ/người
- **Nguồn:** data/1_source/processed/sample-v2/mmash_minutes.csv.gz (bảng phút đã QA của NASA-cl)

## File trong thư mục

| File | Nội dung |
|---|---|
| `mmash_minutes_latest_ridge_20261114_145412.csv` | Dự đoán (mỗi lần chạy predict một file; .json cùng tên = thông tin lần chạy) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Lần chạy mới nhất | mmash_minutes_latest_ridge_20261114_145412 |
| Mô hình | ridge |
| Chế độ | latest |
| Số hàng | 22 |
| Từ chối (abstain) | 9 |
| Trong dữ liệu huấn luyện (in_sample) | 22 |
| Nửa độ rộng khoảng 90% | 8.722 bpm |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `cutoff_time` | phút (tương đối) | Điểm cuối của cửa sổ quá khứ. Không phải UTC. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `unit` |  | Đơn vị của prediction. |
| `prediction` | bpm | Dự báo của mô hình đã lưu. |
| `low90` | bpm | Cận dưới khoảng 90% (split-conformal từ sai số OOF). |
| `high90` | bpm | Cận trên khoảng 90%. |
| `abstain` | bool | True = từ chối dự báo; lý do ở cột reasons. |
| `reasons` |  | missing_features | out_of_training_range | insufficient_calibration_data (phân cách ;). |
| `in_sample` | bool | True = người này nằm trong dữ liệu huấn luyện → KHÔNG phải đánh giá trên người mới. |

## Truy vết (lineage)

- **Mô hình:** `data/3_models/hr/2026-11-14_145321/ridge/final.joblib`
- **Bảng đặc trưng của run:** `data/2_features/hr/2026-11-14_145321/table.csv.gz`

## Giới hạn cần nhớ

- Proxy mặt đất, không phải dữ liệu phi hành gia.
- HR ngoài 30–220 bpm coi là thiếu (ngưỡng kỹ thuật, không phải lâm sàng); chưa lọc artifact sinh lý.
- Cửa sổ chồng lấn: số hàng ≠ số người độc lập (22).
- Thời gian là phút tương đối trong nghiên cứu, không phải UTC.
