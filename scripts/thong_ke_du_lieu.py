# -*- coding: utf-8 -*-
"""Thống kê và phân tích bộ dữ liệu — mục 3 của báo cáo CS106 Nhóm 7.

Đo trên CƠ SỞ TRI THỨC (data/kb/) và BỘ CÂU HỎI CÓ ĐÁP ÁN CHUẨN (eval/qa_dataset.json):

  • phân bố độ dài  — câu hỏi và đơn vị tri thức (số từ)
  • phân bố nhãn    — 7 lớp bài toán, mức độ khó, loại tri thức
  • phân bố chủ đề  — 6 lĩnh vực và các nhóm hành vi, đối chiếu KB với bộ câu hỏi

Đầu ra:
  eval/thong_ke_du_lieu.json        số liệu thô (để báo cáo và slide đọc lại)
  docs/so_do/hinh3_phan_bo_do_dai.png
  docs/so_do/hinh4_phan_bo_nhan.png
  docs/so_do/hinh5_phan_bo_chu_de.png

Chạy được ở hai nơi giống ve_so_do.py: trong repo → docs/so_do/, trong thư mục
nộp bài → bao_cao/hinh/.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import fontManager

for _f in ("Carlito-Regular.ttf", "Carlito-Bold.ttf", "Carlito-Italic.ttf"):
    _p = Path(f"/usr/share/fonts/truetype/crosextra/{_f}")
    if _p.exists():
        fontManager.addfont(str(_p))
if any(f.name == "Carlito" for f in fontManager.ttflist):
    plt.rcParams["font.family"] = "Carlito"

# ── bảng màu Organic (tokens.css của giao diện) ──────────────────────────────
BG, SURFACE, TEXT = "#f5ead8", "#ebddc5", "#201e1d"
ACCENT, ACCENT2 = "#c67139", "#7a8a5e"
N100, N300, N600, N700 = "#f9f4ed", "#dcd3c4", "#82796a", "#645c50"
A200, G200 = "#ffe1d0", "#e1eecc"

GOC = Path(__file__).resolve().parents[1]
TRONG_REPO = (GOC / "eval").is_dir() and (GOC / "data" / "kb").is_dir()


def _thu_muc_hinh() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    if TRONG_REPO:
        return GOC / "docs" / "so_do"
    return Path(__file__).resolve().parents[2] / "bao_cao" / "hinh"


def _tim(*ung_vien: str) -> Path:
    for u in ung_vien:
        p = GOC / u
        if p.exists():
            return p
    raise FileNotFoundError(f"Không tìm thấy: {ung_vien}")


RA = _thu_muc_hinh()
RA.mkdir(parents=True, exist_ok=True)

TEN_LOP = {
    "P1_TRA_CUU_KHAI_NIEM": "P1 Khái niệm",
    "P2_TRA_CUU_QUY_DINH": "P2 Quy định",
    "P3_TRA_CUU_CHE_TAI": "P3 Chế tài",
    "P4_TRA_CUU_NGUOC": "P4 Tra cứu ngược",
    "P5_SUY_DIEN_TINH_HUONG": "P5 Tình huống",
    "P6_TRA_CUU_CAN_CU": "P6 Căn cứ",
    "P7_TRA_CUU_LIEN_QUAN": "P7 Liên quan",
}
TEN_DO_KHO = {"de": "Dễ", "trung_binh": "Trung bình", "kho": "Khó"}
TEN_LOAI_TT = {"concept": "Khái niệm", "rule": "Quy tắc", "violation": "Hành vi vi phạm"}


def _tu(s: str | None) -> int:
    return len((s or "").split())


def _tom_tat(xs: list[int]) -> dict:
    xs = sorted(xs)
    return {
        "n": len(xs),
        "min": xs[0],
        "max": xs[-1],
        "trung_binh": round(statistics.mean(xs), 2),
        "trung_vi": statistics.median(xs),
        "do_lech_chuan": round(statistics.pstdev(xs), 2),
        "p25": xs[int(0.25 * (len(xs) - 1))],
        "p75": xs[int(0.75 * (len(xs) - 1))],
        "p90": xs[int(0.90 * (len(xs) - 1))],
    }


# ═══════════════════════════════ nạp dữ liệu ════════════════════════════════
def nap() -> dict:
    kb_dir = _tim("data/kb", "ma_nguon/data/kb")
    qa_p = _tim("eval/qa_dataset.json", "so_lieu/qa_dataset.json",
                "ma_nguon/eval/qa_dataset.json")

    def j(ten: str):
        return json.loads((kb_dir / ten).read_text(encoding="utf-8"))

    return {
        "concepts": j("concepts.json"),
        "rules": j("rules.json"),
        "violations": j("violations.json"),
        "relations": j("relations.json"),
        "keyphrases": j("keyphrases.json"),
        "taxonomy": j("taxonomy.json"),
        "amendments": j("amendments.json"),
        "documents": j("documents.json"),
        "qa": json.loads(qa_p.read_text(encoding="utf-8")),
    }


def tinh(d: dict) -> dict:
    tx = d["taxonomy"]
    # nhóm → lĩnh vực
    nhom2lv = {n: lv for lv, v in tx["linh_vuc"].items() for n in v["nhom"]}
    ten_lv = {lv: v["ten"] for lv, v in tx["linh_vuc"].items()}
    ten_nhom = tx.get("ten_nhom", {})

    qa = d["qa"]

    # ── quy mô cơ sở tri thức ────────────────────────────────────────────────
    quy_mo = {
        "C_khai_niem": len(d["concepts"]),
        "R_quan_he": len(d["relations"]),
        "Rules_quy_tac": len(d["rules"]),
        "F_hanh_vi": len(d["violations"]),
        "Keyphrase": len(d["keyphrases"]),
        "sua_doi": len(d["amendments"]),
        "van_ban": len(d["documents"]),
    }

    # ── phân bố độ dài ───────────────────────────────────────────────────────
    do_dai = {
        "cau_hoi": _tom_tat([_tu(q["cau_hoi"]) for q in qa]),
        "dap_an_chuan": _tom_tat([_tu(q["dap_an_chuan"]) for q in qa]),
        "khai_niem": _tom_tat([_tu(c.get("dinh_nghia")) for c in d["concepts"]]),
        "quy_tac": _tom_tat([_tu(r.get("nguyen_van")) for r in d["rules"]]),
        "hanh_vi": _tom_tat([_tu(v.get("hanh_vi")) for v in d["violations"]]),
        "keyphrase_so_tu": _tom_tat([int(k.get("so_tu") or _tu(k["cum_tu"]))
                                     for k in d["keyphrases"]]),
    }
    do_dai["histogram_cau_hoi"] = [_tu(q["cau_hoi"]) for q in qa]
    do_dai["histogram_tri_thuc"] = {
        "khai_niem": [_tu(c.get("dinh_nghia")) for c in d["concepts"]],
        "quy_tac": [_tu(r.get("nguyen_van")) for r in d["rules"]],
        "hanh_vi": [_tu(v.get("hanh_vi")) for v in d["violations"]],
    }

    # ── phân bố nhãn ─────────────────────────────────────────────────────────
    nhan = {
        "lop_bai_toan": dict(Counter(q["lop_bai_toan_dung"] for q in qa)),
        "do_kho": dict(Counter(q["do_kho"] for q in qa)),
        "loai_tri_thuc": dict(Counter(q["loai_tri_thuc"] for q in qa)),
        "so_dap_an": dict(Counter(len(q["id_tri_thuc_dung"]) for q in qa)),
    }
    nhan["so_cau_nhieu_dap_an"] = sum(1 for q in qa if len(q["id_tri_thuc_dung"]) > 1)
    # chéo lớp × độ khó
    nhan["lop_x_do_kho"] = {
        lop: dict(Counter(q["do_kho"] for q in qa if q["lop_bai_toan_dung"] == lop))
        for lop in TEN_LOP
    }

    # ── phân bố chủ đề ───────────────────────────────────────────────────────
    nhom_vp = Counter(v.get("nhom") for v in d["violations"])
    lv_vp = Counter(nhom2lv.get(v.get("nhom"), "LV_KHAC") for v in d["violations"])

    # bộ câu hỏi: ánh xạ id tri thức → nhóm → lĩnh vực
    vp_theo_id = {v["id"]: v for v in d["violations"]}
    qt_theo_id = {r["id"]: r for r in d["rules"]}
    lv_qa: Counter = Counter()
    nhom_qa: Counter = Counter()
    khong_gan = 0
    for q in qa:
        nhoms = set()
        for i in q["id_tri_thuc_dung"]:
            it = vp_theo_id.get(i) or qt_theo_id.get(i)
            n = (it or {}).get("nhom")
            if isinstance(n, list):
                nhoms.update(n)
            elif n:
                nhoms.add(n)
        if not nhoms:
            khong_gan += 1
            continue
        for n in nhoms:
            nhom_qa[n] += 1
            lv_qa[nhom2lv.get(n, "LV_KHAC")] += 1

    chu_de = {
        "ten_linh_vuc": ten_lv,
        "ten_nhom": ten_nhom,
        "so_nhom_trong_taxonomy": len(nhom2lv),
        "linh_vuc_kb": dict(lv_vp),
        "linh_vuc_qa": dict(lv_qa),
        "nhom_kb": dict(nhom_vp.most_common()),
        "nhom_qa": dict(nhom_qa.most_common()),
        "cau_hoi_khong_gan_nhom": khong_gan,
        "phuong_tien_kb": dict(Counter(
            pt for v in d["violations"] for pt in (v.get("phuong_tien") or ["khong_ro"]))),
        "chu_the_kb": dict(Counter(v.get("chu_the") for v in d["violations"])),
    }

    # ── đặc tính chế tài (để mục 3 nói được dữ liệu "nặng" ở đâu) ────────────
    tien = [v["phat_tien"]["min"] for v in d["violations"]
            if (v.get("phat_tien") or {}).get("min")]
    che_tai = {
        "co_phat_tien": len(tien),
        "phat_tien_min": min(tien) if tien else 0,
        "phat_tien_max": max(v["phat_tien"]["max"] for v in d["violations"]
                             if (v.get("phat_tien") or {}).get("max")),
        "co_tru_diem": sum(1 for v in d["violations"] if v.get("tru_diem_gplx")),
        "co_hinh_phat_bo_sung": sum(1 for v in d["violations"]
                                    if v.get("hinh_phat_bo_sung")),
        "co_bien_phap_khac_phuc": sum(1 for v in d["violations"]
                                      if v.get("bien_phap_khac_phuc")),
    }

    return {
        "quy_mo_co_so_tri_thuc": quy_mo,
        "do_dai": do_dai,
        "nhan": nhan,
        "chu_de": chu_de,
        "che_tai": che_tai,
    }


# ═══════════════════════════════ vẽ biểu đồ ═════════════════════════════════
def _khung(ax):
    ax.set_facecolor(N100)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(N300)
    ax.tick_params(colors=N700, labelsize=9)
    ax.grid(axis="y", color=N300, linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)


def _luu(fig, ten: str):
    fig.savefig(str(RA / ten), dpi=300, bbox_inches="tight",
                facecolor=BG, pad_inches=0.22)
    plt.close(fig)


def hinh_do_dai(t: dict):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.2, 4.1), facecolor=BG)
    h = t["do_dai"]["histogram_cau_hoi"]
    _khung(a1)
    a1.hist(h, bins=range(0, max(h) + 4, 2), color=ACCENT, edgecolor=BG, linewidth=1.1)
    tb = t["do_dai"]["cau_hoi"]["trung_binh"]
    a1.axvline(tb, color=ACCENT2, linestyle="--", linewidth=1.6)
    a1.set_ylim(0, a1.get_ylim()[1] * 1.16)
    a1.annotate(f"trung bình {tb:.1f} từ".replace(".", ","),
                xy=(tb, a1.get_ylim()[1] * 0.80),
                xytext=(tb + 6.5, a1.get_ylim()[1] * 0.95),
                color=ACCENT2, fontsize=9.8, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=ACCENT2, linewidth=1.2))
    a1.set_title("Độ dài câu hỏi (120 câu)", fontsize=12, color=TEXT,
                 fontweight="bold", pad=10)
    a1.set_xlabel("số từ", fontsize=9.5, color=N700)
    a1.set_ylabel("số câu hỏi", fontsize=9.5, color=N700)

    _khung(a2)
    ht = t["do_dai"]["histogram_tri_thuc"]
    a2.boxplot([ht["khai_niem"], ht["quy_tac"], ht["hanh_vi"]],
               tick_labels=["Khái niệm\n(73)", "Quy tắc\n(109)", "Hành vi\n(345)"],
               patch_artist=True, widths=0.5,
               boxprops=dict(facecolor=A200, edgecolor=ACCENT, linewidth=1.3),
               medianprops=dict(color=ACCENT2, linewidth=2),
               whiskerprops=dict(color=N600), capprops=dict(color=N600),
               flierprops=dict(marker="o", markersize=3, markerfacecolor=N600,
                               markeredgecolor="none", alpha=0.5))
    a2.set_title("Độ dài đơn vị tri thức", fontsize=12, color=TEXT,
                 fontweight="bold", pad=10)
    a2.set_ylabel("số từ", fontsize=9.5, color=N700)
    _luu(fig, "hinh3_phan_bo_do_dai.png")


def hinh_nhan(t: dict):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.2, 4.1), facecolor=BG,
                                 gridspec_kw={"width_ratios": [1.55, 1]})
    lop = t["nhan"]["lop_bai_toan"]
    dk = t["nhan"]["lop_x_do_kho"]
    keys = list(TEN_LOP)
    nhan_x = [TEN_LOP[k] for k in keys]
    _khung(a1)
    duoi = [0] * len(keys)
    for ten_k, mau in (("de", G200), ("trung_binh", ACCENT2), ("kho", ACCENT)):
        v = [dk.get(k, {}).get(ten_k, 0) for k in keys]
        a1.bar(nhan_x, v, bottom=duoi, color=mau, edgecolor=BG, linewidth=1.1,
               label=TEN_DO_KHO[ten_k], width=0.62)
        duoi = [a + b for a, b in zip(duoi, v)]
    for i, k in enumerate(keys):
        a1.text(i, lop.get(k, 0) + 0.8, str(lop.get(k, 0)), ha="center",
                fontsize=9.5, color=TEXT, fontweight="bold")
    a1.set_title("Phân bố nhãn: 7 lớp bài toán × mức độ khó", fontsize=12,
                 color=TEXT, fontweight="bold", pad=10)
    a1.set_ylabel("số câu hỏi", fontsize=9.5, color=N700)
    a1.tick_params(axis="x", labelsize=8.6, rotation=18)
    lg = a1.legend(frameon=False, fontsize=9, loc="upper right")
    for tx in lg.get_texts():
        tx.set_color(N700)

    _khung(a2)
    lt = t["nhan"]["loai_tri_thuc"]
    ten = [TEN_LOAI_TT.get(k, k) for k in lt]
    a2.barh(ten, list(lt.values()), color=[ACCENT, ACCENT2, N600][:len(lt)],
            height=0.5, edgecolor=BG, linewidth=1.1)
    for i, v in enumerate(lt.values()):
        a2.text(v + 1.2, i, str(v), va="center", fontsize=9.5,
                color=TEXT, fontweight="bold")
    a2.set_title("Loại tri thức của đáp án chuẩn", fontsize=12, color=TEXT,
                 fontweight="bold", pad=10)
    a2.set_xlabel("số câu hỏi", fontsize=9.5, color=N700)
    a2.grid(axis="y", alpha=0)
    a2.grid(axis="x", color=N300, linewidth=0.7, alpha=0.7)
    _luu(fig, "hinh4_phan_bo_nhan.png")


def hinh_chu_de(t: dict):
    cd = t["chu_de"]
    TEN_NGAN = {
        "LV_QUY_TAC": "Quy tắc giao thông",
        "LV_AN_TOAN": "An toàn người tham gia",
        "LV_NGUOI_LAI": "Điều kiện người lái",
        "LV_PHUONG_TIEN": "Điều kiện phương tiện",
        "LV_VAN_TAI": "Vận tải, hàng hoá",
        "LV_KHAC": "Nội dung khác",
    }
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.2, 4.3), facecolor=BG,
                                 gridspec_kw={"width_ratios": [1, 1.1], "wspace": 0.42})
    lvs = sorted(cd["linh_vuc_kb"], key=lambda k: -cd["linh_vuc_kb"][k])
    tong_kb = sum(cd["linh_vuc_kb"].values()) or 1
    tong_qa = sum(cd["linh_vuc_qa"].values()) or 1
    kb = [100 * cd["linh_vuc_kb"][k] / tong_kb for k in lvs]
    qa = [100 * cd["linh_vuc_qa"].get(k, 0) / tong_qa for k in lvs]
    y = range(len(lvs))
    _khung(a1)
    a1.barh([i + 0.19 for i in y], kb, height=0.36, color=ACCENT,
            edgecolor=BG, linewidth=1, label="Cơ sở tri thức")
    a1.barh([i - 0.19 for i in y], qa, height=0.36, color=ACCENT2,
            edgecolor=BG, linewidth=1, label="Bộ câu hỏi")
    a1.set_yticks(list(y))
    a1.set_yticklabels([TEN_NGAN.get(k, k) for k in lvs], fontsize=9)
    a1.invert_yaxis()
    a1.set_xlim(0, max(max(kb), max(qa)) * 1.30)
    for i, v in enumerate(kb):
        a1.text(v + 0.8, i + 0.19, f"{v:.0f}%", va="center", fontsize=8.6, color=N700)
    for i, v in enumerate(qa):
        a1.text(v + 0.8, i - 0.19, f"{v:.0f}%", va="center", fontsize=8.6, color=N700)
    a1.set_title("Tỉ trọng theo 6 lĩnh vực", fontsize=12, color=TEXT,
                 fontweight="bold", pad=10)
    a1.set_xlabel("tỉ lệ trong mỗi tập (%)", fontsize=9.5, color=N700)
    a1.grid(axis="y", alpha=0)
    a1.grid(axis="x", color=N300, linewidth=0.7, alpha=0.7)
    lg = a1.legend(frameon=False, fontsize=8.8, loc="lower right")
    for tx in lg.get_texts():
        tx.set_color(N700)

    top = list(cd["nhom_kb"].items())[:14]
    _khung(a2)
    ten_n = [cd["ten_nhom"].get(k, k) for k, _ in top]
    a2.barh(ten_n, [v for _, v in top], height=0.58, color=ACCENT,
            edgecolor=BG, linewidth=1)
    a2.invert_yaxis()
    a2.tick_params(axis="y", labelsize=8.8)
    from matplotlib.ticker import MaxNLocator
    a2.xaxis.set_major_locator(MaxNLocator(integer=True))
    a2.set_xlim(0, max(v for _, v in top) * 1.12)
    for i, (_, v) in enumerate(top):
        a2.text(v + 0.25, i, str(v), va="center", fontsize=8.6, color=N700)
    a2.set_title("14 nhóm hành vi lớn nhất trong cơ sở tri thức",
                 fontsize=12, color=TEXT, fontweight="bold", pad=10)
    a2.set_xlabel("số hành vi vi phạm", fontsize=9.5, color=N700)
    a2.grid(axis="y", alpha=0)
    a2.grid(axis="x", color=N300, linewidth=0.7, alpha=0.7)
    _luu(fig, "hinh5_phan_bo_chu_de.png")


def hinh_phan_tich_loi():
    """Hình 6 — chỉ vẽ khi đã chạy eval/phan_tich_loi.py."""
    try:
        pl = _tim("eval/ket_qua_phan_tich_loi.json", "so_lieu/ket_qua_phan_tich_loi.json")
    except FileNotFoundError:
        print("Chua co ket_qua_phan_tich_loi.json — bo qua hinh 6.")
        return
    d = json.loads(pl.read_text(encoding="utf-8"))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.8, 4.0), facecolor=BG,
                                 gridspec_kw={"width_ratios": [1.25, 1], "wspace": 0.34})
    MAU = {"L1": ACCENT, "L2": "#8c491a", "L3": "#9aa87c", "L4": "#e0a97f",
           "L5": ACCENT2, "L6": N600}
    ma = list(d["theo_nguyen_nhan"])
    so = [d["theo_nguyen_nhan"][m] for m in ma]
    ten = [f"{m} · {d['ten_nguyen_nhan'][m]}" for m in ma]
    _khung(a1)
    a1.barh(ten, so, height=0.6, color=[MAU.get(m, N600) for m in ma],
            edgecolor=BG, linewidth=1)
    a1.invert_yaxis()
    a1.set_xlim(0, max(so) * 1.18)
    a1.tick_params(axis="y", labelsize=9)
    for i, v in enumerate(so):
        a1.text(v + 0.25, i, str(v), va="center", fontsize=9.5,
                color=TEXT, fontweight="bold")
    a1.set_title(f"Nguyên nhân gốc của {d['so_ca_chua_toi_uu']} ca chưa tối ưu",
                 fontsize=12, color=TEXT, fontweight="bold", pad=10)
    a1.set_xlabel("số ca", fontsize=9.5, color=N700)
    a1.grid(axis="y", alpha=0)
    a1.grid(axis="x", color=N300, linewidth=0.7, alpha=0.7)

    h = d["hang_dap_an"]
    thu_tu = sorted((k for k in h if k != "None"), key=int) + \
             (["None"] if "None" in h else [])
    nhan_h = ["ngoài Top-5" if k == "None" else f"hạng {k}" for k in thu_tu]
    _khung(a2)
    a2.bar(nhan_h, [h[k] for k in thu_tu],
           color=[("#8c491a" if k == "None" else ACCENT) for k in thu_tu],
           edgecolor=BG, linewidth=1.1, width=0.62)
    for i, k in enumerate(thu_tu):
        a2.text(i, h[k] + 0.25, str(h[k]), ha="center", fontsize=9.5,
                color=TEXT, fontweight="bold")
    a2.set_title("Đáp án chuẩn rơi vào hạng nào", fontsize=12, color=TEXT,
                 fontweight="bold", pad=10)
    a2.set_ylabel("số ca", fontsize=9.5, color=N700)
    a2.tick_params(axis="x", labelsize=8.8, rotation=20)
    _luu(fig, "hinh6_phan_tich_loi.png")


def main() -> int:
    t = tinh(nap())
    ra_json = (GOC / "eval" / "thong_ke_du_lieu.json") if TRONG_REPO else \
        (GOC / "so_lieu" / "thong_ke_du_lieu.json")
    ra_json.parent.mkdir(parents=True, exist_ok=True)
    ra_json.write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
    hinh_do_dai(t)
    hinh_nhan(t)
    hinh_chu_de(t)
    hinh_phan_tich_loi()
    q = t["quy_mo_co_so_tri_thuc"]
    print(f"KB: C={q['C_khai_niem']} R={q['R_quan_he']} Rules={q['Rules_quy_tac']} "
          f"F={q['F_hanh_vi']} Keyphrase={q['Keyphrase']}")
    print(f"Cau hoi: TB {t['do_dai']['cau_hoi']['trung_binh']} tu, "
          f"{t['do_dai']['cau_hoi']['min']}–{t['do_dai']['cau_hoi']['max']}")
    print(f"Da ghi {ra_json} va 3 hinh vao {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
