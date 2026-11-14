# (1) Dữ liệu đã xử lý — đầu vào mô hình — `sleep_act` / run `2026-11-14_201853`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features sleep_act`
- **Thời điểm (UTC):** 2026-11-14T13:18:53+00:00
- **Cohort:** UTMB Bed Rest Campaign 1 (NASA NLSP, BRSMAct) — 3 người C1G0001–3, 2 đêm trước, ~60 đêm nằm giường, 7 đêm sau
- **Nguồn:** data/1_source/raw/nlsp/BRSMAct.zip › BRSMACT_Campagin_1_Actigraphy.csv (kiểm SHA-256 + MD5 theo download_manifest.csv)

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 162 |
| Số người/chuỗi độc lập | 3 |
| Số đặc trưng | 6 |
| Target | `sleep_efficiency_next_night` (%) |
| Cửa sổ | {'past': 7, 'future': 1, 'step': 1} |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | utmb_c1:C1G000x — tương ứng persona tomas-ortega / yuki-tanaka / noor-abbasi. |
| `cutoff_time` | ngày | Đêm cuối của cửa sổ 7 đêm quá khứ (ngày gốc của nghiên cứu 2004 — KHÔNG đưa lên web, chỉ dùng ngày tương đối). |
| `last_value` | % | Giá trị đo cuối trong cửa sổ quá khứ. |
| `mean_last_5` | % | Trung bình 5 điểm cuối. |
| `mean_all` | % | Trung bình cả cửa sổ quá khứ. |
| `std_all` | % | Độ lệch chuẩn trong cửa sổ quá khứ (độ dao động). |
| `min_all` | % | Nhỏ nhất trong cửa sổ quá khứ. |
| `max_all` | % | Lớn nhất trong cửa sổ quá khứ. |
| `sleep_efficiency_next_night` | % | TARGET: hiệu suất ngủ (actigraphy) của đêm ngay sau cutoff. |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/BRSMAct.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/sleep_act/2026-11-14_201853`

## Giới hạn cần nhớ

- Chỉ 3 người → CI95 theo người gần như vô nghĩa; đây là pilot minh họa, không phải bằng chứng hiệu năng.
- Một số đêm có dùng thuốc ngủ (Ambien) — chưa loại, ghi nhận như yếu tố gây nhiễu.
- Actigraphy đo ngủ/thức theo cử động, không phải giai đoạn ngủ EEG (khác task sleep).
- Analog nằm giường mặt đất, không phải dữ liệu chuyến bay.
