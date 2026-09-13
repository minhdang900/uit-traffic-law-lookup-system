"""Suy diễn khoảng hiệu lực cho từng điều khoản trong cơ sở tri thức.

Không nhập ngày thủ công: mỗi mẩu tri thức đã có ``can_cu.van_ban`` trỏ tới văn
bản nguồn, và mỗi văn bản có ``ngay_hieu_luc``. Quy tắc suy diễn:

    hieu_luc.tu   = ngày hiệu lực của văn bản nguồn
                    (hoặc của văn bản SỬA ĐỔI, nếu điều khoản đã bị sửa —
                     vì bản ghi hiện lưu chính là nội dung SAU sửa đổi)
    hieu_luc.den  = None (còn hiệu lực)

Script tất định và idempotent: chạy nhiều lần cho kết quả giống hệt nhau.

Chạy:  python scripts/suy_dien_hieu_luc.py [--kiem-tra]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
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


def infer(ban_ghi: dict, ban_do: dict[str, date]) -> dict | None:
    """Trả về khoảng hiệu lực cho một bản ghi, hoặc None nếu không suy được."""
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
    tong_doi = tong_thieu = 0

    for name in ("violations.json", "rules.json"):
        data = _nap(name)
        doi = missing = 0
        for r in data:
            moi = infer(r, ban_do)
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
