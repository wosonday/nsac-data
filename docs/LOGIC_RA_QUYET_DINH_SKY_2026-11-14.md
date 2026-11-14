# Logic ra quyết định của Sky cho 6 chỉ số sức khỏe

**Ngày lập:** 14/11/2026, 12:30 (Asia/Bangkok).

**Bổ sung cho:**
- `THIET_KE_TICH_HOP_SKY_NASA-CL_x_NSAC_2026-11-14.md` (v2), mục 4–5;
- spec `docs/superpowers/specs/2026-11-14-sky-ml-design.md`, mục 9.

**Phạm vi:** nhịp tim, huyết áp, tâm trạng, hoạt động và giấc ngủ, nhiệt độ cơ thể, đường huyết.

**Nguyên tắc nền** (hard rule 3 và 4 của nsac):
- Quyết định do **luật tất định** đưa ra.
- Mô hình ML chỉ cung cấp *vùng kỳ vọng*. LLM chỉ diễn giải.
- Phi hành gia phải xác nhận mọi hành động.
- Mọi ngưỡng có `rule_id`, nhãn bằng chứng và nguồn.

**Nhãn bằng chứng:**

| Nhãn | Nghĩa |
|---|---|
| `[NASA-STD]` | Yêu cầu trong NASA-STD-3001 |
| `[GUIDELINE]` | Hướng dẫn lâm sàng trên Trái Đất (phải ghi tài liệu) |
| `[STUDY]` | Số liệu đo được trong một nghiên cứu hoặc xét nghiệm có nguồn |
| `[LOCAL]` | Tính từ dữ liệu của dự án |
| `[HEURISTIC]` | Nhóm tự đặt, phải ghi rõ là heuristic |

---

## 1. Vì sao cần "dữ liệu đủ cấu trúc để ra quyết định"

**Ý nghĩa.** Một con số đơn lẻ, ví dụ "nhiệt độ 37,5 °C", chưa đủ để kết luận. Muốn quyết định đúng, hệ thống phải biết thêm: số đó của ai, đo lúc nào trong nhiệm vụ, so với mức bình thường của chính người đó là bao nhiêu, đo bằng gì, có tin được không, và còn mới không.

**Nguyên nhân.** Các bảng nguồn (UTMB CRF, POMS, actigraphy, xét nghiệm) có:
- header khác nhau giữa các file;
- giá trị kèm ký hiệu, ví dụ `"73  (L)"`, `"138A  (H)"`, `"84B"`;
- thời lượng dạng `7:44:00`;
- ngày đếm lại từ đầu trong mỗi giai đoạn (`BR_Day`);
- ô `NA`.

Nếu đưa thẳng vào luật, hệ thống sẽ cảnh báo sai hoặc bỏ sót.

**Mục tiêu.** Mọi bản ghi đi vào bộ quyết định phải đạt **hợp đồng "decision-ready"** (mục 1.1) và vượt qua **cổng đủ dữ liệu** (mục 1.3). Không đạt thì kết quả là `UNKNOWN`, `STALE` hoặc `INVALID`, không bao giờ là màu xanh.

### 1.1. Hợp đồng bản ghi decision-ready

| Trường | Bắt buộc | Ví dụ | Dùng trong quyết định để |
|---|---|---|---|
| `astronaut_id` | ✓ | `ayla-reyes` | Biết baseline và lịch sử của ai |
| `cohort_ref` | ✓ | `utmb_cft70:5160` | Truy vết nguồn; chặn ghép dữ liệu giữa các cohort |
| `metric` | ✓ | `body_temp` | Chọn bộ luật tương ứng |
| `value` | ✓ | `37.5` | Giá trị đã chuẩn hóa sang đơn vị chuẩn |
| `unit` | ✓ | `°C` | Kiểm tra đơn vị trước khi so ngưỡng |
| `raw_value` | ✓ | `"37.5"`, `"73  (L)"` | Giữ nguyên bản gốc để kiểm toán |
| `phase` | ✓ | `pre` / `in` / `post` | Baseline lấy từ `pre`; luật hậu hạ cánh chỉ áp ở `post` |
| `mission_day` | ✓ | `9` | Trục thời gian liên tục; tính độ mới, chuỗi liên tiếp, xu hướng |
| `measured_at` | khuyến nghị | `07:40` | Phân biệt đo sáng hay tối (nhiệt độ, HR có nhịp ngày đêm) |
| `context` | khuyến nghị | `{"fasting": null, "posture": "supine"}` | Diễn giải đúng (glucose lúc đói hay không; tư thế khi đo HA) |
| `quality_flags` | ✓ (có thể rỗng) | `["source_flag_L"]`, `["converted_from_F"]` | Cổng hợp lệ; cờ của phòng xét nghiệm |
| `data_origin` | ✓ | `human_analog` | Hiển thị và giới hạn tuyên bố |
| `source_sha256` | ✓ | `…` | Tái lập |

