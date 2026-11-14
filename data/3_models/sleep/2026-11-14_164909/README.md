# (3) Mô hình đã huấn luyện — `sleep` / run `2026-11-14_164909`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate sleep`
- **README cập nhật (UTC):** 2026-11-14T14:15:09+00:00
- **Cohort:** Sleep-EDF Expanded 1.0.0 (PhysioNet, ODC-By 1.0) — 10 bản ghi Sleep Cassette, người khỏe mạnh mặt đất, 1 đêm/người
- **Nguồn:** data/1_source/raw/sleep_edfx/1.0.0/sleep-cassette/SC4*-PSG.edf + *-Hypnogram.edf (kênh EEG Fpz-Cz, Pz-Oz, EOG ngang)

## File trong thư mục

| File | Nội dung |
|---|---|
| `oof.csv.gz` | Dự đoán ngoài tập huấn luyện (OOF) của mọi mô hình — nguồn của mọi điểm đánh giá |
| `folds.json` | Danh sách fold và số mẫu train/test |
| `manifest.json` | SHA-256 + phiên bản + tham số |
| `<model>/final.joblib` | Mô hình fit trên toàn bộ người → chỉ dùng cho NGƯỜI MỚI |
| `metrics.csv` | Metric theo đơn vị độc lập, CI95, so baseline |
| `summary.json` | Tóm tắt: metric, độ bao phủ khoảng 90%, kiểm định hoán vị, kết quả ngoài cohort |
| `confusion.csv` | Ma trận nhầm lẫn (hàng = nhãn thật, cột = nhãn dự đoán) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số fold | 10 |
| Mô hình | majority, logistic, lightgbm |
| Số file mô hình | 3 |
| macro_f1 – lightgbm | 0.7843 (CI95 0.760–0.807); so baseline +0.666 |
| macro_f1 – logistic | 0.7598 (CI95 0.727–0.791); so baseline +0.641 |
| macro_f1 – majority | 0.1187 (CI95 0.105–0.131); so baseline +0.000 |
| Mô hình triển khai (chốt trước) | lightgbm |
| Đơn vị độc lập | 10 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Bản ghi bị giữ ra (LOSO theo đêm/người). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã bản ghi, vd. sleep_edfx:SC400 (một đêm của một người). |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` |  | Giai đoạn ngủ thật. |
| `y_pred` |  | Giai đoạn ngủ dự đoán OOF. |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/sleep/2026-11-14_164909/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/sleep/2026-11-14_164909`

## Giới hạn cần nhớ

- Chấm điểm HỒI CỨU (dùng cả epoch sau) — không phải dự báo thời gian thực.
- Bỏ epoch '?' và movement; giữ 30 phút thức trước/sau giấc ngủ.
- Đánh giá theo 10 người; macro-F1 nhạy với lớp hiếm N1.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
