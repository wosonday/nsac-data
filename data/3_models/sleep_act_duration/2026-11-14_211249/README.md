# (3) Mô hình đã huấn luyện — `sleep_act_duration` / run `2026-11-14_211249`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate sleep_act_duration`
- **README cập nhật (UTC):** 2026-11-14T14:30:23+00:00
- **Cohort:** UTMB Bed Rest Campaign 1 (BRSMAct) — 3 người C1G0001–3 (= tomas, yuki, noor)
- **Nguồn:** data/1_source/raw/nlsp/BRSMAct.zip › BRSMACT_Campagin_1_Actigraphy.csv

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
| Số fold | 3 |
| Mô hình | last_value, personal_mean, ridge, lightgbm |
| Số file mô hình | 4 |
| mae – ridge | 0.3695 (CI95 0.319–0.435); so baseline -0.033 |
| mae – lightgbm | 0.3832 (CI95 0.349–0.449); so baseline -0.019 |
| mae – last_value | 0.4025 (CI95 0.315–0.469); so baseline +0.000 |
| mae – personal_mean | 0.4036 (CI95 0.372–0.428); so baseline +0.001 |
| Mô hình triển khai (chốt trước) | personal_mean |
| Độ bao phủ khoảng 90% – ridge | 0.8827 (nửa độ rộng 0.768) |
| Độ bao phủ khoảng 90% (deploy) – personal_mean | 0.9136 (nửa độ rộng 1.071) |
| Đơn vị độc lập | 3 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | giờ | Giá trị thật của target. |
| `y_pred` | giờ | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/sleep_act_duration/2026-11-14_211249/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/sleep_act_duration/2026-11-14_211249`

## Giới hạn cần nhớ

- Chỉ 3 người → pilot; có đêm dùng thuốc ngủ (Ambien).
- 3 persona CFT70 dùng dữ liệu GIẢ ĐỊNH data/1_synthetic/sleep_cft70_actigraphy.csv (cột duration).

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
