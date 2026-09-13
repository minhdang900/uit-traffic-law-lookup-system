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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from traffic_law.acceptance.scenarios import SCENARIOS, check_scenario  # noqa: E402
from traffic_law.reasoning.engine import LawLookup  # noqa: E402


def main() -> int:
    bd = argparse.ArgumentParser(description=__doc__)
    bd.add_argument("--markdown", action="store_true", help="in bảng Markdown")
    bd.add_argument("--chi-tiet", action="store_true", help="in kết quả thực tế")
    ts = bd.parse_args()

    ht = LawLookup()
    ket: list[tuple[object, list[str], float]] = []
    for ca in SCENARIOS:
        t0 = time.perf_counter()
        errors = check_scenario(ht.ask(ca.question, top_k=5), ca)
        ket.append((ca, errors, (time.perf_counter() - t0) * 1000))

    so_dat = sum(1 for _, errors, _ in ket if not errors)

    if ts.markdown:
        print("| Mã | Nhóm | Câu hỏi | Kỳ vọng | Kết quả |")
        print("|---|---|---|---|---|")
        for ca, errors, _ in ket:
            expectation = ca.note or ca.lop or "—"
            print(f"| {ca.code} | {ca.group} | {ca.question} | {expectation} | "
                  f"{'ĐẠT' if not errors else 'KHÔNG ĐẠT — ' + '; '.join(errors)} |")
    else:
        nhom_hien = None
        for ca, errors, ms in ket:
            if ca.group != nhom_hien:
                nhom_hien = ca.group
                print(f"\n── {nhom_hien} " + "─" * (58 - len(nhom_hien)))
            print(f"  {'DAT ' if not errors else 'HONG'} {ca.code}  {ca.question[:52]:<52} {ms:5.1f} ms")
            if ca.note and ts.chi_tiet:
                print(f"         ky vong: {ca.note}")
            for x in errors:
                print(f"         -> {x}")

    print(f"\n{so_dat}/{len(ket)} ca ĐẠT")
    return 0 if so_dat == len(ket) else 1


if __name__ == "__main__":
    raise SystemExit(main())
