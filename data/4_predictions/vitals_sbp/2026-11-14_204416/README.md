# (2) Dữ liệu dự đoán — `vitals_sbp` / run `2026-11-14_204416`

Kết quả dự báo của mô hình đã lưu (bước 5) cho một file đầu vào mới, kèm khoảng 90%, cờ từ chối dự báo (abstain) và cờ in_sample.

- **Tạo bởi:** `sky-ml evaluate vitals_sbp`
- **Thời điểm (UTC):** 2026-11-14T13:44:21+00:00
- **Cohort:** UTMB bed rest CRF Daily Vitals — TRAIN: Campaign 3 (23 người); NGOÀI cohort: CFT70 (5160, 8072, 8936) + Campaign 1 (C1G0001–3) = 6 persona
- **Nguồn:** data/1_source/raw/nlsp/CRF.zip › */Daily_Vitals/*.csv, CFT70_VITALS/*.csv (kiểm SHA-256 + MD5)

## File trong thư mục

| File | Nội dung |
|---|---|
| `external_backtest.csv` | Dự đoán ngày-tới cho người NGOÀI cohort train (chưa từng thấy), có đáp án |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Mô hình | ridge |
| Số hàng | 431 |
| Từ chối | 6 |
| Người | 6 |
| Bao phủ khoảng 90% | 0.899 |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | utmb_c3:<id> (train) · utmb_cft70:<id> · utmb_c1:<id> (ngoài cohort). |
| `cutoff_time` | ngày | Ngày cuối của cửa sổ 7 ngày (ngày gốc của nghiên cứu — KHÔNG hiển thị trên web, chỉ dùng ngày tương đối). |
| `model` |  | Tên mô hình (khóa trong configs/tasks.yaml → models). |
| `unit` |  | Đơn vị của prediction. |
| `prediction` | mmHg | Dự báo của mô hình đã lưu. |
| `low90` | mmHg | Cận dưới khoảng 90% (split-conformal từ sai số OOF). |
| `high90` | mmHg | Cận trên khoảng 90%. |
| `abstain` | bool | True = từ chối dự báo; lý do ở cột reasons. |
| `reasons` |  | missing_features | out_of_training_range | insufficient_calibration_data (phân cách ;). |
| `in_sample` | bool | True = người này nằm trong dữ liệu huấn luyện → KHÔNG phải đánh giá trên người mới. |
| `y_true` | mmHg | Giá trị thật của target. |
| `abs_error` | mmHg | |y_true − prediction| (chỉ chế độ backtest). |

## Truy vết (lineage)

- **Mô hình:** `data/3_models/vitals_sbp/2026-11-14_204416/ridge/final.joblib`
- **Bảng ngoài cohort:** `data/2_features/vitals_sbp/2026-11-14_204416/external.csv.gz`

## Giới hạn cần nhớ

- Một lần đo/ngày (thường ~6:00), tư thế nằm đầu thấp 6° trong giai đoạn nằm giường.
- Ngưỡng kỹ thuật loại số ghi hỏng: HA tâm thu 60–250, tâm trương 30–150 mmHg, nhiệt độ 34–42 °C, mạch 30–220 bpm — KHÔNG phải ngưỡng lâm sàng.
- Campaign 1 chỉ có nhiệt độ 112/252 ngày — ngày không đo để trống, không nội suy.
- external.csv.gz + external_metrics.csv = đánh giá trên người CHƯA TỪNG THẤY (đúng 6 persona).