### 1.2. Bảng trạng thái dữ liệu (đầu ra trước mọi luật màu)

| Trạng thái | Điều kiện | Hiển thị | Được tô màu? |
|---|---|---|---|
| `INVALID` | Ngoài miền kỹ thuật (mục 1.3) hoặc không parse được | "Số đo không hợp lệ" + giá trị gốc | Không |
| `UNKNOWN` | Người này không có dữ liệu cho chỉ số đó | "Chưa có dữ liệu" | Không |
| `INSUFFICIENT_BASELINE` | Có số đo nhưng baseline PRE chưa đủ số điểm | Giá trị + "chưa đủ baseline" | Chỉ được dùng luật tuyệt đối |
| `STALE` | Lần đo cuối cũ hơn ngưỡng độ mới | Giá trị cũ + tuổi dữ liệu | Không (nhắc đo lại) |
| `OK` | Vượt mọi cổng | Đánh giá đầy đủ | Có |

### 1.3. Cổng đủ dữ liệu theo chỉ số

Đây là tham số kỹ thuật `[HEURISTIC]`, đặt theo tần suất đo thực tế của dữ liệu UTMB. Đây **không phải** ngưỡng lâm sàng.

| Chỉ số | Miền kỹ thuật hợp lệ | Baseline tối thiểu (điểm PRE) | Hạn độ mới | Sàn độ phân tán (MAD floor) |
|---|---|---|---|---|
| Nhịp tim (`hr_rest`) | 30–220 bpm | 5 | 2 ngày | 3 bpm |
| Huyết áp (`bp_systolic`/`bp_diastolic`) | 60–260 / 30–160 mmHg | 5 | 2 ngày | 4 mmHg |
| Nhiệt độ (`body_temp`) | 33–43 °C | 5 | 2 ngày | 0,2 °C |
| Tâm trạng (`mood_tmd`) | −32 đến 200 (miền điểm POMS) | 3 | 10 ngày (POMS đo khoảng mỗi tuần) | SD sàn 3 điểm |
| Giấc ngủ (`sleep_hours`, `sleep_efficiency`) | 0–16 h; 0–100 % | 3 đêm | 2 đêm | 0,25 h; 2 % |
| Đường huyết (`glucose_serum`) | 20–600 mg/dL | Không dùng baseline cá nhân (quá ít mẫu) | 30 ngày | — |

**Vì sao cần sàn MAD (ví dụ thật).** Với đối tượng CFT70 5160, nhiệt độ PRE có trung vị 36,4 °C và **MAD chỉ 0,1 °C**. Ngày IN 9 đo được 37,5 °C, cho modified z = 7,42. Theo luật nsac hiện tại (|z| ≥ 5), lần đo này đã là **đỏ**. Thực tế 37,5 °C vẫn chưa tới mức sốt thông dụng (38,0 °C). Sàn MAD 0,2 °C đưa z về khoảng 3,7, tức vàng, và luật hợp nhất ở mục 2.4 giữ mức đó cho tới khi có số đo xác nhận.

---

## 2. Pipeline ra quyết định (8 bước tất định)

```text
Reading ──► [G0] Hợp lệ? ──► [G1] Đủ dữ liệu / còn mới? ──► (UNKNOWN | INVALID | STALE | INSUFFICIENT_BASELINE)
                │ OK
                ▼
   ┌────────────┬──────────────────────┬─────────────────────────┐
   │ [E1] Tương đối:                    │ [E2] Tuyệt đối:          │ [E3] Mô hình:
   │ z so với baseline PRE              │ ngưỡng có nguồn          │ ngoài dải kỳ vọng 90%?
   │ (median/MAD, có sàn)               │ (GUIDELINE/STUDY/…)      │ phần dư > q95/q99 (LOCAL)
   └────────────┴──────────────────────┴─────────────────────────┘
                ▼
          [F] Hợp nhất (mục 2.4) ──► mức đơn lẻ: green / yellow / red
                ▼
          [P] Bền vững theo thời gian: lặp lại? xu hướng? (mục 2.5)
                ▼
          [X] Luật kết hợp nhiều chỉ số (mục 4)
                ▼
          [A] Chọn MỘT hành động theo thứ tự ưu tiên (mục 5)
                ▼
          [C] Phi hành gia xác nhận / từ chối ──► [L] Nhật ký kiểm toán + báo cáo mặt đất (trễ 20 phút)
```

### 2.1. E1: Lệch so với baseline cá nhân

