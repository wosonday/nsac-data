# (3) Mô hình đã huấn luyện — `lv_mass` / run `2026-11-15_090619`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate lv_mass`
- **README cập nhật (UTC):** 2026-11-15T02:07:01+00:00
- **Cohort:** UTMB CFT70 (nằm giường 70 ngày) — người có đo PRE và ngày 70
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip (iDXA) hoặc BRSMCF.zip (siêu âm tim 3D) — xem tasks.yaml › member, value_column

## File trong thư mục

| File | Nội dung |
|---|---|
| `oof.csv.gz` | Dự đoán ngoài tập huấn luyện (OOF) của mọi mô hình — nguồn của mọi điểm đánh giá |
| `folds.json` | Danh sách fold và số mẫu train/test |
| `manifest.json` | SHA-256 + phiên bản + tham số |
| `<model>/final.joblib` | Mô hình fit trên toàn bộ người → chỉ dùng cho NGƯỜI MỚI |
| `metrics.csv` | Metric theo đơn vị độc lập, CI95, so baseline |
| `summary.json` | Tóm tắt: metric, độ bao phủ khoảng 90%, kiểm định hoán vị, kết quả ngoài cohort |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số fold | 35 |
| Mô hình | persistence, mean_delta, ridge |
| Số file mô hình | 3 |
| mae – ridge | 7.6966 (CI95 6.153–9.335); so baseline -2.005 |
| mae – mean_delta | 7.8320 (CI95 6.236–9.471); so baseline -1.870 |
| mae – persistence | 9.7018 (CI95 7.563–11.906); so baseline +0.000 |
| Mô hình triển khai (chốt trước) | mean_delta |
| Kiểm định hoán vị | ridge: p = 0.1343 (200 lần) |
| Độ bao phủ khoảng 90% – ridge | 0.9143 (nửa độ rộng 14.512) |
| Độ bao phủ khoảng 90% (deploy) – mean_delta | 0.9143 (nửa độ rộng 15.399) |
| Đơn vị độc lập | 35 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | % so với PRE | Giá trị thật của target. |
| `y_pred` | % so với PRE | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/lv_mass/2026-11-15_090619/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/lv_mass/2026-11-15_090619`

## Giới hạn cần nhớ

- Một hàng / người — pilot; đánh giá LOSO + kiểm định hoán vị 200 lần.
- Nhóm can thiệp (tập luyện, testosterone…) ảnh hưởng mạnh nhưng KHÔNG dùng làm đặc trưng (phi hành gia thật không có nhãn này).
- Chỉ có ở 3 persona CFT70; persona Campaign 1 → UNKNOWN.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
