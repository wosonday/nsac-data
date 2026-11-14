# Thiết kế tích hợp: dữ liệu và mô hình NASA-cl → website Sky (nsac), bản 2

**Phiên bản:** v2, 14/11/2026 12:10 (Asia/Bangkok). Bản này thay bản v1 lập lúc 09:00 cùng ngày.

**Lý do có v2:**
- **nsac đổi lớn** (commit `3704308`, 14/11):
  - backend chuyển sang **TypeScript + Bun + Drizzle/SQLite** (`apps/backend`);
  - có **bộ chọn 6 phi hành gia hư cấu**, body map 3D, agent core, `DESIGN.md` §14 *SignalWell*;
  - hai hard rule "offline" và "OSI license" đã được bỏ.
- **Phạm vi chỉ số chốt lại thành 6:** nhịp tim, huyết áp, tâm trạng, hoạt động và giấc ngủ, nhiệt độ cơ thể, đường huyết.
- **Phát hiện mới trong dữ liệu UTMB đã tải:** bảng *Daily Vitals* (CRF) có HR, huyết áp, nhiệt độ **hằng ngày theo cùng một người**. Ngoài ra POMS, actigraphy và xét nghiệm glucose **khớp đúng các người đó**.

**Phạm vi đã đọc:**
- nsac `origin/main@3704308`: AGENTS, ARCHITECTURE, DESIGN §14, `apps/backend/src/db/*`, `features/{astronaut,sky-hud,health}`, `docs/references/spaceapps-resources-2026/*`.
- NASA-cl: toàn bộ docs, cộng một lượt kiểm tra trực tiếp các ZIP `nlsp/` (mục 2).
- `nasa-hackathon` (`sky-ml`): copy-data, check và prepare hr đã chạy, tái lập được 5.301 cửa sổ / 22 người.

---

## 0. Tóm tắt điều hành

| # | Kết luận | Lý do |
|---|---|---|
| 1 | **Mỗi phi hành gia hư cấu được gắn với đúng một người thật, đã khử định danh, trong dữ liệu analog nằm giường của NASA.** Mọi chỉ số của một phi hành gia đều đến từ cùng người đó. | Tránh "ghép cohort" (quy tắc 0.3 của Chiến lược). Đây là thay đổi lớn nhất so với v1, vốn chỉ có "persona là bộ sưu tập thẻ từ nhiều cohort". |
| 2 | Bộ 6 người: 3 người UTMB **CFT70** (5160, 8072, 8936) và 3 người **Campaign 1** (C1G0001–3) | CFT70 có HR, BP, nhiệt độ hằng ngày + POMS. Campaign 1 có HR, BP, nhiệt độ + actigraphy giấc ngủ + glucose huyết thanh. |
| 3 | **Huấn luyện trên Campaign 3 (23 người, 2.451 lượt đo vitals), kiểm định ngoài cohort trên 6 người demo** | Nhóm demo không nằm trong tập huấn luyện. Kết quả là **external validation** thật, mạnh hơn LOSO trong một cohort. |
| 4 | Chỉ số không có cho một người thì hiển thị trạng thái **UNKNOWN**, không mượn dữ liệu người khác | DESIGN.md §14 yêu cầu phân biệt UNKNOWN / STALE / INVALID / DEVICE DISCONNECTED. |
| 5 | **Đường nối dữ liệu:** `sky-ml export-nsac` → `assets/fixtures/sky-bundle/v2/*.jsonl` → script seed của `apps/backend` → bảng `readings` và `deviations` → API → web | Backend đã có bảng `readings` trùng contract `Reading`. Chỉ cần thêm cột provenance và API đọc. |
| 6 | Màu trạng thái vẫn do luật tất định quyết định. Ngưỡng lấy từ (a) baseline cá nhân MAD, (b) phân vị phần dư mô hình, (c) khoảng tham chiếu có nguồn | Hard rule 3 và 4 của nsac vẫn còn hiệu lực. |
| 7 | Vẫn cần chốt Rev B hay Rev C của NASA-STD-3001 | nsac vẫn trích Rev B. |

---

