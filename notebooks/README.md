# notebooks/ — Notebook marimo giải thích & trực quan hóa dữ liệu sky-ml

Bộ notebook marimo giúp đọc hiểu toàn bộ dữ liệu trong repo `nsac-data`: nguồn gốc, đặc trưng, mô hình, dự đoán, dữ liệu giả định và bản đồ persona.

## Chạy

```bash
# từ thư mục gốc repo (chứa pyproject.toml)
uv sync                     # đã có sẵn thì bỏ qua; marimo nằm trong group dev
uv run marimo edit notebooks/00_tong_quan.py
uv run marimo run  notebooks/00_tong_quan.py   # chế độ "chỉ đọc", không sửa được code
```

Các notebook đọc dữ liệu theo đường dẫn tương đối từ thư mục gốc repo (hoặc thư mục của file `.py`), không cần server.

## Danh sách

| Notebook | Nội dung |
|---|---|
| `00_tong_quan.py` | Bản đồ repo: pipeline copy → features → models → predictions, số lượng task, kind, artifact |
| `01_danh_muc_catalog.py` | Khám phá `data/CATALOG.csv`: dung lượng theo task, theo kind, theo thời gian; run mới nhất mỗi task |
| `02_nguon_1_source.py` | `COPY_MANIFEST.csv`: nguồn nào được copy, hash verify thế nào, dung lượng từng file |
| `03_dac_trung_2_features.py` | Đặc trưng từng task: hình dạng bảng, mô tả, thiếu dữ liệu, phân phối target, tương quan |
| `04_mo_hinh_3_models.py` | Kết quả OOF từng task: CI95, so sánh với baseline, scatter y_true/y_pred, khoảng dự đoán 90%, test ngoài cohort |
| `05_du_doan_4_predictions.py` | File dự đoán `data/4_predictions/`: backtest ngoài cohort (vitals, cognition), dự đoán mới nhất (hr, dose, mood…) |
| `06_du_lieu_gia_dinh_1_synthetic.py` | ⚠️ DỮ LIỆU GIẢ ĐỊNH: 3 bộ sinh (mood POMS, sleep actigraphy, glucose) — tham số, hiệu chuẩn, đồ thị theo persona |
| `07_persona_crew_map.py` | Bản đồ 6 phi hành gia hư cấu → analog thật/synthetic/không có (`configs/crew_map.yaml`) |

## Quy ước bắt buộc khi đọc

- Mọi file có `is_synthetic = true` hoặc tên chứa `SYNTHETIC-INPUT` là **DỮ LIỆU GIẢ ĐỊNH** — web/hiển thị phải gắn nhãn "Dữ liệu giả định". Không dùng để train hay đánh giá mô hình.
- `dxa_regional`, `cortisol`, `inspiration4_labs` là **mô tả** (descriptive), không có mô hình.
- Khoảng tham chiếu phòng xét nghiệm KHÔNG phải ngưỡng cảnh báo; không có ngưỡng lâm sàng nào được suy ra từ các notebook này.
- Persona nsac là **hư cấu**; analog UTMB/CFT70/Campaign là dữ liệu đã khử danh cho nghiên cứu (bed rest). Không suy ra danh tính.