```text
baseline_median = median(giá trị PRE của chính người đó)
baseline_mad    = max(median(|x − baseline_median|), MAD_floor[metric])
z_rel           = 0.6745 × (x − baseline_median) / baseline_mad
```

- **Ý nghĩa:** "mỗi người là đối chứng của chính mình". Hệ số 0,6745 đưa MAD về thang tương đương độ lệch chuẩn khi dữ liệu xấp xỉ phân phối chuẩn (modified z-score). Cách tính này giống `detection.py` hoặc `detection.ts` của nsac, chỉ thêm sàn MAD.
- **Mức:** |z_rel| ≥ 3 cho vàng, ≥ 5 cho đỏ. Đây là ngưỡng sản phẩm `[HEURISTIC]` đã có trong nsac (`BASE-MAD-Y`, `BASE-MAD-R`).
- **Chiều có hại:** chỉ cảnh báo theo chiều nguy hiểm khi chỉ số có chiều rõ ràng:
  - nhiệt độ: chỉ chiều tăng;
  - giấc ngủ: chỉ chiều giảm;
  - tâm trạng TMD: chỉ chiều tăng (xáo trộn nhiều hơn);
  - nhịp tim, huyết áp: cả hai chiều.

### 2.2. E2: Ngưỡng tuyệt đối có nguồn

Xem bảng của từng chỉ số ở mục 3. Ngưỡng tuyệt đối được dùng ngay cả khi `INSUFFICIENT_BASELINE`, vì nó không cần lịch sử cá nhân.

### 2.3. E3: Bằng chứng từ mô hình

- Mô hình `vitals` được huấn luyện trên Campaign 3 và kiểm định ngoài cohort. Nó cho dải kỳ vọng `[low90, high90]` của **ngày kế tiếp**.
- Phần dư chuẩn hóa `r` được so với q95 và q99. Các phân vị này lấy từ phần dư LOSO trên Campaign 3, tính theo người rồi lấy trung vị, nhãn `[LOCAL]`.
- **E3 không bao giờ tự tạo màu đỏ.** Lý do: mô hình được kiểm định trên cohort analog, chưa có bằng chứng trên phi hành gia. E3 chỉ (a) tạo vàng, hoặc (b) xác nhận cho E1/E2 khi cùng chiều.

### 2.4. F: Luật hợp nhất

| E1 (tương đối) | E2 (tuyệt đối) | E3 (mô hình) | Mức đơn lẻ | Ghi chú |
|---|---|---|---|---|
| bất kỳ | **red** (`GUIDELINE`/`NASA-STD`) | bất kỳ | **red** | Ngưỡng có nguồn mạnh nhất thắng |
| red | yellow / green | cùng chiều ngoài dải | **red** | Hai nguồn độc lập đồng ý |
| red | green | trong dải hoặc không có | **yellow** + `needs_confirmation` | Chỉ lệch so với chính mình, chưa có xác nhận → đo lại |
| yellow | bất kỳ ≤ yellow | bất kỳ | yellow | |
| green | yellow | bất kỳ | yellow | |
| green | green | ngoài dải (q95) | yellow | Mô hình chỉ được tạo vàng |
| green | green | trong dải | green | |

**Giới hạn theo nhãn:**
- `[STUDY]` có `n < 5` không được tự tạo đỏ (luật `STUDY-NSMALL`).
- `[HEURISTIC]` đứng một mình tối đa là vàng.

### 2.5. P: Bền vững theo thời gian

| Luật | Điều kiện | Kết quả |
|---|---|---|
| `PERSIST-RED` | Đỏ ở **2 lần đo hợp lệ liên tiếp** | Giữ đỏ, kích hoạt leo thang (mục 5) |
| `PERSIST-YELLOW` | Vàng ≥ 3 trong 5 lần đo gần nhất | Nâng ưu tiên hành động (đo lại → can thiệp nhẹ) |
| `TREND` | Hệ số góc 7 ngày cùng chiều có hại và \|tổng thay đổi\| ≥ 2 × MAD | Vàng "xu hướng", kể cả khi từng điểm vẫn xanh |
| `RECOVER` | 2 lần đo liên tiếp xanh sau vàng hoặc đỏ | Đóng sự kiện, ghi vào báo cáo |
| `ABSTAIN-ESCALATE` | `UNKNOWN`/`STALE` ≥ 3 lần liên tiếp cho chỉ số đang theo dõi | Nhắc đo; báo mặt đất "mất dữ liệu" |

---

## 3. Bảng quyết định cho từng chỉ số

Mỗi bảng có cùng cấu trúc: đầu vào → cổng → luật → hành động → giới hạn dữ liệu → ví dụ thật.