## 1. Hiện trạng nsac (14/11, `3704308`) và chỗ cắm dữ liệu

| Thành phần | Hiện tại | Chỗ cắm |
|---|---|---|
| `apps/backend/src/db/schema/readings.ts` | `id, astronautId, ts, metric, value, unit, source` | **Đích chính.** Thêm cột provenance (mục 4.2) |
| `apps/backend/src/db/schema/deviations.ts` | `metric, value, baselineMedian, baselineMad, z, slope, severity, thresholdSourceUrl` | **Thiếu `astronautId` và `ts`**, nên không biết độ lệch thuộc ai và lúc nào. Bắt buộc thêm (mục 4.2) |
| `apps/backend/src/db/repositories/astronauts.ts` | Seed 6 người hư cấu: `ayla-reyes, dae-jung-park, lena-fischer, tomas-ortega, yuki-tanaka, noor-abbasi` | Thêm bảng ánh xạ sang nguồn dữ liệu (mục 3) |
| `apps/backend/src/server.ts` | `GET /health`, `/api/astronauts`, `/api/astronauts/:id` | Thêm `/readings`, `/signals`, `/evidence` (mục 4.4) |
| `apps/web/src/features/astronaut/api/astronauts.server.ts` | Gọi `BACKEND_URL`; lỗi thì dùng fixture | Áp cùng mẫu cho `signals.server.ts` |
| `apps/web/src/features/sky-hud/vitals.ts` | 4 vital fixture (HR, nhịp thở, SpO₂, giờ ngủ), nhãn "SIMULATED" | Thay bằng 6 chỉ số thật của phi hành gia đang chọn. Nhịp thở có thật trong CRF; SpO₂ không có dữ liệu |
| `DESIGN.md` §14 SignalWell | Summary signal "so với baseline của bạn", focus view có trục thời gian thật, khoảng trống, rule ID, nguồn | Đúng hình dạng dữ liệu `sky-ml` xuất (mục 5) |
| `docs/references/spaceapps-resources-2026/nasa-hrp/*` | Tài nguyên chính thức của challenge: Standard Measures, ARCHeR, Tempus Pro… | Dùng làm nguồn "đo gì, vì sao đo" cho từng chỉ số (mục 6) |
| AGENTS.md hard rules | Bỏ rule 1 (offline) và rule 2 (OSI) | Web có thể gọi backend lúc chạy. Vẫn giữ fixture dự phòng khi backend lỗi |

---

## 2. Dữ liệu cho 6 chỉ số (đã kiểm tra trực tiếp trong `NASA-cl/data/raw`)

### 2.1. Bảng nguồn

