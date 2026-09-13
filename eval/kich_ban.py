"""Chạy bộ kịch bản nghiệm thu và in bảng kết quả.

    python eval/kich_ban.py            # bảng cho người đọc
    python eval/kich_ban.py --markdown # bảng Markdown, dán thẳng vào báo cáo
    python eval/kich_ban.py --chi-tiet # kèm kết quả thực tế của từng ca

Thoát mã 1 nếu có ca không đạt, nên dùng được trong CI.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "src"))

from tra_cuu_gtdb.kiem_thu.kich_ban import KICH_BAN, kiem_mot_ca  # noqa: E402
from tra_cuu_gtdb.reasoning.engine import TraCuuPhapLuat  # noqa: E402


def main() -> int:
    bd = argparse.ArgumentParser(description=__doc__)
    bd.add_argument("--markdown", action="store_true", help="in bảng Markdown")
    bd.add_argument("--chi-tiet", action="store_true", help="in kết quả thực tế")
    ts = bd.parse_args()

    ht = TraCuuPhapLuat()
    ket: list[tuple[object, list[str], float]] = []
    for ca in KICH_BAN:
        t0 = time.perf_counter()
        loi = kiem_mot_ca(ht.hoi(ca.cau_hoi, top_k=5), ca)
        ket.append((ca, loi, (time.perf_counter() - t0) * 1000))

    so_dat = sum(1 for _, loi, _ in ket if not loi)

    if ts.markdown:
        print("| Mã | Nhóm | Câu hỏi | Kỳ vọng | Kết quả |")
        print("|---|---|---|---|---|")
        for ca, loi, _ in ket:
            ky_vong = ca.ghi_chu or ca.lop or "—"
            print(f"| {ca.ma} | {ca.nhom} | {ca.cau_hoi} | {ky_vong} | "
                  f"{'ĐẠT' if not loi else 'KHÔNG ĐẠT — ' + '; '.join(loi)} |")
    else:
        nhom_hien = None
        for ca, loi, ms in ket:
            if ca.nhom != nhom_hien:
                nhom_hien = ca.nhom
                print(f"\n── {nhom_hien} " + "─" * (58 - len(nhom_hien)))
            print(f"  {'DAT ' if not loi else 'HONG'} {ca.ma}  {ca.cau_hoi[:52]:<52} {ms:5.1f} ms")
            if ca.ghi_chu and ts.chi_tiet:
                print(f"         ky vong: {ca.ghi_chu}")
            for x in loi:
                print(f"         -> {x}")

    print(f"\n{so_dat}/{len(ket)} ca ĐẠT")
    return 0 if so_dat == len(ket) else 1


if __name__ == "__main__":
    raise SystemExit(main())
