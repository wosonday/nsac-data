# (3) Mô hình đã huấn luyện — `hr` / run `2026-11-14_145321`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate hr`
- **Thời điểm (UTC):** 2026-11-14T07:53:28+00:00
- **Cohort:** MMASH 1.0.0 (PhysioNet, ODbL 1.0) — 22 nam khỏe mạnh, mặt đất, ~24 giờ/người
- **Nguồn:** data/1_source/processed/sample-v2/mmash_minutes.csv.gz (bảng phút đã QA của NASA-cl)

## File trong thư mục

| File | Nội dung |
|---|---|
| `oof.csv.gz` | Dự đoán ngoài tập huấn luyện (OOF) của mọi mô hình — nguồn của mọi điểm đánh giá |
| `folds.json` | Danh sách fold và số mẫu train/test |
| `manifest.json` | SHA-256 + phiên bản + tham số |
| `<model>/final.joblib` | Mô hình fit trên toàn bộ người → chỉ dùng cho NGƯỜI MỚI |
| `metrics.csv` | Metric theo người, CI95, so baseline |
| `summary.json` | Tóm tắt + độ bao phủ khoảng 90% |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| mae – ridge | 3.9174 (CI95 3.612–4.239); so baseline -0.548 |
| mae – lightgbm | 4.0660 (CI95 3.713–4.471); so baseline -0.399 |
| mae – last_value | 4.4652 (CI95 4.086–4.872); so baseline +0.000 |
| Độ bao phủ khoảng 90% | 0.9004 (nửa độ rộng 8.714) |
| Đơn vị độc lập | 22 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | bpm | Giá trị thật của target. |
| `y_pred` | bpm | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/hr/2026-11-14_145321/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/hr/2026-11-14_145321`

## Giới hạn cần nhớ

- Proxy mặt đất, không phải dữ liệu phi hành gia.
- HR ngoài 30–220 bpm coi là thiếu (ngưỡng kỹ thuật, không phải lâm sàng); chưa lọc artifact sinh lý.
- Cửa sổ chồng lấn: số hàng ≠ số người độc lập (22).
- Thời gian là phút tương đối trong nghiên cứu, không phải UTC.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
