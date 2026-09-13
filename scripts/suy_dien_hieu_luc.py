"""Suy diễn khoảng hiệu lực cho từng điều khoản trong cơ sở tri thức.

Không nhập ngày thủ công: mỗi mẩu tri thức đã có ``can_cu.van_ban`` trỏ tới văn
bản nguồn, và mỗi văn bản có ``ngay_hieu_luc``. Quy tắc suy diễn:

    hieu_luc.tu   = ngày hiệu lực của văn bản nguồn
                    (hoặc của văn bản SỬA ĐỔI, nếu điều khoản đã bị sửa —
                     vì bản ghi hiện lưu chính là nội dung SAU sửa đổi)
    hieu_luc.den  = ngày TRƯỚC ngày văn bản sửa đổi có hiệu lực, nếu điều khoản bị
                    văn bản đó BÃI BỎ (đọc từ amendments.json); còn lại None

Hai ngoại lệ đều lấy từ chính văn bản pháp luật, không phải phỏng đoán:

- "Bãi bỏ điểm d, điểm đ… khoản 17 Điều 32" chấm dứt hiệu lực các điểm đó.
  "Bỏ cụm từ…" thì KHÔNG — đó chỉ là sửa câu chữ, điều khoản vẫn còn.
- Điều khoản có ngày hiệu lực riêng do văn bản quy định (``HIEU_LUC_RIENG``),
  mỗi dòng bắt buộc kèm căn cứ.

Script tất định và idempotent: chạy nhiều lần cho kết quả giống hệt nhau.

Chạy:  python scripts/suy_dien_hieu_luc.py [--kiem-tra]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THU_MUC_KB = ROOT / "data" / "kb"


def _nap(name: str) -> list[dict]:
    with (THU_MUC_KB / name).open(encoding="utf-8") as f:
        return json.load(f)


def _ghi(name: str, data: list[dict]) -> None:
    with (THU_MUC_KB / name).open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


#: Điều khoản mà văn bản quy định ngày hiệu lực RIÊNG, khác ngày của văn bản chứa nó.
HIEU_LUC_RIENG: dict[str, tuple[str, str]] = {
    "VP_BS_SD_31_2": ("2028-01-01",
                      "khoản 3 Điều 53 Nghị định 168/2024/NĐ-CP: điểm b khoản 9a Điều 32 "
                      "(xe vận tải nội bộ) có hiệu lực thi hành từ 01/01/2028"),
}

#: "Bãi bỏ điểm d, điểm đ, điểm e, điểm g khoản 17 Điều 32."
_BAI_BO = re.compile(r"Bãi bỏ ((?:điểm [a-zđ]+(?:, )?)+) khoản (\d+[a-z]?) Điều (\d+)")
VAN_BAN_BI_SUA = "168/2024/NĐ-CP"


def _ban_do_bai_bo(amendments: list[dict], ban_do: dict[str, date]) -> dict[tuple, date]:
    """(điều, khoản, điểm) của Nghị định 168 bị bãi bỏ → ngày cuối còn hiệu lực."""
    ra: dict[tuple, date] = {}
    for a in amendments:
        m = _BAI_BO.search(a.get("noi_dung_moi") or "") if a.get("loai") == "bai_bo" else None
        sh = _tim_so_hieu(str(a.get("can_cu", {}).get("van_ban", "")), ban_do) if m else None
        if not (m and sh):
            continue
        for diem in re.findall(r"điểm ([a-zđ]+)", m.group(1)):
            ra[(int(m.group(3)), m.group(2), diem)] = ban_do[sh] - timedelta(days=1)
    return ra


def _ban_do_hieu_luc(documents: list[dict]) -> dict[str, date]:
    """Ánh xạ số hiệu văn bản → ngày hiệu lực."""
    return {v["so_hieu"]: date.fromisoformat(v["ngay_hieu_luc"]) for v in documents}


def _tim_so_hieu(chuoi: str, ban_do: dict[str, date]) -> str | None:
    """Tìm số hiệu văn bản xuất hiện trong một chuỗi tự do."""
    for number in sorted(ban_do, key=len, reverse=True):
        if number in chuoi:
            return number
    # Dự phòng: bắt theo mẫu "168/2024/NĐ-CP" rồi đối chiếu
    m = re.search(r"\d+/\d{4}/[A-ZĐ\-]+", chuoi)
    return m.group(0) if m and m.group(0) in ban_do else None


def infer(ban_ghi: dict, ban_do: dict[str, date],
          bai_bo: dict[tuple, date] | None = None) -> dict | None:
    """Trả về khoảng hiệu lực cho một bản ghi, hoặc None nếu không suy được."""
    kq = _infer_bat_dau(ban_ghi, ban_do)
    if kq is None:
        return None
    if ban_ghi.get("id") in HIEU_LUC_RIENG:
        kq["tu"] = HIEU_LUC_RIENG[ban_ghi["id"]][0]
    cc = ban_ghi.get("can_cu") or {}
    if bai_bo and VAN_BAN_BI_SUA in str(cc.get("van_ban", "")):
        het = bai_bo.get((cc.get("dieu"), str(cc.get("khoan")), cc.get("diem")))
        if het is not None:
            kq["den"] = het.isoformat()
    return kq


def _infer_bat_dau(ban_ghi: dict, ban_do: dict[str, date]) -> dict | None:
    amended_by = ban_ghi.get("sua_doi_boi")
    if amended_by:
        sh = _tim_so_hieu(str(amended_by), ban_do)
        if sh:
            # Bản ghi hiện lưu là nội dung SAU sửa đổi, nên hiệu lực tính từ
            # ngày văn bản sửa đổi có hiệu lực.
            return {"tu": ban_do[sh].isoformat(), "den": None}
    sh = _tim_so_hieu(str(ban_ghi.get("can_cu", {}).get("van_ban", "")), ban_do)
    return {"tu": ban_do[sh].isoformat(), "den": None} if sh else None


def chay(kiem_tra: bool = False) -> int:
    ban_do = _ban_do_hieu_luc(_nap("documents.json"))
    bai_bo = _ban_do_bai_bo(_nap("amendments.json"), ban_do)
    tong_doi = tong_thieu = 0

    for name in ("violations.json", "rules.json"):
        data = _nap(name)
        doi = missing = 0
        for r in data:
            moi = infer(r, ban_do, bai_bo)
            if moi is None:
                missing += 1
                continue
            if r.get("hieu_luc") != moi:
                doi += 1
                if not kiem_tra:
                    r["hieu_luc"] = moi
        if not kiem_tra and doi:
            _ghi(name, data)
        print(f"{name:20s} n={len(data):4d}  cập nhật={doi:4d}  không suy được={missing}")
        tong_doi += doi
        tong_thieu += missing

    if kiem_tra:
        if tong_doi:
            print(f"\n❌ Còn {tong_doi} bản ghi chưa có khoảng hiệu lực đúng.")
            return 1
        print("\n✅ Mọi bản ghi đã có khoảng hiệu lực đúng (idempotent).")
    if tong_thieu:
        print(f"⚠️  {tong_thieu} bản ghi không suy được văn bản nguồn.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kiem-tra", action="store_true",
                    help="chỉ kiểm tra, không ghi tệp (dùng cho CI)")
    sys.exit(chay(ap.parse_args().kiem_tra))
