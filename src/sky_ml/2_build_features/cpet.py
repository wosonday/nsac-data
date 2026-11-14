"""UTMB CFT70 (MR080G + 2 bảng đối chiếu GROUP) → một hàng / người: VO2peak PRE → thay đổi tại POST1.

Port nguyên logic của NASA-cl/src/nasa_cl/cpet.py (load_verified, canonicalize, build_task):
kiểm SHA-256 + MD5 từng member ZIP theo download_manifest.csv, gắn cờ QC, chỉ giữ người đủ điều kiện.
Không sửa giá trị nguồn. Ngưỡng QC (HRPK < 20, sai lệch công thức VO2 > 5 %) là ngưỡng KỸ THUẬT thăm dò.
"""
import hashlib
import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

GROUPS = ("CONTROL", "EXERCISE", "FLY")
VISITS = ("PRE", "POST1", "POST2")
REFERENCES = [("MR079G.zip", "cft70/MR079G_CFT70/MR079G_CFT70_Demographics_ALL.csv", "MR079G"),
              ("BRSMImmune.zip", "cft70/BRSMIMMUNE_CFT70/BRSMIMMUNE_CFT70_obsv_All.csv", "BRSMImmune")]


def _verified_csv(zf: zipfile.ZipFile, manifest: pd.DataFrame, archive: str, member: str) -> pd.DataFrame:
    m = manifest[manifest.archive_path.eq(archive) & manifest.member_path.eq(member)]
    if len(m) != 1 or m.iloc[0].status != "downloaded_verified":
        raise ValueError(f"Thiếu hoặc trùng bản ghi manifest đã xác minh: {member}")
    data = zf.read(member)
    if hashlib.sha256(data).hexdigest() != m.iloc[0].sha256 or hashlib.md5(data).hexdigest() != m.iloc[0].source_md5:
        raise ValueError(f"Sai hash nguồn: {member}")
    return pd.read_csv(io.BytesIO(data))


def load_verified(nlsp: Path) -> tuple[pd.DataFrame, dict]:
    manifest = pd.read_csv(nlsp / "download_manifest.csv", keep_default_na=False)
    with zipfile.ZipFile(nlsp / "MR080G.zip") as zf:
        frame = pd.concat([_verified_csv(zf, manifest, "MR080G.zip", f"cft70/MR080G_CFT70/MR080G_CFT70_{v}_ALL.csv")
                           .assign(visit=v) for v in VISITS], ignore_index=True)
    references: dict = {}
    for archive, member, source in REFERENCES:
        with zipfile.ZipFile(nlsp / archive) as zf:
            d = _verified_csv(zf, manifest, archive, member)
        subject = next(c for c in d if c.lower() == "subject")
        group = next(c for c in d if c.lower() in ("group", "grouplabel"))
        for sid, g in d.groupby(subject):
            labels = sorted(set(g[group].dropna().astype(str).str.strip().str.upper()))
            references.setdefault(str(sid).removesuffix(".0"), {})[source] = ",".join(labels)
    return frame, references


