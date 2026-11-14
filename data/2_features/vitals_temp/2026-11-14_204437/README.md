# (1) Dữ liệu đã xử lý — đầu vào mô hình — `vitals_temp` / run `2026-11-14_204437`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features vitals_temp`
- **Thời điểm (UTC):** 2026-11-14T13:44:37+00:00
- **Cohort:** UTMB bed rest CRF Daily Vitals — TRAIN: Campaign 3 (23 người); NGOÀI cohort: CFT70 (5160, 8072, 8936) + Campaign 1 (C1G0001–3) = 6 persona
- **Nguồn:** data/1_source/raw/nlsp/CRF.zip › */Daily_Vitals/*.csv, CFT70_VITALS/*.csv (kiểm SHA-256 + MD5)

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 2272 |
| Số người/chuỗi độc lập | 23 |
| Số đặc trưng | 6 |
| Target | `temp_next_day` (°C) |
| Cửa sổ | {'past': 7, 'future': 1, 'step': 1} |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | utmb_c3:<id> (train) · utmb_cft70:<id> · utmb_c1:<id> (ngoài cohort). |
| `cutoff_time` | ngày | Ngày cuối của cửa sổ 7 ngày (ngày gốc của nghiên cứu — KHÔNG hiển thị trên web, chỉ dùng ngày tương đối). |
| `last_value` | °C | Giá trị đo cuối trong cửa sổ quá khứ. |
| `mean_last_5` | °C | Trung bình 5 điểm cuối. |
| `mean_all` | °C | Trung bình cả cửa sổ quá khứ. |
| `std_all` | °C | Độ lệch chuẩn trong cửa sổ quá khứ (độ dao động). |
| `min_all` | °C | Nhỏ nhất trong cửa sổ quá khứ. |
| `max_all` | °C | Lớn nhất trong cửa sổ quá khứ. |
| `temp_next_day` | °C | TARGET: nhiệt độ cơ thể buổi sáng ngày hôm sau. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/CRF.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/vitals_temp/2026-11-14_204437`

## Giới hạn cần nhớ

- Một lần đo/ngày (thường ~6:00), tư thế nằm đầu thấp 6° trong giai đoạn nằm giường.
- Ngưỡng kỹ thuật loại số ghi hỏng: HA tâm thu 60–250, tâm trương 30–150 mmHg, nhiệt độ 34–42 °C, mạch 30–220 bpm — KHÔNG phải ngưỡng lâm sàng.
- Campaign 1 chỉ có nhiệt độ 112/252 ngày — ngày không đo để trống, không nội suy.
- external.csv.gz + external_metrics.csv = đánh giá trên người CHƯA TỪNG THẤY (đúng 6 persona).