### 3.1. Nhịp tim (`hr_rest`, bpm)

| Hạng mục | Nội dung |
|---|---|
| Đầu vào | Pulse đo sáng (CRF Daily Vitals). Persona: 6 người. Mô hình `vitals` cho dải ngày kế tiếp |
| E1 | `BASE-MAD-Y/R`, cả hai chiều, MAD floor 3 bpm |
| E2 | Không có ngưỡng NASA cho HR nghỉ (NASA-STD đọc được không có giới hạn số cho HR/HA). Khoảng PRD 50–75 bpm chỉ là **bối cảnh hiển thị** `[HEURISTIC]`, không tạo màu. Miền kỹ thuật 30–220 thuộc cổng G0 |
| E3 | `HR-Q95` (vàng) |
| Hành động | Vàng: `remeasure` (đo lại sau 5 phút nghỉ). Vàng kéo dài kèm nhiệt độ tăng: xem luật kết hợp `INFECT-SCREEN` |
| Giới hạn | Không có ECG nên không phát hiện được loạn nhịp; ghi rõ trên UI |
| Ví dụ thật | 5160: PRE trung vị 57, MAD 5. Ngày IN 42 đo 50 bpm → z = −0,94 → **xanh** |

### 3.2. Huyết áp (`bp_systolic`, `bp_diastolic`, mmHg)

| Hạng mục | Nội dung |
|---|---|
| E1 | `BASE-MAD-Y/R`, cả hai chiều, MAD floor 4 mmHg |
| E2 | `BP-HTN-1`: SBP ≥ 130 hoặc DBP ≥ 80 → vàng. `BP-HTN-2`: ≥ 140/90 → vàng + `PERSIST-YELLOW`. `BP-CRISIS`: SBP > 180 hoặc DBP > 120 → đỏ. Nguồn: ACC/AHA 2017 `[GUIDELINE]` (cần đối chiếu lại toàn văn trước khi nộp). **Một lần đo sáng không phải chẩn đoán tăng huyết áp**; UI phải nói rõ điều này |
| E2 (giai đoạn `post`) | `ORTHO-PRD`: SBP giảm ≥ 20 mmHg hoặc HR tăng ≥ 30 bpm khi đổi tư thế → đỏ. Nguồn: PRD; định nghĩa đồng thuận về hạ huyết áp tư thế (Freeman 2011). **Chỉ áp khi `context.posture` có cặp nằm/đứng.** CRF vitals không có cặp này, nên luật này để cho dữ liệu FTT (P2) |
| Tham chiếu hiển thị | R003–R009 (Stenger 2010) `[STUDY]`, n = 2 hoặc 9: chỉ minh họa |
| Hành động | Vàng: `remeasure`. Đỏ `BP-CRISIS`: `contact_ground` ngay, không chờ `PERSIST` |
| Ví dụ thật | 5160: SBP PRE 120 (MAD 5). IN 42 đo 125 → z = 0,67 → xanh theo E1. Nhưng DBP 85 ≥ 80 nên E2 `BP-HTN-1` → **vàng** ("chỉ số tâm trương cao hơn khuyến nghị, đo lại") |

### 3.3. Nhiệt độ cơ thể (`body_temp`, °C)

| Hạng mục | Nội dung |
|---|---|
| Chuẩn hóa | Nguồn có cả °C và °F → chỉ lấy °C. Nếu chỉ có °F thì đổi đơn vị và gắn cờ `converted_from_F` |
| E1 | Chỉ chiều tăng, MAD floor 0,2 °C |
| E2 | `TEMP-FEVER`: ≥ 38,0 °C → đỏ. `TEMP-HIGH`: 37,5–37,9 °C → vàng. Ngưỡng 38,0 °C là định nghĩa sốt thông dụng; ghi `[HEURISTIC]` cho đến khi có nguồn được duyệt. `TEMP-LOW`: < 35,0 °C → đỏ `[HEURISTIC]` |
| Hành động | Vàng: `remeasure` + `log_symptoms`. Đỏ lặp lại: `contact_ground` và kích hoạt `CREW-ALERT` (mục 4) |
| Giới hạn | Campaign 1 chỉ có 35–40/84 ngày có nhiệt độ. Ngày thiếu hiện khoảng trống, không nội suy |
| Ví dụ thật | 5160, IN ngày 9: 37,5 °C. E1 (sau sàn MAD) z ≈ 3,7 → vàng; E2 `TEMP-HIGH` → vàng. Kết quả **vàng**, hành động "đo lại + ghi triệu chứng". (Không có sàn MAD thì luật nsac hiện tại sẽ báo đỏ.) |

### 3.4. Tâm trạng (`mood_tmd` và 6 thang con POMS)