| Chỉ số | Nguồn | Cohort, số người | Số lượt đo | Ghi chú |
|---|---|---|---|---|
| **Nhịp tim** (`Pulse`) | `nlsp/CRF.zip` → `*Daily_Vitals*` / `CRF_CFT70_VITALS_*` | C3: 23 · CFT70: 3 · C1: 3 | C3 2.442; CFT70 63/84/90; C1 84/người | Đo sáng hằng ngày, có `Test_Phase` và `BR_Day` |
| **Huyết áp** (SBP/DBP) | như trên | như trên | C3 2.450 | Header khác nhau giữa các file: `SysBP`, `SysBP (mmHg)`, `"Blood Pressure, systolic"` → cần mapping |
| **Nhiệt độ cơ thể** | như trên (`Body Temp (Celsius)`, `"Temperature, body (Celsius)"`) | như trên | C3 2.449; CFT70 đủ; **C1 chỉ 35–40/84** | C1 thiếu nhiệt độ ở phần lớn ngày → hiển thị khoảng trống, không nội suy |
| **Tâm trạng** (POMS: TMD + 6 thang con) | `nlsp/NNX10AP86G.zip` → `*_CFT70_POMS_*.csv` | CFT70: 24 người (gồm 5160, 8072, 8936) | 367 điểm TMD hợp lệ; 16/16/14 cho 3 người demo | Đo lặp PRE/IN/POST. **Không có cho C1** → UNKNOWN |
| **Hoạt động và giấc ngủ** | `nlsp/BRSMAct.zip` → `BRSMACT_Campagin_1_Actigraphy.csv` (bản chính) | C1: 3 người | 207 dòng | Sleep latency (giờ), sleep duration (giờ), sleep efficiency (%). Không dùng bản `Query_Result` (bản xuất trùng) |
| (hoạt động: số bước, cường độ) | MMASH `sample-v2` (Actigraph) | 22 người, cohort khác | 29.360 phút | **Chỉ dùng làm panel tham chiếu**, không gắn vào phi hành gia nào |
| **Đường huyết** (glucose huyết thanh) | `nlsp/MR010G.zip` → `MR010G_Campaign_1_Flight_Chem_Profile.csv` (+ `MR016G` serum chemistry) | C1: 3 người | 27 dòng (PRE/IN/POST) | Có giá trị gắn cờ dạng `"73  (L)"` → tách số và cờ L/H |
| (đường huyết, tham chiếu bay thật) | `osdr/clinical/OSD-575/LSDS-8_..._CMP_TRANSFORMED.csv` | Inspiration4: 4 người × 7 mốc | 28 | Có sẵn `glucose_range_min/max` của phòng xét nghiệm → nguồn ngưỡng `[STUDY]`. Không gắn vào phi hành gia nào |
| (bổ sung) nhịp thở, cân nặng | CRF vitals | như HR | — | Thay cho thẻ "Respiration" đang là fixture trên HUD |
| (bổ sung) nhận thức WinSCAT | `nlsp/MR085G.zip` | C3: 26 · C1: 3 | 272 / 30 | Không phải tâm trạng. Để ở focus view, không tính vào 6 chỉ số |

**Không có dữ liệu:** SpO₂ (thẻ trên HUD hiện tại), glucose cho 3 người CFT70, POMS cho 3 người C1, số bước cho cả 6 người.

### 2.2. Ánh xạ trục thời gian

- Mọi bảng UTMB dùng `Test_Phase ∈ {PRE_TEST, IN_TEST, POST_TEST}` (POMS viết `PRE-TEST`) và `BR_Day`. **`BR_Day` đếm lại từ đầu trong mỗi phase**, nên phải đổi sang một trục ngày liên tục, có dấu.
- Ánh xạ sang câu chuyện nhiệm vụ: PRE là "trước phóng" (baseline cá nhân), IN là "trong nhiệm vụ" (analog vi trọng lực, nằm đầu thấp 6°), POST là "phục hồi sau hạ cánh".
- Cột `Date` là ngày thật năm 2004 (C1) hoặc 2013 (CFT70). Bundle chỉ giữ **ngày tương đối** (`mission_day`) để tránh lộ thông tin định danh, và để không giả vờ đây là năm 2026.

---

## 3. Ánh xạ phi hành gia hư cấu → người thật (analog)

| Phi hành gia (nsac) | Nguồn | Nhịp tim | Huyết áp | Nhiệt độ | Tâm trạng | Hoạt động / giấc ngủ | Đường huyết |
|---|---|---|---|---|---|---|---|
| `ayla-reyes` | UTMB CFT70 · 5160 | ✓ 63 | ✓ | ✓ | ✓ POMS 16 | — | — |
| `dae-jung-park` | UTMB CFT70 · 8072 | ✓ 84 | ✓ | ✓ | ✓ POMS 16 | — | — |
| `lena-fischer` | UTMB CFT70 · 8936 | ✓ 90 | ✓ | ✓ | ✓ POMS 14 | — | — |
| `tomas-ortega` | UTMB Campaign 1 · C1G0001 | ✓ 84 | ✓ | ◐ 37 | — | ✓ actigraphy | ✓ serum |
| `yuki-tanaka` | UTMB Campaign 1 · C1G0002 | ✓ 84 | ✓ | ◐ 40 | — | ✓ | ✓ |
| `noor-abbasi` | UTMB Campaign 1 · C1G0003 | ✓ 84 | ✓ | ◐ 35 | — | ✓ | ✓ |

✓ có dữ liệu · ◐ thiếu nhiều ngày · — không có → **UNKNOWN**.

