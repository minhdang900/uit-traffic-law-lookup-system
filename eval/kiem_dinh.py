"""
kiem_dinh.py -- Kiểm định độc lập các chỉ số mà evaluate.py công bố.

evaluate.py trả lời "hệ thống đạt bao nhiêu". Tệp này trả lời "con số đó tin
được tới đâu", bằng tám phép thử chỉ đọc:

  1. Chấm được     : mọi định danh đáp án có tồn tại, đúng loại tri thức không
  2. Sai số        : khoảng tin cậy 95% (Wilson) cho Top-1/Top-5/phân lớp, theo lớp
  3. Trần precision: trả 5 kết quả cho câu 1 đáp án thì precision tối đa 0,20
  4. Đủ đáp án     : câu nhiều đáp án (tình huống P5) có tìm được TẤT CẢ không
  5. Bỏ dấu        : bỏ dấu cả 120 câu rồi chấm lại
  6. McNemar       : suy diễn số học (C -> D) cải thiện thật hay may rủi
  7. Ngoài miền    : cấu hình mặc định làm gì với 40 truy vấn rác
  8. Trùng lặp     : ca nghiệm thu nào trùng nguyên văn câu trong bộ đánh giá

Chạy:  python eval/kiem_dinh.py [--ghi]
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))
sys.path.insert(0, os.path.join(BASE, "eval"))
from evaluate import lay_id_tra_ve  # noqa: E402

from traffic_law.acceptance.scenarios import SCENARIOS  # noqa: E402
from traffic_law.kb.text import strip_accents  # noqa: E402
from traffic_law.reasoning.engine import LawLookup  # noqa: E402

TEP_KB = {"concept": "concepts", "rule": "rules", "violation": "violations"}


def wilson(k, n, z=1.96):
    """Khoảng tin cậy Wilson cho tỷ lệ k/n — không vỡ khi k = 0 hoặc k = n như xấp xỉ chuẩn."""
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round((c - h) / d, 4), round((c + h) / d, 4)


def mcnemar_chinh_xac(b, c):
    """p hai phía của kiểm định McNemar chính xác (nhị thức) trên b, c cặp bất đồng."""
    if b + c == 0:
        return 1.0
    duoi = sum(math.comb(b + c, i) for i in range(min(b, c) + 1))
    return min(1.0, 2 * duoi / 2 ** (b + c))


def cham(ht, ds, bien_doi=lambda q: q, k=5):
    """Chấm từng câu, trả về một dòng chi tiết cho mỗi câu (cùng quy tắc với evaluate.py)."""
    dong = []
    for m in ds:
        kq = ht.ask(bien_doi(m["cau_hoi"]), top_k=k)
        toan_bo = lay_id_tra_ve(kq, m["loai_tri_thuc"])
        la_ds = (kq.get("summary") or {}).get("kind") in ("danh_sach", "citation")
        tra_ve = toan_bo if la_ds else toan_bo[:k]
        vang, tap = set(m["id_tri_thuc_dung"]), set(tra_ve)
        dong.append({
            "id": m["id"], "lop": m["lop_bai_toan_dung"],
            "dung_lop": kq["problem_class"] == m["lop_bai_toan_dung"],
            "top1": bool(tra_ve) and tra_ve[0] in vang, "topk": bool(vang & tap),
            "du_dap_an": vang <= tap, "so_dap_an": len(vang),
            "p": len(vang & tap) / len(tap) if tap else 0.0,
            "tran_p": min(len(vang), len(tap)) / len(tap) if tap else 0.0,
        })
    return dong


def ty_le(dong, khoa):
    """Đếm số dòng đạt theo một khoá, kèm tỷ lệ và khoảng tin cậy 95%."""
    k = sum(d[khoa] for d in dong)
    return {"dat": k, "n": len(dong), "ty_le": round(k / len(dong), 4),
            "ktc95": wilson(k, len(dong))}


def main():
    """Chạy tám phép thử, in bảng tóm tắt và (tuỳ chọn) ghi kết quả ra JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ghi", action="store_true", help="ghi eval/ket_qua_kiem_dinh.json")
    a = ap.parse_args()

    ht = LawLookup()
    with open(os.path.join(BASE, "eval", "qa_dataset.json"), encoding="utf-8") as f:
        ds = json.load(f)
    with open(os.path.join(BASE, "eval", "truy_van_ngoai_mien.json"), encoding="utf-8") as f:
        ngoai_mien = [t["cau_hoi"] for t in json.load(f)["truy_van"]]
    kb_ids = {}
    for loai, tep in TEP_KB.items():
        with open(os.path.join(BASE, "data", "kb", tep + ".json"), encoding="utf-8") as f:
            kb_ids[loai] = {x["id"] for x in json.load(f)}
    kq = {}

    # 1. cham duoc
    treo = [(m["id"], g) for m in ds for g in m["id_tri_thuc_dung"]
            if g not in kb_ids[m["loai_tri_thuc"]]]
    kq["cham_duoc"] = {"so_cau": len(ds), "dinh_danh_treo": treo}

    goc = cham(ht, ds)

    # 2. sai so
    theo_lop = defaultdict(list)
    for d in goc:
        theo_lop[d["lop"]].append(d)
    kq["khoang_tin_cay"] = {
        "top1": ty_le(goc, "top1"), "top5": ty_le(goc, "topk"),
        "phan_lop": ty_le(goc, "dung_lop"),
        "top1_theo_lop": {lop: ty_le(v, "top1") for lop, v in sorted(theo_lop.items())},
    }

    # 3. tran precision
    p, tran = sum(d["p"] for d in goc), sum(d["tran_p"] for d in goc)
    kq["tran_precision"] = {"precision": round(p / len(goc), 4),
                            "tran": round(tran / len(goc), 4),
                            "dat_duoc_so_voi_tran": round(p / tran, 4)}

    # 4. du dap an (cau nhieu dap an)
    nhieu = [d for d in goc if d["so_dap_an"] > 1]
    kq["du_dap_an"] = {
        "cau_nhieu_dap_an": ty_le(nhieu, "du_dap_an"),
        "theo_lop": {lop: ty_le([d for d in nhieu if d["lop"] == lop], "du_dap_an")
                     for lop in sorted({d["lop"] for d in nhieu})},
    }

    # 5. bo dau
    bo_dau = cham(ht, ds, strip_accents)
    kq["bo_dau"] = {
        "top1": ty_le(bo_dau, "top1"), "top5": ty_le(bo_dau, "topk"),
        "phan_lop": ty_le(bo_dau, "dung_lop"),
        "top1_theo_lop": {lop: {"co_dau": sum(d["top1"] for d in goc if d["lop"] == lop),
                                "bo_dau": sum(d["top1"] for d in bo_dau if d["lop"] == lop),
                                "n": len(v)}
                          for lop, v in sorted(theo_lop.items())},
    }

    # 6. McNemar: C (tat suy dien so hoc) vs D (day du)
    luu = ht.kb.numeric.theo_dai_luong
    ht.kb.numeric.theo_dai_luong = {}
    try:
        cau_hinh_c = cham(ht, ds)
    finally:
        ht.kb.numeric.theo_dai_luong = luu
    b = sum(1 for x, y in zip(cau_hinh_c, goc, strict=True) if y["top1"] and not x["top1"])
    c = sum(1 for x, y in zip(cau_hinh_c, goc, strict=True) if x["top1"] and not y["top1"])
    kq["mcnemar_suy_dien_so_hoc"] = {"sai_thanh_dung": b, "dung_thanh_sai": c,
                                     "p": round(mcnemar_chinh_xac(b, c), 6)}

    # 7. ngoai mien o cau hinh mac dinh
    so_muc = [sum(len(r[x]) for x in ("concepts", "rules", "violations"))
              for r in (ht.ask(q, top_k=5) for q in ngoai_mien)]
    kq["ngoai_mien"] = {"so_truy_van": len(ngoai_mien),
                        "van_tra_ve_ket_qua": sum(1 for s in so_muc if s > 0)}

    # 8. trung lap ca nghiem thu
    cau = {m["cau_hoi"].strip().lower(): m["id"] for m in ds}
    kq["ca_nghiem_thu_trung_bo_danh_gia"] = {
        s.code: cau[s.question.strip().lower()]
        for s in SCENARIOS if s.question.strip().lower() in cau}

    # ---- in bao cao
    kt, bd, mc = kq["khoang_tin_cay"], kq["bo_dau"], kq["mcnemar_suy_dien_so_hoc"]

    def pct(x):
        return "%.1f%%" % (100 * x)

    def ktc(x):
        return "[%s, %s]" % (pct(x["ktc95"][0]), pct(x["ktc95"][1]))

    print("=" * 74)
    print("KIEM DINH CHI SO — %d cau hoi, %d truy van ngoai mien" % (len(ds), len(ngoai_mien)))
    print("=" * 74)
    print("1. Dinh danh dap an treo : %d" % len(treo))
    print("2. Top-1 %s KTC95 %s" % (pct(kt["top1"]["ty_le"]), ktc(kt["top1"])))
    print("   Top-5 %s KTC95 %s" % (pct(kt["top5"]["ty_le"]), ktc(kt["top5"])))
    for lop, v in kt["top1_theo_lop"].items():
        print("   %-26s %2d/%-3d KTC95 %s" % (lop, v["dat"], v["n"], ktc(v)))
    tp = kq["tran_precision"]
    print("3. Precision %.4f / tran %.4f = %s tran"
          % (tp["precision"], tp["tran"], pct(tp["dat_duoc_so_voi_tran"])))
    for lop, v in kq["du_dap_an"]["theo_lop"].items():
        print("4. Du dap an %-24s %d/%d" % (lop, v["dat"], v["n"]))
    print("5. Bo dau: Top-1 %s  Top-5 %s  phan lop %s"
          % (pct(bd["top1"]["ty_le"]), pct(bd["top5"]["ty_le"]), pct(bd["phan_lop"]["ty_le"])))
    for lop, v in bd["top1_theo_lop"].items():
        if v["co_dau"] != v["bo_dau"]:
            print("   %-26s co dau %d/%d -> bo dau %d/%d"
                  % (lop, v["co_dau"], v["n"], v["bo_dau"], v["n"]))
    print("6. McNemar C->D: %d sai->dung, %d dung->sai, p = %.4g" % (b, c, mc["p"]))
    print("7. Ngoai mien van tra ket qua : %d/%d"
          % (kq["ngoai_mien"]["van_tra_ve_ket_qua"], len(ngoai_mien)))
    print("8. Ca nghiem thu trung bo danh gia: %s"
          % (kq["ca_nghiem_thu_trung_bo_danh_gia"] or "khong co"))

    if a.ghi:
        out = os.path.join(BASE, "eval", "ket_qua_kiem_dinh.json")
        with open(out, "w", encoding="utf-8") as f:
            json.dump(kq, f, ensure_ascii=False, indent=1)
        print("\n-> Da ghi: %s" % out)


if __name__ == "__main__":
    main()
