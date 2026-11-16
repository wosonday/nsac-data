# (3) Mô hình đã huấn luyện — `glucose` / run `2026-11-15_090515`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate glucose`
- **README cập nhật (UTC):** 2026-11-15T02:05:45+00:00
- **Cohort:** UTMB CFT70 — NNX10AP86G OGTT, 23 người đủ dữ liệu PRE + ngày nằm giường 66
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip › NNX10AP86G_CFT70_OGTT.csv (phút 0 = lúc đói; 30–120 = sau uống glucose)

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
| Số fold | 23 |
| Mô hình | persistence, mean_delta, ridge |
| Số file mô hình | 3 |
| mae – ridge | 2.9797 (CI95 2.032–4.030); so baseline -0.317 |
| mae – persistence | 3.2971 (CI95 2.159–4.590); so baseline +0.000 |
| mae – mean_delta | 3.3348 (CI95 2.158–4.691); so baseline +0.038 |
| Mô hình triển khai (chốt trước) | mean_delta |
| Kiểm định hoán vị | ridge: p = 0.0149 (200 lần) |
| Độ bao phủ khoảng 90% – ridge | 0.9130 (nửa độ rộng 7.531) |
| Độ bao phủ khoảng 90% (deploy) – mean_delta | 0.9130 (nửa độ rộng 8.958) |
| Đơn vị độc lập | 23 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | mg/dL | Giá trị thật của target. |
| `y_pred` | mg/dL | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/glucose/2026-11-15_090515/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/glucose/2026-11-15_090515`

## Giới hạn cần nhớ

- Một hàng / người (23 hàng) — pilot. OGTT là nghiệm pháp tại phòng thí nghiệm, không phải CGM.
- Đường huyết hằng ngày của persona trên web là DỮ LIỆU GIẢ ĐỊNH (data/1_synthetic/glucose_daily_personas.csv), neo vào giá trị OGTT thật với CFT70.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
