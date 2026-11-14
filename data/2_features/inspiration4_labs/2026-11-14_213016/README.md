# (1) Dữ liệu đã xử lý — đầu vào mô hình — `inspiration4_labs` / run `2026-11-14_213016`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features inspiration4_labs`
- **README cập nhật (UTC):** 2026-11-14T14:30:26+00:00
- **Cohort:** Inspiration4 (SpaceX, 2021) — 4 phi hành đoàn dân sự THẬT, bay 3 ngày; mẫu L-92, L-44, L-3, R+1, R+45, R+82, R+194
- **Nguồn:** data/1_source/raw/osdr/clinical/OSD-569 (CBC), OSD-575 (CMP, Eve tim mạch, Eve miễn dịch) — bản TRANSFORMED

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng MÔ TẢ dữ liệu thật (không có mô hình) — dùng hiển thị trực tiếp |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng | 3268 |
| Số người | 4 |
| Loại | MÔ TẢ — không train/evaluate |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `panel` |  | Bảng xét nghiệm nguồn. |
| `subject_id` |  | i4:C00x — mã phi hành đoàn Inspiration4 (KHÔNG phải persona nsac). |
| `timepoint` |  | L-n = n ngày trước phóng; R+n = n ngày sau hạ cánh. |
| `phase` |  | (chưa mô tả trong data_dictionary.yaml) |
| `relative_day` | ngày | Số ngày tương đối (âm = trước phóng, dương = sau hạ cánh). |
| `analyte` |  | Tên chất xét nghiệm (theo nguồn). |
| `unit` |  | Đơn vị của prediction. |
| `value` | cột unit | Giá trị đo. |
| `range_min` | cột unit | Cận dưới khoảng tham chiếu của PHÒNG XÉT NGHIỆM (không phải ngưỡng cảnh báo). |
| `range_max` | cột unit | Cận trên khoảng tham chiếu của phòng xét nghiệm. |
| `out_of_range` | bool | Ngoài khoảng tham chiếu nguồn (chỉ mô tả; rỗng nếu analyte không có khoảng). |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/osdr/clinical/OSD-569/LSDS-7_Complete_Blood_Count_CBC_TRANSFORMED.csv, data/1_source/raw/osdr/clinical/OSD-575/LSDS-8_Comprehensive_Metabolic_Panel_CMP_TRANSFORMED.csv, data/1_source/raw/osdr/clinical/OSD-575/LSDS-8_Multiplex_serum_cardiovascular_EvePanel_TRANSFORMED.csv, data/1_source/raw/osdr/clinical/OSD-575/LSDS-8_Multiplex_serum_immune_EvePanel_TRANSFORMED.csv`
- **Mô hình dùng bảng này:** `data/3_models/inspiration4_labs/2026-11-14_213016`

## Giới hạn cần nhớ

- Bảng MÔ TẢ — 4 người, không train mô hình.
- Glucose R+45: 3/4 người 36–44 mg/dL, thấp bất thường so với mọi mốc khác → nghi lỗi tiền phân tích, cần gắn cờ khi hiển thị.
- Khoảng tham chiếu của phòng xét nghiệm KHÔNG phải ngưỡng cảnh báo cho phi hành gia.
