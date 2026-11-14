# Thiết kế: `sky-ml`, pipeline dữ liệu và huấn luyện chạy trên máy cá nhân

**Ngày:** 14/11/2026. **Vị trí:** `D:\Project\nasa-hackathon\` (thư mục làm việc). Bước đầu tiên của source là **copy dữ liệu cần thiết** từ `D:\Project\NASA-cl\data\` sang `nasa-hackathon\data\` (có kiểm hash). Mọi bước sau chỉ đọc bản copy này.
**Tài liệu liên quan:** `THIET_KE_TICH_HOP_SKY_NASA-CL_x_NSAC_2026-11-14.md` (cùng thư mục), cùng KE_HOACH_TRAINING_LAI và PIPELINE_CHI_TIET_48H trong NASA-cl.

## 1. Mục đích và lý do

- **Mục đích:** có một bộ mã mới, gọn, chạy trực tiếp trên máy Windows của người dùng. Bộ mã đi từ kiểm tra dữ liệu, xử lý, huấn luyện đến đánh giá và xuất kết quả cho bốn task `cpet`, `sleep`, `hr`, `dose`.
- **Lý do:**
  - Người dùng muốn tự chạy, kiểm thử, đào sâu và tinh giản code.
  - Code NASA-cl hiện trải trên nhiều module (crawler, EDA, audit, preprocessing, pipeline) nên khó nắm toàn bộ.
  - Kết quả 11/11 còn các lỗi Y1, Y5 và `payload_examples` dự đoán trên chính dữ liệu đã học, nên chưa dùng được cho UI.
- **Thành công nghĩa là:**
  1. `uv sync` và `uv run sky-ml check` chạy được trên Windows.
  2. Mỗi bước chạy riêng được và để lại file trung gian đọc được.
  3. Chạy lại bốn task cho ra các metric trùng kết quả 11/11 trong dung sai (bằng chứng code mới không làm sai).
  4. Sau đó mới thêm cải tiến (T0, T1, OOF cho demo, phân vị phần dư).

## 2. Mục tiêu, ngoài phạm vi, điều cấm

| Loại | Nội dung |
|---|---|
| Mục tiêu | Môi trường `uv` + Python 3.12; CLI theo bước; tái lập 4 task; ghi SHA-256 dữ liệu vào mỗi run; xuất OOF, metric, phân vị phần dư, model card JSON |
| Ngoài phạm vi | Crawler, tải dữ liệu mới, xử lý MMASH raw (dùng bảng `processed/sample-v2` đã QA), SEISS, omics, nested CV và hiệu chuẩn sleep (để vòng 2), giao diện web, bundle cho nsac |
| Điều cấm | Ghi vào bất kỳ đâu trong `NASA-cl`; ghép cohort; dùng dự đoán in-sample làm kết quả; ngưỡng không có nguồn; dependency không phải OSI |

## 3. Ràng buộc

- Máy chạy là Windows. Lệnh phải chạy được trong PowerShell (WSL dùng được nhưng không bắt buộc). Đường dẫn dùng `pathlib`, không hard-code `/mnt/d`.
- Dữ liệu được copy từ NASA-cl ở bước 0 (mục 5.2), cần khoảng 680 MB trống trên ổ D: Sleep-EDF 479 MB, MMASH 123 MB, RadLab 41 MB, UTMB `nlsp` 31 MB, `sample-v2` 2,7 MB.
- Dependency (đều OSI): numpy, pandas, scipy, scikit-learn, lightgbm, mne (đọc EDF), shap, matplotlib, pytest, ruff.
- Hạn nộp hackathon là 15/11 23:59, nên cần có kết quả vòng 1 sớm.

## 4. Các cách đã cân nhắc

| Cách | Mô tả | Đánh đổi | Kết quả |
|---|---|---|---|
| A | Package gọn + bản sao dữ liệu riêng trong `nasa-hackathon` | Độc lập hoàn toàn, nhưng tốn khoảng 680 MB và có hai bản dữ liệu | Không chọn |
| **B** | **Code mới trong `nasa-hackathon`; dữ liệu lấy từ NASA-cl bằng một bước copy có kiểm hash** | Tốn khoảng 680 MB nhưng tách hẳn khỏi thay đổi về sau ở NASA-cl. Lần copy được ghi lại trong `data/COPY_MANIFEST.csv` | **Người dùng chọn** (14/11 10:45: "source ban đầu là code để copy dữ liệu trước") |
| C | Cài NASA-cl làm thư viện, chỉ viết script | Ít code nhất, nhưng muốn tinh giản thì phải sửa NASA-cl | Không chọn |

## 5. Thiết kế

### 5.1. Cây thư mục

```text
nasa-hackathon/
├── pyproject.toml          # uv, requires-python ">=3.12,<3.13", entry point sky-ml
├── .python-version         # 3.12
├── sky_ml.yaml             # đường dẫn dữ liệu NASA-cl + thư mục runs (có thể ghi đè bằng biến môi trường)
├── README.md               # lệnh PowerShell từng bước
├── data/                   # BẢN COPY từ NASA-cl (gitignored), cấu trúc giữ nguyên đường dẫn tương đối
│   ├── raw/nlsp/  raw/sleep_edfx/1.0.0/  raw/radlab/instruments/Lidal/
│   ├── processed/sample-v2/
│   └── COPY_MANIFEST.csv   # src_path, dst_path, bytes, sha256, nguồn hash (manifest NASA-cl | tính mới), copied_at
├── src/sky_ml/
│   ├── settings.py         # đọc sky_ml.yaml / env SKY_NASA_CL_DATA; chặn ghi vào NASA-cl
│   ├── copydata.py         # bước 0: danh sách file cần (allowlist) → copy → kiểm SHA-256 → COPY_MANIFEST
│   ├── datacheck.py        # bước 1: kiểm bản copy khớp COPY_MANIFEST (phát hiện file bị sửa sau copy)
│   ├── prepare/            # bước 2: một file một task, trả (table, features)
│   │   ├── cpet.py         # đọc ZIP UTMB, kiểm hash, QC HRPK/VO2, task PRE→POST1
│   │   ├── sleep.py        # EDF → epoch 30 s → công suất dải tần (mne + welch)
│   │   ├── hr.py           # sample-v2 mmash_minutes → cửa sổ 30→5 phút
│   │   ├── dose.py         # RadLab Lidal → lưới 5 phút → cửa sổ 6h→1h
│   │   └── windows.py      # make_windows dùng chung (chỉ quá khứ → tương lai)
│   ├── train.py            # bước 3: folds (LOSO / by_month) + fit mọi mô hình trên cùng fold
│   ├── evaluate.py         # bước 4: metric theo fold, CI bootstrap, so baseline, bao phủ, hoán vị
│   ├── explain.py          # bước 5: SHAP + hình 3 ô
│   ├── export.py           # bước 6: phân vị phần dư, OOF người được giữ ra, model_card.json
│   └── cli.py              # sky-ml check | prepare | train | evaluate | explain | export | run
├── tests/                  # pytest: fixture nhỏ tổng hợp + 1 test tái lập (đánh dấu slow)
└── runs/<task>/<YYYY-MM-DD_HHMMSS>/   # đầu ra, không ghi đè
    ├── snapshot.json       # SHA-256 đầu vào, phiên bản python/thư viện, seed, git rev nếu có
    ├── table.csv.gz        # bảng mẫu sau prepare (đọc được bằng Excel/pandas)
    ├── oof.csv.gz          # dự đoán ngoài tập huấn luyện
    ├── metrics.csv, summary.json, figure.png, shap_importance.csv
    └── export/residual_quantiles.csv, model_card.json, heldout_<subject>.csv