| Hạng mục | Nội dung |
|---|---|
| Đầu vào | POMS (CFT70) đo khoảng mỗi tuần. TMD cao hơn nghĩa là tâm trạng xáo trộn hơn |
| Cổng | Cần ≥ 3 điểm PRE. Thang Vigor đảo chiều khi diễn giải |
| E1 | `MOOD-Z`: z = (TMD − mean_PRE) / max(SD_PRE, 3) ≥ 1,5 → vàng `[HEURISTIC]`. Bối cảnh: NASA Cognition dùng z ≤ −1,5 so với baseline cá nhân cho điểm "thấp" (Dev 2024) |
| E2 | Không có ngưỡng tuyệt đối có nguồn cho POMS trong phạm vi đã đọc → không dùng |
| P | `MOOD-PERSIST`: vàng ở 2 lần đo liên tiếp → đề xuất `rest_shift` và gợi ý trò chuyện với người hỗ trợ tâm lý ở mặt đất (hành động `contact_ground`, mức thường) |
| Đỏ | **Không có luật tự tạo đỏ** cho tâm trạng. Rủi ro hành vi cần chuyên gia đánh giá; Sky chỉ đề xuất liên hệ |
| Ví dụ thật | 5160: PRE TMD −13, −15, −18, −16 (mean −15,5; SD ≈ 2,1 → sàn 3). IN ngày 10: TMD 3 → z ≈ 6,2 → **vàng**. Ngày 17: −13 → xanh → `RECOVER`. Đây là một đợt xáo trộn ngắn; hệ thống không leo thang |

### 3.5. Hoạt động và giấc ngủ (`sleep_hours`, `sleep_efficiency`, `sleep_latency`)

| Hạng mục | Nội dung |
|---|---|
| Chuẩn hóa | `"7:44:00"` → 7,733 h (**không** đọc thành 7,44). Bản actigraphy chính, không dùng `Query_Result` |
| E1 | Chỉ chiều giảm (`sleep_hours`, `sleep_efficiency`); chiều tăng cho `sleep_latency` |
| E2 | `SLEEP-TST-LOW`: TST < 6 h → vàng. `SLEEP-TST-7`: TST < 6 h ở 7 đêm liên tiếp → đỏ (PRD) `[HEURISTIC]`. `SLEEP-EFF-LOW`: hiệu quả < 85 % → vàng; `< 75 %` ở 7 đêm liên tiếp → đỏ (PRD) `[HEURISTIC]`. Bối cảnh `[NASA-STD]`: V6001 lấy 8,5 giờ làm cơ sở lịch ngủ |
| Hoạt động | Không có số bước cho 6 persona. Panel tham chiếu MMASH (cohort khác) chỉ minh họa, **không tham gia quyết định** |
| Hành động | Vàng: `rest_shift` (bảo vệ giấc ngủ kế tiếp, đo lại). Đỏ: `rest_shift` + báo mặt đất |
| Ví dụ thật | C1G0001: PRE 7:44 và 7:50, hiệu quả 92,1–95,8 %. IN: 7:52, 90,8 % → **xanh** |

### 3.6. Đường huyết (`glucose_serum`, mg/dL)

| Hạng mục | Nội dung |
|---|---|
| Chuẩn hóa | Tách số khỏi ký hiệu: `"138A  (H)"` → 138 + cờ `source_flag_H` + chú thích `A`; `"84B"` → 84 + chú thích `B`. Ý nghĩa A/B phải tra codebook MR010G; trước khi tra được thì giữ nguyên chú thích, không diễn giải |
| Cổng | Không dùng baseline cá nhân (3–4 mẫu/người). `context.fasting` không có trong nguồn → UI ghi "không rõ lúc đói" |
| E2 | `GLU-REF`: ngoài khoảng tham chiếu phòng xét nghiệm (`glucose_range_min/max`, OSD-575 Inspiration4) → vàng `[STUDY]`. `GLU-LAB-FLAG`: cờ L/H của chính phòng xét nghiệm nguồn → vàng `[STUDY]`. `GLU-HYPO-2`: < 54 mg/dL → đỏ; `GLU-HYPO-1`: < 70 mg/dL → vàng (ADA Standards of Care, mức hạ đường huyết 1 và 2) `[GUIDELINE]`, cần đối chiếu |
| Không làm | Không chẩn đoán đái tháo đường từ một mẫu không rõ lúc đói. Ngưỡng ≥ 126 mg/dL chỉ áp khi `fasting = true` |
| Hành động | Vàng: `remeasure` ở lần lấy máu kế tiếp, ghi chế độ ăn. Đỏ (hạ đường huyết mức 2): `contact_ground` |
| Ví dụ thật | C1G0002: PRE 138 (H), IN 118 (H), POST 114 (H), 120 (H) → `GLU-LAB-FLAG` **vàng kéo dài**. Đây là đặc điểm có từ trước nhiệm vụ (đã cao ở PRE), không phải do nhiệm vụ gây ra. UI nên nói "cao hơn khoảng tham chiếu từ trước nhiệm vụ; theo dõi". C1G0001: POST 0 đo 73 (L) → vàng (cờ L), nhưng chưa dưới 70 |

