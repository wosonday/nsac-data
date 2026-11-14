# (3) Mô hình đã huấn luyện — `muscle_soleus` / run `2026-11-14_212910`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate muscle_soleus`
- **README cập nhật (UTC):** 2026-11-14T14:30:25+00:00
- **Cohort:** UTMB CFT70 iRATS — MRI thể tích cơ, 27 người (gồm persona dae-jung 8072, lena 8936; KHÔNG có ayla 5160)
- **Nguồn:** data/1_source/raw/nlsp/BEDREST_iRATS.zip › BEDREST_IRATS_MRI_ULTRASOUND_CFT70_MRI_<cơ>.csv

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
| Số fold | 27 |
| Mô hình | persistence, mean_delta, ridge |
| Số file mô hình | 3 |
| mae – mean_delta | 8.1577 (CI95 6.569–9.800); so baseline -4.943 |
| mae – ridge | 8.4026 (CI95 6.839–10.090); so baseline -4.698 |
| mae – persistence | 13.1008 (CI95 9.825–16.440); so baseline +0.000 |
| Mô hình triển khai (chốt trước) | mean_delta |
| Kiểm định hoán vị | mean_delta: p = 0.9900 (200 lần) |
| Độ bao phủ khoảng 90% – mean_delta | 0.9259 (nửa độ rộng 14.228) |
| Đơn vị độc lập | 27 |

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

- **Bảng đặc trưng (đầu vào):** `data/2_features/muscle_soleus/2026-11-14_212910/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/muscle_soleus/2026-11-14_212910`

## Giới hạn cần nhớ

- Một hàng / người — pilot; nhóm tập luyện (iRATS) ảnh hưởng mạnh nhưng không dùng làm đặc trưng.
- Persona ayla (5160) và 3 persona Campaign 1 không có MRI → UNKNOWN.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