```

### 5.2. Copy dữ liệu từ NASA-cl (bước 0)

- **Ý nghĩa:** `nasa-hackathon` có bản dữ liệu riêng, cố định; các lần thử và tinh giản code không phụ thuộc NASA-cl đang thay đổi.
- `sky_ml.yaml` có khóa `nasa_cl_data = "D:/Project/NASA-cl/data"` (nguồn) và `data_dir = "data"` (đích). Biến `SKY_NASA_CL_DATA` ghi đè nguồn (tiện cho WSL `/mnt/d/...`).
- **Allowlist** (chỉ copy những gì 4 task dùng, khoảng 680 MB):

| Task | Nguồn trong `NASA-cl/data` | Ghi chú |
|---|---|---|
| cpet | `raw/nlsp/MR080G.zip` + ZIP tham chiếu GROUP mà `cpet.load_verified` đọc, `raw/nlsp/download_manifest.csv` | Danh sách ZIP chính xác lấy từ code `cpet.py` khi viết `copydata.py` |
| sleep | `raw/sleep_edfx/1.0.0/**/SC4*-PSG.edf`, `*-Hypnogram.edf`, `download_manifest.csv`, `SHA256SUMS`/license | 10 cặp PSG/hypnogram |
| hr | `processed/sample-v2/mmash_minutes.csv.gz`, `manifest.json`, `quality_report.md` | Bảng phút đã QA |
| dose | `raw/radlab/instruments/Lidal/*.csv` + sidecar | 2022 |
| chung | License/README của từng nguồn | Giữ để trích dẫn |

- **Cách copy:** chỉ đọc nguồn; ghi vào file tạm rồi đổi tên (không để file dở). Sau khi copy, tính SHA-256 và so với hash trong manifest NASA-cl nếu có. Lệch thì xóa file đích và báo lỗi. File đích đã tồn tại với hash đúng thì bỏ qua, nên chạy lại an toàn.
- `copydata.py --dry-run` in danh sách và tổng dung lượng trước khi copy.
- `datacheck.py` (bước 1) chỉ đối chiếu `data/` với `COPY_MANIFEST.csv`; `snapshot.json` của mỗi run trỏ tới hash này.
- `settings.py` từ chối mọi đường ghi nằm trong `nasa_cl_data`.

### 5.3. Các bước chạy (mỗi bước là một lệnh, có thể chạy riêng)

```powershell
uv sync                                   # môi trường
uv run sky-ml copy-data --dry-run         # 0a. xem danh sách + dung lượng sẽ copy
uv run sky-ml copy-data                   # 0b. copy NASA-cl → data/, kiểm SHA-256, ghi COPY_MANIFEST.csv
uv run sky-ml check                       # 1. bản copy còn khớp COPY_MANIFEST
uv run sky-ml prepare hr                  # 2. bảng mẫu → runs/hr/<run>/table.csv.gz
uv run sky-ml train hr --run latest       # 3. folds + mô hình → oof.csv.gz
uv run sky-ml evaluate hr --run latest    # 4. metrics.csv, summary.json
uv run sky-ml explain hr --run latest     # 5. SHAP + hình
uv run sky-ml export hr --run latest      # 6. phân vị phần dư, model card, OOF người được giữ ra
uv run sky-ml run all                     # 1→6 cho cả 4 task
```

### 5.4. Hai vòng công việc

- **Vòng 1, tái lập:** viết lại logic trùng NASA-cl (cùng mô hình, tham số, seed 17). Tiêu chí: MAE và macro-F1 trùng run 11/11 với sai lệch ≤ 1e-6 với cpet/hr/dose và ≤ 0,005 với sleep (do khác phiên bản mne/scipy có thể gây lệch nhỏ). Nếu lệch lớn hơn, dừng và tìm nguyên nhân trước khi đi tiếp.
- **Vòng 2, cải tiến** (mỗi mục có test riêng):
  - T0: snapshot hash.
  - T1: cpet có hai bộ đặc trưng, `physio_only` và `with_group`, báo cáo hai dòng; ghi phân bố lớp của sleep.
  - Thay `payload_examples` in-sample bằng `export` lấy OOF của người được giữ ra.
  - Phân vị phần dư q90/q95/q99, tính theo người rồi lấy trung vị.
  - Nested CV (T2) và hiệu chuẩn sleep (T4) chỉ làm khi còn giờ.

### 5.5. Kiểm thử

- Fixture tổng hợp nhỏ cho từng `prepare` (không cần dữ liệu thật): cửa sổ chỉ dùng quá khứ, phút thiếu không bị nội suy, mốc dose xung đột bị bỏ, nhãn N3 = stage 3+4.
- `train`: train và test không giao nhau; LOSO giữ trọn một người.
- `settings`: từ chối ghi vào NASA-cl.
- `export`: OOF xuất ra chỉ thuộc người không có trong train của fold đó.
- Test `slow` tái lập kết quả 11/11. Test này cần dữ liệu thật và chạy bằng `uv run pytest -m slow`.

## 6. Quyết định của người dùng

- Chạy và kiểm thử trên máy Windows của mình (không chạy trên máy từ xa).
- Cách B: code mới ở `nasa-hackathon`, dữ liệu lấy từ NASA-cl.
- Bước đầu tiên của source là code copy dữ liệu.

## 7. Quyết định do Claude đề xuất (người dùng có thể sửa)

1. Dùng `processed/sample-v2` cho HR thay vì xử lý lại MMASH raw. Lý do: đã QA và có manifest; xử lý raw nằm ngoài mục tiêu huấn luyện.
2. Port logic CPET (kiểm hash ZIP, QC, task) sang code mới thay vì import từ NASA-cl, để tinh giản. Chỉ giữ phần pipeline cần, bỏ phần báo cáo riêng của `cpet.py`.
3. Lưu bảng trung gian bằng CSV nén (không dùng Parquet) để mở được bằng Excel và không cần pyarrow.
4. Ghim phiên bản scikit-learn và lightgbm theo đúng run 11/11 (sklearn 1.9.1, lightgbm 4.7.0) để tái lập; Python 3.12.
5. Chưa dùng git trong `nasa-hackathon`. Đề xuất `git init` ở bước 0 để theo dõi các lần tinh giản (không push).

## 8. Để lại cho người thực hiện

- Tên lệnh con và cờ CLI chi tiết, định dạng log.
- Thứ tự viết 4 task. Đề xuất: hr → dose → cpet → sleep (từ nhẹ đến nặng; sleep cần mne và nhiều RAM nhất).

## 9. Cập nhật 14/11/2026 12:10

Các mục trên vẫn giữ hiệu lực, trừ những điểm được thay đổi dưới đây.

### 9.1. Cấu hình bằng YAML (người dùng yêu cầu, 11:09)

- `sky_ml.toml` được thay bằng `sky_ml.yaml` (khóa `nasa_cl_data, data_dir, runs_dir, tasks_config`), đọc bằng `yaml.safe_load`. Thêm dependency `pyyaml>=6.0`.
- `src/sky_ml/tasks.py` được thay bằng `configs/tasks.yaml`.
- Mô hình được khai báo trong YAML theo dạng `{class, params, scale}`, rồi dựng bằng `build_model(spec)` ở bước `train`.
- Sẽ thêm `configs/crew_map.yaml` và `configs/rules.yaml` (mục 9.3).

### 9.2. Trạng thái đã chạy trên máy người dùng

- `copy-data`: 37 file, 496,3 MB; 25 file đã đối chiếu SHA-256 với manifest của NASA-cl. `check` báo OK 37.
- `prepare hr`: 5.301 cửa sổ, 22 người. Hàng đầu `mmash:user_1` có `cutoff_time = 29` và `hr_next_5min = 94,16`, trùng run 11/11.

### 9.3. Mở rộng phạm vi: 6 chỉ số và tích hợp nsac v2

Xem chi tiết ở `THIET_KE_TICH_HOP_SKY_NASA-CL_x_NSAC_2026-11-14.md` (v2). Tóm tắt các thay đổi đối với `sky-ml`:

| Hạng mục | Nội dung |
|---|---|
| Chỉ số | Nhịp tim, huyết áp, tâm trạng, hoạt động và giấc ngủ, nhiệt độ cơ thể, đường huyết |
| Dữ liệu thêm vào allowlist | `nlsp/CRF.zip`, `NNX10AP86G.zip`, `BRSMAct.zip`, `MR010G.zip`, `MR016G.zip`, `MR085G.zip`, `osdr/clinical/OSD-575/*CMP*`. Tổng thêm khoảng 7,3 MB |
| Task mới | `vitals`: HR/SBP/DBP/nhiệt độ ngày kế tiếp; train Campaign 3 (23 người, LOSO); **external test** trên 6 người CFT70 và Campaign 1. `mood`: POMS TMD so với baseline PRE. `sleep_act`: actigraphy Campaign 1. `glucose`: serum Campaign 1 + khoảng tham chiếu OSD-575 |
| Persona | `configs/crew_map.yaml` gắn 6 phi hành gia hư cấu của nsac với 6 người analog (3 CFT70, 3 Campaign 1). Mọi chỉ số của một phi hành gia đến từ **cùng một người**. Chỉ số không có thì là UNKNOWN |
| Đầu ra mới | `sky-ml export-nsac` → `sky-bundle/v2` (`readings.jsonl`, `deviations.jsonl`, `evidence_refs.jsonl`, `crew_map.json`, `model_cards.json`, `manifest.json`) để backend TS của nsac nạp vào SQLite |
| Ràng buộc mới | Không chọn persona từ Campaign 3 (cohort huấn luyện). Bundle chỉ giữ `mission_day` tương đối, không giữ ngày thật |
