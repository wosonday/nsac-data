# (3) Mô hình đã huấn luyện — `lipid_ldl` / run `2026-11-14_212926`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate lipid_ldl`
- **README cập nhật (UTC):** 2026-11-14T14:30:25+00:00
- **Cohort:** UTMB CFT70 NNX10AP86G lipid, 24 người, đo ngày nằm giường 14, 42, 70 (không có PRE)
- **Nguồn:** data/1_source/raw/nlsp/NNX10AP86G.zip › NNX10AP86G_CFT70_LIPIDS.csv

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
| Số fold | 24 |
| Mô hình | persistence, mean_delta, ridge |
| Số file mô hình | 3 |
| mae – ridge | 9.1343 (CI95 5.898–13.493); so baseline -0.974 |
| mae – persistence | 10.1080 (CI95 6.812–14.320); so baseline +0.000 |
| mae – mean_delta | 10.5474 (CI95 7.077–14.916); so baseline +0.439 |
| Mô hình triển khai (chốt trước) | mean_delta |
| Kiểm định hoán vị | ridge: p = 0.0100 (200 lần) |
| Độ bao phủ khoảng 90% – ridge | 0.9167 (nửa độ rộng 28.973) |
| Độ bao phủ khoảng 90% (deploy) – mean_delta | 0.9167 (nửa độ rộng 29.156) |
| Đơn vị độc lập | 24 |

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

- **Bảng đặc trưng (đầu vào):** `data/2_features/lipid_ldl/2026-11-14_212926/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/lipid_ldl/2026-11-14_212926`

## Giới hạn cần nhớ

- Baseline là ngày 14 TRONG nằm giường, không phải trước nằm giường.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
