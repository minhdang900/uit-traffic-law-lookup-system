"""
evaluate.py -- Đánh giá thực nghiệm hệ thống tra cứu kiến thức pháp luật.

Đo các chỉ số:
  1. Độ chính xác phân loại lớp bài toán
  2. Độ chính xác truy hồi tri thức: Top-1 / Top-3 / Top-5, MRR
  3. Precision / Recall / F1 (macro) trên tập tri thức trả về
  4. Thống kê theo từng lớp bài toán và theo độ khó
  5. Thời gian trả lời trung bình

Chạy:  python3 tests/evaluate.py [--k 5] [--out tests/ket_qua_danh_gia.json]
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))
from tra_cuu_gtdb.reasoning.engine import TraCuuPhapLuat  # noqa: E402

DATASET = os.path.join(BASE, "eval", "qa_dataset.json")


def lay_id_tra_ve(kq, loai):
    """Lấy danh sách định danh tri thức hệ thống trả về, theo đúng loại cần đánh giá."""
    if loai == "concept":
        return [c["id"] for c in kq["khai_niem"]]
    if loai == "rule":
        return [r["id"] for r in kq["quy_tac"]]
    return [v["id"] for v in kq["hanh_vi"]]


def danh_gia(k=5, chi_tiet=False):
    """Chạy toàn bộ bộ câu hỏi kiểm thử, tính các chỉ số đánh giá và trả về
    (bảng chỉ số tổng hợp, danh sách câu trả lời chưa đúng).
    """
    ht = TraCuuPhapLuat()
    with open(DATASET, encoding="utf-8") as f:
        ds = json.load(f)

    n = len(ds)
    dung_lop = 0
    top1 = top3 = topk = 0
    mrr = 0.0
    P = R = F = 0.0
    thoi_gian = []
    theo_lop = defaultdict(lambda: {"n": 0, "lop": 0, "top1": 0, "topk": 0})
    theo_do_kho = defaultdict(lambda: {"n": 0, "topk": 0})
    loi = []

    for m in ds:
        t0 = time.time()
        kq = ht.hoi(m["cau_hoi"], top_k=k)
        thoi_gian.append(time.time() - t0)

        lop_dung = kq["lop_bai_toan"] == m["lop_bai_toan_dung"]
        dung_lop += lop_dung

        vang = list(dict.fromkeys(m["id_tri_thuc_dung"]))
        toan_bo = lay_id_tra_ve(kq, m["loai_tri_thuc"])
        # Cau hoi dang DANH SACH (P4): he thong tra ve tron ven mot TAP hop
        # thoa rang buoc -> danh gia tren toan bo tap, khong cat theo top-k.
        la_danh_sach = (kq.get("tong_hop") or {}).get("kieu") in ("danh_sach", "can_cu")
        tra_ve = toan_bo if la_danh_sach else toan_bo[:k]
        tap_vang, tap_tra = set(vang), set(tra_ve)

        hit1 = bool(tra_ve[:1]) and tra_ve[0] in tap_vang
        hit3 = bool(tap_vang & set(tra_ve[:3]))
        hitk = bool(tap_vang & tap_tra)
        top1 += hit1
        top3 += hit3
        topk += hitk

        rr = 0.0
        for i, vid in enumerate(tra_ve, 1):
            if vid in tap_vang:
                rr = 1.0 / i
                break
        mrr += rr

        giao = len(tap_vang & tap_tra)
        p = giao / len(tap_tra) if tap_tra else 0.0
        r = giao / len(tap_vang) if tap_vang else 0.0
        f = 2 * p * r / (p + r) if (p + r) else 0.0
        P += p
        R += r
        F += f

        s = theo_lop[m["lop_bai_toan_dung"]]
        s["n"] += 1
        s["lop"] += lop_dung
        s["top1"] += hit1
        s["topk"] += hitk
        d = theo_do_kho[m.get("do_kho", "?")]
        d["n"] += 1
        d["topk"] += hitk

        if not hitk or not lop_dung:
            loi.append({"id": m["id"], "cau_hoi": m["cau_hoi"],
                        "lop_dung": m["lop_bai_toan_dung"],
                        "lop_he_thong": kq["lop_bai_toan"],
                        "tri_thuc_dung": vang, "tri_thuc_tra_ve": tra_ve,
                        "sai_lop": not lop_dung, "sai_truy_hoi": not hitk})

    kq_tong = {
        "so_cau_hoi": n, "top_k": k,
        "do_chinh_xac_phan_lop": round(dung_lop / n, 4),
        "top1": round(top1 / n, 4), "top3": round(top3 / n, 4),
        "top%d" % k: round(topk / n, 4),
        "mrr": round(mrr / n, 4),
        "precision_macro": round(P / n, 4),
        "recall_macro": round(R / n, 4),
        "f1_macro": round(F / n, 4),
        "thoi_gian_tb_ms": round(1000 * sum(thoi_gian) / n, 1),
        "theo_lop_bai_toan": {kk: {"n": v["n"],
                                   "acc_phan_lop": round(v["lop"] / v["n"], 4),
                                   "top1": round(v["top1"] / v["n"], 4),
                                   "top%d" % k: round(v["topk"] / v["n"], 4)}
                              for kk, v in sorted(theo_lop.items())},
        "theo_do_kho": {kk: {"n": v["n"], "top%d" % k: round(v["topk"] / v["n"], 4)}
                        for kk, v in sorted(theo_do_kho.items())},
        "so_cau_sai": len(loi),
    }

    print("=" * 74)
    print("KET QUA DANH GIA HE THONG TRA CUU KIEN THUC PHAP LUAT GIAO THONG")
    print("=" * 74)
    print("So cau hoi kiem thu           : %d" % n)
    print("Do chinh xac phan lop bai toan: %.2f%%" % (100 * dung_lop / n))
    print("Truy hoi dung  Top-1          : %.2f%%" % (100 * top1 / n))
    print("Truy hoi dung  Top-3          : %.2f%%" % (100 * top3 / n))
    print("Truy hoi dung  Top-%d          : %.2f%%" % (k, 100 * topk / n))
    print("MRR                           : %.4f" % (mrr / n))
    print("Precision (macro)             : %.4f" % (P / n))
    print("Recall    (macro)             : %.4f" % (R / n))
    print("F1        (macro)             : %.4f" % (F / n))
    print("Thoi gian tra loi trung binh  : %.1f ms" % (1000 * sum(thoi_gian) / n))

    print("\n" + "-" * 74)
    print("%-28s %5s %12s %8s %8s" % ("LOP BAI TOAN", "N", "ACC PHAN LOP", "TOP-1",
                                      "TOP-%d" % k))
    print("-" * 74)
    for kk, v in kq_tong["theo_lop_bai_toan"].items():
        print("%-28s %5d %11.1f%% %7.1f%% %7.1f%%"
              % (kk, v["n"], 100 * v["acc_phan_lop"], 100 * v["top1"],
                 100 * v["top%d" % k]))
    print("-" * 74)
    print("%-28s %5s %12s" % ("DO KHO", "N", "TOP-%d" % k))
    for kk, v in kq_tong["theo_do_kho"].items():
        print("%-28s %5d %11.1f%%" % (kk, v["n"], 100 * v["top%d" % k]))

    if chi_tiet and loi:
        print("\n" + "-" * 74)
        print("CAC CAU TRA LOI CHUA DUNG (%d)" % len(loi))
        print("-" * 74)
        for e in loi:
            print("\n[%s] %s" % (e["id"], e["cau_hoi"]))
            if e["sai_lop"]:
                print("   lop: dung=%s  he_thong=%s" % (e["lop_dung"], e["lop_he_thong"]))
            if e["sai_truy_hoi"]:
                print("   vang: %s" % e["tri_thuc_dung"])
                print("   tra ve: %s" % e["tri_thuc_tra_ve"])
    return kq_tong, loi


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate-top1", type=float, default=None,
                    help="thoat ma loi neu Top-1 thap hon nguong nay (dung cho CI)")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--chi-tiet", action="store_true")
    ap.add_argument("--out", default=os.path.join(BASE, "eval", "ket_qua_danh_gia.json"))
    a = ap.parse_args()
    tong, loi = danh_gia(a.k, a.chi_tiet)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"tong_hop": tong, "cau_sai": loi}, f, ensure_ascii=False, indent=1)
    print("\n-> Da ghi ket qua: %s" % a.out)

    if a.gate_top1 is not None:
        top1 = tong["top1"]
        if top1 + 1e-9 < a.gate_top1:
            print("\n[CONG CHI SO] THAT BAI: Top-1 %.4f < nguong %.4f"
                  % (top1, a.gate_top1))
            sys.exit(1)
        print("\n[CONG CHI SO] DAT: Top-1 %.4f >= nguong %.4f" % (top1, a.gate_top1))