---

## 4. Luật kết hợp nhiều chỉ số (X)

Chỉ áp cho **cùng một `astronaut_id`**, trong cửa sổ ±1 ngày nhiệm vụ.

| `rule_id` | Điều kiện | Mức | Hành động | Bằng chứng |
|---|---|---|---|---|
| `INFECT-SCREEN` | `body_temp` ≥ vàng **và** `hr_rest` tăng (z_rel ≥ 2) | vàng → đỏ nếu `TEMP-FEVER` | `log_symptoms` + `remeasure`; đỏ thì `contact_ground` | `[HEURISTIC]`; bối cảnh rủi ro miễn dịch (NASA HRP Immune) |
| `CREW-ALERT` | `TEMP-FEVER` ở ≥ 1 thành viên **hoặc** `INFECT-SCREEN` ở ≥ 2 thành viên trong 3 ngày | đỏ cấp đội | Thông báo cả phi hành đoàn + `contact_ground` (PRD: "alert all members") | PRD + `[HEURISTIC]` |
| `SLEEP-MOOD` | `sleep_hours` vàng ≥ 2 đêm **và** `mood_tmd` vàng | vàng | `rest_shift` | `[HEURISTIC]`; NASA HRP Risk from Inadequate Sleep |
| `POST-ORTHO-SAFETY` | `phase = post`, ≤ 1 ngày sau hạ cánh, HR tăng **và** SBP giảm so với baseline | vàng | `safety_compression_garment` / `assisted_stand` | Stenger 2010 `[STUDY]`; PRD |

Lưu ý: không persona nào có đủ cả 6 chỉ số (mục 3 của v2). Luật nào cần chỉ số mà persona thiếu sẽ **không kích hoạt**, và lý do được ghi vào log (`skipped: missing mood_tmd`).

---

## 5. Danh mục hành động và thứ tự chọn MỘT hành động

Mở rộng `Recommendation.action` của nsac (hiện có `exercise_dose`, `safety_compression_garment`, `assisted_stand`, `rest_shift`, `contact_ground`) thêm:

| Hành động mới | Ý nghĩa | Cần xác nhận? |
|---|---|---|
| `remeasure` | Đo lại chỉ số trong N phút hoặc N giờ, kèm hướng dẫn cách đo | Có (nhẹ) |
| `log_symptoms` | Mở biểu mẫu triệu chứng (sốt, ho, đau đầu…) | Có |

**Thứ tự ưu tiên** (harness triage chỉ chọn một hành động):
1. `contact_ground` khi có bất kỳ đỏ nào sau `PERSIST-RED`, hoặc `BP-CRISIS`, `GLU-HYPO-2`, `CREW-ALERT`;
2. an toàn quanh hạ cánh (`POST-ORTHO-SAFETY`, `days_to_landing ≤ 1`);
3. `log_symptoms` (`INFECT-SCREEN`);
4. `rest_shift` (giấc ngủ, tâm trạng);
5. `exercise_dose` (cơ xương; luật cũ của nsac);
6. `remeasure` (mọi vàng đơn lẻ, `needs_confirmation`).

Mỗi hành động mang `checklist_ref` (ISS Medical Checklist) **chỉ khi** hành động đó có trong checklist. Nếu không có thì ghi `checklist_ref: null`, `rationale_source: rule_id`.

---

## 6. Định dạng đầu ra và cấu hình

### 6.1. `configs/rules.yaml` (sky-ml) và bản tương đương ở nsac

