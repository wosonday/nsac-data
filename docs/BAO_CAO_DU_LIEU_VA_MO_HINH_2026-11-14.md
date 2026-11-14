# Báo cáo dữ liệu và mô hình sky-ml × nsac

> Ngày 14/11/2026 · Thư mục: `D:\Project\nasa-hackathon` · Bảng chi tiết: [`docs/Tong_hop_du_lieu_mo_hinh.xlsx`](Tong_hop_du_lieu_mo_hinh.xlsx)

## 1. Tóm tắt

- **7 task đã chạy:** `hr`, `dose`, `dose_orbit`, `cpet`, `cpet_physio`, `sleep`, `sleep_act`. Mỗi task có đủ 3 nhóm dữ liệu: (1) đặc trưng, (3) mô hình, (2) dự đoán hoặc OOF.
- **Tái lập:** 5 task gốc trùng run NASA-cl ngày 11/11, sai lệch ≤ 1e-15.
- **Hai task mới:**
  - `dose_orbit`: thêm vị trí ISS lúc dự báo, giảm MAE khoảng 17%.
  - `sleep_act`: pilot giấc ngủ theo đêm cho đúng 3 persona.
- **Phủ 6 chỉ số web:**
  - nhịp tim: đã có;
  - hoạt động và giấc ngủ: có một phần;
  - huyết áp, nhiệt độ, tâm trạng: chưa có;
  - đường huyết: chỉ đủ làm thẻ mô tả.
- **Gói `NSAC_Data_Supplement` (14/11):** không đưa vào. 33 file NLSP trùng từng byte với dữ liệu đã có; OMNI làm mô hình xấu đi; các phần còn lại không phục vụ mô hình.

## 2. Dữ liệu, nguồn gốc, lý do và mục tiêu

| Task | Chỉ số web | Dữ liệu · nguồn | Lý do sử dụng | Mục tiêu dự báo |
|---|---|---|---|---|
| `hr` | Nhịp tim | MMASH 1.0.0 · PhysioNet, ODbL | Chuỗi nhịp tim theo phút liên tục, đã QA | Nhịp tim trung bình 5 phút tới (bpm) |
| `dose` | Bức xạ (ngoài 6 chỉ số) | RadLab Lidal 2022 · NASA OSDR | Liều đo thật trên ISS | Liều trung bình 1 giờ tới (uGy/h) |
| `dose_orbit` | Bức xạ | Như trên + vĩ độ, kinh độ, độ cao | Liều phụ thuộc vị trí quỹ đạo | Như trên |
| `cpet` | Thể lực (ngoài 6 chỉ số) | UTMB CFT70 · NASA NLSP | Analog chuẩn của mất thể lực khi bay dài ngày | Thay đổi VO2peak sau 70 ngày nằm giường |
| `cpet_physio` | Thể lực | Như trên, bỏ biến nhóm can thiệp | Đặc trưng mà phi hành gia thật có | Như trên |
| `sleep` | Giấc ngủ (giai đoạn) | Sleep-EDF Expanded · PhysioNet, ODC-By | EEG/EOG có nhãn chuyên gia | Giai đoạn ngủ của từng epoch 30 s (W/N1/N2/N3/REM) |
| `sleep_act` | Giấc ngủ (chất lượng) | UTMB Campaign 1 BRSMAct · NASA NLSP | 3 người C1G0001–3 = 3 persona | Hiệu suất ngủ của đêm tới (%) |

## 3. Kết quả

Kết quả là dự đoán ngoài tập huấn luyện (OOF): mỗi người hoặc mỗi tháng được dự đoán bởi một mô hình chưa từng thấy họ. CI95 tính bằng bootstrap theo đơn vị độc lập (người hoặc tháng).

