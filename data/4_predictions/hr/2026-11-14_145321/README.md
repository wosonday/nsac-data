# (2) Dữ liệu dự đoán — `hr` / run `2026-11-14_145321`

Kết quả dự báo của mô hình đã lưu (bước 5) cho một file đầu vào mới, kèm khoảng 90%, cờ từ chối dự báo (abstain) và cờ in_sample.

- **Tạo bởi:** `sky-ml predict / evaluate hr`
- **README cập nhật (UTC):** 2026-11-14T14:30:18+00:00
- **Cohort:** MMASH 1.0.0 (PhysioNet, ODbL 1.0) — 22 nam khỏe mạnh, mặt đất, ~24 giờ/người
- **Nguồn:** data/1_source/processed/sample-v2/mmash_minutes.csv.gz (bảng phút đã QA của NASA-cl)

## File trong thư mục

| File | Nội dung |
|---|---|
| `mmash_minutes_latest_ridge_20261114_145412.csv` | Dự đoán (.json cùng tên = thông tin lần chạy) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| mmash_minutes_latest_ridge_20261114_145412 | mô hình ridge, chế độ latest, 22 hàng, từ chối 9, in_sample 22, đầu vào giả định 0, nửa độ rộng 90% 8.722 bpm |

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
| `reasons` |  | Lý do từ chối, phân cách bằng dấu chấm phẩy: missing_features, out_of_training_range, insufficient_calibration_data. |
| `in_sample` | bool | True = người này nằm trong dữ liệu huấn luyện → KHÔNG phải đánh giá trên người mới. |

## Truy vết (lineage)

- **Mô hình:** `data/3_models/hr/2026-11-14_145321/ridge/final.joblib`
- **Bảng đặc trưng của run:** `data/2_features/hr/2026-11-14_145321/table.csv.gz`

## Giới hạn cần nhớ

- Proxy mặt đất, không phải dữ liệu phi hành gia.
- HR ngoài 30–220 bpm coi là thiếu (ngưỡng kỹ thuật, không phải lâm sàng); chưa lọc artifact sinh lý.
- Cửa sổ chồng lấn: số hàng ≠ số người độc lập (22).
- Thời gian là phút tương đối trong nghiên cứu, không phải UTC.
