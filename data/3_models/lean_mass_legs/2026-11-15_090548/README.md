# (3) Mô hình đã huấn luyện — `lean_mass_legs` / run `2026-11-15_090548`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate lean_mass_legs`
- **README cập nhật (UTC):** 2026-11-15T02:06:01+00:00
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
| Số fold | 18 |
| Mô hình | persistence, mean_delta, ridge |
| Số file mô hình | 3 |
| mae – persistence | 6.0049 (CI95 4.081–7.994); so baseline +0.000 |
| mae – mean_delta | 6.1155 (CI95 4.266–7.913); so baseline +0.111 |
| mae – ridge | 6.5082 (CI95 4.464–8.515); so baseline +0.503 |
| Mô hình triển khai (chốt trước) | mean_delta |
| Kiểm định hoán vị | persistence: p = 0.5224 (200 lần) |
| Độ bao phủ khoảng 90% – persistence | 0.9444 (nửa độ rộng 13.209) |
| Độ bao phủ khoảng 90% (deploy) – mean_delta | 0.9444 (nửa độ rộng 11.846) |
| Đơn vị độc lập | 18 |

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

- **Bảng đặc trưng (đầu vào):** `data/2_features/lean_mass_legs/2026-11-15_090548/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/lean_mass_legs/2026-11-15_090548`

## Giới hạn cần nhớ

- Một hàng / người — pilot; đánh giá LOSO + kiểm định hoán vị 200 lần.
- Nhóm can thiệp (tập luyện, testosterone…) ảnh hưởng mạnh nhưng KHÔNG dùng làm đặc trưng (phi hành gia thật không có nhãn này).
- Chỉ có ở 3 persona CFT70; persona Campaign 1 → UNKNOWN.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