**Quy tắc bắt buộc:**
1. Ánh xạ được khai báo trong **`configs/crew_map.yaml`** của `sky-ml` và xuất vào bundle. Không hard-code trong web.
2. UI luôn hiện dòng nguồn: "Dữ liệu analog mặt đất · UTMB CFT70, đối tượng 5160 · nằm giường 70 ngày". Tên phi hành gia là hư cấu, còn số đo là thật.
3. Nếu cần chọn lại người, chỉ chọn trong cohort **không dùng để huấn luyện** (CFT70, C1). Không bao giờ chọn từ Campaign 3.
4. ID 6546 (xung đột GROUP, theo báo cáo CPET) không được dùng làm persona.

---

## 4. Hợp đồng dữ liệu nsac (TypeScript / Drizzle)

### 4.1. `metric` id (dùng chung giữa `sky-ml`, backend và web)

| Chỉ số | `metric` | `unit` | Ghi chú |
|---|---|---|---|
| Nhịp tim | `hr_rest` (đã có) | bpm | Nhịp tim lúc đo vitals buổi sáng |
| Huyết áp | `bp_systolic`, `bp_diastolic` (đã có) | mmHg | |
| Nhiệt độ | `body_temp` **[M]** | °C | Nếu nguồn chỉ có °F thì đổi: (°F − 32) × 5/9, kèm cờ `converted_from_F` |
| Tâm trạng | `mood_tmd` **[M]** + `mood_{tension,depression,anger,vigor,fatigue,confusion}` **[M]** | điểm POMS | TMD cao hơn nghĩa là xáo trộn tâm trạng nhiều hơn. Vigor ngược chiều |
| Giấc ngủ | `sleep_hours` (đã có), `sleep_efficiency` **[M]**, `sleep_latency` **[M]** | h, %, h | Parse `HH:mm` / `H:MM:SS` thành giờ, **không đọc `7:44` thành 7,44** |
| Đường huyết | `glucose_serum` **[M]** | mg/dL | Cờ nguồn `L`/`H` giữ ở `quality_flags` |
| Bổ sung | `resp_rate` **[M]**, `body_mass` **[M]** | rpm, kg | Thay thẻ Respiration fixture |

### 4.2. Migration Drizzle (`apps/backend/src/db/schema/`)

**`readings`:** giữ các cột cũ, thêm:

```ts
phase: text("phase"),                       // pre | in | post
missionDay: integer("mission_day"),         // trục ngày liên tục, có dấu (âm = trước nhiệm vụ)
dataOrigin: text("data_origin").notNull().default("synthetic"), // human_analog | human_spaceflight | terrestrial_proxy | synthetic
cohortRef: text("cohort_ref"),              // "utmb_cft70:5160"
qualityFlags: text("quality_flags"),        // JSON array: ["converted_from_F","source_flag_L"]
bundleVersion: text("bundle_version"),      // "sky-bundle/v2@<sha>"
```

**`deviations`:** thêm các cột còn thiếu:

```ts
astronautId: text("astronaut_id").notNull(),
ts: text("ts").notNull(),
ruleId: text("rule_id").notNull(),          // "HR-Q95", "BASE-MAD-Y", "GLU-REF-LOW"
evidenceLabel: text("evidence_label").notNull(), // NASA-STD | STUDY | LOCAL | HEURISTIC
expectedLow: real("expected_low"), expectedHigh: real("expected_high"),
modelId: text("model_id"),
abstain: integer("abstain", { mode: "boolean" }).notNull().default(false),
```

**Bảng mới `evidence_refs`:** `ref_id, metric, label, n, value, dispersion, source_url, note`. Nạp từ `reference_table.csv`.

### 4.3. Bundle v2 (`sky-ml export-nsac` → `nsac/assets/fixtures/sky-bundle/v2/`)

