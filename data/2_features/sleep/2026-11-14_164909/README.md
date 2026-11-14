# (1) Dữ liệu đã xử lý — đầu vào mô hình — `sleep` / run `2026-11-14_164909`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features sleep`
- **README cập nhật (UTC):** 2026-11-14T14:15:09+00:00
- **Cohort:** Sleep-EDF Expanded 1.0.0 (PhysioNet, ODC-By 1.0) — 10 bản ghi Sleep Cassette, người khỏe mạnh mặt đất, 1 đêm/người
- **Nguồn:** data/1_source/raw/sleep_edfx/1.0.0/sleep-cassette/SC4*-PSG.edf + *-Hypnogram.edf (kênh EEG Fpz-Cz, Pz-Oz, EOG ngang)

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 9913 |
| Số người/chuỗi độc lập | 10 |
| Số đặc trưng | 54 |
| Target | `stage` (None) |
| Cửa sổ | — (một hàng / người) |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã bản ghi, vd. sleep_edfx:SC400 (một đêm của một người). |
| `epoch` | epoch 30 s | Chỉ số epoch trong đêm (tính từ đầu bản ghi PSG). |
| `stage` |  | TARGET: giai đoạn ngủ do chuyên gia chấm (W, N1, N2, N3 = R&K 3+4, REM). |
| `fpz_logpow` | log µV² | Kênh fpz: log tổng năng lượng 0,5–30 Hz của epoch hiện tại. |
| `fpz_delta` | log tỷ lệ | Kênh fpz: log(năng lượng dải delta / tổng) của epoch hiện tại. |
| `fpz_theta` | log tỷ lệ | Kênh fpz: log(năng lượng dải theta / tổng) của epoch hiện tại. |
| `fpz_alpha` | log tỷ lệ | Kênh fpz: log(năng lượng dải alpha / tổng) của epoch hiện tại. |
| `fpz_sigma` | log tỷ lệ | Kênh fpz: log(năng lượng dải sigma / tổng) của epoch hiện tại. |
| `fpz_beta` | log tỷ lệ | Kênh fpz: log(năng lượng dải beta / tổng) của epoch hiện tại. |
| `pz_logpow` | log µV² | Kênh pz: log tổng năng lượng 0,5–30 Hz của epoch hiện tại. |
| `pz_delta` | log tỷ lệ | Kênh pz: log(năng lượng dải delta / tổng) của epoch hiện tại. |
| `pz_theta` | log tỷ lệ | Kênh pz: log(năng lượng dải theta / tổng) của epoch hiện tại. |
| `pz_alpha` | log tỷ lệ | Kênh pz: log(năng lượng dải alpha / tổng) của epoch hiện tại. |
| `pz_sigma` | log tỷ lệ | Kênh pz: log(năng lượng dải sigma / tổng) của epoch hiện tại. |
| `pz_beta` | log tỷ lệ | Kênh pz: log(năng lượng dải beta / tổng) của epoch hiện tại. |
| `eog_logpow` | log µV² | Kênh eog: log tổng năng lượng 0,5–30 Hz của epoch hiện tại. |
| `eog_delta` | log tỷ lệ | Kênh eog: log(năng lượng dải delta / tổng) của epoch hiện tại. |
| `eog_theta` | log tỷ lệ | Kênh eog: log(năng lượng dải theta / tổng) của epoch hiện tại. |
| `eog_alpha` | log tỷ lệ | Kênh eog: log(năng lượng dải alpha / tổng) của epoch hiện tại. |
| `eog_sigma` | log tỷ lệ | Kênh eog: log(năng lượng dải sigma / tổng) của epoch hiện tại. |
| `eog_beta` | log tỷ lệ | Kênh eog: log(năng lượng dải beta / tổng) của epoch hiện tại. |
| `fpz_logpow_prev` | như cột gốc | Kênh fpz, đặc trưng logpow của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `fpz_logpow_next` | như cột gốc | Kênh fpz, đặc trưng logpow của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `fpz_delta_prev` | như cột gốc | Kênh fpz, đặc trưng delta của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `fpz_delta_next` | như cột gốc | Kênh fpz, đặc trưng delta của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `fpz_theta_prev` | như cột gốc | Kênh fpz, đặc trưng theta của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `fpz_theta_next` | như cột gốc | Kênh fpz, đặc trưng theta của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `fpz_alpha_prev` | như cột gốc | Kênh fpz, đặc trưng alpha của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `fpz_alpha_next` | như cột gốc | Kênh fpz, đặc trưng alpha của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `fpz_sigma_prev` | như cột gốc | Kênh fpz, đặc trưng sigma của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `fpz_sigma_next` | như cột gốc | Kênh fpz, đặc trưng sigma của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `fpz_beta_prev` | như cột gốc | Kênh fpz, đặc trưng beta của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `fpz_beta_next` | như cột gốc | Kênh fpz, đặc trưng beta của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `pz_logpow_prev` | như cột gốc | Kênh pz, đặc trưng logpow của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `pz_logpow_next` | như cột gốc | Kênh pz, đặc trưng logpow của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `pz_delta_prev` | như cột gốc | Kênh pz, đặc trưng delta của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `pz_delta_next` | như cột gốc | Kênh pz, đặc trưng delta của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `pz_theta_prev` | như cột gốc | Kênh pz, đặc trưng theta của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `pz_theta_next` | như cột gốc | Kênh pz, đặc trưng theta của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `pz_alpha_prev` | như cột gốc | Kênh pz, đặc trưng alpha của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `pz_alpha_next` | như cột gốc | Kênh pz, đặc trưng alpha của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `pz_sigma_prev` | như cột gốc | Kênh pz, đặc trưng sigma của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `pz_sigma_next` | như cột gốc | Kênh pz, đặc trưng sigma của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `pz_beta_prev` | như cột gốc | Kênh pz, đặc trưng beta của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `pz_beta_next` | như cột gốc | Kênh pz, đặc trưng beta của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `eog_logpow_prev` | như cột gốc | Kênh eog, đặc trưng logpow của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `eog_logpow_next` | như cột gốc | Kênh eog, đặc trưng logpow của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `eog_delta_prev` | như cột gốc | Kênh eog, đặc trưng delta của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `eog_delta_next` | như cột gốc | Kênh eog, đặc trưng delta của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `eog_theta_prev` | như cột gốc | Kênh eog, đặc trưng theta của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `eog_theta_next` | như cột gốc | Kênh eog, đặc trưng theta của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `eog_alpha_prev` | như cột gốc | Kênh eog, đặc trưng alpha của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `eog_alpha_next` | như cột gốc | Kênh eog, đặc trưng alpha của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `eog_sigma_prev` | như cột gốc | Kênh eog, đặc trưng sigma của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `eog_sigma_next` | như cột gốc | Kênh eog, đặc trưng sigma của epoch next (trước/sau; biên đêm dùng chính epoch). |
| `eog_beta_prev` | như cột gốc | Kênh eog, đặc trưng beta của epoch prev (trước/sau; biên đêm dùng chính epoch). |
| `eog_beta_next` | như cột gốc | Kênh eog, đặc trưng beta của epoch next (trước/sau; biên đêm dùng chính epoch). |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/sleep_edfx/1.0.0/sleep-cassette/SC4*-PSG.edf, data/1_source/raw/sleep_edfx/1.0.0/sleep-cassette/SC4*-Hypnogram.edf`
- **Mô hình dùng bảng này:** `data/3_models/sleep/2026-11-14_164909`

## Giới hạn cần nhớ

- Chấm điểm HỒI CỨU (dùng cả epoch sau) — không phải dự báo thời gian thực.
- Bỏ epoch '?' và movement; giữ 30 phút thức trước/sau giấc ngủ.
- Đánh giá theo 10 người; macro-F1 nhạy với lớp hiếm N1.
