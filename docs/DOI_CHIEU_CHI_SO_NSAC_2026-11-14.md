# Đối chiếu dữ liệu sky-ml với danh mục chỉ số của nsac

> 14/11/2026, 21:10 · nsac `main` @ `34e1173` (14/11 20:03)
> Đối chiếu với:
> 1. [`docs/references/astronaut-health-metrics-by-system.md`](https://github.com/KeiosStarqua/nsac/blob/main/docs/references/astronaut-health-metrics-by-system.md) — 17 hệ cơ quan;
> 2. hợp đồng `backend/src/nsac/contracts/schemas.py › MetricId`;
> 3. HUD web `apps/web/src/features/hud-gen/presets.ts`.

**Ký hiệu:**
- ✅ đã có mô hình / dữ liệu trong `nasa-hackathon/data`;
- 🟡 dữ liệu THẬT đã có trong `NASA-cl/data`, chưa đưa vào pipeline;
- ⚠️ chỉ có dữ liệu giả định;
- ❌ không có nguồn trong NASA-cl.

## 1. Ba điểm lệch quan trọng

1. **Danh sách chỉ số của nsac đã khác với 6 chỉ số mà sky-ml đang theo** (nhịp tim, huyết áp, tâm trạng, hoạt động và giấc ngủ, nhiệt độ, đường huyết).
   - Hợp đồng backend hiện là `MetricId = hr_rest, hrv_rmssd, bp_systolic, bp_diastolic, lv_volume, stroke_volume, bone_density, muscle_strength, sleep_hours, exercise_minutes`.
   - Vì vậy **mood, nhiệt độ và glucose sẽ bị Pydantic từ chối** nếu đẩy vào `readings`, trừ khi nsac mở rộng `MetricId`.
2. **HUD web hiển thị `heartRate, respiration, spo2, sleep`:**
   - nhịp thở có dữ liệu thật trong CRF nhưng chưa có task;
   - **SpO₂ không có nguồn nào** trong NASA-cl.
3. **Định dạng `readings` của nsac là `astronaut_id, ts (bắt buộc có múi giờ), metric, value, unit, source`.** Bundle `export-nsac` phải:
   - đổi ngày nghiên cứu sang `ts` trên dòng thời gian nhiệm vụ;
   - ghi `source` rõ ràng, ví dụ `utmb-crf:vitals_sbp:external_backtest` hoặc `synthetic:sky-ml-synthetic-1.0`.

   ID persona đã khớp (`ayla-reyes`, `tomas-ortega`, …).

## 2. Hợp đồng `MetricId` của nsac ↔ dữ liệu sky-ml

| `MetricId` | sky-ml hiện có | Nguồn thật còn chưa dùng | Persona có dữ liệu? | Việc cần làm |
|---|---|---|---|---|
| `hr_rest` | ✅ `vitals_pulse` (mạch buổi sáng, nằm nghỉ) | — | 6/6 | Đổi tên khi export; đơn vị bpm |
| `bp_systolic`, `bp_diastolic` | ✅ `vitals_sbp`, `vitals_dbp` | — | 6/6 | Đổi tên khi export; mmHg |
| `sleep_hours` | ✅ dữ liệu: `sleep_act` (có cả thời lượng ngủ); task hiện dự báo **hiệu suất ngủ** | — | C1 thật, CFT70 ⚠️ giả định | Thêm task `sleep_act_duration` (đổi `measure: duration`) |
| `hrv_rmssd` | ❌ | 🟡 khoảng RR thô của MMASH (`raw/mmash`, người mặt đất, không phải persona) | 0/6 | Tính RMSSD từ RR của MMASH, chỉ minh họa; persona cần dữ liệu giả định nếu muốn hiển thị |
| `lv_volume`, `stroke_volume` | ❌ | 🟡 `BRSMCF.zip`, siêu âm tim của C1, C3 và CFT70 (184 lần đo CFT70): **đường kính** thất trái tâm trương/tâm thu, không phải thể tích | Có (C1 + CFT70) | Thể tích phải suy ra bằng công thức Teichholz, V = 7/(2,4 + D)·D³ (Teichholz 1976); stroke volume = EDV − ESV. Cần ghi rõ là giá trị **suy ra** |
| `bone_density` | ❌ | 🟡 `BRSMiDXA.zip` (iDXA CFT70: toàn thân, hông), `NNX10AP86G_iDXA`, `MR035G` (DXA C3), `BRSMpQCT`, `BRSMQCT` | CFT70 | Task `bone_density` dạng một hàng/người (thay đổi PRE → POST), giống `cpet` |
| `muscle_strength` | ❌ | 🟡 iRATS (công suất đỉnh xe đạp, 35 người CFT70; MRI/siêu âm thể tích cơ), `MR078G` (fitness C3), `BRSMFMT` (vận động chức năng C1) | CFT70, C1 | Chọn một thước đo, đổi sang `% baseline` như hợp đồng nsac |
| `exercise_minutes` | ❌ | 🟡 có thể có trong iRATS/BRSMPT (Campaign 1 ARES): cần kiểm biến | ? | Kiểm tra trước khi hứa |

**Bổ sung cho HUD:**

| HUD | sky-ml | Ghi chú |
|---|---|---|
| `heartRate` | ✅ `vitals_pulse` (+ `hr` của MMASH) | — |
| `respiration` | 🟡 CRF có `Resp Rate` ở 2.934 ngày (C3 2.448, CFT70 237, C1 249) | Chỉ cần thêm task `vitals_resp` (`measure: resp`), vài phút |
| `spo2` | ❌ | Không có trong NASA-cl. Nếu giữ trên HUD: phải dùng dữ liệu giả định có nhãn, hoặc thay bằng nhịp thở / nhiệt độ |
| `sleep` | ✅ `sleep_act`, `sleep` | — |

## 3. Theo 17 hệ cơ quan trong tài liệu tham chiếu

| # | Hệ | Chỉ số (⭐ = NASA đo) | sky-ml | Ghi chú |
|---|---|---|---|---|
| 1 | Sinh tồn | Nhịp tim ⭐ | ✅ `vitals_pulse`, `hr` | — |
| | | Huyết áp tâm thu/tâm trương/trung bình ⭐ | ✅ `vitals_sbp`, `vitals_dbp` | HA trung bình suy được: DBP + (SBP − DBP)/3 |
| | | Nhịp thở ⭐ | 🟡 CRF | Xem mục 2 |
| | | SpO₂ ⭐ | ❌ | — |
| | | Nhiệt độ lõi ⭐ | ✅ một phần: `vitals_temp` | Nhiệt độ cơ thể **buổi sáng** trong CRF, **không phải nhiệt độ lõi** (Thermolab); cần ghi rõ trên web |
| 2 | Tim mạch | HRV ⭐ | 🟡 RR của MMASH | Người mặt đất |
| | | Siêu âm tim (LVEDV, SV…) ⭐ | 🟡 `BRSMCF` | Đường kính → thể tích bằng công thức |
| | | Thể tích huyết tương ⭐ | 🟡 `BRSMPV.zip` (cần kiểm) | — |
| | | ECG, PWV, tilt test… | ❌ / cần kiểm `BRSMVSI` | — |
| 3 | Hô hấp | VO2peak ⭐ | ✅ `cpet`, `cpet_physio` | — |
| | | FVC, DLCO, EtCO₂ | ❌ | — |
| 4 | Xương | DXA, QCT, pQCT ⭐ | 🟡 `BRSMiDXA`, `MR035G`, `BRSMQCT`, `BRSMpQCT` | — |
| | | Canxi, PTH… ⭐ | 🟡 `MR016G` (khoáng chất huyết thanh, sỏi thận) | — |
| 5 | Cơ | Thể tích cơ (MRI/siêu âm) ⭐ | 🟡 iRATS MRI | — |
| | | Lực / công suất ⭐ | 🟡 iRATS power cycle, `MR078G` | — |
| | | Cân nặng ⭐ | 🟡 CRF `Weight` (2.898 ngày) | — |
| | | Test chức năng ⭐ | 🟡 `BRSMFMT` | — |
| 6 | Thần kinh | Đánh giá thần kinh chức năng | 🟡 `MR042G` (C3) | Thị lực, OCT, MRI não: ❌ |
| 7 | Nhận thức, tâm lý | POMS ⭐ | ✅ `mood` (CFT70) + ⚠️ giả định cho C1 | PHQ-9, GAD-7: ❌ |
| | | Bộ test nhận thức ⭐ | 🟡 WinSCAT (`MR085G`, C1 + C3) | — |
| | | Mệt mỏi | 🟡 MFSI-SF (`NNX10AP86G`) | — |
| 8 | Giấc ngủ | Actigraphy ⭐ | ✅ `sleep_act` (C1) + ⚠️ giả định cho CFT70 | — |
| | | Đa ký giấc ngủ ⭐ | ✅ `sleep` (Sleep-EDF, người mặt đất) | — |
| | | Thuốc ngủ ⭐ | ✅ được ghi nhận | Cột `sedative` (Ambien) |
| | | Cortisol ⭐ | 🟡 `BRSMLVR` cortisol nước bọt (C3) | — |
| 9 | Máu, xét nghiệm | Glucose, insulin ⭐ | ✅ `glucose` (OGTT CFT70), insulin dùng làm đặc trưng | — |
| | | CGM ⭐ | ⚠️ chỉ có chuỗi giả định | — |
| | | CBC, CMP ⭐ | 🟡 OSD-569, OSD-575 trong NASA-cl | Có thể làm thẻ mô tả |
| | | Lipid ⭐ | 🟡 `NNX10AP86G_LIPIDS` | — |
| | | Hormone ⭐ | 🟡 `NNX10AP86G_IMMULITE` (cần kiểm) | — |
| 10 | Miễn dịch | Cytokine ⭐ | 🟡 OSD-575 | — |
| | | Tái hoạt virus tiềm ẩn ⭐ | 🟡 `BRSMLVR` (C3, CFT70) | — |
| 11 | Thận, dịch | Nước uống, nước tiểu ⭐ | 🟡 CRF (Water Intake, Urine Collection), `MR016G` | — |
| 12 | Chuyển hóa | Năng lượng nạp vào ⭐ | 🟡 CRF Meal Status (chỉ ghi trạng thái bữa ăn) | — |
| 13 | Omics | — | ❌ | Ngoài phạm vi |
| 14 | Phóng xạ, môi trường | Liều ⭐ | ✅ `dose`, `dose_orbit` | Đây là **liều môi trường trong module**, không phải liều cá nhân đeo người |
| | | DONKI, CO₂ cabin | ❌ trong sky-ml | nsac đã có adapter DONKI |
| 15 | Da, tóc, răng | — | ❌ | — |
| 16 | Vận động hằng ngày | Số bước ⭐ | ❌ | Actigraphy C1 chỉ có tóm tắt giấc ngủ |
| | | Chiều cao ⭐ | 🟡 CRF `Height` | — |
| 17 | EVA | — | ❌ | — |

**Phù hợp với ghi chú kiến trúc của nsac** (chỉ một phần nhỏ đo liên tục; phần lớn lấy mẫu định kỳ). Cách tổ chức dữ liệu của sky-ml khớp với ghi chú này:
- vitals: 1 lần/ngày;
- POMS: hằng tuần;
- OGTT, DXA, siêu âm tim: theo đợt PRE/IN/POST;
- chỉ `hr` (theo phút) và `dose` (5 phút) là gần liên tục.

## 4. Đề xuất theo thứ tự

| Ưu tiên | Việc | Lý do | Khối lượng |
|---|---|---|---|
| 1 | `vitals_resp` từ CRF | HUD có ô `respiration`; đủ dữ liệu thật cho cả 6 persona | Rất nhỏ: chỉ thêm khai báo YAML |
| 2 | `sleep_act_duration` | Khớp `sleep_hours` của nsac | Rất nhỏ: YAML |
| 3 | `export-nsac`: ánh xạ task → `MetricId`, ngày nghiên cứu → `ts`, `source` có cờ real/synthetic | Web và backend đọc được ngay | Vừa |
| 4 | `bone_density` (iDXA CFT70) và `muscle_strength` (iRATS) | Hai `MetricId` chưa có dữ liệu, mà NASA-cl có nguồn thật cho persona CFT70 | Vừa |
| 5 | `lv_volume` / `stroke_volume` từ `BRSMCF` (Teichholz) | `MetricId` chưa có dữ liệu; phải ghi rõ là giá trị suy ra từ đường kính | Vừa |
| 6 | Thống nhất với nhóm web: mở rộng `MetricId` thêm `body_temp`, `resp_rate`, `mood_tmd`, `glucose_fasting` **hoặc** bỏ khỏi bundle | Hiện các chỉ số này sẽ bị hợp đồng nsac từ chối | Quyết định của nhóm |
| 7 | SpO₂ | Không có nguồn thật: dùng dữ liệu giả định có nhãn hoặc bỏ khỏi HUD | Quyết định của nhóm |

## Nguồn

- nsac `docs/references/astronaut-health-metrics-by-system.md`, `backend/src/nsac/contracts/schemas.py`, `apps/web/src/features/hud-gen/presets.ts` (commit `34e1173`)
- NASA-cl `data/raw/nlsp/*.zip` (đã kiểm danh sách file và cột ngày 14/11)
- Teichholz LE, Kreulen T, Herman MV, Gorlin R. Problems in echocardiographic volume determinations: echocardiographic-angiographic correlations in the presence or absence of asynergy. *Am J Cardiol* 1976;37(1):7–11