```yaml
version: 2026-11-14.1
gates:
  hr_rest:        {valid: [30, 220],  baseline_min: 5, stale_days: 2,  mad_floor: 3}
  bp_systolic:    {valid: [60, 260],  baseline_min: 5, stale_days: 2,  mad_floor: 4}
  bp_diastolic:   {valid: [30, 160],  baseline_min: 5, stale_days: 2,  mad_floor: 4}
  body_temp:      {valid: [33, 43],   baseline_min: 5, stale_days: 2,  mad_floor: 0.2, harmful: up}
  mood_tmd:       {valid: [-32, 200], baseline_min: 3, stale_days: 10, sd_floor: 3,    harmful: up}
  sleep_hours:    {valid: [0, 16],    baseline_min: 3, stale_days: 2,  mad_floor: 0.25, harmful: down}
  glucose_serum:  {valid: [20, 600],  baseline_min: null, stale_days: 30}
rules:
  - {id: BASE-MAD-Y, metric: "*", when: "abs(z_rel) >= 3", level: yellow, evidence: HEURISTIC,
     source: "nsac detection (product triage)"}
  - {id: BASE-MAD-R, metric: "*", when: "abs(z_rel) >= 5", level: red, evidence: HEURISTIC, cap: yellow_unless_confirmed}
  - {id: TEMP-HIGH,  metric: body_temp, when: "37.5 <= value < 38.0", level: yellow, evidence: HEURISTIC}
  - {id: TEMP-FEVER, metric: body_temp, when: "value >= 38.0", level: red, evidence: HEURISTIC}
  - {id: BP-HTN-1,   metric: bp, when: "sbp >= 130 or dbp >= 80", level: yellow, evidence: GUIDELINE,
     source: "Whelton PK et al. 2017 ACC/AHA Hypertension guideline (verify)"}
  - {id: BP-CRISIS,  metric: bp, when: "sbp > 180 or dbp > 120", level: red, evidence: GUIDELINE}
  - {id: GLU-LAB-FLAG, metric: glucose_serum, when: "'source_flag_H' in flags or 'source_flag_L' in flags",
     level: yellow, evidence: STUDY, source: "lab flag in UTMB MR010G"}
  - {id: GLU-HYPO-2, metric: glucose_serum, when: "value < 54", level: red, evidence: GUIDELINE,
     source: "ADA Standards of Care, hypoglycemia level 2 (verify)"}
  - {id: MOOD-Z,     metric: mood_tmd, when: "z_pre >= 1.5", level: yellow, evidence: HEURISTIC,
     source: "context: Dev et al. 2024 Front Physiol (cognition z <= -1.5)"}
  - {id: SLEEP-TST-LOW, metric: sleep_hours, when: "value < 6", level: yellow, evidence: HEURISTIC,
     source: "PRD; NASA-STD-3001 V6001 rationale (8.5 h)"}
persistence: {red_consecutive: 2, yellow_window: [3, 5], recover_consecutive: 2, abstain_escalate: 3}
```

Mọi `when` được viết bằng một **ngôn ngữ biểu thức nhỏ, đã liệt kê sẵn biến** (`value, z_rel, z_pre, sbp, dbp, flags`). Không dùng `eval` cho chuỗi tùy ý; bộ đánh giá chỉ hỗ trợ so sánh, `and`/`or` và `in`.

### 6.2. Bản ghi quyết định (JSON, ghi vào `deviations` và nhật ký kiểm toán)

```json
{
  "astronaut_id": "ayla-reyes", "metric": "body_temp", "mission_day": 9, "phase": "in",
  "value": 37.5, "unit": "°C", "data_state": "OK",
  "evidence": {
    "relative": {"baseline_median": 36.4, "baseline_mad": 0.2, "mad_floored": true, "z_rel": 3.7, "rule_id": "BASE-MAD-Y"},
    "absolute": {"rule_id": "TEMP-HIGH", "label": "HEURISTIC"},
    "model":    {"expected_low": 36.1, "expected_high": 36.8, "rule_id": "TEMP-Q95", "label": "LOCAL"}
  },
  "level": "yellow", "needs_confirmation": true,
  "persistence": {"consecutive_red": 0, "yellow_in_last_5": 1},
  "combined_rules": [],
  "action": {"type": "remeasure", "dose": "Đo lại nhiệt độ sau 30 phút nghỉ; ghi triệu chứng nếu có", "requires_confirmation": true},
  "rules_version": "2026-11-14.1", "cohort_ref": "utmb_cft70:5160", "source_sha256": "…"
}
```

*(Giá trị `expected_low/high` ở trên là minh họa định dạng. Số thật do task `vitals` sinh ra.)*

---

## 7. Triển khai

| Nơi | File | Việc làm |
|---|---|---|
| sky-ml | `configs/rules.yaml` | Mục 6.1 |
| sky-ml | `src/sky_ml/decide/normalize.py` | Parse `"73  (L)"`, `"7:44:00"`, °F→°C, mapping header; trả về bản ghi decision-ready (1.1) |
| sky-ml | `src/sky_ml/decide/gates.py` | G0/G1 → `data_state` |
| sky-ml | `src/sky_ml/decide/evidence.py` | E1/E2/E3 + hợp nhất F |
| sky-ml | `src/sky_ml/decide/timeline.py` | Bền vững P, luật kết hợp X, chọn hành động A |
| sky-ml | `export_nsac.py` | Ghi `deviations.jsonl` theo 6.2 |
| nsac | `apps/backend/src/domain/decision.ts` | Cùng logic, đọc `rules.json` từ bundle, dùng khi có reading mới |
| nsac | `apps/backend/tests/decision.test.ts` | Dùng chung fixture JSON với sky-ml để hai bên cho **cùng kết quả** |