```text
manifest.json         bundle_version, sky_ml git rev, run_ids, sha256 từng file, nguồn + license
crew_map.json         {astronaut_id: {cohort_ref, cohort_label, available_metrics[]}}
readings.jsonl        một dòng một Reading (khớp schema 4.2): 6 người × các metric ở mục 3
deviations.jsonl      độ lệch tính bằng luật + mô hình (mục 5), kèm rule_id và expected band
evidence_refs.jsonl   bảng tham chiếu có nguồn (STUDY/LOCAL/NASA-STD/HEURISTIC)
model_cards.json      mỗi task: dữ liệu train, cách chia tập, baseline, metric, coverage, external test
reference_panels/     mmash_activity.json, inspiration4_glucose.json (KHÔNG gắn vào phi hành gia nào)
```

Seed nằm ở `apps/backend/src/db/seed/skyBundle.ts` **[M]**:
- đọc bundle → kiểm sha256 → `insert … onConflictDoNothing`;
- gọi từ `server.ts` sau `astronautsRepo.seed()`, có thể tắt bằng `SKY_BUNDLE_DIR`.

### 4.4. API backend mới (`apps/backend/src/server.ts`)

| Route | Trả về | Dùng ở |
|---|---|---|
| `GET /api/astronauts/:id/signals` | Mỗi metric gồm: giá trị mới nhất, `missionDay`, baseline (median/MAD của PRE), expected band, severity, rule_id, freshness, trạng thái `ok/unknown/stale/invalid` | HUD SignalWell (summary) |
| `GET /api/astronauts/:id/readings?metric=&from=&to=` | Chuỗi thời gian thật, có khoảng trống | Focus view (biểu đồ) |
| `GET /api/astronauts/:id/evidence?metric=` | Deviations + evidence_refs + model card rút gọn | Panel "Vì sao?" |
| `GET /api/crew-map` | `crew_map.json` | Dòng nguồn trên UI |

### 4.5. Web (`apps/web/src/features/`)

- `signals/` **[M]**: `api/signals.server.ts` (gọi backend, lỗi thì dùng fixture giống `astronauts.server.ts`), `api/signals.functions.ts`, `model/signals.ts` (thuần, có vitest), `components/SignalWell.tsx`, `SignalFocus.tsx`, `WhyPanel.tsx`.
- `sky-hud/vitals.ts` **[S]**: bỏ 4 fixture cố định. Hiện 6 chỉ số của phi hành gia đang chọn. SpO₂ bỏ khỏi HUD vì không có dữ liệu; thay bằng nhiệt độ hoặc đường huyết.
- `shared/sky.ts` **[S]**: thêm fact id cho kết quả mô hình (MAE, coverage, n) để panel Sky đọc số qua `Fact(id)`.
- `shared/sources.ts` **[S]**: thêm `nlspUtmb`, `utmbCrfVitals`, `utmbPoms`, `utmbActigraphy`, `utmbChem`, `osd575Cmp`, `mmash`, `nasaHrpStandardMeasures`, `nasaHrpArcher`.

---

## 5. Mô hình và luật cho từng chỉ số

| Chỉ số | Task `sky-ml` | Dữ liệu train → test | Baseline bắt buộc | Mô hình | Luật màu |
|---|---|---|---|---|---|
| Nhịp tim, huyết áp, nhiệt độ | `vitals` **[M]**: dự báo giá trị ngày kế tiếp từ 7 ngày trước + phase | **Train:** Campaign 3, LOSO 23 người. **External test:** 6 người CFT70/C1 | Giá trị hôm trước; median 7 ngày | Ridge, LightGBM (cùng fold) | `BASE-MAD-Y/R` (baseline PRE của chính người đó, \|z\| ≥ 3/5) + `*-Q95/Q99` (phân vị phần dư LOSO C3) |
| Nhịp tim (bổ sung) | `hr` (đã có): HR 5 phút tới | MMASH 22 người, LOSO | last_value | ridge (MAE 3,917) | Panel tham chiếu "wearable liên tục"; không gắn vào phi hành gia |
| Tâm trạng | `mood` **[M]**: thay đổi TMD so với baseline PRE | CFT70 POMS 24 người, LOSO; 3 người demo là các fold được giữ ra | Trung bình PRE của chính người đó | Không học máy, vì quá ít điểm/người | `MOOD-MAD-Y` (z ≥ 1,5 so với PRE, `[HEURISTIC]`, tham khảo quy tắc z ≤ −1,5 của Dev 2024 cho Cognition) |
| Hoạt động và giấc ngủ | `sleep_act` **[M]** | C1 actigraphy 3 người (chỉ mô tả); Sleep-EDF (`sleep`, đã có) cho model card | median PRE | Không huấn luyện trên 3 người | `SLEEP-TST-LOW` (< 6 h, `[HEURISTIC]`; lý do 8,5 h theo NASA-STD V6001), `SLEEP-EFF-LOW` (< 85%, PRD, `[HEURISTIC]`) |
| Đường huyết | `glucose` **[M]** | C1 serum 3 người; Inspiration4 CMP làm tham chiếu | Khoảng tham chiếu phòng xét nghiệm (`glucose_range_min/max`, OSD-575) | Không huấn luyện | `GLU-REF-LOW/HIGH` (`[STUDY]`, nguồn OSD-575) + cờ L/H của nguồn |

