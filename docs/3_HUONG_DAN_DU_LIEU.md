# 3. Hướng dẫn dữ liệu: phân loại, tài liệu kèm, truy vết

> Cập nhật 14/11/2026. Áp dụng cho task `hr` (mô hình duy nhất đang chạy). Bảng nguồn: `docs/Du_lieu_nguon_mo_hinh_hr.xlsx`.

## 1. Mục tiêu

Mỗi file dữ liệu phải trả lời được bốn câu hỏi mà không cần đọc code: **là loại gì, do lệnh nào tạo, từ dữ liệu nào, dùng được đến đâu.** Vì vậy dữ liệu được tách thành ba nhóm theo vai trò, mỗi thư mục có `README.md` tự sinh, và mọi file được ghi vào `data/CATALOG.csv`.

## 2. Ba nhóm dữ liệu

| Nhóm | Thư mục | Ai đọc | Đọc để làm gì |
|---|---|---|---|
| (1) Dữ liệu đã xử lý | `data/2_features/<task>/<run_id>/` | bước train, người kiểm tra đặc trưng | Biết chính xác mô hình nhìn thấy gì |
| (3) Mô hình đã huấn luyện | `data/3_models/<task>/<run_id>/` | bước predict, người đánh giá | Nạp mô hình; đọc MAE, CI95, độ bao phủ |
| (2) Dữ liệu dự đoán | `data/4_predictions/<task>/<run_id>/` | nsac / bước ra quyết định | Giá trị dự báo + khoảng 90% + cờ tin cậy |

`data/1_source/` là bản copy chỉ đọc từ NASA-cl (bước 1), không thuộc ba nhóm trên.

### 2.1 (1) `2_features` — đầu vào mô hình

| File | Nội dung |
|---|---|
| `table.csv.gz` | Mỗi hàng = một mẫu: `subject_id`, `cutoff_time` (phút), 7 đặc trưng cửa sổ 30 phút, target `hr_next_5min` (bpm) |
| `features.json` | Danh sách cột mô hình được dùng (lấy từ `configs/tasks.yaml › hr.features`) |
| `snapshot.json` | SHA-256 file nguồn, phiên bản thư viện, seed → tái lập |

Ví dụ (run 14/11): 5301 hàng, 22 người. Số hàng ≠ số người độc lập vì cửa sổ chồng lấn; mọi CI tính theo **người**.

### 2.2 (3) `3_models` — mô hình

| File | Nội dung |
|---|---|
| `<model>/final.joblib` | Fit trên toàn bộ 22 người → **chỉ dùng cho người mới** |
| `manifest.json` | SHA-256 từng mô hình, tham số, đặc trưng, đường dẫn bảng đặc trưng |
| `oof.csv.gz` | Dự đoán ngoài tập huấn luyện (LOSO) — nguồn của mọi điểm đánh giá |
| `metrics.csv`, `summary.json` | MAE theo người, CI95 bootstrap, chênh lệch so baseline, độ bao phủ khoảng 90% |

Kết quả tham chiếu (khớp run NASA-cl 11/11): ridge MAE 3,917 bpm (CI95 3,61–4,24), lightgbm 4,066, last_value 4,465; độ bao phủ khoảng 90% = 0,900.

Bảo mật: `.joblib` có thể chạy mã khi nạp — chỉ nạp qua `sky_ml._artifacts.load_model` (kiểm SHA-256).

### 2.3 (2) `4_predictions` — dự đoán

Mỗi lần `predict` tạo một cặp `<input>_<mode>_<model>_<YYYYmmdd_HHMMSS>.csv/.json`. Cột: `subject_id`, `cutoff_time`, `model`, `unit`, `prediction`, `low90`, `high90`, `abstain`, `reasons` (lý do từ chối, vd. thiếu đặc trưng / ngoài miền huấn luyện), `in_sample` (+ `y_true`, `abs_error` ở chế độ `backtest`). Ý nghĩa từng cột có trong `README.md` của thư mục (lấy từ `configs/data_dictionary.yaml`).

Quy tắc diễn giải: `abstain=True` → không hiển thị số, ghi "không đủ dữ liệu"; `in_sample=True` → không phải đánh giá trên người mới, không dùng làm bằng chứng hiệu năng.

## 3. Tài liệu tự sinh

| Thành phần | Vị trí | Nguồn nội dung |
|---|---|---|
| Data card | `README.md` trong mỗi thư mục run | `_datacards.write_card` + `configs/data_dictionary.yaml` |
| Sổ cái | `data/CATALOG.csv` | `_datacards.register` |
| Từ điển cột | `configs/data_dictionary.yaml` | viết tay; sửa ở đây thì mọi README mới cập nhật theo |

Thêm task mới: khai báo `tasks.<task>` (cohort, source, caveats) và cột mới trong `data_dictionary.yaml`.

## 4. Truy vết một dự đoán (ví dụ)

1. `data/4_predictions/hr/2026-11-14_144709/README.md` → mục *Truy vết* chỉ tới `data/3_models/hr/2026-11-14_144709/ridge/final.joblib`.
2. `manifest.json` của mô hình → `features_table` = `data/2_features/hr/2026-11-14_144709/table.csv.gz`.
3. `snapshot.json` của bảng đặc trưng → SHA-256 của `data/1_source/processed/sample-v2/mmash_minutes.csv.gz`.
4. Đối chiếu SHA-256 đó với sheet `Tep_dau_vao` trong `docs/Du_lieu_nguon_mo_hinh_hr.xlsx` và nguồn gốc ở sheet `Trich_dan`.

## 5. Nguồn dữ liệu (tóm tắt từ file Excel)

| Mục | Giá trị |
|---|---|
| Bộ dữ liệu | MMASH 1.0.0, PhysioNet — 22 nam trẻ khỏe mạnh, ~24 giờ ghi liên tục (Rossi et al., 2020) |
| File mô hình đọc | `data/1_source/processed/sample-v2/mmash_minutes.csv.gz` (bảng phút đã QA của NASA-cl) |
| Giấy phép | ODbL v1.0 — phải ghi nguồn |
| Giới hạn | Proxy mặt đất, không phải phi hành gia; thời gian là phút tương đối |

Trích dẫn bắt buộc: Rossi et al. (2020) PhysioNet doi:10.13026/cerq-fc86; Rossi et al. (2020) *Data* 5(4):91 doi:10.3390/data5040091; Pollard et al. (2026) *Nature Health* doi:10.1038/s44360-026-00096-z.

File Excel **chỉ giữ phần phục vụ task hr**. Nguồn cho các task sau (UTMB vitals/POMS/glucose, Sleep-EDF, RadLab) vẫn ở file gốc `NASA-cl/docs/Du_lieu_health_monitoring_NASA_Sky.xlsx` và sẽ được thêm khi task tương ứng được xây.

## 6. Lệnh

```powershell
uv run sky-ml load-data          # → data/1_source
uv run sky-ml build-features hr  # → (1) data/2_features/hr/<run>
uv run sky-ml train hr           # → (3) data/3_models/hr/<run>
uv run sky-ml evaluate hr        # → (3) metrics.csv, summary.json
uv run sky-ml predict hr --input data/1_source/processed/sample-v2/mmash_minutes.csv.gz   # → (2) data/4_predictions/hr/<run>
```