**Test bắt buộc** (dùng các ví dụ thật ở mục 3):

| Test | Kỳ vọng |
|---|---|
| `test_temp_mad_floor_prevents_false_red` | 5160 ngày 9, 37,5 °C → vàng, không phải đỏ |
| `test_dbp_guideline_yellow` | 5160 ngày 42, 125/85 → vàng `BP-HTN-1` |
| `test_mood_spike_then_recover` | 5160 TMD 3 rồi −13 → vàng rồi `RECOVER` |
| `test_glucose_flag_parsed_and_preexisting` | C1G0002 "138A  (H)" → 138, cờ H, vàng; PRE cũng vàng nên ghi "từ trước nhiệm vụ" |
| `test_sleep_hhmm` | "7:44:00" → 7,733 h → xanh |
| `test_missing_metric_unknown` | `ayla-reyes` + `glucose_serum` → `UNKNOWN`, không màu |
| `test_red_needs_two_consecutive` | Một đỏ đơn lẻ → yellow + `needs_confirmation`; hai đỏ liên tiếp → `contact_ground` |
| `test_heuristic_alone_caps_yellow` | Chỉ có luật HEURISTIC kích hoạt → tối đa vàng (trừ các luật được đánh dấu rõ là đỏ) |
| `test_one_action_only` | Nhiều luật cùng kích hoạt → đúng một hành động theo thứ tự ở mục 5 |
| `test_rules_parity_py_ts` | Cùng fixture → sky-ml và nsac cho cùng `level`, `rule_id`, `action` |

---

## 8. Giới hạn cần nói rõ khi trình bày

1. Dữ liệu là **analog nằm giường trên mặt đất**, không phải dữ liệu bay. Ngưỡng được kiểm thử trên 6 người analog.
2. Một lần đo không phải chẩn đoán. Mọi đỏ cần 2 lần đo liên tiếp, trừ các ngưỡng nguy hiểm có nguồn (`BP-CRISIS`, `GLU-HYPO-2`).
3. Các ngưỡng `[GUIDELINE]` (ACC/AHA, ADA) và ngưỡng sốt 38,0 °C phải được đối chiếu toàn văn trước khi nộp; đến lúc đó UI ghi "cần xác minh".
4. Không có dữ liệu ECG, SpO₂, số bước, glucose lúc đói cho 6 persona. Các luật cần những dữ liệu này để ở trạng thái `not_applicable`.
5. Sky **hỗ trợ tự đánh giá, không chẩn đoán**. Leo thang luôn dẫn tới "liên hệ flight surgeon".

---

## 9. Nguồn

**Dữ liệu**
- UTMB (NASA Life Sciences Portal): CRF Daily Vitals (Campaign 1, CFT70), NNX10AP86G POMS (CFT70), BRSMAct (Campaign 1), MR010G Flight Chem Profile (Campaign 1). https://nlsp.nasa.gov/
- OSD-575 Inspiration4 CMP (khoảng tham chiếu glucose). https://osdr.nasa.gov/bio/repo/data/studies/OSD-575

**Chuẩn và hướng dẫn**
- NASA-STD-3001 Vol 1 Rev C (2023); V6001 (lịch ngủ 8,5 giờ).
- Whelton P.K. et al. (2018). 2017 ACC/AHA Guideline for the Prevention, Detection, Evaluation, and Management of High Blood Pressure in Adults. *Hypertension* 71:e13–e115. *(cần đối chiếu)*
- American Diabetes Association. Standards of Care in Diabetes, mục Glycemic Goals / Hypoglycemia. *(cần đối chiếu phiên bản mới nhất)*
- Freeman R. et al. (2011). Consensus statement on the definition of orthostatic hypotension… *Clin Auton Res* 21:69–72. *(cần đối chiếu)*

**Nghiên cứu**
- Stenger M.B. et al. (2010). NTRS 20100038346; *Aviat Space Environ Med* 81:883–887.
- Dev S.I. et al. (2024). *Front Physiol*, doi:10.3389/fphys.2024.1451269.

**Tài nguyên challenge** (nsac `docs/references/spaceapps-resources-2026/nasa-hrp/`): Standard Measures, ARCHeR, Risk of Altered Immune System Responses, Risk from Inadequate Sleep and Irregular Schedules, Risk of Cardiovascular Adaptations.
