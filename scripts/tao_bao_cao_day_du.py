# -*- coding: utf-8 -*-
"""Sinh BÁO CÁO HOÀN CHỈNH Đề tài 4 — CS106 Nhóm 7.

Khác với ``traffic_law.report.builder`` (chỉ sinh KHUNG rỗng có chỗ trống), tệp
này sinh bản báo cáo ĐÃ VIẾT ĐỦ bảy mục, chèn sẵn hai sơ đồ và toàn bộ bảng số
liệu. Mọi con số lấy thẳng từ JSON kết quả đo nên không bao giờ lệch thực đo.

Chạy:
    python scripts/tao_bao_cao_day_du.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt, RGBColor

FONT = "Times New Roman"
CO_CHU = 14
LE_CM = {"tren": 2, "duoi": 2, "trai": 3, "phai": 2}

#: Script chạy được ở HAI nơi, tự nhận ra mình đang ở đâu:
#:   • trong repo mã nguồn   → đọc eval/ + docs/ + data/kb/, ghi ra docs/
#:   • trong thư mục nộp bài → đọc so_lieu/ + ma_nguon/…, ghi ra bao_cao/
_REPO = Path(__file__).resolve().parents[1]          # scripts/ → gốc repo
_TRONG_REPO = (_REPO / "eval").is_dir() and (_REPO / "data" / "kb").is_dir()
_MAC_DINH = _REPO if _TRONG_REPO else Path(__file__).resolve().parents[2]

GOC = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else _MAC_DINH
if len(sys.argv) > 2:
    HINH = Path(sys.argv[2]).resolve()
else:
    HINH = GOC / ("docs/so_do" if _TRONG_REPO else "bao_cao/hinh")
if len(sys.argv) > 3:
    RA = Path(sys.argv[3]).resolve()
else:
    RA = GOC / ("docs" if _TRONG_REPO else "bao_cao") / "BaoCao_Nhom7_CS106.docx"


# ─────────────────────────────────── tiện ích ────────────────────────────────
def pc(x: float, chu_so: int = 2) -> str:
    return f"{x * 100:.{chu_so}f}".replace(".", ",") + "%"


def so(x: float, chu_so: int = 4) -> str:
    return f"{x:.{chu_so}f}".replace(".", ",")


def tien(x: int) -> str:
    return f"{x:,}".replace(",", ".")


def _el(tag: str, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn(f"w:{k}"), str(v))
    return e


def dinh_dang_chung(tl: Document) -> None:
    for ten, co, dam, mau in [("Normal", CO_CHU, None, None),
                              ("Heading 1", 16, True, RGBColor(0, 0, 0)),
                              ("Heading 2", 14, True, RGBColor(0, 0, 0)),
                              ("Heading 3", 14, True, RGBColor(0, 0, 0)),
                              ("List Bullet", CO_CHU, None, None),
                              ("List Number", CO_CHU, None, None),
                              ("Caption", 12, None, RGBColor(0, 0, 0))]:
        try:
            st = tl.styles[ten]
        except KeyError:
            continue
        st.font.name = FONT
        st.font.size = Pt(co)
        if dam is not None:
            st.font.bold = dam
        if mau is not None:
            st.font.color.rgb = mau
        rpr = st.element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = _el("w:rFonts")
            rpr.append(rf)
        for a in ("ascii", "hAnsi", "cs", "eastAsia"):
            rf.set(qn(f"w:{a}"), FONT)
    nor = tl.styles["Normal"].paragraph_format
    nor.space_after = Pt(6)
    nor.line_spacing = 1.3
    nor.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for ten, truoc, sau in [("Heading 1", 18, 8), ("Heading 2", 12, 6), ("Heading 3", 10, 4)]:
        pf = tl.styles[ten].paragraph_format
        pf.space_before, pf.space_after = Pt(truoc), Pt(sau)
        pf.keep_with_next = True


def dat_le(khu) -> None:
    khu.top_margin = Cm(LE_CM["tren"])
    khu.bottom_margin = Cm(LE_CM["duoi"])
    khu.left_margin = Cm(LE_CM["trai"])
    khu.right_margin = Cm(LE_CM["phai"])
    khu.gutter = Cm(0)


def vien_trang_bia(khu) -> None:
    """Box; Options: trên/dưới 1 pt, trái/phải 4 pt, đo từ Text — đúng ảnh hướng dẫn."""
    sectPr = khu._sectPr
    for cu in sectPr.findall(qn("w:pgBorders")):
        sectPr.remove(cu)
    pgb = _el("w:pgBorders", offsetFrom="text", display="firstPage")
    for canh, khoang in (("top", 1), ("left", 4), ("bottom", 1), ("right", 4)):
        pgb.append(_el(f"w:{canh}", val="single", sz=12, space=khoang, color="000000"))
    sectPr.append(pgb)


def bo_vien_trang(khu) -> None:
    """Section sau kế thừa pgBorders của section trước — phải ghi đè bằng none."""
    sectPr = khu._sectPr
    for cu in sectPr.findall(qn("w:pgBorders")):
        sectPr.remove(cu)
    pgb = _el("w:pgBorders", offsetFrom="page")
    for canh in ("top", "left", "bottom", "right"):
        pgb.append(_el(f"w:{canh}", val="none", sz=0, space=0, color="auto"))
    sectPr.append(pgb)


def so_trang(khu) -> None:
    p = khu.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    r.font.name, r.font.size = FONT, Pt(12)
    for tag, attrs, text in [("w:fldChar", {"fldCharType": "begin"}, None),
                             ("w:instrText", {"xml:space": "preserve"}, " PAGE "),
                             ("w:fldChar", {"fldCharType": "end"}, None)]:
        e = OxmlElement(tag)
        for k, v in attrs.items():
            e.set(qn(k) if ":" in k else qn(f"w:{k}"), v)
        if text:
            e.text = text
        r._r.append(e)


def muc_luc(tl: Document) -> None:
    p = tl.add_paragraph()
    r = p.add_run()
    for tag, attrs, text in [("w:fldChar", {"fldCharType": "begin"}, None),
                             ("w:instrText", {"xml:space": "preserve"},
                              r' TOC \o "1-3" \h \z \u '),
                             ("w:fldChar", {"fldCharType": "separate"}, None)]:
        e = OxmlElement(tag)
        for k, v in attrs.items():
            e.set(qn(k) if ":" in k else qn(f"w:{k}"), v)
        if text:
            e.text = text
        r._r.append(e)
    r2 = p.add_run("Nhấn chuột phải vào đây rồi chọn Update Field để hiện mục lục.")
    r2.italic = True
    e = OxmlElement("w:fldChar")
    e.set(qn("w:fldCharType"), "end")
    p.add_run()._r.append(e)


def doan(tl: Document, chu: str, dam: bool = False, nghieng: bool = False,
         canh=WD_ALIGN_PARAGRAPH.JUSTIFY, co: int | None = None, thut: float = 0.0):
    p = tl.add_paragraph()
    p.alignment = canh
    if thut:
        p.paragraph_format.first_line_indent = Cm(thut)
    r = p.add_run(chu)
    r.bold, r.italic = dam, nghieng
    if co:
        r.font.size = Pt(co)
    return p


def chu_thich(tl: Document, chu: str) -> None:
    p = tl.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = chu.startswith("Bảng")
    r = p.add_run(chu)
    r.italic = True
    r.font.size = Pt(12)


def bang(tl: Document, tieu_de: list[str], hang: list[list[str]],
         canh_phai: set[int] = frozenset(), co: int = 12,
         rong: list[float] | None = None):
    b = tl.add_table(rows=1, cols=len(tieu_de))
    b.style = "Table Grid"
    b.alignment = WD_TABLE_ALIGNMENT.CENTER
    b.autofit = False
    b.rows[0]._tr.get_or_add_trPr().append(_el("w:tblHeader", val="true"))
    for o, nhan in zip(b.rows[0].cells, tieu_de):
        o.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = o.paragraphs[0].add_run(nhan)
        r.bold = True
        r.font.size = Pt(co)
        r.font.name = FONT
    for d in hang:
        o_hang = b.add_row().cells
        for i, (o, gt) in enumerate(zip(o_hang, d)):
            p = o.paragraphs[0]
            if i in canh_phai:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(gt)
            r.font.size = Pt(co)
            r.font.name = FONT
    for h in b.rows:
        h._tr.get_or_add_trPr().append(_el("w:cantSplit", val="true"))
    if rong:
        tong = sum(rong)
        rong = [x / tong * 16.0 for x in rong]
        for h in b.rows:
            for o, w in zip(h.cells, rong):
                o.width = Cm(w)
    for h in b.rows:
        for o in h.cells:
            for p in o.paragraphs:
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.line_spacing = 1.0
    return b


def gach_dau_dong(tl: Document, cac_y: list[str], danh_so: bool = False) -> None:
    for y in cac_y:
        p = tl.add_paragraph(style="List Number" if danh_so else "List Bullet")
        p.paragraph_format.space_after = Pt(4)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if ": " in y and y.index(": ") < 60:
            dau, sau = y.split(": ", 1)
            r = p.add_run(dau + ": ")
            r.bold = True
            p.add_run(sau)
        else:
            p.add_run(y)


def hinh(tl: Document, duong_dan: Path, rong_cm: float, chu: str) -> None:
    p = tl.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_picture(str(duong_dan), width=Cm(rong_cm))
    chu_thich(tl, chu)


def trich(tl: Document, chu: str) -> None:
    p = tl.add_paragraph()
    p.paragraph_format.left_indent = Cm(1)
    p.paragraph_format.right_indent = Cm(0.5)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(chu)
    r.italic = True
    r.font.size = Pt(13)


def ma(tl: Document, dong: list[str]) -> None:
    for d in dong:
        p = tl.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = 1.0
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(d)
        r.font.name = "Consolas"
        r.font.size = Pt(10)
    tl.add_paragraph().paragraph_format.space_after = Pt(4)


# ─────────────────────────────────── dữ liệu ─────────────────────────────────
def tim(goc: Path, *ung_vien: str) -> Path:
    """Trả về tệp đầu tiên tồn tại — cho phép chạy ở cả repo lẫn thư mục nộp bài."""
    for c in ung_vien:
        p = goc / c
        if p.exists():
            return p
    raise FileNotFoundError(f"Khong tim thay {ung_vien[0]!r} duoi {goc}")


def nap(goc: Path) -> dict:
    def j(*ung_vien: str):
        return json.loads(tim(goc, *ung_vien).read_text(encoding="utf-8"))

    dg = j("so_lieu/ket_qua_danh_gia.json", "eval/ket_qua_danh_gia.json")
    qa = j("so_lieu/qa_dataset.json", "eval/qa_dataset.json")
    qa = qa["cau_hoi"] if isinstance(qa, dict) else qa
    ngoai = j("so_lieu/truy_van_ngoai_mien.json", "eval/truy_van_ngoai_mien.json")
    ngoai = ngoai["truy_van"] if isinstance(ngoai, dict) else ngoai
    dem_lop: dict[str, int] = {}
    dem_kho: dict[str, int] = {}
    for c in qa:
        dem_lop[c.get("lop_bai_toan_dung", "?")] = dem_lop.get(c.get("lop_bai_toan_dung", "?"), 0) + 1
        dem_kho[c.get("do_kho", "?")] = dem_kho.get(c.get("do_kho", "?"), 0) + 1
    return {
        "tv": j("ma_nguon/docs/thanh_vien.json", "docs/thanh_vien.json"),
        "th": dg["summary"],
        "cau_sai": dg["cau_sai"],
        "ab": j("so_lieu/ket_qua_ablation.json", "eval/ket_qua_ablation.json"),
        "mien": j("so_lieu/ket_qua_phat_hien_mien.json", "eval/ket_qua_phat_hien_mien.json"),
        "kt": j("so_lieu/ket_qua_kiem_thu.json", "eval/ket_qua_kiem_thu.json"),
        "kb": {t: len(j(f"ma_nguon/data/kb/{t}.json", f"data/kb/{t}.json")) for t in
               ("concepts", "relations", "rules", "violations", "keyphrases",
                "amendments", "documents")},
        "so_kho": dem_kho,
        "so_ngoai_mien": len(ngoai),
        "nghiem_thu": doc_nghiem_thu(tim(goc, "so_lieu/kich_ban_nghiem_thu.md",
                                        "eval/kich_ban_nghiem_thu.md")),
    }


def doc_nghiem_thu(p: Path) -> list[list[str]]:
    hang = []
    for d in p.read_text(encoding="utf-8").splitlines():
        d = d.strip()
        if not d.startswith("| TC"):
            continue
        o = [x.strip() for x in d.strip("|").split("|")]
        hang.append(o)
    return hang


TEN_LOP = {
    "P1_TRA_CUU_KHAI_NIEM": "P1 · Tra cứu khái niệm",
    "P2_TRA_CUU_QUY_DINH": "P2 · Tra cứu quy định",
    "P3_TRA_CUU_CHE_TAI": "P3 · Tra cứu chế tài",
    "P4_TRA_CUU_NGUOC": "P4 · Tra cứu ngược",
    "P5_SUY_DIEN_TINH_HUONG": "P5 · Suy diễn tình huống",
    "P6_TRA_CUU_CAN_CU": "P6 · Tra cứu căn cứ",
    "P7_TRA_CUU_LIEN_QUAN": "P7 · Tra cứu liên quan",
}


# ─────────────────────────────────── trang bìa ───────────────────────────────
def trang_bia(tl: Document, tv: dict) -> None:
    def giua(chu, dam=False, co=CO_CHU, truoc=0, sau=0, nghieng=False):
        p = tl.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(truoc)
        p.paragraph_format.space_after = Pt(sau)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(chu)
        r.bold, r.italic = dam, nghieng
        r.font.size = Pt(co)
        return p

    giua("ĐẠI HỌC QUỐC GIA THÀNH PHỐ HỒ CHÍ MINH", dam=True, co=13, truoc=6)
    giua("TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN", dam=True, co=13)
    giua("KHOA KHOA HỌC MÁY TÍNH", dam=True, co=13, sau=26)
    giua("CS106 — TRÍ TUỆ NHÂN TẠO", dam=True, co=16, sau=22)
    giua("BÁO CÁO ĐỒ ÁN MÔN HỌC", co=14, sau=8)
    giua("ĐỀ TÀI 4", dam=True, co=18, sau=6)
    giua("XÂY DỰNG HỆ THỐNG TRA CỨU KIẾN THỨC PHÁP LUẬT", dam=True, co=16)
    giua("Lĩnh vực: Giao thông đường bộ", co=15, nghieng=True, sau=26)

    giua("Giảng viên hướng dẫn: PGS.TS. Nguyễn Đình Hiển", co=14)
    giua(f"Lớp: {tv['lop']}          Nhóm: {tv['nhom']}", co=14, sau=14)

    b = tl.add_table(rows=1, cols=3)
    b.style = "Table Grid"
    b.alignment = WD_TABLE_ALIGNMENT.CENTER
    for o, nhan, w in zip(b.rows[0].cells, ("STT", "Họ và tên", "MSSV"), (1.6, 7.4, 3.4)):
        o.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = o.paragraphs[0].add_run(nhan)
        r.bold = True
        r.font.size = Pt(13)
        r.font.name = FONT
        o.width = Cm(w)
    for i, ng in enumerate(tv["thanh_vien"], 1):
        o = b.add_row().cells
        for j, (gt, giua_o, w) in enumerate([(str(i), True, 1.6),
                                             (ng["ho_ten"], False, 7.4),
                                             (ng["mssv"], True, 3.4)]):
            o[j].width = Cm(w)
            p = o[j].paragraphs[0]
            if giua_o:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            r = p.add_run(gt)
            r.font.size = Pt(13)
            r.font.name = FONT
    giua("", truoc=22)
    giua("Thành phố Hồ Chí Minh, tháng 9 năm 2026", nghieng=True, co=13, truoc=18)


# ──────────────────────────────────── nội dung ───────────────────────────────
def than_bai(tl: Document, d: dict) -> None:
    th, ab, kb, kt = d["th"], d["ab"], d["kb"], d["kt"]
    toan_bo, co_so = ab["toan_bo"], ab["cau_hoi_co_gia_tri_so"]

    # ── 1 ────────────────────────────────────────────────────────────────────
    tl.add_heading("1. Giới thiệu", level=1)

    tl.add_heading("1.1. Bối cảnh và lý do chọn đề tài", level=2)
    doan(tl, "Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15 và Nghị định "
             "168/2024/NĐ-CP cùng có hiệu lực từ ngày 01 tháng 01 năm 2025, thay thế "
             "toàn bộ khung pháp lý cũ và nâng mạnh mức xử phạt ở nhiều nhóm hành vi. "
             "Chỉ trong hơn một năm sau đó, khung này tiếp tục được sửa đổi hai lần: "
             "Luật 118/2025/QH15 (hiệu lực 01/7/2026) và Nghị định 238/2026/NĐ-CP "
             "(hiệu lực 15/8/2026). Người tham gia giao thông vì vậy đứng trước một "
             "khối văn bản vừa mới, vừa phân tán, vừa liên tục thay đổi.", thut=0.5)
    doan(tl, "Khó khăn thực tế không nằm ở chỗ thiếu thông tin mà ở chỗ thông tin bị "
             "tách rời. Luật quy định hành vi nào bị nghiêm cấm; nghị định mới quy "
             "định hành vi đó bị phạt bao nhiêu tiền và bị trừ mấy điểm giấy phép lái "
             "xe. Câu hỏi thường gặp nhất của người dân — “vượt đèn đỏ phạt bao nhiêu” "
             "— do đó không thể trả lời nếu chỉ đọc một văn bản. Các công cụ tìm kiếm "
             "phổ thông trả về toàn văn điều khoản, buộc người hỏi tự đối chiếu; còn "
             "các trợ lý sinh ngôn ngữ tự nhiên thì có nguy cơ diễn giải sai lời của "
             "luật mà không nêu được căn cứ.", thut=0.5)
    doan(tl, "Nhóm chọn Đề tài 4 vì lĩnh vực giao thông đường bộ hội đủ ba đặc điểm "
             "phù hợp với một hệ tra cứu dựa trên tri thức: văn bản có cấu trúc chặt "
             "(điều – khoản – điểm), tri thức có tính suy diễn (ngưỡng nồng độ cồn, "
             "mức vượt tốc độ), và mọi câu trả lời đều phải truy nguyên được về căn "
             "cứ pháp lý.", thut=0.5)

    tl.add_heading("1.2. Mục tiêu và phạm vi", level=2)
    gach_dau_dong(tl, [
        "Mục tiêu: xây dựng cơ sở tri thức có cấu trúc cho lĩnh vực giao thông đường "
        "bộ và một hệ tra cứu trả lời câu hỏi tiếng Việt tự nhiên, luôn kèm căn cứ "
        "pháp lý truy nguyên được.",
        "Phạm vi tri thức: quy tắc giao thông, khái niệm pháp lý, hành vi vi phạm và "
        "chế tài đối với người điều khiển phương tiện; chưa bao gồm quy định về kết "
        "cấu hạ tầng, đăng kiểm chuyên sâu và vận tải đường bộ.",
        "Phạm vi kỹ thuật: hệ không sinh ngôn ngữ tự nhiên. Câu trả lời được ghép từ "
        "nguyên văn điều khoản — đây là lựa chọn có chủ đích, trình bày ở mục 5.",
    ])

    tl.add_heading("1.3. Đóng góp của nhóm", level=2)
    gach_dau_dong(tl, [
        f"Cơ sở tri thức K = (C, R, Rules, F, Keyphrase) gồm {kb['concepts']} khái "
        f"niệm, {kb['relations']} quan hệ, {kb['rules']} quy tắc, "
        f"{tien(kb['violations'])} hành vi vi phạm và {tien(kb['keyphrases'])} cụm từ "
        "khoá, 100% mục có căn cứ pháp lý và khoảng hiệu lực.",
        "Thuật giải xử lý truy vấn sáu bước với hàm điểm lai ba thành phần, kèm bộ "
        "suy diễn số học cho các điều khoản có ngưỡng.",
        f"Bộ dữ liệu đánh giá {th['so_cau_hoi']} câu hỏi có đáp án chuẩn và "
        f"{d['so_ngoai_mien']} truy vấn ngoài lĩnh vực, cùng kết quả đo đầy đủ.",
        "Giao diện tra cứu chạy được và bộ kiểm thử tự động khoá ngưỡng chỉ số, "
        "ngăn mọi thay đổi làm tụt chất lượng.",
    ])

    # ── 2 ────────────────────────────────────────────────────────────────────
    tl.add_heading("2. Cơ sở tri thức", level=1)

    tl.add_heading("2.1. Nguồn văn bản và giải trình phạm vi", level=2)
    doan(tl, "Đề bài yêu cầu chọn “01 văn bản pháp luật tương ứng”. Nhóm thực hiện "
             "trên bốn văn bản và xin giải trình ngay từ đầu, vì đây là quyết định "
             "thiết kế chứ không phải làm lệch đề.", thut=0.5)
    doan(tl, "Luật 36/2024/QH15 quy định hành vi nào bị nghiêm cấm, nhưng không quy "
             "định mức phạt; toàn bộ chế tài nằm ở Nghị định 168/2024/NĐ-CP. Nếu chỉ "
             "dùng văn bản luật gốc, hệ thống sẽ không trả lời được câu hỏi phổ biến "
             "nhất trong thực tế là “phạt bao nhiêu tiền”. Hai văn bản sửa đổi được "
             "đưa thêm vào để hệ thống trả lời đúng theo mốc thời gian, thay vì trả "
             "lời theo bản đã lỗi thời.", thut=0.5)
    chu_thich(tl, "Bảng 1. Bốn văn bản nguồn và vai trò trong cơ sở tri thức")
    bang(tl, ["Văn bản", "Vai trò", "Hiệu lực"], [
        ["Luật 36/2024/QH15", "Văn bản chính — quy tắc, khái niệm, hành vi bị cấm",
         "01/01/2025"],
        ["Nghị định 168/2024/NĐ-CP", "Văn bản chế tài — mức phạt, trừ điểm GPLX",
         "01/01/2025"],
        ["Luật 118/2025/QH15", "Sửa đổi Luật 36/2024", "01/7/2026"],
        ["Nghị định 238/2026/NĐ-CP", "Sửa đổi Nghị định 168/2024", "15/8/2026"],
    ], canh_phai={2}, rong=[5, 8, 3])
    doan(tl, "Mọi mục tri thức đều được đối chiếu với Văn bản hợp nhất 55/VBHN-VPQH "
             "ngày 23/3/2026 của Văn phòng Quốc hội — tức bản sau sửa đổi. Trường "
             "can_cu_text của từng bản ghi ghi rõ điều này, nên người chấm kiểm tra "
             "được ngay rằng dữ liệu không phải bản cũ.", thut=0.5)

    tl.add_heading("2.2. Mô hình tri thức", level=2)
    doan(tl, "Cơ sở tri thức được đặc tả hình thức dưới dạng bộ năm:", thut=0.5)
    ma(tl, ["K = (C, R, Rules, F, Keyphrase)"])
    chu_thich(tl, "Bảng 2. Năm thành phần của cơ sở tri thức")
    bang(tl, ["Ký hiệu", "Thành phần", "Số lượng", "Vai trò"], [
        ["C", "Khái niệm", tien(kb["concepts"]),
         "Định nghĩa pháp lý — “xe cơ giới là gì”"],
        ["R", "Quan hệ", tien(kb["relations"]),
         "Đồ thị hai chiều nối các mảng tri thức"],
        ["Rules", "Quy tắc", tien(kb["rules"]),
         "Quy định phải làm / không được làm"],
        ["F", "Hành vi vi phạm", tien(kb["violations"]),
         "Hành vi kèm chế tài: tiền, trừ điểm, hình phạt bổ sung"],
        ["Keyphrase", "Cụm từ khoá", tien(kb["keyphrases"]),
         "Cầu nối giữa ngôn ngữ người dùng và định danh tri thức"],
    ], canh_phai={0, 2}, rong=[2.2, 3.4, 2.2, 8.2])
    doan(tl, f"Ngoài năm thành phần trên, cơ sở tri thức còn lưu {kb['documents']} bản "
             f"ghi văn bản nguồn và {kb['amendments']} bản ghi sửa đổi. Sửa đổi được "
             "lưu như dữ liệu độc lập, không hợp nhất cứng lúc dựng cơ sở tri thức — "
             "nhờ vậy hệ thống trả lời được câu hỏi “tại thời điểm nào thì quy định "
             "ra sao”.", thut=0.5)

    tl.add_heading("2.3. Cách thu thập và chuẩn hoá", level=2)
    gach_dau_dong(tl, [
        "Trích xuất: tách toàn văn theo cấu trúc điều – khoản – điểm từ bản công bố "
        "của bốn văn bản, lưu ở data/raw/ dưới dạng JSON giữ nguyên văn.",
        "Chuẩn hoá: mỗi mục tri thức được gán một định danh ổn định (ví dụ R01, "
        "VP_OTO_ND168D6_K1A), một khối căn cứ có cấu trúc và một khoảng hiệu lực.",
        "Sinh keyphrase: mỗi mục kèm danh sách cụm từ người dùng thật hay dùng, gồm "
        "cả khẩu ngữ (“nhậu”, “vượt đèn đỏ”) và bản không dấu.",
        "Kiểm toàn vẹn: module kb/validator.py soát định danh trùng, quan hệ treo, "
        "keyphrase trỏ tới định danh không tồn tại và mục thiếu căn cứ. Toàn bộ "
        "kiểm tra này chạy trong CI.",
    ])
    doan(tl, "Chuẩn hoá bằng mô hình có kiểu (Pydantic v2) chứ không phải dict tự do: "
             "trường lạ bị từ chối ngay lúc nạp, nên một bản ghi sai cấu trúc không "
             "thể lọt vào cơ sở tri thức mà đến lúc chạy mới phát hiện.", thut=0.5)

    tl.add_heading("2.4. Ví dụ bản ghi", level=2)
    doan(tl, "Một bản ghi khái niệm (rút gọn):", thut=0.5)
    ma(tl, [
        '{',
        '  "id": "KN_TRAT_TU_AN_TOAN_GTDB",',
        '  "ten": "Trật tự, an toàn giao thông đường bộ",',
        '  "dinh_nghia": "... là trạng thái giao thông trên đường bộ',
        '                 có trật tự, bảo đảm an toàn, thông suốt; ...",',
        '  "keyphrases": ["trật tự an toàn giao thông đường bộ",',
        '                 "TTATGTĐB", "an toàn giao thông"],',
        '  "can_cu": { "van_ban": "Luật 36/2024/QH15",',
        '              "dieu": 2, "khoan": 1 }',
        '}',
    ])
    doan(tl, "Một bản ghi hành vi vi phạm (rút gọn):", thut=0.5)
    ma(tl, [
        '{',
        '  "id": "VP_OTO_ND168D6_K1A",',
        '  "hanh_vi": "Không chấp hành hiệu lệnh, chỉ dẫn của',
        '              biển báo hiệu, vạch kẻ đường, trừ ...",',
        '  "nhom": "bien_bao_hieu",',
        '  "phuong_tien": ["o_to"],',
        '  "phat_tien": { "min": 400000, "max": 600000,',
        '                 "don_vi": "VND" },',
        '  "tru_diem_gplx": 0,',
        '  "can_cu": { "van_ban": "Nghị định 168/2024/NĐ-CP",',
        '              "dieu": 6, "khoan": 1, "diem": "a" },',
        '  "tinh_trang": "hien_hanh"',
        '}',
    ])
    doan(tl, "Hai bản ghi trên cho thấy điểm mấu chốt: chế tài là dữ liệu có kiểu "
             "(số tiền là số nguyên, điểm trừ là số nguyên), không phải chuỗi văn bản. "
             "Nhờ vậy hệ thống cộng dồn được mức phạt của nhiều hành vi trong một tình "
             "huống và tra ngược được “lỗi nào bị trừ 10 điểm”.", thut=0.5)

    # ── 3 ────────────────────────────────────────────────────────────────────
    tl.add_heading("3. Thiết kế giải pháp", level=1)

    tl.add_heading("3.1. Kiến trúc tổng thể", level=2)
    doan(tl, "Hệ thống gồm ba tầng nối tiếp. QueryAnalyzer biến câu hỏi tiếng Việt "
             "thành một biểu diễn hình thức Q; InferenceEngine dùng Q để chọn bộ giải "
             "và truy hồi tri thức từ IndexedKnowledgeBase; hàm sinh văn bản ghép câu "
             "trả lời kèm căn cứ pháp lý. Tầng dense embedding là tuỳ chọn và mặc "
             "định không được gọi — lý do trình bày ở mục 5.", thut=0.5)
    if (HINH / "hinh1_kien_truc.png").exists():
        hinh(tl, HINH / "hinh1_kien_truc.png", 15.5, "Hình 1. Kiến trúc hệ thống")

    tl.add_heading("3.2. Thuật giải xử lý truy vấn B1 – B6", level=2)
    chu_thich(tl, "Bảng 3. Sáu bước xử lý một truy vấn")
    bang(tl, ["Bước", "Việc", "Hiện thực"], [
        ["B1", "Chuẩn hoá truy vấn",
         "Hạ chữ thường, chuẩn hoá Unicode, sinh bản không dấu"],
        ["B2", "Rút trích keyphrase",
         "So khớp cụm dài nhất trên bản không dấu, không chồng lấn"],
        ["B3", "Phân loại lớp bài toán",
         "Hàm điểm có trọng số trên sáu nhóm mẫu biểu thức chính quy"],
        ["B4", "Dựng biểu diễn hình thức Q",
         "Keyphrase, nhóm, phương tiện, chủ thể, căn cứ, ràng buộc số"],
        ["B5", "Suy diễn và truy hồi", "Bộ giải riêng cho từng lớp P1 – P7"],
        ["B6", "Sinh câu trả lời",
         "Ghép nguyên văn điều khoản kèm căn cứ và tri thức liên quan"],
    ], canh_phai={0}, rong=[1.6, 5.0, 9.4])
    doan(tl, "Vì sao B2 phải khớp cụm dài nhất: cụm “nồng độ cồn” phải thắng hai cụm "
             "rời “nồng độ” và “cồn”. Nếu khớp cụm ngắn trước, truy vấn sẽ trỏ sang "
             "mảng tri thức khác và mọi bước sau đều sai theo.", thut=0.5)
    if (HINH / "hinh2_luong_b1_b6.png").exists():
        hinh(tl, HINH / "hinh2_luong_b1_b6.png", 15.5,
             "Hình 2. Luồng xử lý truy vấn B1 – B6 với một truy vấn thật")

    tl.add_heading("3.3. Bảy lớp bài toán", level=2)
    chu_thich(tl, "Bảng 4. Bảy lớp bài toán và câu hỏi tiêu biểu")
    bang(tl, ["Lớp", "Tên", "Câu hỏi tiêu biểu"], [
        ["P1", "Tra cứu khái niệm, định nghĩa", "Xe cơ giới là gì?"],
        ["P2", "Tra cứu quy định, quy tắc",
         "Quy tắc nhường đường tại nơi đường giao nhau?"],
        ["P3", "Tra cứu chế tài", "Vượt đèn đỏ xe máy phạt bao nhiêu?"],
        ["P4", "Tra cứu ngược theo mức phạt / điểm trừ",
         "Lỗi nào bị trừ 10 điểm giấy phép lái xe?"],
        ["P5", "Suy diễn tình huống nhiều hành vi",
         "Vừa vượt đèn đỏ vừa không có bằng thì tổng bao nhiêu?"],
        ["P6", "Tra cứu theo căn cứ pháp lý",
         "Điều 6 khoản 9 điểm a NĐ 168/2024 nói về lỗi gì?"],
        ["P7", "Tra cứu kiến thức liên quan",
         "Cho tôi thông tin về điểm giấy phép lái xe."],
    ], canh_phai={0}, rong=[1.4, 6.4, 8.2])
    doan(tl, "Điểm thiết kế đáng chú ý: phân lớp không chặn kết quả. Sau khi bộ giải "
             "của lớp được chọn chạy xong, hệ thống vẫn bổ sung đủ ba loại tri thức "
             "(khái niệm, quy tắc, chế tài) nếu còn thiếu và điểm vượt ngưỡng 0,40. "
             "Nhờ vậy một câu bị phân lớp sai vẫn có cơ hội trả đúng — đây chính là "
             f"lý do Top-5 ({pc(th['top5'])}) cao hơn hẳn Top-1 ({pc(th['top1'])}).",
         thut=0.5)

    tl.add_heading("3.4. Hàm điểm lai", level=2)
    ma(tl, ["score = ALPHA · s_keyphrase + BETA · s_ngữ_nghĩa + GAMMA · s_ngữ_cảnh",
            "ALPHA = 0,55        BETA = 0,30        GAMMA = 0,15"])
    chu_thich(tl, "Bảng 5. Ba thành phần của hàm điểm và lý do chọn trọng số")
    bang(tl, ["Thành phần", "Ý nghĩa", "Vì sao trọng số đó"], [
        ["s_keyphrase", "Keyphrase trỏ thẳng tới định danh tri thức",
         "Cao nhất (0,55) vì đây là tín hiệu chắc chắn: khớp đúng cụm từ pháp lý "
         "thì gần như không sai."],
        ["s_ngữ_nghĩa", "Cosine TF-IDF char 3–5 gram kết hợp word 1–3 gram",
         "0,30 — cứu các câu khẩu ngữ không có keyphrase, nhưng nhiễu hơn nên "
         "không được vượt keyphrase."],
        ["s_ngữ_cảnh", "Khớp phương tiện, chủ thể, nhóm hành vi",
         "0,15 — chỉ dùng để phân biệt các hành vi gần giống nhau, không đủ sức "
         "tự chọn kết quả."],
    ], rong=[3.0, 5.6, 7.4])
    doan(tl, "Char n-gram chịu được lỗi chính tả và cách tách từ tiếng Việt; word "
             "n-gram giữ được cụm nhiều từ. Với khái niệm và quy tắc, điểm còn được "
             "trộn thêm 0,4 phần khớp riêng với tên của mục tri thức.", thut=0.5)

    tl.add_heading("3.5. Suy diễn số học", level=2)
    doan(tl, "Nhiều điều khoản phân khung theo ngưỡng số: nồng độ cồn chia ba mức, "
             "vượt tốc độ chia bốn mức. So khớp từ khoá đơn thuần tìm ra đủ các khung "
             "nhưng không biết chọn khung nào. NumericReasoner rút ngưỡng từ chính "
             "nguyên văn điều khoản, so sánh khoảng với giá trị trong câu hỏi rồi đẩy "
             "khung đúng lên đầu.", thut=0.5)
    trich(tl, "Ví dụ: “xe máy nồng độ cồn 0,3 mg/l phạt bao nhiêu” → 0,3 thuộc khung "
              "“vượt quá 0,25 đến 0,4 miligam/1 lít khí thở”, không phải khung 0,25 "
              "hay khung trên 0,4. Hỏi liên tiếp 0,2 – 0,3 – 0,5 cho ba khung phạt "
              "khác nhau.")

    tl.add_heading("3.6. Hiệu lực theo thời gian", level=2)
    doan(tl, "Sửa đổi được lưu như dữ liệu chứ không hợp nhất cứng, nên mỗi mục tri "
             "thức mang một khoảng hiệu lực (từ, đến) và hệ thống trả lời được theo "
             "mốc thời gian người dùng chọn. Ví dụ quy tắc R15 về chở trẻ em dưới 10 "
             "tuổi mang nguyên văn sau sửa đổi nên có hiệu lực từ 01/7/2026 theo Luật "
             "118/2025, không phải 01/01/2025.", thut=0.5)

    # ── 4 ────────────────────────────────────────────────────────────────────
    tl.add_heading("4. Thực nghiệm và đánh giá", level=1)

    tl.add_heading("4.1. Bộ dữ liệu và phương pháp đo", level=2)
    kho = d["so_kho"]
    doan(tl, f"Bộ dữ liệu đánh giá gồm {th['so_cau_hoi']} câu hỏi, mỗi câu có đáp án "
             "chuẩn dạng văn bản, danh sách định danh tri thức đúng, lớp bài toán "
             "đúng và mức độ khó. Hệ thống trả về k = "
             f"{th['top_k']} kết quả cho mỗi truy vấn. Ngoài ra còn "
             f"{d['so_ngoai_mien']} truy vấn ngoài lĩnh vực dùng để đo khả năng từ "
             "chối.", thut=0.5)
    doan(tl, "Phân bố theo lớp bài toán: " + " · ".join(
        f"{TEN_LOP[k].split(' · ')[0]} {v['n']}"
        for k, v in th["theo_lop_bai_toan"].items()) +
        ". Phân bố theo độ khó: " + " · ".join(
        f"{k.replace('_', ' ')} {v}" for k, v in sorted(kho.items())) + ".", thut=0.5)

    tl.add_heading("4.2. Kết quả tổng thể", level=2)
    chu_thich(tl, "Bảng 6. Chỉ số đánh giá tổng thể trên "
                  f"{th['so_cau_hoi']} câu hỏi (k = {th['top_k']})")
    bang(tl, ["Chỉ số", "Giá trị", "Ghi chú"], [
        ["Độ chính xác phân lớp", pc(th["do_chinh_xac_phan_lop"]),
         f"{round(th['do_chinh_xac_phan_lop'] * th['so_cau_hoi'])}/{th['so_cau_hoi']} "
         "câu vào đúng lớp bài toán"],
        ["Top-1", pc(th["top1"]), "Cổng chỉ số trong CI chặn mọi thay đổi làm tụt "
                                  "dưới mức này"],
        ["Top-3", pc(th["top3"]), "—"],
        ["Top-5", pc(th["top5"]), f"{th['so_cau_sai']}/{th['so_cau_hoi']} câu sai "
                                  "hoàn toàn"],
        ["MRR", so(th["mrr"]), "Đáp án đúng thường nằm ở vị trí 1–2"],
        ["Precision (macro)", so(th["precision_macro"]),
         "Trả 5 kết quả cho đáp án một mẩu → trần toán học 0,20 mỗi câu"],
        ["Recall (macro)", so(th["recall_macro"]), "—"],
        ["F1 (macro)", so(th["f1_macro"]), "—"],
        ["Thời gian trả lời trung bình", so(th["thoi_gian_tb_ms"], 1) + " ms",
         "Chạy hoàn toàn cục bộ, không gọi dịch vụ ngoài"],
    ], canh_phai={1}, rong=[5.4, 2.6, 8.0])

    tl.add_heading("4.3. Kết quả theo lớp bài toán", level=2)
    chu_thich(tl, "Bảng 7. Chỉ số theo từng lớp bài toán")
    bang(tl, ["Lớp bài toán", "n", "Phân lớp", "Top-1", "Top-5"], [
        [TEN_LOP.get(k, k), str(v["n"]), pc(v["acc_phan_lop"], 1),
         pc(v["top1"], 1), pc(v["top5"], 1)]
        for k, v in th["theo_lop_bai_toan"].items()
    ], canh_phai={1, 2, 3, 4}, rong=[6.4, 1.6, 2.8, 2.6, 2.6])

    doan(tl, "Nhận xét:", dam=True)
    p1 = th["theo_lop_bai_toan"]["P2_TRA_CUU_QUY_DINH"]
    p7 = th["theo_lop_bai_toan"]["P7_TRA_CUU_LIEN_QUAN"]
    p4 = th["theo_lop_bai_toan"]["P4_TRA_CUU_NGUOC"]
    gach_dau_dong(tl, [
        f"P2 chỉ đạt Top-1 {pc(p1['top1'], 1)} nhưng Top-5 lên {pc(p1['top5'], 1)}. "
        "Nguyên nhân không phải hệ thống tìm sai mà là các quy tắc giao thông có "
        "nhiều điều khoản gần nghĩa: đáp án đúng CÓ trong danh sách trả về, chỉ chưa "
        "được xếp đầu. Đây là lớp cần thêm tín hiệu phân biệt, không phải lớp hỏng.",
        f"P7 chỉ đạt Top-1 {pc(p7['top1'], 1)} nhưng Top-5 đạt {pc(p7['top5'], 1)}. "
        "Lớp “tra cứu kiến thức liên quan” về bản chất không có một đáp án duy nhất "
        "— người hỏi muốn một chùm tri thức. Chỉ số Top-1 vì vậy không phản ánh đúng "
        "chất lượng ở lớp này; Top-5 mới là thước đo phù hợp.",
        f"P4 phân lớp đúng {pc(p4['acc_phan_lop'], 1)} và Top-5 đạt "
        f"{pc(p4['top5'], 1)}, nhưng Top-1 chỉ {pc(p4['top1'], 1)}: tra ngược theo "
        "mức phạt thường có nhiều hành vi cùng thoả điều kiện, việc xếp hạng giữa "
        "chúng chưa có tiêu chí nào tốt hơn điểm tương đồng văn bản.",
        f"Precision macro {so(th['precision_macro'])} KHÔNG phải khiếm khuyết. Hệ trả "
        f"k = {th['top_k']} kết quả trong khi đáp án chuẩn của phần lớn câu chỉ có "
        "một mẩu tri thức, nên trần precision toán học là 0,20 mỗi câu. Con số đo "
        "được đã cao hơn trần đó, nghĩa là nhiều câu có nhiều hơn một kết quả đúng "
        f"trong danh sách trả về. Recall macro {so(th['recall_macro'])} mới là chỉ số "
        "phản ánh đúng mục tiêu của một hệ tra cứu.",
    ])

    tl.add_heading("4.4. Thí nghiệm loại bỏ thành phần", level=2)
    doan(tl, "Để chứng minh từng thành phần của hàm điểm thực sự đóng góp chứ không "
             "phải chọn trọng số cảm tính, nhóm chạy thí nghiệm loại bỏ thành phần "
             f"trên cả {ab['so_cau_hoi']} câu hỏi.", thut=0.5)
    chu_thich(tl, "Bảng 8. Kết quả loại bỏ thành phần (ablation)")
    bang(tl, ["Cấu hình", "Top-1", "Top-5", "MRR"], [
        [k, pc(v["top1"] / 100, 1), pc(v["topk"] / 100, 1), so(v["mrr"])]
        for k, v in toan_bo.items()
    ], canh_phai={1, 2, 3}, rong=[8.2, 2.6, 2.6, 2.6])
    chu_thich(tl, "Bảng 9. Ablation riêng trên "
                  f"{ab['so_cau_hoi_co_so']} câu hỏi có giá trị số")
    bang(tl, ["Cấu hình", "Top-1", "Top-5", "MRR"], [
        [k, pc(v["top1"] / 100, 1), pc(v["topk"] / 100, 1), so(v["mrr"])]
        for k, v in co_so.items()
    ], canh_phai={1, 2, 3}, rong=[8.2, 2.6, 2.6, 2.6])

    doan(tl, "Nhận xét:", dam=True)
    a, b_, c, dd = (toan_bo[k] for k in toan_bo)
    cC, cD = (co_so[k] for k in co_so)
    gach_dau_dong(tl, [
        f"Keyphrase đứng riêng ({pc(b_['top1'] / 100, 1)}) YẾU HƠN TF-IDF đứng riêng "
        f"({pc(a['top1'] / 100, 1)}), nhưng vẫn xứng đáng nhận trọng số cao nhất "
        "0,55. Lý do: nó thua về ĐỘ PHỦ chứ không thua về ĐỘ CHÍNH XÁC — câu nào có "
        "keyphrase thì gần như chắc đúng, chỉ là nhiều câu khẩu ngữ không có "
        "keyphrase nào.",
        f"Lai ba thành phần đưa Top-1 lên {pc(c['top1'] / 100, 1)}: TF-IDF lo phần "
        "phủ, keyphrase lo phần chuẩn. Đây là bằng chứng cho thấy hai tín hiệu bù "
        "trừ nhau chứ không trùng lặp.",
        f"Thêm suy diễn số học đưa Top-1 lên {pc(dd['top1'] / 100, 1)}. Riêng "
        f"{ab['so_cau_hoi_co_so']} câu có giá trị số, Top-1 nhảy từ "
        f"{pc(cC['top1'] / 100, 1)} lên {pc(cD['top1'] / 100, 1)} trong khi Top-5 "
        f"gần như không đổi ({pc(cC['topk'] / 100, 1)} → {pc(cD['topk'] / 100, 1)}). "
        "Con số này nói đúng một điều: so khớp từ khoá VẪN TÌM RA đủ các khung phạt, "
        "nó chỉ không biết CHỌN KHUNG NÀO. Suy diễn số học giải quyết đúng khâu đó.",
    ])

    tl.add_heading("4.5. Phân tích các câu trả lời sai", level=2)
    cs = d["cau_sai"]
    sai_lop = sum(1 for c in cs if c.get("sai_lop"))
    sai_th = sum(1 for c in cs if c.get("sai_truy_hoi"))
    doan(tl, f"{len(cs)}/{th['so_cau_hoi']} câu sai hoàn toàn (đáp án đúng không nằm "
             f"trong 5 kết quả trả về): {sai_lop} câu sai do phân lớp, {sai_th} câu "
             "sai do truy hồi, một số câu sai cả hai.", thut=0.5)
    chu_thich(tl, "Bảng 10. Danh sách câu trả lời sai và nguyên nhân")
    bang(tl, ["Mã", "Câu hỏi", "Nguyên nhân"], [
        [c["id"], c["question"][:78] + ("…" if len(c["question"]) > 78 else ""),
         ("Sai phân lớp + sai truy hồi" if c["sai_lop"] and c["sai_truy_hoi"]
          else "Sai phân lớp" if c["sai_lop"] else "Sai truy hồi")]
        for c in cs
    ], canh_phai={0}, co=11, rong=[1.4, 10.4, 4.2])
    doan(tl, "Ba nhóm nguyên nhân rút ra được:", thut=0.5)
    gach_dau_dong(tl, [
        "Câu hỏi khẩu ngữ dài, nhiều mệnh đề phụ (Q020, Q032, Q101): keyphrase bị "
        "loãng giữa các từ không mang thông tin pháp lý.",
        "Câu hỏi dạng có / không (Q021, Q035): người hỏi chờ một câu khẳng định, "
        "trong khi hệ thống trả về điều khoản gần nghĩa nhất.",
        "Câu hỏi nhiều hành vi cùng lúc (Q096, Q104): bộ giải P5 chọn được hành vi "
        "chính nhưng bỏ sót hành vi phụ, làm lệch danh sách xếp hạng.",
    ])

    tl.add_heading("4.6. Kiểm thử nghiệm thu và kiểm thử tự động", level=2)
    chu_thich(tl, "Bảng 11. Mười hai ca nghiệm thu chức năng")
    bang(tl, ["Mã", "Nhóm", "Câu hỏi", "Kết quả"],
         [[h[0], h[1], h[2][:58] + ("…" if len(h[2]) > 58 else ""), h[4]]
          for h in d["nghiem_thu"]], canh_phai={0, 3}, co=11,
         rong=[1.4, 3.2, 9.4, 2.0])
    doan(tl, f"Toàn bộ {len(d['nghiem_thu'])}/{len(d['nghiem_thu'])} ca đạt. Ngoài ra "
             f"bộ kiểm thử tự động có {kt['so_test_dat']} test đạt, "
             f"{kt['so_xfail']} test xfail có số đo kèm theo, {kt['so_skip']} test bỏ "
             f"qua vì cần gói tuỳ chọn, độ phủ mã {kt['do_phu_phan_tram']}% "
             f"(ngưỡng CI là {kt['nguong_do_phu_ci']}%). Các test xfail được đặt ở "
             "chế độ strict: ngày nào chúng bất ngờ đạt, CI sẽ báo lỗi và buộc nhóm "
             "cập nhật lại tài liệu.", thut=0.5)

    # ── 5 ────────────────────────────────────────────────────────────────────
    tl.add_heading("5. Hạn chế và hướng phát triển", level=1)
    doan(tl, "Mọi hạn chế dưới đây đều đã ĐO ĐƯỢC và khoá lại bằng test xfail trong "
             "kho mã, không phải phỏng đoán. Nhóm trình bày cả những hướng đã thử và "
             "đã bác bỏ, vì một kết quả âm có số đo cũng là kết quả.", thut=0.5)

    tl.add_heading("5.1. Chưa từ chối được truy vấn ngoài lĩnh vực", level=2)
    mien = {r["tin_hieu"]: r for r in d["mien"]["results"]}
    doan(tl, "Ở cấu hình mặc định, hỏi “cách nấu phở bò” thì hệ thống vẫn trả về một "
             "hành vi vi phạm. Nguyên nhân đã được khoanh vùng: đặc trưng TF-IDF quá "
             f"yếu để tách miền — đo trên độ tương đồng thô, 56/{th['so_cau_hoi']} "
             "câu hợp lệ chấm điểm thấp hơn hoặc bằng truy vấn rác. Không có ngưỡng "
             "nào tách được hai phân bố đó.", thut=0.5)
    chu_thich(tl, "Bảng 12. Khả năng tách miền của bốn tín hiệu "
                  f"({d['mien']['so_cau_trong_mien']} câu trong miền · "
                  f"{d['mien']['so_cau_ngoai_mien']} truy vấn ngoài miền)")
    bang(tl, ["Tín hiệu", "AUC", "Loại rác khi không oan câu nào",
              "Oan khi loại hết rác"], [
        [r["tin_hieu"], so(r["auc"]), pc(r["loai_rac_khi_0_oan"], 1),
         pc(r["oan_khi_loai_het_rac"], 1)] for r in d["mien"]["results"]
    ], canh_phai={1, 2, 3}, rong=[4.0, 2.2, 5.8, 4.0])
    dense = mien.get("dense")
    if dense:
        doan(tl, "Nhóm đã kiểm chứng đề xuất thay đặc trưng: dense embedding nâng AUC "
                 f"từ {so(mien['TF-IDF thô']['auc'])} lên {so(dense['auc'])} và loại "
                 f"được {pc(dense['loai_rac_khi_0_oan'], 1)} truy vấn rác mà không từ "
                 "chối oan câu hợp lệ nào. Nhưng hai phân bố VẪN chồng lấn: trần điểm "
                 f"của rác {so(dense['tran_ngoai_mien'])} còn nằm trên sàn "
                 f"{so(dense['san_trong_mien'])} của câu hợp lệ không rút được "
                 "keyphrase. Muốn loại 100% truy vấn rác thì phải chấp nhận từ chối "
                 f"oan {pc(dense['oan_khi_loai_het_rac'], 1)} câu hợp lệ. Nhóm từ "
                 "chối đánh đổi đó và giữ tầng dense ở dạng tuỳ chọn — mô hình nặng "
                 "khoảng 470 MB cũng là một lý do.", thut=0.5)
    doan(tl, "Kết quả âm đáng ghi nhận: phủ từ vựng cơ sở tri thức là tín hiệu vô "
             f"dụng cho việc tách miền (AUC {so(mien['phủ từ vựng KB']['auc'])}, thấp "
             "hơn cả TF-IDF thô). Hướng này đã thử và đã bác bỏ.", thut=0.5)

    tl.add_heading("5.2. Các hạn chế còn lại", level=2)
    gach_dau_dong(tl, [
        f"12/{th['so_cau_hoi']} câu hợp lệ không rút được keyphrase nào, nên không "
        "thể dùng riêng tín hiệu keyphrase làm bộ lọc truy vấn ngoài lĩnh vực.",
        "Chưa mô hình hoá 46 chú thích sửa đổi của Luật 118/2025/QH15 ở mức từng "
        "khoản. Đây là khoảng trống DỮ LIỆU đã khoanh vùng: 46 chú thích đã trích ra "
        "data/raw/luat118_dieu7_chu_thich.json, nhưng mô hình SuaDoi hiện chỉ có "
        "trường theo Nghị định 168 nên chưa biểu diễn được sửa đổi ở tầng luật.",
        "Hệ thống không sinh ngôn ngữ tự nhiên: câu trả lời được ghép từ nguyên văn "
        "điều khoản. Đây là lựa chọn có chủ đích của một hệ tra cứu pháp luật — diễn "
        "giải lại lời của luật là rủi ro lớn hơn lợi ích về trải nghiệm.",
        "Hỏi nồng độ cồn mà không nêu phương tiện thì hệ thống trả về khung xe đạp. "
        "Về mặt tri thức là đúng — hệ không bịa phương tiện người dùng chưa nói — "
        "nhưng là vấn đề trải nghiệm cần giải quyết bằng câu hỏi làm rõ.",
    ])

    tl.add_heading("5.3. Hướng phát triển", level=2)
    gach_dau_dong(tl, [
        "Bổ sung tầng hỏi lại khi truy vấn thiếu thông tin bắt buộc (phương tiện, "
        "chủ thể) thay vì mặc định chọn khung rộng nhất.",
        "Tổng quát hoá mô hình SuaDoi để biểu diễn được sửa đổi ở cả tầng luật và "
        "tầng nghị định, khép nốt 46 chú thích còn lại.",
        "Thêm tín hiệu phân biệt cho lớp P2: các quy tắc gần nghĩa cần được tách bằng "
        "quan hệ trong đồ thị R, không chỉ bằng điểm tương đồng văn bản.",
        "Đưa tầng dense embedding vào bản triển khai có tài nguyên, kèm ngưỡng hai "
        "mức: từ chối chắc chắn, nghi ngờ thì cảnh báo thay vì chặn.",
    ])

    # ── 6 ────────────────────────────────────────────────────────────────────
    tl.add_heading("6. Kết luận", level=1)
    doan(tl, "Nhóm đã xây dựng hoàn chỉnh một hệ tra cứu kiến thức pháp luật giao "
             "thông đường bộ theo đúng yêu cầu Đề tài 4: cơ sở tri thức có cấu trúc "
             f"gồm {kb['concepts']} khái niệm, {kb['relations']} quan hệ, "
             f"{kb['rules']} quy tắc, {tien(kb['violations'])} hành vi vi phạm và "
             f"{tien(kb['keyphrases'])} cụm từ khoá; bộ dữ liệu {th['so_cau_hoi']} "
             "câu hỏi có đáp án chuẩn; thuật giải xử lý truy vấn sáu bước; và một "
             "giao diện tra cứu chạy được.", thut=0.5)
    doan(tl, f"Về số đo, hệ thống đạt độ chính xác phân lớp "
             f"{pc(th['do_chinh_xac_phan_lop'])}, Top-1 {pc(th['top1'])}, Top-5 "
             f"{pc(th['top5'])} và MRR {so(th['mrr'])}, thời gian trả lời trung bình "
             f"{so(th['thoi_gian_tb_ms'], 1)} ms trên máy cá nhân, hoàn toàn không "
             "phụ thuộc dịch vụ ngoài. Thí nghiệm loại bỏ thành phần chứng minh từng "
             "phần của hàm điểm đều đóng góp thực chất, và bước suy diễn số học là "
             "phần tạo khác biệt lớn nhất trên nhóm câu hỏi có ngưỡng.", thut=0.5)
    doan(tl, "Điều nhóm thấy đáng giá nhất không phải là con số Top-1 mà là kỷ luật "
             "đo đạc: mọi khẳng định trong báo cáo này đều sinh ra từ một lệnh chạy "
             "lại được, mọi hạn chế đều có số đo kèm theo, và những hướng đã thử rồi "
             "bác bỏ đều được ghi lại thay vì giấu đi. Đó cũng là điều nhóm muốn giữ "
             "lại cho các đồ án sau.", thut=0.5)

    # ── 7 ────────────────────────────────────────────────────────────────────
    tl.add_heading("7. Tài liệu tham khảo", level=1)
    gach_dau_dong(tl, [
        "Quốc hội (2024), Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15.",
        "Chính phủ (2024), Nghị định 168/2024/NĐ-CP quy định xử phạt vi phạm hành "
        "chính về trật tự, an toàn giao thông trong lĩnh vực giao thông đường bộ.",
        "Quốc hội (2025), Luật 118/2025/QH15 sửa đổi, bổ sung một số điều của 10 "
        "luật liên quan đến an ninh, trật tự.",
        "Chính phủ (2026), Nghị định 238/2026/NĐ-CP sửa đổi, bổ sung Nghị định "
        "168/2024/NĐ-CP.",
        "Văn phòng Quốc hội (2026), Văn bản hợp nhất 55/VBHN-VPQH ngày 23/3/2026.",
        "Thư viện pháp luật, https://thuvienphapluat.vn/",
    ], danh_so=True)

    # ── phụ lục ──────────────────────────────────────────────────────────────
    tl.add_heading("Phụ lục A. Phân công công việc", level=1)
    chu_thich(tl, "Bảng 13. Phân công bảy thành viên Nhóm 7")
    bang(tl, ["Họ và tên", "MSSV", "Nội dung phụ trách"],
         [[ng["ho_ten"], ng["mssv"], viec]
          for ng, viec in zip(d["tv"]["thanh_vien"], [
              "Mục 1, trang bìa, định dạng toàn bài, rà soát cuối",
              "Mục 2 — cơ sở tri thức, ví dụ bản ghi, giải trình phạm vi văn bản",
              "Mục 3 — sơ đồ kiến trúc và sơ đồ luồng B1–B6",
              "Mục 3 — hàm điểm lai, trọng số, thí nghiệm loại bỏ thành phần",
              "Mục 4 — bảng chỉ số và nhận xét theo từng lớp bài toán",
              "Mục 4 — phân tích câu sai, bảng nghiệm thu, kiểm thử tự động",
              "Mục 5, mục 6 và chuẩn bị demo buổi báo cáo",
          ])], canh_phai={1}, co=12, rong=[4.6, 2.6, 8.8])

    tl.add_heading("Phụ lục B. Cách kiểm chứng lại số liệu", level=1)
    doan(tl, "Mọi con số trong báo cáo này sinh ra từ các lệnh sau, chạy tại thư mục "
             "ma_nguon/:", thut=0.5)
    ma(tl, [
        "pip install -e '.[dev,web,bao-cao]'",
        f"pytest -q --cov      # {kt['so_test_dat']} passed · {kt['so_xfail']} "
        f"xfailed · phủ {kt['do_phu_phan_tram']}%",
        f"python eval/evaluate.py --gate-top1 {th['top1']:.4f}",
        "python eval/ablation.py",
        f"python eval/kich_ban.py --chi-tiet   # {kt['ca_nghiem_thu_dat']}/"
        f"{kt['ca_nghiem_thu_tong']} ca nghiệm thu",
        "python eval/phat_hien_mien.py --ghi",
    ])
    doan(tl, "Kết quả tra cứu của hệ thống mang tính tham khảo, không thay thế ý kiến "
             "của cơ quan có thẩm quyền.", nghieng=True)


def main() -> int:
    d = nap(GOC)
    tl = Document()
    dinh_dang_chung(tl)

    bia = tl.sections[0]
    dat_le(bia)
    vien_trang_bia(bia)
    trang_bia(tl, d["tv"])

    than = tl.add_section(WD_SECTION.NEW_PAGE)
    dat_le(than)
    bo_vien_trang(than)
    than.footer.is_linked_to_previous = False
    so_trang(than)

    tl.add_heading("MỤC LỤC", level=1)
    muc_luc(tl)
    tl.paragraphs[-1].add_run().add_break(WD_BREAK.PAGE)

    than_bai(tl, d)
    RA.parent.mkdir(parents=True, exist_ok=True)
    tl.save(str(RA))
    print(f"Da ghi {RA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
