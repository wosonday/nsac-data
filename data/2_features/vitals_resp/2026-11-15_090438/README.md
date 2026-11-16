# (1) Dữ liệu đã xử lý — đầu vào mô hình — `vitals_resp` / run `2026-11-15_090438`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features vitals_resp`
- **README cập nhật (UTC):** 2026-11-15T02:04:39+00:00
- **Cohort:** UTMB bed rest CRF Daily Vitals — TRAIN: Campaign 3 (23 người); NGOÀI cohort: CFT70 (5160, 8072, 8936) + Campaign 1 (C1G0001–3) = 6 persona
- **Nguồn:** data/1_source/raw/nlsp/CRF.zip › */Daily_Vitals/*.csv, CFT70_VITALS/*.csv (kiểm SHA-256 + MD5)

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |
| `external.csv.gz` | Bảng NGOÀI cohort (cùng quy tắc, KHÔNG dùng để train) — cohort cft70, campaign_1; chấm điểm ở bước evaluate |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 2256 |
| Số người/chuỗi độc lập | 23 |
| Số đặc trưng | 6 |
| Target | `resp_next_day` (lần/phút) |
| Cửa sổ | {'past': 7, 'future': 1, 'step': 1} |
| Ngoài cohort | 411 hàng, 6 người (utmb_c1:C1G0001, utmb_c1:C1G0002, utmb_c1:C1G0003, utmb_cft70:5160, utmb_cft70:8072, utmb_cft70:8936) |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | utmb_c3:<id> (train) · utmb_cft70:<id> · utmb_c1:<id> (ngoài cohort). |
| `cutoff_time` | ngày | Ngày cuối của cửa sổ 7 ngày (ngày gốc của nghiên cứu — KHÔNG hiển thị trên web, chỉ dùng ngày tương đối). |
| `last_value` | lần/phút | Giá trị đo cuối trong cửa sổ quá khứ. |
| `mean_last_5` | lần/phút | Trung bình 5 điểm cuối. |
| `mean_all` | lần/phút | Trung bình cả cửa sổ quá khứ. |
| `std_all` | lần/phút | Độ lệch chuẩn trong cửa sổ quá khứ (độ dao động). |
| `min_all` | lần/phút | Nhỏ nhất trong cửa sổ quá khứ. |
| `max_all` | lần/phút | Lớn nhất trong cửa sổ quá khứ. |
| `resp_next_day` |  | (chưa mô tả trong data_dictionary.yaml) |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/CRF.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/vitals_resp/2026-11-15_090438`

## Giới hạn cần nhớ

- Một lần đo/ngày (thường ~6:00), tư thế nằm đầu thấp 6° trong giai đoạn nằm giường.
- Ngưỡng kỹ thuật loại số ghi hỏng: HA tâm thu 60–250, tâm trương 30–150 mmHg, nhiệt độ 34–42 °C, mạch 30–220 bpm — KHÔNG phải ngưỡng lâm sàng.
- Campaign 1 chỉ có nhiệt độ 112/252 ngày — ngày không đo để trống, không nội suy.
- external.csv.gz + external_metrics.csv = đánh giá trên người CHƯA TỪNG THẤY (đúng 6 persona).
