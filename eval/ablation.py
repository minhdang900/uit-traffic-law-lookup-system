"""
ablation.py -- Thí nghiệm loại bỏ thành phần (ablation study).

So sánh hiệu quả của từng thành phần trong giải pháp:
  A. Chỉ so khớp ngữ nghĩa (TF-IDF)  -- mốc so sánh của truy hồi văn bản
  B. Chỉ so khớp keyphrase (tri thức)
  C. Lai keyphrase + ngữ nghĩa + ngữ cảnh, KHÔNG suy diễn số học
  D. Hệ thống đầy đủ (C + suy diễn số học)

Chạy: python eval/ablation.py
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))
sys.path.insert(0, os.path.join(BASE, "tests"))
from evaluate import lay_id_tra_ve  # noqa: E402

from tra_cuu_gtdb.reasoning.engine import InferenceEngine, TraCuuPhapLuat  # noqa: E402

DATASET = os.path.join(BASE, "eval", "qa_dataset.json")

CAU_HINH = [
    ("A. Chỉ so khớp ngữ nghĩa (TF-IDF)", dict(a=0.0, b=1.0, g=0.0, so_hoc=False)),
    ("B. Chỉ so khớp keyphrase", dict(a=1.0, b=0.0, g=0.0, so_hoc=False)),
    ("C. Lai keyphrase + ngữ nghĩa + ngữ cảnh", dict(a=0.55, b=0.30, g=0.15, so_hoc=False)),
    ("D. Hệ thống đầy đủ (C + suy diễn số học)", dict(a=0.55, b=0.30, g=0.15, so_hoc=True)),
]


def chay(ht, ds, cfg, k=5):
    """Chạy đánh giá với một cấu hình trọng số và chế độ bật/tắt suy diễn số học;
    trả về Top-1, Top-k và MRR.
    """
    InferenceEngine.ALPHA = cfg["a"]
    InferenceEngine.BETA = cfg["b"]
    InferenceEngine.GAMMA = cfg["g"]
    goc = ht.kb.numeric.theo_dai_luong
    if not cfg["so_hoc"]:
        ht.kb.numeric.theo_dai_luong = {}      # tat suy dien so hoc
    top1 = topk = 0
    mrr = 0.0
    try:
        for m in ds:
            kq = ht.hoi(m["cau_hoi"], top_k=k)
            toan_bo = lay_id_tra_ve(kq, m["loai_tri_thuc"])
            la_ds = (kq.get("tong_hop") or {}).get("kieu") in ("danh_sach", "can_cu")
            tra_ve = toan_bo if la_ds else toan_bo[:k]
            vang = set(m["id_tri_thuc_dung"])
            top1 += bool(tra_ve[:1]) and tra_ve[0] in vang
            topk += bool(vang & set(tra_ve))
            for i, vid in enumerate(tra_ve, 1):
                if vid in vang:
                    mrr += 1.0 / i
                    break
    finally:
        ht.kb.numeric.theo_dai_luong = goc
    n = len(ds)
    return {"top1": 100 * top1 / n, "topk": 100 * topk / n, "mrr": mrr / n}


def main():
    """Chạy lần lượt bốn cấu hình, in bảng so sánh và ghi kết quả ra tệp JSON."""
    ht = TraCuuPhapLuat()
    with open(DATASET, encoding="utf-8") as f:
        ds = json.load(f)
    # rieng nhom cau hoi co gia tri so, de thay ro tac dung cua suy dien so hoc
    ds_so = [m for m in ds if any(c.isdigit() for c in m["cau_hoi"])
             and ("mg/" in m["cau_hoi"] or "km/h" in m["cau_hoi"])]

    print("=" * 78)
    print("THI NGHIEM LOAI BO THANH PHAN (ABLATION STUDY) — %d cau hoi" % len(ds))
    print("=" * 78)
    print("%-44s %8s %8s %8s" % ("CAU HINH", "TOP-1", "TOP-5", "MRR"))
    print("-" * 78)
    ket_qua = {}
    for ten, cfg in CAU_HINH:
        r = chay(ht, ds, cfg)
        ket_qua[ten] = r
        print("%-44s %7.1f%% %7.1f%% %8.4f" % (ten, r["top1"], r["topk"], r["mrr"]))

    print("\n" + "-" * 78)
    print("Rieng %d cau hoi CO GIA TRI SO (nong do con / muc vuot toc do):" % len(ds_so))
    print("-" * 78)
    kq_so = {}
    for ten, cfg in CAU_HINH[2:]:
        r = chay(ht, ds_so, cfg)
        kq_so[ten] = r
        print("%-44s %7.1f%% %7.1f%% %8.4f" % (ten, r["top1"], r["topk"], r["mrr"]))

    out = os.path.join(BASE, "eval", "ket_qua_ablation.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"toan_bo": ket_qua, "cau_hoi_co_gia_tri_so": kq_so,
                   "so_cau_hoi": len(ds), "so_cau_hoi_co_so": len(ds_so)},
                  f, ensure_ascii=False, indent=1)
    print("\n-> Da ghi: %s" % out)


if __name__ == "__main__":
    main()
