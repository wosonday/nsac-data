# (2) Dữ liệu dự đoán — `cognition_math_acc` / run `2026-11-14_213004`

Kết quả dự báo của mô hình đã lưu (bước 5) cho một file đầu vào mới, kèm khoảng 90%, cờ từ chối dự báo (abstain) và cờ in_sample.

- **Tạo bởi:** `sky-ml predict / evaluate cognition_math_acc`
- **README cập nhật (UTC):** 2026-11-14T14:30:26+00:00
- **Cohort:** UTMB MR085G WinSCAT — TRAIN: Campaign 3 (25 người); NGOÀI cohort: Campaign 1 C1G0001–3 (= tomas, yuki, noor), 10 lần test/người
- **Nguồn:** data/1_source/raw/nlsp/MR085G.zip › MR085G_Campaign_3_WinSCAT_*.csv, MR085G_Campaign_1_WinSCAT_All.csv

## File trong thư mục

| File | Nội dung |
|---|---|
| `external_backtest.csv` | Dự đoán ngày tới cho người NGOÀI cohort train (chưa từng thấy), có đáp án `y_true` |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| external_backtest – người | 3 (utmb_c1:C1G0001, utmb_c1:C1G0002, utmb_c1:C1G0003) |
| external_backtest – hàng / từ chối | 21 / 0 |
| external_backtest – MAE gộp mọi hàng / bao phủ 90% | 6.825 / 0.952 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `cutoff_time` | thời điểm test | Ngày giờ của lần test cuối trong cửa sổ (ngày gốc — KHÔNG hiển thị, chỉ dùng thứ tự tương đối). |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `unit` |  | Đơn vị của prediction. |
| `prediction` | % | Dự báo của mô hình đã lưu. |
| `low90` | % | Cận dưới khoảng 90% (split-conformal từ sai số OOF). |
| `high90` | % | Cận trên khoảng 90%. |
| `abstain` | bool | True = từ chối dự báo; lý do ở cột reasons. |
| `reasons` |  | Lý do từ chối, phân cách bằng dấu chấm phẩy: missing_features, out_of_training_range, insufficient_calibration_data. |
| `in_sample` | bool | True = người này nằm trong dữ liệu huấn luyện → KHÔNG phải đánh giá trên người mới. |
| `y_true` | % | Giá trị thật của target. |
| `abs_error` | % | |y_true − prediction| (chỉ chế độ backtest). |

## Truy vết (lineage)

- **Mô hình:** `data/3_models/cognition_math_acc/2026-11-14_213004/personal_mean/final.joblib`
- **Bảng đặc trưng của run:** `data/2_features/cognition_math_acc/2026-11-14_213004/table.csv.gz`

## Giới hạn cần nhớ

- WinSCAT = Spaceflight Cognitive Assessment Tool for Windows (NASA); có hiệu ứng học (luyện tập) giữa các lần test.
- Chuỗi theo thứ tự lần test, khoảng cách giữa các lần không đều.
