# (3) Mô hình đã huấn luyện — `sleep_act` / run `2026-11-15_090339`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate sleep_act`
- **README cập nhật (UTC):** 2026-11-15T02:03:45+00:00
- **Cohort:** UTMB Bed Rest Campaign 1 (NASA NLSP, BRSMAct) — 3 người C1G0001–3, 2 đêm trước, ~60 đêm nằm giường, 7 đêm sau
- **Nguồn:** data/1_source/raw/nlsp/BRSMAct.zip › BRSMACT_Campagin_1_Actigraphy.csv (kiểm SHA-256 + MD5 theo download_manifest.csv)

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
| mae – personal_mean | 5.3991 (CI95 4.653–5.859); so baseline -0.230 |
| mae – last_value | 5.6289 (CI95 4.411–6.379); so baseline +0.000 |
| mae – ridge | 5.9025 (CI95 5.179–7.132); so baseline +0.274 |
| mae – lightgbm | 6.1706 (CI95 5.438–7.371); so baseline +0.542 |
| Mô hình triển khai (chốt trước) | personal_mean |
| Độ bao phủ khoảng 90% – personal_mean | 0.8951 (nửa độ rộng 12.857) |
| Đơn vị độc lập | 3 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | utmb_c1:C1G000x — tương ứng persona tomas-ortega / yuki-tanaka / noor-abbasi. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | % | Giá trị thật của target. |
| `y_pred` | % | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/sleep_act/2026-11-15_090339/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/sleep_act/2026-11-15_090339`

## Giới hạn cần nhớ

- Chỉ 3 người → CI95 theo người gần như vô nghĩa; đây là pilot minh họa, không phải bằng chứng hiệu năng.
- Một số đêm có dùng thuốc ngủ (Ambien) — chưa loại, ghi nhận như yếu tố gây nhiễu.
- Actigraphy đo ngủ/thức theo cử động, không phải giai đoạn ngủ EEG (khác task sleep).
- Analog nằm giường mặt đất, không phải dữ liệu chuyến bay.

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