| Task | Đơn vị độc lập | Mô hình triển khai | Kết quả | Baseline | Đánh giá |
|---|---|---|---|---|---|
| `hr` | 22 người | ridge | MAE 3,92 bpm (3,61–4,24); khoảng 90% bao phủ 0,900 | 4,47 | Tốt hơn baseline rõ ràng |
| `dose` | 9 tháng | lightgbm | MAE 0,769 uGy/h (0,686–0,871); bao phủ 0,898 | 2,14 | Tốt |
| `dose_orbit` | 9 tháng | lightgbm | MAE **0,637** (0,559–0,731); bao phủ 0,897 | 2,14 | Tốt hơn `dose` ở 9/9 tháng; cần kiểm lại trên năm khác |
| `cpet` | 33 người | mean_delta | ridge 2,84 (2,12–3,64), hoán vị p = 0,005 | 4,13 | Lợi thế đến từ biến nhóm can thiệp |
| `cpet_physio` | 33 người | mean_delta | 3,62 (2,66–4,75); ridge 3,67; hoán vị p = 0,51 | 4,13 | **Không mô hình nào vượt mức giảm trung bình** |
| `sleep` | 10 người | lightgbm | macro-F1 0,784 (0,760–0,807); kappa 0,777 | 0,119 | Tốt |
| `sleep_act` | 3 người | personal_mean | MAE 5,40 điểm % (4,65–5,86); khoảng 90% ±12,9 | 5,63 | ML không tốt hơn trung bình cá nhân; CI thiếu tin cậy vì chỉ 3 người |

### Cách hiểu

1. **Nhịp tim, bức xạ và giai đoạn ngủ có mô hình thực sự hữu ích.** Ba task này vượt baseline với khoảng tin cậy không chồng lên nhau.
2. **Thể lực (cpet):**
   - Mô hình ridge chỉ tốt khi biết nhóm can thiệp, mà phi hành gia thật không có biến này.
   - Khi bỏ biến nhóm, kiểm định hoán vị cho p = 0,51, tức là không phân biệt được với ngẫu nhiên.
   - Vì vậy web nên hiển thị "mức giảm trung bình của nhóm analog" kèm khoảng 90%, không phải dự báo cá nhân hóa.
3. **Giấc ngủ theo đêm (sleep_act):** với 3 người, dự báo tốt nhất là trung bình 7 đêm gần nhất của chính người đó. Đây là kết quả trung thực và vẫn đủ dùng cho persona, kèm khoảng ±12,9 điểm %.
4. **Vị trí ISS (dose_orbit):** giảm sai số khoảng 17% một cách nhất quán, phù hợp với cơ chế vật lý (liều tăng khi đi qua vùng dị thường Nam Đại Tây Dương).
   - Cấu hình được chốt sau một thí nghiệm thăm dò trên cùng các tháng test, nên kết quả có thể hơi lạc quan.

## 4. Dữ liệu cho web

| Task | Web đọc file nào | Ghi chú |
|---|---|---|
| `hr`, `dose`, `dose_orbit` | `data/4_predictions/<task>/<run>/*_latest_*.csv` | Có `prediction`, `low90`, `high90`, `abstain` |
| `cpet`, `cpet_physio`, `sleep`, `sleep_act` | `data/3_models/<task>/<run>/oof.csv.gz`, lọc theo `deploy_model` | Chưa có dữ liệu "người mới"; OOF là dữ liệu trung thực nhất để hiển thị |

**Quy tắc hiển thị:** xem `data/README.md` mục 2. Tóm tắt:
- khi `abstain` → hiển thị UNKNOWN, không hiện số;
- luôn hiện khoảng 90% kèm dự báo;
- dòng `in_sample` không được dùng làm bằng chứng độ chính xác;
- chỉ dùng ngày tương đối, không dùng ngày thật của nghiên cứu.

## 5. Đánh giá gói NSAC_Data_Supplement_20261114

| Phần | Kết luận | Căn cứ |
|---|---|---|
| NLSP actigraphy, iRATS (33 file) | Trùng | Trùng từng byte với `BRSMAct.zip`, `BEDREST_iRATS.zip` trong NASA-cl |
| Lidal 12 tháng | Không cần | Cùng 103.058 mốc và cùng giá trị; chỉ thêm `b`, `l` (cải thiện thêm khoảng 0,024 uGy/h) |
| OMNI 2022 | Không cần | MAE xấu hơn 0,017 khi thêm vào (8/9 tháng kém hơn) |
| GOES 7 ngày, quỹ đạo ISS hiện tại | Không cần cho mô hình | Snapshot 11/2026, không trùng thời gian với dữ liệu train |
| OSD-569 omics QC | Không cần | Không thuộc 6 chỉ số |
| OSD-575 CMP bản SUBMITTED | Để sau | Hữu ích cho thẻ đường huyết mô tả |

