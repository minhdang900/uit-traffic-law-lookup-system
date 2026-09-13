# -*- coding: utf-8 -*-
"""Sinh 2 sơ đồ cho báo cáo CS106 Nhóm 7, dùng đúng bảng màu hệ thiết kế Organic."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.font_manager import FontProperties, fontManager

for f in ("Carlito-Regular.ttf", "Carlito-Bold.ttf", "Carlito-Italic.ttf"):
    fontManager.addfont(f"/usr/share/fonts/truetype/crosextra/{f}")
plt.rcParams["font.family"] = "Carlito"

#: Nơi ghi sơ đồ. Chạy trong repo → docs/so_do/; chạy trong thư mục nộp bài →
#: bao_cao/hinh/. Truyền đối số để ghi đè.
def _noi_ghi() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1])
    repo = Path(__file__).resolve().parents[1]          # scripts/ → gốc repo
    if (repo / "docs").is_dir() and (repo / "eval").is_dir():
        return repo / "docs" / "so_do"
    return Path(__file__).resolve().parents[2] / "bao_cao" / "hinh"


RA = _noi_ghi()
RA.mkdir(parents=True, exist_ok=True)

BG      = "#f5ead8"
SURFACE = "#ebddc5"
TEXT    = "#201e1d"
ACCENT  = "#c67139"
ACCENT2 = "#7a8a5e"
N100, N300, N600, N700 = "#f9f4ed", "#dcd3c4", "#82796a", "#645c50"
A100, A200, A700 = "#fff2eb", "#ffe1d0", "#8c491a"
G100, G200, G700 = "#f0fae1", "#e1eecc", "#56633f"


def hop(ax, x, y, w, h, tieu_de, dong=(), nen=N100, vien=N300, mau_tieu_de=TEXT,
        r=0.055, co_td=12.5, co_dong=10.2, dam=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0,rounding_size={r}",
                                facecolor=nen, edgecolor=vien, linewidth=1.4, zorder=2))
    if dong:
        buoc_dong = 0.185
        cao = 0.215 + buoc_dong * (len(dong) - 1)
        ty = y + h / 2 + cao / 2 + 0.055
        ax.text(x + w / 2, ty, tieu_de, ha="center", va="center", fontsize=co_td,
                color=mau_tieu_de, fontweight="bold" if dam else "normal", zorder=3)
        b = ty - 0.215
        for d in dong:
            ax.text(x + w / 2, b, d, ha="center", va="center",
                    fontsize=co_dong, color=N700, zorder=3)
            b -= buoc_dong
    else:
        ax.text(x + w / 2, y + h / 2, tieu_de, ha="center", va="center", fontsize=co_td,
                color=mau_tieu_de, fontweight="bold" if dam else "normal", zorder=3)


def pill(ax, x, y, w, h, chu, nen=ACCENT, mau=BG, co=10.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0,rounding_size={h/2}",
                                facecolor=nen, edgecolor="none", zorder=3))
    ax.text(x + w / 2, y + h / 2, chu, ha="center", va="center",
            fontsize=co, color=mau, fontweight="bold", zorder=4)


def mui_ten(ax, p1, p2, mau=ACCENT, nét=2.0, hai_chieu=False, cong=0.0):
    ax.add_patch(FancyArrowPatch(
        p1, p2, arrowstyle="<|-|>" if hai_chieu else "-|>",
        mutation_scale=15, linewidth=nét, color=mau, zorder=1,
        connectionstyle=f"arc3,rad={cong}", shrinkA=2, shrinkB=2))


def nhan(ax, x, y, chu, mau=N600, co=9.6, nghieng=True):
    ax.text(x, y, chu, ha="center", va="center", fontsize=co, color=mau,
            style="italic" if nghieng else "normal", zorder=4,
            bbox=dict(boxstyle="round,pad=0.28", facecolor=BG, edgecolor="none"))


def khung(w, h):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 10); ax.set_ylim(0, h / w * 10)
    ax.axis("off")
    return fig, ax


# ───────────────────────────── Hình 1 — Kiến trúc ─────────────────────────────
fig, ax = khung(10.4, 7.1)
Y = 7.1 / 10.4 * 10

ax.text(0.15, Y - 0.22, "KIẾN TRÚC TỔNG THỂ", fontsize=10.5, color=A700,
        fontweight="bold")
ax.text(0.15, Y - 0.55, "Tra cứu kiến thức pháp luật giao thông đường bộ",
        fontsize=13.5, color=TEXT, fontweight="bold")

# đầu vào
hop(ax, 3.05, Y - 1.55, 3.9, 0.62, "Câu hỏi ngôn ngữ tự nhiên",
    nen=SURFACE, vien=N300, co_td=12)
mui_ten(ax, (5.0, Y - 1.55), (5.0, Y - 2.02))

# B1–B4
hop(ax, 2.25, Y - 3.22, 5.5, 1.20, "QueryAnalyzer",
    ("B1 chuẩn hoá  ·  B2 rút keyphrase (cụm dài nhất)",
     "B3 phân lớp bài toán  ·  B4 dựng biểu diễn Q"),
    nen=A100, vien="#ffc6a5", mau_tieu_de=A700, co_td=13.5)
pill(ax, 2.43, Y - 2.38, 0.95, 0.30, "B1–B4", nen=ACCENT)

mui_ten(ax, (5.0, Y - 3.22), (5.0, Y - 3.80))
nhan(ax, 5.0, Y - 3.51, "Q — biểu diễn hình thức")

# suy diễn + KB
hop(ax, 0.55, Y - 5.00, 4.55, 1.20, "InferenceEngine",
    ("điều phối bộ giải P1 – P7",
     "bổ sung tri thức nếu điểm ≥ 0,40"),
    nen=A200, vien=ACCENT, mau_tieu_de=A700, co_td=13.5)
pill(ax, 0.73, Y - 4.16, 0.72, 0.30, "B5", nen=ACCENT)

hop(ax, 5.55, Y - 5.00, 3.90, 1.20, "IndexedKnowledgeBase",
    ("K = (C, R, Rules, F, Keyphrase)",
     "chỉ mục  ·  TF-IDF  ·  NumericReasoner"),
    nen=G200, vien=ACCENT2, mau_tieu_de=G700, co_td=13.5)

mui_ten(ax, (5.10, Y - 4.40), (5.55, Y - 4.40), mau=ACCENT2, hai_chieu=True)

# dense tuỳ chọn
ax.add_patch(FancyBboxPatch((5.55, Y - 5.72), 3.90, 0.52,
                            boxstyle="round,pad=0,rounding_size=0.055",
                            facecolor=G100, edgecolor=ACCENT2, linewidth=1.3,
                            linestyle=(0, (4, 3)), zorder=2))
ax.text(7.50, Y - 5.46, "retrieval/dense.py  —  tuỳ chọn, mặc định tắt",
        ha="center", va="center", fontsize=10, color=G700, style="italic", zorder=3)
mui_ten(ax, (7.50, Y - 5.20), (7.50, Y - 5.00), mau=ACCENT2, nét=1.3, cong=0.0)

# sinh câu trả lời
mui_ten(ax, (2.82, Y - 5.00), (2.82, Y - 5.52))
hop(ax, 0.55, Y - 6.72, 4.55, 1.20, "sinh_van_ban",
    ("câu trả lời + căn cứ pháp lý (điều – khoản – điểm)",
     "+ tri thức liên quan"),
    nen=SURFACE, vien=N300, co_td=13.5)
pill(ax, 0.73, Y - 5.88, 0.72, 0.30, "B6", nen=ACCENT2)

ax.text(9.45, 0.28, "Hình 1. Kiến trúc hệ thống", ha="right", va="bottom",
        fontsize=9.5, color=N600, style="italic")
fig.savefig(str(RA / "hinh1_kien_truc.png"), dpi=300,
            bbox_inches="tight", facecolor=BG, pad_inches=0.22)
plt.close(fig)

# ────────────────────────── Hình 2 — Luồng B1 → B6 ───────────────────────────
fig, ax = khung(10.4, 5.2)
Y = 5.2 / 10.4 * 10

ax.text(0.15, Y - 0.20, "QUY TRÌNH XỬ LÝ TRUY VẤN", fontsize=10.5,
        color=A700, fontweight="bold")
ax.text(0.15, Y - 0.53, "Sáu bước B1 – B6, minh hoạ bằng một truy vấn thật",
        fontsize=13.5, color=TEXT, fontweight="bold")

buoc = [
    ("B1", "Chuẩn hoá", "hạ chữ thường,\nchuẩn Unicode,\nsinh bản không dấu"),
    ("B2", "Rút keyphrase", "so khớp cụm\ndài nhất,\nkhông chồng lấn"),
    ("B3", "Phân lớp bài toán", "hàm điểm có\ntrọng số trên 6 nhóm\nmẫu biểu thức"),
    ("B4", "Dựng biểu diễn Q", "keyphrase, nhóm,\nphương tiện, chủ thể,\ncăn cứ, ràng buộc số"),
    ("B5", "Suy diễn / truy hồi", "bộ giải riêng\nP1 – P7 +\nsuy diễn số học"),
    ("B6", "Sinh câu trả lời", "ghép nguyên văn\nđiều khoản kèm\ncăn cứ pháp lý"),
]
x0, w, gap = 0.22, 1.47, 0.145
ytop, hh = Y - 2.52, 1.62
for i, (ma, ten, mo_ta) in enumerate(buoc):
    x = x0 + i * (w + gap)
    cuoi = i == len(buoc) - 1
    ax.add_patch(FancyBboxPatch((x, ytop), w, hh,
                                boxstyle="round,pad=0,rounding_size=0.06",
                                facecolor=G200 if cuoi else N100,
                                edgecolor=ACCENT2 if cuoi else N300,
                                linewidth=1.5, zorder=2))
    pill(ax, x + w / 2 - 0.27, ytop + hh - 0.40, 0.54, 0.28, ma,
         nen=ACCENT2 if cuoi else ACCENT, co=9.5)
    ax.text(x + w / 2, ytop + hh - 0.70, ten, ha="center", va="center",
            fontsize=9.8, color=G700 if cuoi else TEXT, fontweight="bold", zorder=3)
    ax.text(x + w / 2, ytop + 0.40, mo_ta, ha="center", va="center",
            fontsize=7.9, color=N700, linespacing=1.55, zorder=3)
    if i < len(buoc) - 1:
        mui_ten(ax, (x + w + 0.02, ytop + hh / 2), (x + w + gap - 0.02, ytop + hh / 2),
                nét=1.6)

# dải ví dụ chạy suốt
ax.text(0.28, Y - 2.90, "VÍ DỤ — TRUY VẤN ĐI QUA SÁU BƯỚC", fontsize=9.2,
        color=A700, fontweight="bold")
vi_du = [
    ("nhau xong lai xe\nmay bi phat nhieu tien", False),
    ("«nồng độ cồn»\n«xe máy»", False),
    ("P3_TRA_CUU_\nCHE_TAI", True),
    ("Q(kp, pt = xe máy,\nràng buộc số: không)", False),
    ("V_NONG_DO_CON_XM_2\nđiểm 0,79", False),
    ("6.000.000 – 8.000.000 đ\nĐ.7 k.9 đ.a NĐ 168", False),
]
yv, hv = Y - 4.02, 0.92
for i, (v, mono) in enumerate(vi_du):
    x = x0 + i * (w + gap)
    ax.add_patch(FancyBboxPatch((x, yv), w, hv,
                                boxstyle="round,pad=0,rounding_size=0.06",
                                facecolor=SURFACE, edgecolor="none", zorder=2))
    ax.text(x + w / 2, yv + hv / 2, v, ha="center", va="center",
            fontsize=7.5 if mono else 7.9, color=N700, linespacing=1.6, zorder=3,
            family="DejaVu Sans Mono" if mono else "Carlito")
    if i < len(vi_du) - 1:
        ax.text(x + w + gap / 2, yv + hv / 2, "›", ha="center", va="center",
                fontsize=13, color=N600, zorder=3)

ax.text(0.28, Y - 4.45,
        "Chữ “nhậu” không xuất hiện trong bất kỳ văn bản luật nào — B2 không khớp cụm nào, "
        "B5 vẫn tìm đúng khung phạt nhờ thành phần ngữ nghĩa TF-IDF.",
        fontsize=9.3, color=N700, style="italic", va="center")

ax.text(9.72, 0.10, "Hình 2. Luồng xử lý truy vấn B1 – B6", ha="right", va="bottom",
        fontsize=9.5, color=N600, style="italic")
fig.savefig(str(RA / "hinh2_luong_b1_b6.png"), dpi=300,
            bbox_inches="tight", facecolor=BG, pad_inches=0.22)
plt.close(fig)
print(f"Da ghi 2 so do vao {RA}")