**Giải thích cho giám khảo:** mô hình vitals được huấn luyện trên 23 người Campaign 3 và chấm điểm trên 6 người thuộc **hai chiến dịch khác** (CFT70 năm 2013, Campaign 1 năm 2004). Đây là kiểm định ngoài cohort. Nếu sai số tăng nhiều so với LOSO, Sky báo đúng con số đó và thu hẹp vùng kỳ vọng, không che giấu.

---

## 6. Diễn giải trên UI (khớp DESIGN.md §14)

| Phần UI | Nội dung | Nguồn trong bundle/API |
|---|---|---|
| Summary signal | `NHỊP TIM 76 bpm · ngày nhiệm vụ 34 · So với baseline trước nhiệm vụ: +9 bpm (median 7 ngày PRE)` | `/signals` |
| Focus view | Trục `mission_day` thật; vùng PRE tô làm baseline; dải kỳ vọng 90%; khoảng trống không nối; bảng dữ liệu tương đương | `/readings`, `/evidence` |
| "Vì sao?" | rule_id, nhãn bằng chứng, `n`, phiên bản ngưỡng, model card (train C3 → test ngoài cohort) | `/evidence` |
| "Đo gì, vì sao đo" | Một câu cho mỗi chỉ số, trích tài nguyên challenge: Standard Measures (vitals, sinh hóa, actigraphy), ARCHeR (actigraphy, tâm trạng), Tempus Pro (thiết bị vitals) | `docs/references/spaceapps-resources-2026/nasa-hrp/*` |
| Trạng thái | `UNKNOWN` (không có dữ liệu cho người này), `STALE` (lần đo cuối quá cũ), `INVALID` (giá trị ngoài miền kỹ thuật) | `/signals.status` |
| Dòng nguồn | "Analog mặt đất · UTMB CFT70 · đối tượng 5160 · tên hiển thị là hư cấu" | `crew_map.json` |

---

## 7. Thay đổi phía `sky-ml` (nasa-hackathon)

| Hạng mục | Thay đổi |
|---|---|
| `copydata.ALLOWLIST` | Thêm `raw/nlsp/CRF.zip` (1,7 MB), `NNX10AP86G.zip` (0,14 MB), `BRSMAct.zip` (6 KB), `MR010G.zip` (0,17 MB), `MR016G.zip` (5,3 MB), `MR085G.zip` (24 KB), `raw/osdr/clinical/OSD-575/*CMP*` (+ `.meta.json`). Tổng thêm khoảng 7,3 MB |
| `configs/tasks.yaml` | Thêm `vitals`, `mood`, `sleep_act`, `glucose` |
| `configs/crew_map.yaml` | **[M]** ánh xạ ở mục 3 |
| `configs/rules.yaml` | **[M]** luật ở mục 5, mỗi luật có `rule_id`, `evidence`, `source` |
| `prepare/utmb.py` | **[M]** đọc member trong ZIP, kiểm SHA-256 + MD5 theo `nlsp/download_manifest.csv`, chuẩn hóa header (mapping tên cột), trục `mission_day` |
| `export_nsac.py` + lệnh `sky-ml export-nsac` | **[M]** ghi bundle v2 (mục 4.3) |

---

## 8. Thứ tự thực hiện (từ 14/11 12:30)

