# (1) Dữ liệu đã xử lý — đầu vào mô hình — `cpet_physio` / run `2026-11-14_164654`

Bảng mẫu sau khi chuẩn hóa và tạo đặc trưng (bước 2). Mỗi hàng là MỘT mẫu đưa vào mô hình: đặc trưng chỉ lấy từ quá khứ, target là giá trị cần dự báo. Đây là dữ liệu duy nhất bước train đọc.

- **Tạo bởi:** `sky-ml build-features cpet_physio`
- **README cập nhật (UTC):** 2026-11-14T14:30:19+00:00
- **Cohort:** UTMB CFT70 — như task cpet, 33 người
- **Nguồn:** Như task cpet; chỉ dùng pre_vo2 và age

## File trong thư mục

| File | Nội dung |
|---|---|
| `table.csv.gz` | Bảng mẫu TRAIN: subject_id, cutoff_time, đặc trưng, target |
| `features.json` | Danh sách cột mô hình được phép dùng (theo `features` trong tasks.yaml) |
| `snapshot.json` | SHA-256 file nguồn + phiên bản thư viện + seed (tái lập) |

## Số liệu chính

| Chỉ tiêu | Giá trị |
|---|---|
| Số hàng (mẫu) | 33 |
| Số người/chuỗi độc lập | 33 |
| Số đặc trưng | 2 |
| Target | `delta_vo2` (source_REL_VO2PK) |
| Cửa sổ | — (một hàng / người) |

## Cột dữ liệu

| Cột | Đơn vị | Ý nghĩa |
|---|---|---|
| `subject_id` |  | Mã người/chuỗi, có namespace nguồn (vd. mmash:user_1). Đơn vị độc lập khi chia fold. |
| `pre_vo2` | source_REL_VO2PK | VO2peak tương đối đo trước nằm giường (PRE). |
| `age` | năm | Tuổi tại PRE (nguồn MR080G). |
| `group_CONTROL` | 0/1 | Nhóm CONTROL (đã đối chiếu MR079G/BRSMImmune). Không tồn tại với phi hành gia thật. |
| `group_EXERCISE` | 0/1 | Nhóm EXERCISE (gồm cả EXERCISE + TESTOSTERONE). Không tồn tại với phi hành gia thật. |
| `group_FLY` | 0/1 | Nhóm FLY (tập luyện trên thiết bị bay). Không tồn tại với phi hành gia thật. |
| `delta_vo2` | source_REL_VO2PK | TARGET: REL VO2peak POST1 − PRE (âm = giảm thể lực hiếu khí). |

## Truy vết (lineage)

- **Dữ liệu nguồn:** `data/1_source/raw/nlsp/MR080G.zip, data/1_source/raw/nlsp/MR079G.zip, data/1_source/raw/nlsp/BRSMImmune.zip, data/1_source/raw/nlsp/download_manifest.csv`
- **Mô hình dùng bảng này:** `data/3_models/cpet_physio/2026-11-14_164654`

## Giới hạn cần nhớ

- Contract đầu vào áp dụng được cho phi hành gia (không cần nhóm can thiệp).
- Một hàng / người (33 hàng): mẫu rất nhỏ; kết quả là pilot kỹ thuật.
