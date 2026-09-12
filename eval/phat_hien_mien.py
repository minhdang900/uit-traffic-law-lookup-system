"""Đo khả năng tách miền của từng tín hiệu ứng viên.

Trả lời một câu hỏi đã treo từ pha trước: TF-IDF không tách được truy vấn ngoài
lĩnh vực — vậy đặc trưng nào tách được?

Chạy:
    python eval/phat_hien_mien.py                 # chỉ các tín hiệu thưa
    python eval/phat_hien_mien.py --dense         # thêm dense (cần gói '.[dense]')
    python eval/phat_hien_mien.py --dense --ghi   # ghi kết quả ra JSON

Hai con số quan trọng:
    AUC              xác suất một câu hợp lệ được chấm cao hơn một câu rác.
    "loại rác @0 oan" tỷ lệ truy vấn rác bị loại khi BẮT BUỘC không câu hợp lệ
                     nào bị từ chối oan — đây mới là con số dùng được thực tế,
                     vì từ chối oan người dùng thật tệ hơn nhiều so với lỡ trả
                     lời một câu vớ vẩn.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GOC / "src"))

from tra_cuu_gtdb.kb.text import bo_dau, chuan_hoa  # noqa: E402
from tra_cuu_gtdb.reasoning.engine import TraCuuPhapLuat  # noqa: E402

TU_DUNG = set("la gi cua va co khong the nao bao nhieu duoc mot cac nhung khi thi "
              "o tai ra vao cho de tu den voi".split())


def auc(trong: list[float], ngoai: list[float]) -> float:
    """Xác suất một mẫu trong-miền được chấm cao hơn một mẫu ngoài-miền."""
    a, b = np.asarray(trong, dtype=float), np.asarray(ngoai, dtype=float)
    hon = (a[:, None] > b[None, :]).sum()
    hoa = (a[:, None] == b[None, :]).sum()
    return float((hon + 0.5 * hoa) / (a.size * b.size))


def loai_rac_khi_khong_oan(trong: list[float], ngoai: list[float]) -> tuple[float, float]:
    """Tỷ lệ rác loại được khi ép buộc 0 câu hợp lệ bị từ chối oan.

    Ngưỡng phải nằm DƯỚI điểm thấp nhất của tập hợp lệ; mọi câu rác dưới ngưỡng
    đó bị loại.
    """
    san = min(trong)
    return float(np.mean(np.asarray(ngoai) < san)), san


def oan_khi_loai_het_rac(trong: list[float], ngoai: list[float]) -> tuple[float, float]:
    """Tỷ lệ câu hợp lệ bị oan khi ép buộc loại 100% truy vấn rác."""
    tran = max(ngoai)
    return float(np.mean(np.asarray(trong) <= tran)), tran


def nap_du_lieu() -> tuple[list[str], list[str]]:
    with (GOC / "eval" / "qa_dataset.json").open(encoding="utf-8") as f:
        trong = [m["cau_hoi"] for m in json.load(f)]
    with (GOC / "eval" / "truy_van_ngoai_mien.json").open(encoding="utf-8") as f:
        ngoai = [t["cau_hoi"] for t in json.load(f)["truy_van"]]
    return trong, ngoai


def main() -> int:
    bd = argparse.ArgumentParser(description=__doc__)
    bd.add_argument("--dense", action="store_true", help="đo thêm dense embedding")
    bd.add_argument("--ghi", action="store_true", help="ghi kết quả ra JSON")
    tham_so = bd.parse_args()

    trong, ngoai = nap_du_lieu()
    ht = TraCuuPhapLuat()
    kb = ht.kb
    print(f"{len(trong)} câu trong miền · {len(ngoai)} truy vấn ngoài miền\n")

    tu_vung: set[str] = set()
    for doan in kb.v_corpus + kb.c_corpus + kb.r_corpus:
        tu_vung.update(doan.split())

    def tfidf_tho(q: str) -> float:
        return max(float(kb.sim(q, k).max()) for k in ("violation", "concept", "rule"))

    def so_keyphrase(q: str) -> float:
        return float(len(ht.engine.analyzer.rut_trich_keyphrase(q)))

    def phu_tu_vung(q: str) -> float:
        toks = [t for t in bo_dau(chuan_hoa(q)).split()
                if t not in TU_DUNG and len(t) > 1]
        return sum(t in tu_vung for t in toks) / len(toks) if toks else 0.0

    tin_hieu: list[tuple[str, object]] = [
        ("TF-IDF thô", tfidf_tho),
        ("số keyphrase", so_keyphrase),
        ("phủ từ vựng KB", phu_tu_vung),
    ]
    if tham_so.dense:
        from tra_cuu_gtdb.retrieval.dense import BoLocMien, dense_kha_dung
        if not dense_kha_dung():
            print("Thiếu gói 'dense' — bỏ qua. Cài: pip install -e '.[dense]'")
        else:
            tin_hieu.append(("dense", BoLocMien(kb).diem_mien))

    bang = []
    print(f"{'tín hiệu':<16} {'AUC':>8} {'loại rác @0 oan':>17} {'oan @loại hết rác':>19}")
    print("-" * 64)
    for ten, ham in tin_hieu:
        p = [ham(q) for q in trong]      # type: ignore[operator]
        n = [ham(q) for q in ngoai]      # type: ignore[operator]
        a = auc(p, n)
        loai, san = loai_rac_khi_khong_oan(p, n)
        oan, tran = oan_khi_loai_het_rac(p, n)
        print(f"{ten:<16} {a:>8.4f} {loai:>16.1%} {oan:>18.1%}")
        bang.append({"tin_hieu": ten, "auc": round(a, 4),
                     "loai_rac_khi_0_oan": round(loai, 4), "san_trong_mien": round(san, 4),
                     "oan_khi_loai_het_rac": round(oan, 4), "tran_ngoai_mien": round(tran, 4)})

    if tham_so.ghi:
        dd = GOC / "eval" / "ket_qua_phat_hien_mien.json"
        with dd.open("w", encoding="utf-8") as f:
            json.dump({"so_cau_trong_mien": len(trong), "so_cau_ngoai_mien": len(ngoai),
                       "ket_qua": bang}, f, ensure_ascii=False, indent=1)
        print(f"\nĐã ghi {dd.relative_to(GOC)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
