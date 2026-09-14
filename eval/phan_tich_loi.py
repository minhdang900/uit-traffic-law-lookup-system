"""
phan_tich_loi.py -- Phân tích lỗi sâu (deep error analysis) cho mục 5 của báo cáo.

Không chỉ đếm câu sai: chạy lại toàn bộ 120 câu hỏi, ghi lại HẠNG của đáp án
chuẩn trong danh sách trả về, rồi quy mỗi ca chưa đúng về MỘT nguyên nhân gốc.

Sáu nhóm nguyên nhân, xét theo thứ tự ưu tiên (một ca chỉ thuộc một nhóm):

  L1 ĐỊNH TUYẾN SAI       bộ phân lớp chọn nhầm lớp bài toán → giải sai kiểu.
                          Đây là lỗi nặng nhất vì hỏng ngay ở bước B4.
  L2 TRƯỢT HẲN TOP-K      đáp án chuẩn không nằm trong tập trả về. Lỗi truy hồi
                          thật sự — người dùng không thấy đáp án ở đâu cả.
  L3 THỨ TỰ TRONG TẬP     câu trả về NGUYÊN MỘT TẬP (tra cứu ngược P4, liên quan
                          P7, căn cứ P6): đáp án có trong tập, chỉ không đứng đầu
                          → recall đủ, chỉ là thứ tự trình bày.
  L4 NHIỀU ĐÁP ÁN CHUẨN   đáp án chuẩn gồm nhiều mẩu tri thức; hạng 1 là một mẩu
                          khác cũng hợp lệ nhưng không trùng mẩu được chấm.
  L5 KHOẢNG TRỐNG TỪ VỰNG câu hỏi dùng từ đời thường, không cụm từ khoá nào của
                          đáp án xuất hiện → làn keyphrase im lặng, chỉ còn
                          TF-IDF gánh, đáp án tụt xuống hạng 2–3.
  L6 KHÁC                 chưa quy được về năm nhóm trên

Chạy:  python eval/phan_tich_loi.py [--out eval/ket_qua_phan_tich_loi.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from collections import Counter, defaultdict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "src"))
from traffic_law.reasoning.engine import LawLookup  # noqa: E402

DATASET = os.path.join(BASE, "eval", "qa_dataset.json")
KB = os.path.join(BASE, "data", "kb")

TEN_NGUYEN_NHAN = {
    "L1": "Định tuyến sai lớp bài toán",
    "L2": "Trượt hẳn ngoài Top-k",
    "L3": "Thứ tự trong tập trả về (P4/P6/P7)",
    "L4": "Câu nhiều đáp án chuẩn",
    "L5": "Khoảng trống từ vựng làm tụt hạng",
    "L6": "Khác",
}
MUC_DO = {"L1": "nang", "L2": "nang", "L3": "nhe", "L4": "nhe", "L5": "vua",
          "L6": "vua"}


def _bo_dau(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d")


def _nap_kb() -> dict:
    def j(t):
        with open(os.path.join(KB, t), encoding="utf-8") as f:
            return json.load(f)
    vp, qt, kn = j("violations.json"), j("rules.json"), j("concepts.json")
    kp = j("keyphrases.json")
    # định danh tri thức → nhóm chủ đề
    nhom = {}
    for v in vp:
        nhom[v["id"]] = v.get("nhom")
    for r in qt:
        n = r.get("nhom")
        nhom[r["id"]] = n[0] if isinstance(n, list) and n else n
    # định danh tri thức → các cụm từ khoá trỏ tới nó
    cum = defaultdict(list)
    for k in kp:
        for truong in ("khai_niem", "quy_tac", "hanh_vi"):
            for i in k.get(truong) or []:
                cum[i].append(k["cum_tu"])
    for c in kn:
        cum[c["id"]].extend(c.get("keyphrases") or [])
    return {"nhom": nhom, "cum": dict(cum),
            "ten": {**{v["id"]: v.get("hanh_vi", "") for v in vp},
                    **{r["id"]: r.get("ten", "") for r in qt},
                    **{c["id"]: c.get("ten", "") for c in kn}}}


def _ids(kq, kind):
    if kind == "concept":
        return [c["id"] for c in kq["concepts"]]
    if kind == "rule":
        return [r["id"] for r in kq["rules"]]
    return [v["id"] for v in kq["violations"]]


def phan_tich(k: int = 5) -> dict:
    ht, kb = LawLookup(), _nap_kb()
    with open(DATASET, encoding="utf-8") as f:
        ds = json.load(f)

    ca = []
    for m in ds:
        kq = ht.ask(m["cau_hoi"], top_k=k)
        vang = list(dict.fromkeys(m["id_tri_thuc_dung"]))
        toan_bo = _ids(kq, m["loai_tri_thuc"])
        la_ds = (kq.get("summary") or {}).get("kind") in ("danh_sach", "citation")
        tra_ve = toan_bo if la_ds else toan_bo[:k]

        hang = next((i for i, x in enumerate(tra_ve, 1) if x in set(vang)), None)
        dung_lop = kq["problem_class"] == m["lop_bai_toan_dung"]
        if hang == 1 and dung_lop:
            continue                                    # đúng hoàn toàn, bỏ qua

        q = _bo_dau(m["cau_hoi"])
        co_cum = any(_bo_dau(c) in q for i in vang for c in kb["cum"].get(i, []))
        nhom_vang = {kb["nhom"].get(i) for i in vang} - {None}
        nhom_dau = kb["nhom"].get(tra_ve[0]) if tra_ve else None

        if not dung_lop:
            nn = "L1"
        elif hang is None:
            nn = "L2"
        elif la_ds:
            nn = "L3"
        elif len(vang) > 1:
            nn = "L4"
        elif not co_cum:
            nn = "L5"
        else:
            nn = "L6"

        ca.append({
            "id": m["id"], "cau_hoi": m["cau_hoi"],
            "lop_dung": m["lop_bai_toan_dung"], "lop_he_thong": kq["problem_class"],
            "do_kho": m.get("do_kho"), "loai_tri_thuc": m["loai_tri_thuc"],
            "so_dap_an": len(vang), "so_tu": len(m["cau_hoi"].split()),
            "hang_dap_an": hang, "trong_top_k": hang is not None,
            "tra_nguyen_tap": la_ds, "so_ket_qua_tra_ve": len(tra_ve),
            "sai_lop": not dung_lop, "co_cum_tu_khoa": co_cum,
            "nhom_dap_an": sorted(nhom_vang), "nhom_ket_qua_dau": nhom_dau,
            "tri_thuc_dung": vang, "tri_thuc_tra_ve": tra_ve[:k],
            "nguyen_nhan": nn, "ten_nguyen_nhan": TEN_NGUYEN_NHAN[nn],
            "muc_do": MUC_DO[nn],
        })

    n = len(ds)
    ngoai_top1 = [c for c in ca if c["hang_dap_an"] != 1]
    ngoai_topk = [c for c in ca if c["hang_dap_an"] is None]
    return {
        "so_cau_hoi": n,
        "so_ca_chua_toi_uu": len(ca),
        "so_ca_ngoai_top1": len(ngoai_top1),
        "so_ca_ngoai_top_k": len(ngoai_topk),
        "ten_nguyen_nhan": TEN_NGUYEN_NHAN,
        "theo_nguyen_nhan": dict(Counter(c["nguyen_nhan"] for c in ca).most_common()),
        "theo_nguyen_nhan_ngoai_top1": dict(
            Counter(c["nguyen_nhan"] for c in ngoai_top1).most_common()),
        "theo_lop": {lop: dict(Counter(c["nguyen_nhan"] for c in ca
                                       if c["lop_dung"] == lop).most_common())
                     for lop in sorted({c["lop_dung"] for c in ca})},
        "theo_do_kho": {dk: dict(Counter(c["nguyen_nhan"] for c in ca
                                         if c["do_kho"] == dk).most_common())
                        for dk in sorted({c["do_kho"] for c in ca})},
        "hang_dap_an": dict(Counter(str(c["hang_dap_an"]) for c in ca).most_common()),
        "theo_muc_do": dict(Counter(c["muc_do"] for c in ca).most_common()),
        "so_ca_trong_top_k_nhung_khong_hang_1": sum(
            1 for c in ca if c["hang_dap_an"] and c["hang_dap_an"] > 1),
        "so_ca_khong_co_cum_tu_khoa": sum(1 for c in ca if not c["co_cum_tu_khoa"]),
        "do_dai_ca_sai_tb": round(
            sum(c["so_tu"] for c in ca) / len(ca), 2) if ca else 0,
        "ca": ca,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--out", default=os.path.join(BASE, "eval",
                                                  "ket_qua_phan_tich_loi.json"))
    a = ap.parse_args()
    kq = phan_tich(a.k)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(kq, f, ensure_ascii=False, indent=1)

    print("PHAN TICH LOI SAU -- %d cau hoi" % kq["so_cau_hoi"])
    print("Ca chua toi uu (khong dat Top-1 hoac sai lop): %d" % kq["so_ca_chua_toi_uu"])
    print("  trong do ngoai Top-%d hoan toan: %d" % (a.k, kq["so_ca_ngoai_top_k"]))
    print("\n%-4s %-52s %6s" % ("Ma", "Nguyen nhan goc", "So ca"))
    print("-" * 64)
    for ma, so in kq["theo_nguyen_nhan"].items():
        print("%-4s %-52s %6d" % (ma, _bo_dau(TEN_NGUYEN_NHAN[ma]), so))
    print("\nDa ghi %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