**Toàn vẹn gói:** 79/79 file khớp manifest của gói. Các script trong gói chỉ dùng thư viện chuẩn để tải về, không có thao tác nguy hiểm.

## 6. Giới hạn chung

1. **Không có dữ liệu phi hành gia thật** cho mô hình. Các nguồn đều là analog mặt đất (MMASH, Sleep-EDF, UTMB) hoặc dữ liệu thiết bị (RadLab).
2. **Không ghép người hay thời gian giữa các nguồn.** Ánh xạ persona ↔ người analog chỉ dùng để minh họa.
3. **Timestamp RadLab chưa xác minh múi giờ.**
4. **Ngưỡng QC là ngưỡng kỹ thuật.** Ví dụ HR 30–220 bpm, HRPK < 20; đây không phải ngưỡng lâm sàng.
5. **Đường huyết OSD-575 mốc R+45:** 3/4 người có giá trị 36–44 mg/dL, nghi lỗi xử lý mẫu. Đây là suy luận từ số liệu, cần đối chiếu bài gốc (Jones et al., 2024).

## 7. Đề xuất bổ sung

| Ưu tiên | Việc | Vì sao |
|---|---|---|
| Cao | Task `vitals` từ UTMB CRF (huyết áp, nhiệt độ) | Hai chỉ số web chưa có dữ liệu; CRF có đủ 6 người analog đã gán persona |
| Cao | Task `mood` từ POMS (NNX10AP86G) | Chỉ số tâm trạng chưa có dữ liệu |
| Cao | `export-nsac` (bundle v2) + `crew_map.yaml` | Một hợp đồng JSON duy nhất cho web thay vì đọc rời từng file OOF/CSV |
| Trung bình | Thẻ đường huyết mô tả từ OSD-575 | Phi hành đoàn thật, nhưng chỉ đủ để mô tả |
| Trung bình | Kiểm lại `dose_orbit` trên Lidal 2023 | Loại bỏ nghi ngờ chọn cấu hình theo tháng test |
| Trung bình | Xác minh múi giờ RadLab | Bắt buộc trước khi ghép với dữ liệu UTC |
| Trung bình | `sleep_act` cho thời lượng ngủ và độ trễ vào giấc | Chỉ cần khai báo thêm trong YAML (`measure:`) |
| Thấp | Thêm `b`, `l` vào `dose_orbit`; mở rộng `cpet` bằng iRATS; kiểm định hoán vị cho `sleep_act` | Cải thiện nhỏ hoặc để củng cố kết quả |

## 8. Tái lập

```powershell
uv run sky-ml load-data
foreach ($t in "hr","dose","dose_orbit","cpet","cpet_physio","sleep","sleep_act") {
  uv run sky-ml build-features $t; uv run sky-ml train $t; uv run sky-ml evaluate $t
}
uv run pytest -m slow     # đối chiếu với run NASA-cl 11/11 (hr, dose, cpet, sleep)
```

## Nguồn

- Rossi A, et al. MMASH 1.0.0. PhysioNet, 2020. doi:10.13026/cerq-fc86
- Kemp B, et al. *IEEE Trans Biomed Eng* 2000;47(9):1185–1194; Sleep-EDF Expanded doi:10.13026/C2X676
- Iber C, et al. *The AASM Manual for the Scoring of Sleep and Associated Events*. AASM, 2007
- NASA NTRS 20210016728 (CFT70 Aerobic Fitness, HDBR); NASA Life Sciences Portal (MR080G, MR079G, BRSMImmune, BRSMAct)
- NASA OSDR RadLab data API — https://visualization.osdr.nasa.gov/radlab/gui/data-api/
- Jones CW, et al. Molecular and physiological changes in the SpaceX Inspiration4 civilian crew. *Nature* 2024. doi:10.1038/s41586-024-07648-x
- Pollard T, et al. PhysioNet as a global platform for biomedical research. *Nature Health* 2026. doi:10.1038/s44360-026-00096-z