| Mốc | Việc | Repo | Tiêu chí đạt |
|---|---|---|---|
| 12:30–14:00 | `train`/`evaluate` HR (tái lập MAE 3,9174) | nasa-hackathon | Test slow đạt |
| 14:00–16:00 | `prepare/utmb.py` + task `vitals` (C3 LOSO + test ngoài cohort trên 6 người) | nasa-hackathon | Có metrics LOSO và external |
| 14:00–16:00 (song song) | Migration Drizzle (4.2) + seed + 3 route API | nsac `apps/backend` | `bun test` đạt; `/api/astronauts/ayla-reyes/signals` trả 6 metric |
| 16:00–18:00 | Task `mood`, `sleep_act`, `glucose` (luật + tham chiếu); `export-nsac` → bundle v2 | nasa-hackathon | `validate` bundle đạt |
| 18:00–22:00 | Web `features/signals` + HUD 6 chỉ số + panel "Vì sao?" | nsac `apps/web` | Chọn từng phi hành gia → thẻ đổi đúng; UNKNOWN hiện đúng chỗ |
| 15/11 sáng | Model card, SOURCES, demo script; DOX pass ARCHITECTURE/AGENTS | cả hai | — |

**Luật cắt:** nếu đến 15/11 10:00 web chưa đọc được backend, giữ HUD đọc trực tiếp `sky-bundle/v2` bằng import tĩnh (server function), bỏ route `/evidence`.

---

## 9. Quyết định cần chốt và rủi ro

| ID | Vấn đề | Đề xuất |
|---|---|---|
| D1 | NASA-STD-3001 Rev B hay Rev C | Chuyển sang Rev C. Nếu không kịp, ghi rõ "Rev B, đã được Rev C thay thế" |
| D2 | Gắn tên hư cấu với người thật đã khử định danh | Chấp nhận được (ID số, không PII) nếu UI luôn hiện dòng nguồn. Không dùng ngày thật (mục 2.2) |
| D3 | Thẻ SpO₂ trên HUD không có dữ liệu | Thay bằng nhiệt độ. Nếu giữ SpO₂ thì phải hiện UNKNOWN |
| D4 | Ngưỡng tâm trạng z ≥ 1,5 là heuristic | Ghi `[HEURISTIC]` và trích Dev 2024 làm bối cảnh, không gọi là chuẩn |
| D5 | Dữ liệu nằm giường không phải dữ liệu bay | Model card và dòng nguồn ghi "analog mặt đất". Inspiration4 (bay thật, n = 4) chỉ là tham chiếu glucose |
| D6 | Header CRF khác nhau giữa các file | Mapping tường minh trong `prepare/utmb.py` + test cho cả 4 kiểu header đã thấy |

---

## 10. Nguồn

**Dữ liệu**
- NASA Life Sciences Portal, UTMB Campaign 1 / Campaign 3 / CFT70 (CRF Daily Vitals, NNX10AP86G POMS, BRSMAct, MR010G, MR016G, MR085G). https://nlsp.nasa.gov/
- NASA OSDR OSD-575 (Inspiration4 CMP). https://osdr.nasa.gov/bio/repo/data/studies/OSD-575
- Rossi A. et al. *MMASH*, PhysioNet, doi:10.13026/cerq-fc86 (ODbL 1.0).

**Tài nguyên challenge** (bản lưu trong nsac `docs/references/spaceapps-resources-2026/nasa-hrp/`)
- Standard Measures: https://www.nasa.gov/reference/standard-measures
- ARCHeR: https://www.nasa.gov/reference/archer
- Tempus Pro: https://www.nasa.gov/reference/tempus-pro

**Chuẩn và phương pháp**
- NASA-STD-3001 Vol 1 Rev C (2023).
- Dev S.I. et al. (2024). *Front Physiol*, doi:10.3389/fphys.2024.1451269.
- Angelopoulos A.N., Bates S. (2021). arXiv:2107.07511.
- Varoquaux G. (2018). *NeuroImage* 180:68–77.
- Collins G.S. et al. (2024). *TRIPOD+AI*. BMJ 385:e078378.