def canonicalize(frame: pd.DataFrame, references: dict) -> pd.DataFrame:
    """Mỗi visit một hàng: giá trị nguồn + trạng thái GROUP + cờ QC (cpet_qc_pass)."""
    rows = []
    for _, r in frame.iterrows():
        sid = str(r.SUBJECT).removesuffix(".0")
        group = str(r.GROUP).strip().upper()
        evidence = {"MR080G": group, **references.get(sid, {})}
        labels = {str(v).strip().upper() for v in evidence.values() if pd.notna(v) and str(v).strip()}
        refs = {str(v).strip().upper() for k, v in evidence.items() if k != "MR080G" and pd.notna(v) and str(v).strip()}
        # "EXERCISE + TESTOSTERONE" là nhóm con của EXERCISE theo protocol CFT70 → không coi là mâu thuẫn
        normalized = {"EXERCISE" if v == "EXERCISE + TESTOSTERONE" else v for v in labels}
        parent = "EXERCISE" if group == "EXERCISE + TESTOSTERONE" else group
        status = ("unresolved_conflict" if len(normalized) > 1 else
                  "consistent" if refs and parent in GROUPS else "unverified")
        num = {c: pd.to_numeric(pd.Series([r.get(c)]), errors="coerce").iloc[0]
               for c in ["REL VO2PK", "VO2PK", "WEIGHT", "HRPK", "AGE", "BR DAY"]}
        rel, absolute, weight, peak = num["REL VO2PK"], num["VO2PK"], num["WEIGHT"], num["HRPK"]
        date = pd.to_datetime(str(r.DATE), format="%m/%d/%Y", errors="coerce")
        flags = []
        if not np.isfinite(rel) or rel <= 0:
            flags.append("relative_vo2_missing_or_nonpositive")
        if not np.isfinite(peak):
            flags.append("peak_hr_missing")
        elif peak < 20:
            flags.append("peak_hr_below_20")
        if all(np.isfinite(v) and v > 0 for v in [rel, absolute, weight]):
            if abs(100 * (absolute * 1000 / weight / rel - 1)) > 5:
                flags.append("vo2_identity_error_gt_5pct")
        else:
            flags.append("vo2_identity_inputs_invalid")
        if pd.isna(date):
            flags.append("invalid_date")
        if not np.isfinite(num["BR DAY"]) or num["BR DAY"] < 0:
            flags.append("invalid_phase_day")
        rows.append({"person_id": "utmb_cft70:" + sid, "visit": r.visit,
                     "observed_date": "" if pd.isna(date) else date.date().isoformat(),
                     "group": parent if status == "consistent" else "", "group_status": status,
                     "rel_vo2pk": rel, "age": num["AGE"], "qc_pass": not flags, "qc_flags": ";".join(flags)})
    out = pd.DataFrame(rows)
    if out.empty or out.duplicated(["person_id", "visit"]).any():
        raise ValueError("Trùng người/visit hoặc dữ liệu CPET rỗng")
    return out


def build_task(visits: pd.DataFrame) -> pd.DataFrame:
    """Mỗi người có PRE một hàng; `eligible` = qua mọi điều kiện, `exclusion_reason` ghi lý do loại."""
    rows = []
    for _, pre in visits[visits.visit.eq("PRE")].sort_values("person_id").iterrows():
        posts = visits[visits.person_id.eq(pre.person_id) & visits.visit.eq("POST1")]
        if len(posts) > 1:
            raise ValueError("Trùng visit POST1")
        post = posts.iloc[0] if len(posts) else None
        reasons = []
        if not pre.qc_pass:
            reasons.append("PRE_cpet_qc")
        if pre.group_status != "consistent":
            reasons.append("PRE_group_unresolved")
        if not np.isfinite(pre.age):
            reasons.append("missing_PRE_age")
        if post is None:
            reasons.append("missing_POST1")
        else:
            if not post.qc_pass:
                reasons.append("POST1_cpet_qc")
            if post.group_status != "consistent" or post.group != pre.group:
                reasons.append("POST1_group_unresolved")
            if not pre.observed_date or not post.observed_date or post.observed_date <= pre.observed_date:
                reasons.append("invalid_visit_chronology")
        target = np.nan if post is None else post.rel_vo2pk
        rows.append({"subject_id": pre.person_id, "pre_vo2": pre.rel_vo2pk, "age": pre.age, "group": pre.group,
                     "delta_vo2": target - pre.rel_vo2pk, "eligible": not reasons,
                     "exclusion_reason": ";".join(reasons)})
    return pd.DataFrame(rows)


def cpet_table(task: pd.DataFrame) -> pd.DataFrame:
    t = task[task.eligible].sort_values("subject_id").reset_index(drop=True)
    table = t[["subject_id", "pre_vo2", "age"]].copy()
    for g in GROUPS:
        table[f"group_{g}"] = (t.group == g).to_numpy(float)
    table["delta_vo2"] = t.delta_vo2.to_numpy()
    return table


def build_cpet(data_dir: Path, cfg: dict) -> tuple[pd.DataFrame, list[str]]:
    frame, references = load_verified(data_dir / Path(cfg["inputs"][0]).parent)
    task = build_task(canonicalize(frame, references))
    table = cpet_table(task)
    unknown = set(cfg["features"]) - set(table.columns)
    if unknown:
        raise ValueError(f"Đặc trưng CPET không tồn tại: {sorted(unknown)}; có: {list(table.columns[1:-1])}")
    table.attrs["excluded"] = task[~task.eligible][["subject_id", "exclusion_reason"]]
    return table, list(cfg["features"])
