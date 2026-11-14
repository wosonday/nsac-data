# (3) Mô hình đã huấn luyện — `cpet` / run `2026-11-14_164613`

Mô hình đã fit (joblib) + dự đoán ngoài tập huấn luyện (OOF) + kết quả đánh giá. `final` fit trên TOÀN BỘ người của bảng đặc trưng → chỉ dùng dự báo cho NGƯỜI MỚI. Điểm đánh giá luôn lấy từ OOF (mỗi người được dự đoán bởi mô hình chưa từng thấy họ).

- **Tạo bởi:** `sky-ml train/evaluate cpet`
- **Thời điểm (UTC):** 2026-11-14T09:46:52+00:00
- **Cohort:** UTMB CFT70 (NASA NLSP) — nằm giường đầu thấp 70 ngày, người khỏe mạnh mặt đất; 33/38 người đủ điều kiện
- **Nguồn:** data/1_source/raw/nlsp/MR080G.zip (+ MR079G, BRSMImmune để đối chiếu GROUP), kiểm SHA-256 + MD5 theo download_manifest.csv

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
| mae – ridge | 2.8363 (CI95 2.119–3.638); so baseline -1.289 |
| mae – lightgbm | 3.3981 (CI95 2.623–4.254); so baseline -0.727 |
| mae – mean_delta | 3.6169 (CI95 2.656–4.754); so baseline -0.508 |
| mae – persistence | 4.1253 (CI95 2.974–5.493); so baseline +0.000 |
| Kiểm định hoán vị | ridge: p = 0.0050 (200 lần) |
| Độ bao phủ khoảng 90% | 0.9091 (nửa độ rộng 6.020) |
| Đơn vị độc lập | 33 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `fold` |  | Tên fold (LOSO = subject bị giữ ra). |
| `row` |  | Chỉ số hàng trong bảng đặc trưng (truy ngược về table.csv.gz). |
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `y_true` | source_REL_VO2PK | Giá trị thật của target. |
| `y_pred` | source_REL_VO2PK | Dự đoán OOF (mô hình chưa thấy người này). |

## Truy vết (lineage)

- **Bảng đặc trưng (đầu vào):** `data/2_features/cpet/2026-11-14_164613/table.csv.gz`
- **Dự đoán từ các mô hình này:** `data/4_predictions/cpet/2026-11-14_164613`

## Giới hạn cần nhớ

- Loại 5/38 người: 4 do cờ QC CPET (HRPK < 20 hoặc sai lệch công thức VO2 > 5 %, ngưỡng kỹ thuật), 1 do GROUP mâu thuẫn giữa các bảng (ID 6546).
- Một hàng / người (33 hàng): mẫu rất nhỏ; kết quả là pilot kỹ thuật.
- group_* chỉ có trong nghiên cứu nằm giường; phi hành gia thật không có → xem task cpet_physio.
- EXERCISE gộp cả nhóm có testosterone; không diễn giải thành tác dụng nhân quả của tập luyện.
- Đơn vị REL VO2PK giữ như nguồn (suy luận mL/kg/min, chờ codebook).

## Cảnh báo bảo mật

File `.joblib` có thể chạy mã khi nạp. Chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256 theo manifest.json); không nạp file từ nguồn khác.
