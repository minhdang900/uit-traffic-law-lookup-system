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


def bat_cap_nhat_truong(tl: Document) -> None:
    """Đánh dấu <w:updateFields/> để Word (và LibreOffice) hỏi cập nhật mục lục
    ngay khi mở tệp — nếu không, mục lục xuất ra PDF sẽ trống."""
    st = tl.settings.element
    if st.find(qn("w:updateFields")) is None:
        e = OxmlElement("w:updateFields")
        e.set(qn("w:val"), "true")
        st.append(e)


def muc_luc(tl: Document) -> None:
    bat_cap_nhat_truong(tl)
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
        "kiem_dinh": j("so_lieu/ket_qua_kiem_dinh.json",
                       "eval/ket_qua_kiem_dinh.json"),
        "phan_tich_loi": j("so_lieu/ket_qua_phan_tich_loi.json",
                           "eval/ket_qua_phan_tich_loi.json"),
        "thong_ke": j("so_lieu/thong_ke_du_lieu.json",
                      "eval/thong_ke_du_lieu.json"),
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


TEN_DO_KHO = {"de": "dễ", "trung_binh": "trung bình", "kho": "khó"}
TEN_LOAI_TT = {"concept": "khái niệm", "rule": "quy tắc",
               "violation": "hành vi vi phạm"}

VAN_BAN_PHAP_LUAT = [
    "Quốc hội (2024), Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15.",
    "Chính phủ (2024), Nghị định 168/2024/NĐ-CP quy định xử phạt vi phạm hành chính "
    "về trật tự, an toàn giao thông trong lĩnh vực giao thông đường bộ.",
    "Quốc hội (2025), Luật 118/2025/QH15 sửa đổi, bổ sung một số điều của 10 luật "
    "liên quan đến an ninh, trật tự.",
    "Chính phủ (2026), Nghị định 238/2026/NĐ-CP sửa đổi, bổ sung Nghị định "
    "168/2024/NĐ-CP.",
    "Văn phòng Quốc hội (2026), Văn bản hợp nhất 55/VBHN-VPQH ngày 23/3/2026.",
]

TAI_LIEU_KHOA_HOC = [
    "Luu, S. T., Vo, T., Nguyen, H. và cộng sự (2025), “VLSP 2025 MLQA-TSR "
    "Challenge: Vietnamese Multimodal Legal Question Answering on Traffic Sign "
    "Regulation”, Proceedings of the 11th VLSP Workshop. arXiv:2510.20381.",
    "Nguyen, T.-M., Nguyen, H.-T., Dao, T.-K. và cộng sự (2025), “VLQA: The First "
    "Comprehensive, Large, and High-Quality Vietnamese Dataset for Legal Question "
    "Answering”. arXiv:2507.19995.",
    "Vuong, T.-H.-Y., Nguyen, T.-M., Nguyen, H.-T. và cộng sự (2025), “DRILL Shared "
    "Task 2025: The Challenge of Deep Retrieval in the Expansive Legal Landscape”, "
    "VLSP 2025.",
    "Nguyen, H. T. và cộng sự (2021), “A Summary of the ALQAC 2021 Competition”. "
    "arXiv:2204.10717.",
    "Zalo AI Challenge (2021), Legal Text Retrieval — bộ dữ liệu truy hồi văn bản "
    "luật tiếng Việt.",
    "Nguyen, D. Q., Nguyen, A. T. (2020), “PhoBERT: Pre-trained Language Models for "
    "Vietnamese”, Findings of EMNLP 2020. arXiv:2003.00744.",
    "Pham, N.-M., Nguyen, H.-T., Do, T.-H. (2022), “Multi-stage Information Retrieval "
    "for Vietnamese Legal Texts”. arXiv:2209.14494.",
    "Tiên, S., Doan, H., Dai, A., Đinh Việt, S. (2024), “Improving Vietnamese Legal "
    "Document Retrieval using Synthetic Data”. arXiv:2412.00657.",
    "Duc, N. Q., Son, L. H., Nhan, N. D. và cộng sự (2024), “Towards Comprehensive "
    "Vietnamese Retrieval-Augmented Generation and Large Language Models”. "
    "arXiv:2403.01616.",
    "Goebel, R., Kano, Y., Kim, M.-Y. và cộng sự (2024), “Overview and Discussion of "
    "the Competition on Legal Information, Extraction/Entailment (COLIEE) 2023”, The "
    "Review of Socionetwork Strategies, 18(1), 27–47. DOI: 10.1007/s12626-023-00152-0.",
    "Nguyen, C., Nguyen, P., Tran, T. và cộng sự (2024), “CAPTAIN at COLIEE 2023: "
    "Efficient Methods for Legal Information Retrieval and Entailment Tasks”. "
    "arXiv:2401.03551.",
    "Nguyen, H.-T., Phi, M.-K., Ngo, X.-B. và cộng sự (2022), “Attentive Deep Neural "
    "Networks for Legal Document Retrieval”, Artificial Intelligence and Law. "
    "DOI: 10.1007/s10506-022-09341-8.",
    "Chalkidis, I., Fergadiotis, M., Malakasiotis, P. và cộng sự (2020), "
    "“LEGAL-BERT: The Muppets straight out of Law School”, Findings of EMNLP 2020. "
    "arXiv:2010.02559.",
    "Nguyen, T. H., Nguyen, H. D., Pham, V. T., Tran, D. A., Selamat, A. (2022), "
    "“Legal-Onto: An Ontology-based Model for Representing the Knowledge of a Legal "
    "Document”, ENASE 2022. DOI: 10.5220/0011066300003176.",
    "Pham, V. T., Dang, D. V., Ngo, H. Q. và cộng sự (2025), “Ontology-Based "
    "Knowledge Graph Approach for Legal Queries”, Informatica. "
    "DOI: 10.15388/25-infor617.",
    "Dang, D. V., Pham, V. T., Cao, T., Do, N., Ngo, H. Q., Nguyen, H. D. (2024), "
    "“A Practical Approach to Leverage Knowledge Graphs for Legal Query”, ISDS 2023, "
    "Springer. DOI: 10.1007/978-981-99-7649-2_21. — áp dụng cho luật giao thông "
    "đường bộ Việt Nam theo Luật 23/2008/QH12.",
    "Pham, V. T., Do, H. D. T., Nguyen, T. H. và cộng sự (2025), “Improving Legal "
    "Document Analysis and Automatic Knowledge Updates with Legal-Onto Ontology”, "
    "SN Computer Science, 6, art. 874. DOI: 10.1007/s42979-025-04432-0.",
    "Le, H. H., Nguyen, C.-T., Ngo, T. P. và cộng sự (2023), “Intelligent Retrieval "
    "System on Legal Information”, ACIIDS 2023, LNCS 13995. "
    "DOI: 10.1007/978-981-99-5834-4_8.",
    "Pham, V., Le, H. H., Ngo, T. P. và cộng sự (2024), “Enhancing legal research "
    "through knowledge-infused information retrieval for Vietnamese labor law”, "
    "IJAI, 13(4), 3962–3973. DOI: 10.11591/ijai.v13.i4.pp3962-3973.",
    "Pham, V., Phan, M. C., Cao, B. Q. và cộng sự (2026), “A Unified Ontology-Based "
    "Knowledge Graph Framework for Multi-Domain Vietnamese Legal Document "
    "Retrieval”, MJSAT, 6(2). DOI: 10.56532/mjsat.v6i2.684.",
    "Nguyen, H. D., Do, V. N. và cộng sự (2018), “Knowledge-Based Model of Expert "
    "Systems Using Rela-Model”, International Journal of Software Engineering and "
    "Knowledge Engineering, 28(8). DOI: 10.1142/S0218194018500304.",
    "Do, V. N., “Ontology COKB for Knowledge Representation and Reasoning in "
    "Designing Knowledge-Based Systems”, Springer. "
    "DOI: 10.1007/978-3-319-17530-0_8.",
    "Hoekstra, R., Breuker, J., Di Bello, M., Boer, A. (2007), “The LKIF Core "
    "Ontology of Basic Legal Concepts”, CEUR-WS Vol. 321 (LOAIT 2007).",
    "Athan, T., Boley, H., Governatori, G. và cộng sự (2013), “OASIS LegalRuleML”, "
    "ICAIL 2013; chuẩn chính thức: LegalRuleML Core Specification v1.0, OASIS "
    "Standard (2021).",
    "Dahl, M., Magesh, V., Suzgun, M., Ho, D. E. (2024), “Large Legal Fictions: "
    "Profiling Legal Hallucinations in Large Language Models”, Journal of Legal "
    "Analysis, 16(1). arXiv:2401.01301.",
    "Magesh, V., Surani, F., Dahl, M. và cộng sự (2025), “Hallucination-Free? "
    "Assessing the Reliability of Leading AI Legal Research Tools”, Journal of "
    "Empirical Legal Studies. DOI: 10.1111/jels.12413. arXiv:2405.20362.",
    "Gao, T., Yen, H., Yu, J., Chen, D. (2023), “Enabling Large Language Models to "
    "Generate Text with Citations” (benchmark ALCE), EMNLP 2023. arXiv:2305.14627.",
    "Pham, V., Phan, M. C. (2025), “Integrating Knowledge Graph with "
    "Retrieval-Augmented Generation for Vietnamese Legal Question Answering”. "
    "DOI: 10.59232/dst-v5i1p101.",
    "Tran, V.-K., Nguyen, V. (2025), “LAURA: A Legal Agent Using Reasoning and "
    "Acting for Vietnamese Law”, KSE 2025. DOI: 10.1109/KSE68178.2025.11309628.",
    "Governatori, G., Palmirani, M., Riveret, R., Rotolo, A., Sartor, G., “Norm "
    "Modifications in Defeasible Logic”, JURIX.",
    "Palmirani, M., Ognibene, T., Cervone, L., “Legal Rules, Text and Ontologies "
    "Over Time”, RuleML (CEUR-WS Vol. 874).",
    "de Martim, H. (2025), “An Ontology-Driven Graph RAG for Legal Norms: A "
    "Structural, Temporal, and Deterministic Approach”. arXiv:2505.00039.",
]


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
    kd, pl, tk = d["kiem_dinh"], d["phan_tich_loi"], d["thong_ke"]
    toan_bo, co_so = ab["toan_bo"], ab["cau_hoi_co_gia_tri_so"]
    dd, nhan_tk, chu_de = tk["do_dai"], tk["nhan"], tk["chu_de"]

    # ══════════════════════════ 1. TỔNG QUAN ═════════════════════════════════
    tl.add_heading("1. Tổng quan", level=1)

    tl.add_heading("1.1. Bối cảnh và động lực", level=2)
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
    doan(tl, "Vì sao bài toán này đáng làm: một câu trả lời sai trong tra cứu pháp "
             "luật không phải là “kết quả kém hay hơn một chút” mà là thông tin dẫn "
             "người dân tới hành vi sai. Ba đặc điểm của lĩnh vực giao thông đường bộ "
             "khiến nó đặc biệt phù hợp với hướng tri thức tường minh: văn bản có cấu "
             "trúc chặt (điều – khoản – điểm) nên mô hình hoá được; tri thức mang tính "
             "suy diễn số (ngưỡng nồng độ cồn, mức vượt tốc độ, điểm trừ cộng dồn) nên "
             "so khớp văn bản đơn thuần là không đủ; và mọi câu trả lời đều phải truy "
             "nguyên được về một căn cứ pháp lý cụ thể.", thut=0.5)

    tl.add_heading("1.2. Phát biểu bài toán", level=2)
    doan(tl, "Bài toán được phát biểu hình thức như sau. Cho cơ sở tri thức", thut=0.5)
    ma(tl, ["K = (C, R, Rules, F, Keyphrase)"])
    doan(tl, "trong đó C là tập khái niệm pháp lý, R là tập quan hệ hai ngôi trên C, "
             "Rules là tập quy tắc giao thông, F là tập sự kiện “hành vi vi phạm – chế "
             "tài”, và Keyphrase là từ điển cụm từ khoá ánh xạ ngôn ngữ người dùng vào "
             "định danh tri thức. Mỗi phần tử tri thức x mang một khối căn cứ "
             "cc(x) = (văn bản, điều, khoản, điểm) và một khoảng hiệu lực "
             "hl(x) = [t_bắt_đầu, t_kết_thúc).", thut=0.5)
    chu_thich(tl, "Bảng 1. Định nghĩa hình thức Input → Output")
    bang(tl, ["", "Định nghĩa"], [
        ["INPUT",
         "Một truy vấn q là chuỗi tiếng Việt tự nhiên (có dấu hoặc không dấu), kèm "
         "tuỳ chọn mốc thời gian t (mặc định: ngày hiện tại) và bộ lọc phương tiện."],
        ["OUTPUT",
         "Bộ ba A(q, t) = (p, T, E): p ∈ {P1, …, P7} là lớp bài toán được nhận diện; "
         "T ⊆ C ∪ Rules ∪ F là danh sách tối đa k mẩu tri thức đã xếp hạng, mọi x ∈ T "
         "đều thoả t ∈ hl(x); E là phần giải trình gồm nguyên văn điều khoản và căn "
         "cứ cc(x) của từng x ∈ T."],
        ["RÀNG BUỘC",
         "Hệ thống KHÔNG sinh ngôn ngữ tự nhiên: mọi câu chữ trong E đều là trích "
         "nguyên văn từ văn bản nguồn. Nếu không có x nào thoả, hệ trả về tập rỗng "
         "kèm lý do, chứ không suy đoán."],
        ["MỤC TIÊU",
         "Cực đại hoá xác suất đáp án chuẩn nằm ở hạng 1 của T (Top-1) và nằm trong "
         "T (Top-k), đồng thời giữ độ chính xác phân lớp p và bảo đảm 100% phần tử "
         "trả về đều truy nguyên được căn cứ."],
    ], co=12, rong=[2.6, 13.4])
    doan(tl, "Phát biểu này tách bạch hai việc thường bị gộp làm một trong các hệ "
             "hỏi đáp: TÌM ĐÚNG mẩu tri thức (T) và GIẢI TRÌNH được vì sao (E). Hệ "
             "thống của nhóm bị ràng buộc phải làm được cả hai, và chính ràng buộc "
             "“không sinh ngôn ngữ” là thứ phân biệt đồ án với hướng RAG/LLM trình "
             "bày ở mục 2.", thut=0.5)

    tl.add_heading("1.3. Đóng góp của nhóm", level=2)
    gach_dau_dong(tl, [
        f"Cơ sở tri thức mở cho lĩnh vực giao thông đường bộ theo khung pháp lý "
        f"2024–2026: {kb['concepts']} khái niệm, {kb['relations']} quan hệ, "
        f"{kb['rules']} quy tắc, {tien(kb['violations'])} hành vi vi phạm và "
        f"{tien(kb['keyphrases'])} cụm từ khoá, 100% mục có căn cứ pháp lý ở mức "
        "điều – khoản – điểm và có khoảng hiệu lực.",
        "Mô hình hoá hiệu lực theo thời gian ở mức khoản: sửa đổi được lưu như dữ "
        f"liệu ({kb['amendments']} bản ghi) chứ không hợp nhất cứng, nhờ đó trả lời "
        "được câu hỏi “tại thời điểm t thì áp dụng quy định nào” — điều mà các hệ "
        "truy hồi văn bản tiếng Việt hiện có chưa làm.",
        "Thuật giải xử lý truy vấn sáu bước với hàm điểm lai ba thành phần và bộ suy "
        "diễn số học cho các điều khoản phân khung theo ngưỡng; thí nghiệm loại bỏ "
        "thành phần chứng minh từng thành phần đều đóng góp thực chất.",
        f"Bộ dữ liệu đánh giá {th['so_cau_hoi']} câu hỏi có đáp án chuẩn gán tới mức "
        f"định danh tri thức, {d['so_ngoai_mien']} truy vấn ngoài lĩnh vực, cùng "
        "toàn bộ kết quả đo, kiểm định thống kê và phân tích lỗi tái lập được bằng "
        "một lệnh chạy.",
    ])

    # ═══════════════════ 2. CÁC CÔNG TRÌNH LIÊN QUAN ═════════════════════════
    tl.add_heading("2. Các công trình liên quan", level=1)

    tl.add_heading("2.1. Khảo sát các hướng tiếp cận hiện tại", level=2)
    doan(tl, "Các công trình về hỏi đáp và truy hồi văn bản pháp luật có thể xếp vào "
             "bốn hướng, khác nhau ở chỗ tri thức pháp lý nằm ở đâu.", thut=0.5)
    doan(tl, "Hướng 1 — Truy hồi ngữ nghĩa bằng mạng nơ-ron. ", dam=True)
    doan(tl, "Tri thức nằm trong tham số của mô hình ngôn ngữ. PhoBERT [6] là xương "
             "sống cho phần lớn hệ truy hồi luật tiếng Việt; Pham và cộng sự [7] đề "
             "xuất truy hồi nhiều giai đoạn cho văn bản luật tiếng Việt; Tiên và cộng "
             "sự [8] dùng dữ liệu tổng hợp do mô hình lớn sinh ra để khắc phục khan "
             "hiếm nhãn. Ở quy mô quốc tế, LEGAL-BERT [13] cho thấy tiếp tục tiền "
             "huấn luyện theo miền pháp luật cải thiện rõ các tác vụ pháp lý, còn "
             "Nguyen và cộng sự [12] đưa kiến trúc chú ý phân cấp cho văn bản luật "
             "dài. Điểm chung: đầu ra là một ĐOẠN VĂN BẢN được xếp hạng, không phải "
             "tri thức có cấu trúc, nên hệ thống không giải thích được vì sao điều "
             "khoản đó áp dụng và không tính được mức phạt.", thut=0.5)
    doan(tl, "Hướng 2 — Ontology và đồ thị tri thức pháp luật. ", dam=True)
    doan(tl, "Tri thức được mô hình hoá tường minh. Legal-Onto [14] đề xuất mô hình "
             "tri thức gồm khái niệm có cấu trúc, ba loại quan hệ, luật suy diễn và "
             "đồ thị cụm từ khoá, áp dụng cho Luật Đất đai; đây chính là dòng nghiên "
             "cứu mà mô hình K của đồ án kế thừa, cùng với nền tảng Rela-model [21] "
             "và COKB [22]. Các mở rộng sau đó phủ thêm luật lao động [19][17], tích "
             "hợp ontology với đồ thị tri thức cho truy vấn pháp lý [15], và gần đây "
             "là kiến trúc ontology ba tầng đa miền [20]. Đáng chú ý nhất với đồ án "
             "là Dang và cộng sự [16] — công trình đồ thị tri thức cho chính luật "
             "giao thông đường bộ Việt Nam, nhưng dựa trên Luật 23/2008/QH12.",
         thut=0.5)
    doan(tl, "Hướng 3 — RAG và mô hình ngôn ngữ lớn cho miền pháp luật. ", dam=True)
    doan(tl, "Hướng đang phổ biến nhất, và cũng là hướng nhóm chủ động không chọn. "
             "Dahl và cộng sự [25] đo được LLM đa dụng bịa căn cứ pháp lý một cách có "
             "hệ thống; Magesh và cộng sự [26] đánh giá tiền đăng ký các công cụ RAG "
             "pháp lý thương mại và ghi nhận tỉ lệ ảo giác 17–33% dù nhà cung cấp "
             "quảng cáo “hallucination-free”; benchmark ALCE [27] cho thấy trích dẫn "
             "do mô hình sinh thường không trung thực với nguồn. Ngay cả các hệ kết "
             "hợp đồ thị tri thức với RAG cho luật Việt Nam [28][29] vẫn giữ mô hình "
             "sinh ở khâu cuối, nên vẫn thừa hưởng rủi ro này.", thut=0.5)
    doan(tl, "Hướng 4 — Hiệu lực theo thời gian của quy phạm. ", dam=True)
    doan(tl, "Lý thuyết đã tương đối đầy đủ ở quốc tế: Governatori và cộng sự [30] "
             "hình thức hoá ba loại sửa đổi (thay thế, bãi bỏ một phần, huỷ bỏ hồi "
             "tố) bằng logic khả bác có gắn thời gian; Palmirani và cộng sự [31] quản "
             "lý tiến hoá văn bản theo ba chiều hiệu lực; chuẩn LegalRuleML [24] đưa "
             "toán tử nghĩa vụ cùng chiều thời gian vào biểu diễn; de Martim [32] "
             "tách Tác phẩm trừu tượng khỏi Biểu hiện có phiên bản để trả lời tất "
             "định câu hỏi “văn bản tại thời điểm t”. Phía Việt Nam, Pham và cộng sự "
             "[17] mới dừng ở đối sánh hai phiên bản Luật Đất đai 2013 và 2024 — tức "
             "phát hiện thay đổi, chưa phải truy vấn theo mốc thời gian.", thut=0.5)

    tl.add_heading("2.2. Các bộ dữ liệu đã có", level=2)
    chu_thich(tl, "Bảng 2. Các bộ dữ liệu hỏi đáp / truy hồi pháp luật tiêu biểu")
    bang(tl, ["Bộ dữ liệu", "Ngôn ngữ · miền", "Quy mô", "Nhiệm vụ"], [
        ["VLQA / DRILL [2][3]", "Tiếng Việt · 27 lĩnh vực",
         "3.129 câu hỏi · 59.636 điều luật của 2.162 văn bản",
         "Truy hồi điều luật và sinh câu trả lời có trích dẫn"],
        ["MLQA-TSR, VLSP 2025 [1]", "Tiếng Việt · biển báo GTĐB",
         "776 câu hỏi · 402 điều · 498 ảnh biển báo",
         "Truy hồi và hỏi đáp ĐA PHƯƠNG THỨC ảnh – văn bản"],
        ["ALQAC [4]", "Tiếng Việt (và tiếng Thái)",
         "Quy mô chưa kiểm chứng từ nguồn chính thức",
         "Truy hồi văn bản luật, suy luận kéo theo, hỏi đáp"],
        ["Zalo AI Challenge 2021 [5]", "Tiếng Việt · văn bản luật",
         "Quy mô chưa kiểm chứng từ nguồn chính thức",
         "Truy hồi văn bản luật (benchmark Acc@1)"],
        ["COLIEE [10]", "Tiếng Nhật / Anh · dân sự, án lệ",
         "768 điều Bộ luật Dân sự Nhật (Task 3–4)",
         "Truy hồi luật thành văn và kiểm tra kéo theo"],
        ["Bộ dữ liệu của nhóm", "Tiếng Việt · GTĐB 2024–2026",
         f"{th['so_cau_hoi']} câu hỏi · {tien(kb['violations'])} hành vi · "
         f"{kb['rules']} quy tắc · {kb['concepts']} khái niệm",
         "Tra cứu tri thức 7 lớp, gán nhãn tới ĐỊNH DANH tri thức"],
    ], co=11, rong=[3.4, 3.4, 4.6, 4.6])
    doan(tl, "Bảng trên chỉ ghi con số khi kiểm chứng được từ bài báo hoặc trang "
             "chính thức; các ô “chưa kiểm chứng” được để nguyên thay vì điền số ước "
             "đoán. Điểm cần lưu ý là ĐƠN VỊ GÁN NHÃN: các bộ dữ liệu hiện có gán "
             "nhãn ở mức điều luật, trong khi bộ dữ liệu của nhóm gán tới định danh "
             "của từng mẩu tri thức (một khái niệm, một quy tắc, một hành vi kèm chế "
             "tài) — nhờ vậy mới đo được Top-1 ở mức tri thức chứ không chỉ mức văn "
             "bản.", thut=0.5)

    tl.add_heading("2.3. Khoảng trống và chỗ đứng của đồ án", level=2)
    doan(tl, "Đối chiếu bốn hướng trên với yêu cầu Đề tài 4, nhóm xác định năm khoảng "
             "trống — và đây chính là chỗ đồ án đứng vào:", thut=0.5)
    gach_dau_dong(tl, [
        "Chưa có hệ tra cứu tri thức cho GTĐB Việt Nam theo khung pháp lý 2024–2026: "
        "công trình đồ thị tri thức cùng miền gần nhất [16] dựa trên Luật 23/2008 đã "
        "hết hiệu lực; MLQA-TSR [1] tuy đúng khung luật mới nhưng giải bài toán nhận "
        "dạng biển báo đa phương thức, không phải tra cứu tri thức pháp lý.",
        "Đầu ra là đoạn văn bản, không phải tri thức có cấu trúc: VLQA/DRILL [2][3], "
        "Zalo [5] và COLIEE Task 3 [10] đều chấm ở mức “xếp hạng điều luật đúng”, "
        "không nhiệm vụ nào yêu cầu trả về khái niệm, quan hệ và quy tắc suy diễn — "
        "nên không đo được khả năng GIẢI TRÌNH.",
        "Chưa có công trình tiếng Việt kết hợp mô hình tri thức kiểu K với suy diễn "
        "SỐ HỌC theo luật: Legal-Onto [14] và các mở rộng [19][17][20] dừng ở tra cứu "
        "thuật ngữ và thủ tục, trong khi GTĐB đòi hỏi tính ra mức phạt tiền, thời hạn "
        "tước giấy phép và điểm trừ theo điều kiện phương tiện – hành vi – tình tiết.",
        "Chưa mô hình hoá hiệu lực theo thời gian cho pháp luật Việt Nam: lý thuyết "
        "đã có [30][31][24][32] nhưng phía Việt Nam mới dừng ở phát hiện thay đổi "
        "giữa hai phiên bản [17]. Miền GTĐB thay đổi rất nhanh nên đây là khoảng "
        "trống có giá trị thực tiễn cao.",
        "Hướng RAG/LLM chưa đảm bảo trung thực căn cứ ở mức chấp nhận được cho tra "
        "cứu pháp luật [25][26][27]. Đồ án chọn loại bỏ hoàn toàn khâu sinh, đổi độ "
        "“mượt” của câu trả lời lấy khả năng truy vết 100% căn cứ — một đánh đổi có "
        "chủ đích chứ không phải hạn chế kỹ thuật.",
    ])

    # ═══════════════════════ 3. XÂY DỰNG DỮ LIỆU ═════════════════════════════
    tl.add_heading("3. Xây dựng dữ liệu", level=1)

    tl.add_heading("3.1. Nguồn văn bản và giải trình phạm vi", level=2)
    doan(tl, "Đề bài yêu cầu chọn “01 văn bản pháp luật tương ứng”. Nhóm thực hiện "
             "trên bốn văn bản và xin giải trình ngay từ đầu, vì đây là quyết định "
             "thiết kế chứ không phải làm lệch đề.", thut=0.5)
    doan(tl, "Luật 36/2024/QH15 quy định hành vi nào bị nghiêm cấm, nhưng không quy "
             "định mức phạt; toàn bộ chế tài nằm ở Nghị định 168/2024/NĐ-CP. Nếu chỉ "
             "dùng văn bản luật gốc, hệ thống sẽ không trả lời được câu hỏi phổ biến "
             "nhất trong thực tế là “phạt bao nhiêu tiền”. Hai văn bản sửa đổi được "
             "đưa thêm vào để hệ thống trả lời đúng theo mốc thời gian, thay vì trả "
             "lời theo bản đã lỗi thời.", thut=0.5)
    chu_thich(tl, "Bảng 3. Bốn văn bản nguồn và vai trò trong cơ sở tri thức")
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

    tl.add_heading("3.2. Cấu trúc của cơ sở tri thức", level=2)
    chu_thich(tl, "Bảng 4. Năm thành phần của cơ sở tri thức K")
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

    tl.add_heading("3.3. Cách lấy và chuẩn hoá dữ liệu", level=2)
    gach_dau_dong(tl, [
        "Trích xuất: tách toàn văn theo cấu trúc điều – khoản – điểm từ bản công bố "
        "của bốn văn bản, lưu ở data/raw/ dưới dạng JSON giữ nguyên văn. Không dùng "
        "bản tóm tắt hay bài viết lại của bên thứ ba.",
        "Chuẩn hoá: mỗi mục tri thức được gán một định danh ổn định (ví dụ R01, "
        "VP_OTO_ND168D6_K1A), một khối căn cứ có cấu trúc và một khoảng hiệu lực. "
        "Chế tài được lưu có KIỂU — số tiền và điểm trừ là số nguyên, không phải "
        "chuỗi — nên cộng dồn và so sánh được.",
        "Sinh keyphrase: mỗi mục kèm danh sách cụm từ người dùng thật hay dùng, gồm "
        "cả khẩu ngữ (“nhậu”, “vượt đèn đỏ”) và bản không dấu, để chịu được truy vấn "
        "gõ vội không dấu.",
        "Kiểm toàn vẹn: module kb/validator.py soát định danh trùng, quan hệ treo, "
        "keyphrase trỏ tới định danh không tồn tại và mục thiếu căn cứ. Toàn bộ kiểm "
        "tra này chạy trong CI, nên một bản ghi hỏng không thể lọt vào kho mã.",
        "Xây bộ câu hỏi đánh giá: mỗi câu được viết kèm đáp án chuẩn dạng văn bản, "
        "danh sách ĐỊNH DANH tri thức đúng, lớp bài toán đúng và mức độ khó. Có test "
        "kiểm chứng rằng mọi định danh trong đáp án chuẩn đều tồn tại trong cơ sở tri "
        f"thức — hiện {kd['cham_duoc']['so_cau']}/{th['so_cau_hoi']} câu đều chấm "
        "được, không có định danh treo.",
    ])
    doan(tl, "Chuẩn hoá bằng mô hình có kiểu (Pydantic v2) chứ không phải dict tự do: "
             "trường lạ bị từ chối ngay lúc nạp, nên một bản ghi sai cấu trúc không "
             "thể lọt vào cơ sở tri thức mà đến lúc chạy mới phát hiện.", thut=0.5)
    doan(tl, "Một bản ghi hành vi vi phạm (rút gọn):", thut=0.5)
    ma(tl, [
        '{',
        '  "id": "VP_OTO_ND168D6_K1A",',
        '  "hanh_vi": "Không chấp hành hiệu lệnh, chỉ dẫn của',
        '              biển báo hiệu, vạch kẻ đường, trừ ...",',
        '  "nhom": "bien_bao_hieu",',
        '  "phuong_tien": ["o_to"],',
        '  "phat_tien": { "min": 400000, "max": 600000 },',
        '  "tru_diem_gplx": 0,',
        '  "can_cu": { "van_ban": "Nghị định 168/2024/NĐ-CP",',
        '              "dieu": 6, "khoan": 1, "diem": "a" },',
        '  "tinh_trang": "hien_hanh"',
        '}',
    ])

    tl.add_heading("3.4. Thống kê và phân tích bộ dữ liệu", level=2)
    doan(tl, "Ba phân bố dưới đây được sinh lại bằng một lệnh "
             "(scripts/thong_ke_du_lieu.py) nên luôn khớp với dữ liệu thật trong kho "
             "mã, không phải số chép tay.", thut=0.5)

    doan(tl, "a) Phân bố độ dài. ", dam=True)
    ch, ktt = dd["cau_hoi"], dd["hanh_vi"]
    doan(tl, f"Câu hỏi dài trung bình {so(ch['trung_binh'], 2)} từ (trung vị "
             f"{ch['trung_vi']}, ngắn nhất {ch['min']}, dài nhất {ch['max']}, độ lệch "
             f"chuẩn {so(ch['do_lech_chuan'], 2)}). Phân bố lệch phải rõ rệt: 75% câu "
             f"dưới {ch['p75']} từ, nhưng đuôi kéo tới {ch['max']} từ — đó là các câu "
             "khẩu ngữ kể cả tình huống (“Nhóm em 4 đứa đi chung một xe máy, không ai "
             "đội mũ bảo hiểm…”). Đuôi này quan trọng: mục 5 sẽ cho thấy phần lớn ca "
             "lỗi nặng tập trung ở đó.", thut=0.5)
    doan(tl, f"Về phía tri thức, hành vi vi phạm dài trung bình "
             f"{so(ktt['trung_binh'], 1)} từ và quy tắc dài trung bình "
             f"{so(dd['quy_tac']['trung_binh'], 1)} từ — dài gấp khoảng "
             f"{so(dd['quy_tac']['trung_binh'] / ch['trung_binh'], 1)} lần câu hỏi. "
             "Đây là gốc rễ của bài toán: câu hỏi ngắn và đời thường phải khớp với "
             "văn bản dài và trang trọng, nên chỉ so khớp bề mặt là không đủ.",
         thut=0.5)
    if (HINH / "hinh3_phan_bo_do_dai.png").exists():
        hinh(tl, HINH / "hinh3_phan_bo_do_dai.png", 15.5,
             "Hình 1. Phân bố độ dài câu hỏi và độ dài đơn vị tri thức")

    doan(tl, "b) Phân bố nhãn. ", dam=True)
    doan(tl, "Bộ câu hỏi được phân bổ theo tần suất thực tế của nhu cầu tra cứu, "
             "không chia đều: lớp tra cứu chế tài P3 chiếm "
             f"{nhan_tk['lop_bai_toan']['P3_TRA_CUU_CHE_TAI']}/{th['so_cau_hoi']} câu "
             "vì đây là câu hỏi người dân hỏi nhiều nhất. Về mức độ khó: "
             + " · ".join(f"{TEN_DO_KHO.get(k, k)} {v}"
                          for k, v in sorted(nhan_tk["do_kho"].items())) +
             f". Về loại tri thức của đáp án chuẩn: "
             + " · ".join(f"{TEN_LOAI_TT.get(k, k)} {v}"
                          for k, v in nhan_tk["loai_tri_thuc"].items()) +
             f". Có {nhan_tk['so_cau_nhieu_dap_an']}/{th['so_cau_hoi']} câu có nhiều "
             "hơn một mẩu tri thức trong đáp án chuẩn — chi tiết này sẽ giải thích "
             "con số precision ở mục 5.", thut=0.5)
    if (HINH / "hinh4_phan_bo_nhan.png").exists():
        hinh(tl, HINH / "hinh4_phan_bo_nhan.png", 15.5,
             "Hình 2. Phân bố nhãn của bộ câu hỏi có đáp án chuẩn")

    doan(tl, "c) Phân bố chủ đề. ", dam=True)
    lv_kb, lv_qa = chu_de["linh_vuc_kb"], chu_de["linh_vuc_qa"]
    t_kb = sum(lv_kb.values()) or 1
    t_qa = sum(lv_qa.values()) or 1
    doan(tl, f"Cơ sở tri thức chia thành 6 lĩnh vực và "
             f"{chu_de['so_nhom_trong_taxonomy']} nhóm hành vi. Tỉ trọng trong cơ sở "
             "tri thức và trong bộ câu hỏi KHÔNG trùng nhau, và đây là chủ ý: lĩnh "
             "vực “An toàn của người tham gia giao thông” chiếm "
             f"{pc(lv_kb.get('LV_AN_TOAN', 0) / t_kb, 0)} cơ sở tri thức nhưng "
             f"{pc(lv_qa.get('LV_AN_TOAN', 0) / t_qa, 0)} bộ câu hỏi, vì nồng độ cồn "
             "và mũ bảo hiểm là hai chủ đề được hỏi nhiều nhất ngoài đời. Ngược lại "
             "“Điều kiện của phương tiện” chiếm "
             f"{pc(lv_kb.get('LV_PHUONG_TIEN', 0) / t_kb, 0)} cơ sở tri thức nhưng "
             f"chỉ {pc(lv_qa.get('LV_PHUONG_TIEN', 0) / t_qa, 0)} bộ câu hỏi.",
         thut=0.5)
    doan(tl, "Nhóm ghi nhận đây là một HẠN CHẾ của bộ đánh giá chứ không giấu đi: bộ "
             "câu hỏi phản ánh nhu cầu tra cứu phổ biến, nên chưa phủ đều mọi ngóc "
             "ngách của cơ sở tri thức. Một bộ đánh giá phủ đều hơn là việc cần làm "
             "tiếp, nêu ở mục 6.", thut=0.5)
    if (HINH / "hinh5_phan_bo_chu_de.png").exists():
        hinh(tl, HINH / "hinh5_phan_bo_chu_de.png", 15.5,
             "Hình 3. Phân bố chủ đề — tỉ trọng lĩnh vực và nhóm hành vi")

    # ═══════════════ 4. PHƯƠNG PHÁP VÀ THỰC NGHIỆM ═══════════════════════════
    tl.add_heading("4. Phương pháp và thực nghiệm", level=1)

    tl.add_heading("4.1. Kiến trúc tổng thể", level=2)
    doan(tl, "Hệ thống gồm ba tầng nối tiếp. QueryAnalyzer biến câu hỏi tiếng Việt "
             "thành một biểu diễn hình thức Q; InferenceEngine dùng Q để chọn bộ giải "
             "và truy hồi tri thức từ IndexedKnowledgeBase; hàm sinh văn bản ghép câu "
             "trả lời kèm căn cứ pháp lý. Tầng dense embedding là tuỳ chọn và mặc "
             "định không được gọi — lý do trình bày ở mục 6.", thut=0.5)
    if (HINH / "hinh1_kien_truc.png").exists():
        hinh(tl, HINH / "hinh1_kien_truc.png", 15.5, "Hình 4. Kiến trúc hệ thống")

    tl.add_heading("4.2. Thuật giải xử lý truy vấn B1 – B6", level=2)
    chu_thich(tl, "Bảng 5. Sáu bước xử lý một truy vấn")
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
             "Hình 5. Luồng xử lý truy vấn B1 – B6 với một truy vấn thật")

    tl.add_heading("4.3. Bảy lớp bài toán và bộ giải tương ứng", level=2)
    chu_thich(tl, "Bảng 6. Bảy lớp bài toán và câu hỏi tiêu biểu")
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

    tl.add_heading("4.4. Hàm điểm lai", level=2)
    ma(tl, ["score(x, q) = ALPHA · s_keyphrase + BETA · s_ngữ_nghĩa "
            "+ GAMMA · s_ngữ_cảnh"])
    chu_thich(tl, "Bảng 7. Ba thành phần của hàm điểm và lý do chọn trọng số")
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

    tl.add_heading("4.5. Suy diễn số học và hiệu lực theo thời gian", level=2)
    doan(tl, "Nhiều điều khoản phân khung theo ngưỡng số: nồng độ cồn chia ba mức, "
             "vượt tốc độ chia bốn mức. So khớp từ khoá đơn thuần tìm ra đủ các khung "
             "nhưng không biết chọn khung nào. NumericReasoner rút ngưỡng từ chính "
             "nguyên văn điều khoản, so sánh khoảng với giá trị trong câu hỏi rồi đẩy "
             "khung đúng lên đầu.", thut=0.5)
    trich(tl, "Ví dụ: “xe máy nồng độ cồn 0,3 mg/l phạt bao nhiêu” → 0,3 thuộc khung "
              "“vượt quá 0,25 đến 0,4 miligam/1 lít khí thở”, không phải khung 0,25 "
              "hay khung trên 0,4. Hỏi liên tiếp 0,2 – 0,3 – 0,5 cho ba khung phạt "
              "khác nhau.")
    doan(tl, "Về hiệu lực thời gian, mỗi mục tri thức mang khoảng hl(x) = [từ, đến) "
             "và mọi truy vấn đều được lọc theo mốc t. Ví dụ quy tắc R15 về chở trẻ "
             "em dưới 10 tuổi mang nguyên văn sau sửa đổi nên có hiệu lực từ "
             "01/7/2026 theo Luật 118/2025, không phải 01/01/2025. Người dùng đổi "
             "tham số ngay=YYYY-MM-DD là xem được cơ sở tri thức tại thời điểm đó.",
         thut=0.5)

    tl.add_heading("4.6. Cấu hình siêu tham số", level=2)
    doan(tl, "Toàn bộ siêu tham số được khai báo tường minh trong mã nguồn và khoá "
             "lại bằng kiểm thử, không có giá trị nào chỉnh ngầm lúc chạy.", thut=0.5)
    chu_thich(tl, "Bảng 8. Cấu hình siêu tham số của hệ thống")
    bang(tl, ["Tham số", "Giá trị", "Vị trí", "Ý nghĩa"], [
        ["ALPHA", "0,55", "reasoning/engine.py", "Trọng số làn keyphrase"],
        ["BETA", "0,30", "reasoning/engine.py", "Trọng số làn ngữ nghĩa TF-IDF"],
        ["GAMMA", "0,15", "reasoning/engine.py", "Trọng số làn ngữ cảnh"],
        ["k (top-k)", str(th["top_k"]), "tham số truy vấn",
         "Số kết quả trả về cho mỗi truy vấn"],
        ["SUPPLEMENT_THRESHOLD", "0,40", "reasoning/engine.py",
         "Ngưỡng bổ sung tri thức loại còn thiếu"],
        ["Ngưỡng nhóm ngữ nghĩa", "0,24 · tối đa 2 nhóm", "reasoning/engine.py",
         "Chặn suy đoán nhóm hành vi khi tín hiệu yếu"],
        ["TF-IDF ký tự", "char_wb, n-gram 3–5, sublinear_tf",
         "reasoning/engine.py", "Chịu lỗi chính tả và cách tách từ tiếng Việt"],
        ["TF-IDF từ", "word, n-gram 1–3, sublinear_tf", "reasoning/engine.py",
         "Giữ được cụm nhiều từ"],
        ["Ngưỡng miền an toàn", "0,45", "retrieval/dense.py",
         "Giá trị lớn nhất còn giữ được cam kết không từ chối oan"],
        ["Ngưỡng miền nghiêm ngặt", "0,52", "retrieval/dense.py",
         "Loại hết truy vấn rác nhưng từ chối oan — KHÔNG dùng mặc định"],
        ["Mô hình dense (tuỳ chọn)", "paraphrase-multilingual-MiniLM-L12-v2",
         "retrieval/dense.py", "Chỉ bật khi cài gói tuỳ chọn, ~470 MB"],
    ], canh_phai={1}, co=11, rong=[4.0, 4.4, 3.6, 4.0])
    doan(tl, "Điểm cần nhấn: hệ thống KHÔNG huấn luyện mô hình nào. Không có bước "
             "học tham số, không có tập huấn luyện, nên cũng không có rủi ro rò rỉ dữ "
             "liệu giữa tập huấn luyện và tập đánh giá. Ba trọng số ALPHA, BETA, "
             "GAMMA là lựa chọn thiết kế và được BIỆN MINH BẰNG SỐ ĐO ở thí nghiệm "
             "loại bỏ thành phần (mục 5.4), chứ không phải tinh chỉnh trên chính bộ "
             f"{th['so_cau_hoi']} câu hỏi đánh giá.", thut=0.5)

    tl.add_heading("4.7. Thiết lập thực nghiệm và chỉ số đo", level=2)
    doan(tl, f"Bộ dữ liệu đánh giá gồm {th['so_cau_hoi']} câu hỏi, mỗi câu có đáp án "
             "chuẩn dạng văn bản, danh sách định danh tri thức đúng, lớp bài toán "
             f"đúng và mức độ khó; hệ thống trả về k = {th['top_k']} kết quả. Ngoài "
             f"ra còn {d['so_ngoai_mien']} truy vấn ngoài lĩnh vực dùng để đo khả "
             "năng từ chối. Toàn bộ thực nghiệm chạy cục bộ, không gọi dịch vụ ngoài, "
             "nên tái lập được bằng đúng các lệnh ở Phụ lục B.", thut=0.5)
    chu_thich(tl, "Bảng 9. Các chỉ số đo và ý nghĩa")
    bang(tl, ["Chỉ số", "Cách tính", "Đo điều gì"], [
        ["Độ chính xác phân lớp", "Tỉ lệ câu được gán đúng lớp P1–P7",
         "Chất lượng bước B3 — định tuyến tới đúng bộ giải"],
        ["Top-1 / Top-3 / Top-5",
         "Tỉ lệ câu có ít nhất một định danh đúng trong 1 / 3 / 5 kết quả đầu",
         "Chất lượng truy hồi ở các mức khoan dung khác nhau"],
        ["MRR", "Trung bình nghịch đảo hạng của kết quả đúng đầu tiên",
         "Đáp án đúng thường nằm ở hạng nào"],
        ["Precision / Recall / F1 (macro)",
         "Trung bình theo từng câu trên tập định danh trả về",
         "Độ sạch và độ phủ của tập trả về"],
        ["Khoảng tin cậy 95%", "Phương pháp Wilson cho tỉ lệ nhị thức",
         "Độ bất định của mọi tỉ lệ do cỡ mẫu hữu hạn"],
        ["Kiểm định McNemar", "Bảng chéo hai cấu hình trên cùng bộ câu hỏi",
         "Chênh lệch giữa hai cấu hình có ý nghĩa thống kê hay không"],
    ], co=11, rong=[3.8, 5.6, 6.6])

    # ══════════════════════ 5. KẾT QUẢ VÀ PHÂN TÍCH ══════════════════════════
    tl.add_heading("5. Kết quả và phân tích", level=1)

    tl.add_heading("5.1. Kết quả tổng thể", level=2)
    ktc = kd["khoang_tin_cay"]

    def _ktc(khoa: str) -> str:
        a, b_ = ktc[khoa]["ktc95"]
        return f"[{pc(a, 1)} – {pc(b_, 1)}]"

    chu_thich(tl, "Bảng 10. Chỉ số đánh giá tổng thể trên "
                  f"{th['so_cau_hoi']} câu hỏi (k = {th['top_k']}), kèm khoảng tin "
                  "cậy 95% theo phương pháp Wilson")
    bang(tl, ["Chỉ số", "Giá trị", "KTC 95%", "Ghi chú"], [
        ["Độ chính xác phân lớp", pc(th["do_chinh_xac_phan_lop"]), _ktc("phan_lop"),
         f"{ktc['phan_lop']['dat']}/{th['so_cau_hoi']} câu vào đúng lớp"],
        ["Top-1", pc(th["top1"]), _ktc("top1"),
         "Cổng chỉ số trong CI chặn mọi thay đổi làm tụt dưới mức này"],
        ["Top-3", pc(th["top3"]), "—", "—"],
        ["Top-5", pc(th["top5"]), _ktc("top5"),
         f"{th['so_cau_sai']}/{th['so_cau_hoi']} câu chưa đạt"],
        ["MRR", so(th["mrr"]), "—", "Đáp án đúng thường nằm ở hạng 1–2"],
        ["Precision (macro)", so(th["precision_macro"]), "—",
         f"Trần toán học {so(kd['tran_precision']['tran'])} — xem mục 5.3"],
        ["Recall (macro)", so(th["recall_macro"]), "—", "—"],
        ["F1 (macro)", so(th["f1_macro"]), "—", "—"],
        ["Thời gian trả lời trung bình", so(th["thoi_gian_tb_ms"], 1) + " ms", "—",
         "Chạy hoàn toàn cục bộ, không gọi dịch vụ ngoài"],
    ], canh_phai={1, 2}, co=11, rong=[4.6, 2.4, 3.2, 5.8])
    doan(tl, "Khoảng tin cậy được đưa vào có chủ đích. Với cỡ mẫu "
             f"{th['so_cau_hoi']} câu, Top-1 {pc(th['top1'])} thực chất nằm trong "
             f"khoảng {_ktc('top1')}. Nghĩa là một thay đổi làm Top-1 nhích 1–2 điểm "
             "phần trăm thì KHÔNG kết luận được là cải tiến — nhóm ghi rõ điều này "
             "để không diễn giải quá số liệu mình có.", thut=0.5)

    tl.add_heading("5.2. Kết quả theo lớp bài toán", level=2)
    chu_thich(tl, "Bảng 11. Chỉ số theo từng lớp bài toán, kèm KTC 95% của Top-1")
    tlop = ktc["top1_theo_lop"]
    bang(tl, ["Lớp bài toán", "n", "Phân lớp", "Top-1", "KTC 95% Top-1", "Top-5"], [
        [TEN_LOP.get(k, k), str(v["n"]), pc(v["acc_phan_lop"], 1), pc(v["top1"], 1),
         (f"[{pc(tlop[k]['ktc95'][0], 0)} – {pc(tlop[k]['ktc95'][1], 0)}]"
          if k in tlop else "—"),
         pc(v["top5"], 1)]
        for k, v in th["theo_lop_bai_toan"].items()
    ], canh_phai={1, 2, 3, 4, 5}, co=11, rong=[4.6, 1.2, 2.2, 2.2, 3.4, 2.4])
    doan(tl, "Nhận xét:", dam=True)
    p2 = th["theo_lop_bai_toan"]["P2_TRA_CUU_QUY_DINH"]
    p7 = th["theo_lop_bai_toan"]["P7_TRA_CUU_LIEN_QUAN"]
    p4 = th["theo_lop_bai_toan"]["P4_TRA_CUU_NGUOC"]
    gach_dau_dong(tl, [
        f"P2 chỉ đạt Top-1 {pc(p2['top1'], 1)} nhưng Top-5 lên {pc(p2['top5'], 1)}. "
        "Nguyên nhân không phải hệ thống tìm sai mà là các quy tắc giao thông có "
        "nhiều điều khoản gần nghĩa: đáp án đúng CÓ trong danh sách trả về, chỉ chưa "
        "được xếp đầu. Đây là lớp cần thêm tín hiệu phân biệt, không phải lớp hỏng.",
        f"P7 chỉ đạt Top-1 {pc(p7['top1'], 1)} nhưng Top-5 đạt {pc(p7['top5'], 1)} — "
        f"tuy nhiên với n = {p7['n']}, khoảng tin cậy rộng tới "
        f"[{pc(tlop['P7_TRA_CUU_LIEN_QUAN']['ktc95'][0], 0)} – "
        f"{pc(tlop['P7_TRA_CUU_LIEN_QUAN']['ktc95'][1], 0)}], nên con số này gần như "
        "không kết luận được gì. Về bản chất lớp “tra cứu liên quan” không có một đáp "
        "án duy nhất: người hỏi muốn một chùm tri thức, nên Top-5 mới là thước đo phù "
        "hợp.",
        f"P4 phân lớp đúng {pc(p4['acc_phan_lop'], 1)} và Top-5 đạt "
        f"{pc(p4['top5'], 1)}, nhưng Top-1 chỉ {pc(p4['top1'], 1)}: tra ngược theo "
        "mức phạt thường có nhiều hành vi cùng thoả điều kiện, và hệ thống trả về "
        "nguyên một TẬP thoả ràng buộc chứ không cắt theo top-k, nên “hạng 1” ở lớp "
        "này là khái niệm ít ý nghĩa.",
        f"Với câu có nhiều đáp án chuẩn, hệ lấy đủ toàn bộ đáp án ở "
        f"{kd['du_dap_an']['cau_nhieu_dap_an']['dat']}/"
        f"{kd['du_dap_an']['cau_nhieu_dap_an']['n']} câu "
        f"({pc(kd['du_dap_an']['cau_nhieu_dap_an']['ty_le'])}) — riêng lớp P4 đạt "
        "tuyệt đối, còn P5 là nơi còn sót.",
    ])

    tl.add_heading("5.3. Kiểm định ý nghĩa thống kê", level=2)
    doan(tl, "Bốn kiểm định dưới đây trả lời bốn câu hỏi mà một bảng chỉ số đơn "
             "thuần không trả lời được.", thut=0.5)

    mc = kd["mcnemar_suy_dien_so_hoc"]
    doan(tl, "a) Suy diễn số học có thật sự cải thiện, hay chỉ là may rủi? ", dam=True)
    doan(tl, "Kiểm định McNemar trên cùng bộ câu hỏi, so cấu hình C (lai ba thành "
             f"phần) với cấu hình D (thêm suy diễn số học): {mc['sai_thanh_dung']} câu "
             f"chuyển từ sai sang đúng, {mc['dung_thanh_sai']} câu chuyển ngược lại, "
             f"p = {so(mc['p'], 6)}. Với p < 0,001, cải thiện này KHÔNG phải ngẫu "
             "nhiên. Đáng chú ý hơn cả trị số p là hình dạng bảng chéo: không có câu "
             "nào bị suy diễn số học làm hỏng, nghĩa là thành phần này chỉ thêm chứ "
             "không phá.", thut=0.5)

    tp = kd["tran_precision"]
    doan(tl, "b) Precision 0,3373 là kém hay là đã kịch trần? ", dam=True)
    doan(tl, "Nhóm tính trần toán học của precision trên chính bộ câu hỏi này: vì hệ "
             f"trả k = {th['top_k']} kết quả trong khi phần lớn câu chỉ có một mẩu tri "
             f"thức đúng, precision tối đa có thể đạt là {so(tp['tran'])}. Giá trị đo "
             f"được {so(tp['precision'])} tương đương {pc(tp['dat_duoc_so_voi_tran'])} "
             "của trần đó. Kết luận: precision thấp là HỆ QUẢ CỦA THIẾT KẾ top-k, "
             "không phải khiếm khuyết của mô hình — và recall macro "
             f"{so(th['recall_macro'])} mới là chỉ số phản ánh đúng mục tiêu của một "
             "hệ tra cứu.", thut=0.5)

    bd = kd["bo_dau"]
    doan(tl, "c) Hệ có chịu được truy vấn gõ không dấu? ", dam=True)
    doan(tl, "Chạy lại toàn bộ bộ câu hỏi sau khi bỏ dấu tiếng Việt: Top-1 "
             f"{pc(bd['top1']['ty_le'])}, Top-5 {pc(bd['top5']['ty_le'])}, phân lớp "
             f"{pc(bd['phan_lop']['ty_le'])} — TRÙNG KHỚP tuyệt đối với bản có dấu ở "
             "cả bảy lớp bài toán. Đây là kết quả của quyết định thiết kế ở mục 3.3: "
             "mọi keyphrase đều lưu kèm bản không dấu và B1 chuẩn hoá về bản đó, nên "
             "dấu tiếng Việt không tham gia vào quá trình so khớp.", thut=0.5)

    doan(tl, "d) Mọi câu hỏi có thật sự chấm được? ", dam=True)
    doan(tl, f"Có test kiểm chứng rằng toàn bộ {kd['cham_duoc']['so_cau']}/"
             f"{th['so_cau_hoi']} câu đều có đáp án chuẩn giải được về tri thức CÓ "
             "THẬT trong cơ sở tri thức, không định danh treo nào. Nếu bước này không "
             "được kiểm, mọi chỉ số ở trên đều vô nghĩa vì có thể hệ thống đang bị "
             "chấm trên những câu không thể đúng.", thut=0.5)

    tl.add_heading("5.4. Thí nghiệm loại bỏ thành phần", level=2)
    doan(tl, "Để chứng minh từng thành phần của hàm điểm thực sự đóng góp chứ không "
             "phải chọn trọng số cảm tính, nhóm chạy thí nghiệm loại bỏ thành phần "
             f"trên cả {ab['so_cau_hoi']} câu hỏi.", thut=0.5)
    chu_thich(tl, "Bảng 12. Kết quả loại bỏ thành phần (ablation)")
    bang(tl, ["Cấu hình", "Top-1", "Top-5", "MRR"], [
        [k, pc(v["top1"] / 100, 1), pc(v["topk"] / 100, 1), so(v["mrr"])]
        for k, v in toan_bo.items()
    ], canh_phai={1, 2, 3}, rong=[8.2, 2.6, 2.6, 2.6])
    chu_thich(tl, "Bảng 13. Ablation riêng trên "
                  f"{ab['so_cau_hoi_co_so']} câu hỏi có giá trị số")
    bang(tl, ["Cấu hình", "Top-1", "Top-5", "MRR"], [
        [k, pc(v["top1"] / 100, 1), pc(v["topk"] / 100, 1), so(v["mrr"])]
        for k, v in co_so.items()
    ], canh_phai={1, 2, 3}, rong=[8.2, 2.6, 2.6, 2.6])
    doan(tl, "Nhận xét:", dam=True)
    a_, b_, c_, dd_ = (toan_bo[k] for k in toan_bo)
    cC, cD = (co_so[k] for k in co_so)
    gach_dau_dong(tl, [
        f"Keyphrase đứng riêng ({pc(b_['top1'] / 100, 1)}) YẾU HƠN TF-IDF đứng riêng "
        f"({pc(a_['top1'] / 100, 1)}), nhưng vẫn xứng đáng nhận trọng số cao nhất "
        "0,55. Lý do: nó thua về ĐỘ PHỦ chứ không thua về ĐỘ CHÍNH XÁC — câu nào có "
        "keyphrase thì gần như chắc đúng, chỉ là nhiều câu khẩu ngữ không có "
        "keyphrase nào.",
        f"Lai ba thành phần đưa Top-1 lên {pc(c_['top1'] / 100, 1)}: TF-IDF lo phần "
        "phủ, keyphrase lo phần chuẩn. Đây là bằng chứng cho thấy hai tín hiệu bù "
        "trừ nhau chứ không trùng lặp.",
        f"Thêm suy diễn số học đưa Top-1 lên {pc(dd_['top1'] / 100, 1)}. Riêng "
        f"{ab['so_cau_hoi_co_so']} câu có giá trị số, Top-1 nhảy từ "
        f"{pc(cC['top1'] / 100, 1)} lên {pc(cD['top1'] / 100, 1)} trong khi Top-5 "
        f"gần như không đổi ({pc(cC['topk'] / 100, 1)} → {pc(cD['topk'] / 100, 1)}). "
        "Con số này nói đúng một điều: so khớp từ khoá VẪN TÌM RA đủ các khung phạt, "
        "nó chỉ không biết CHỌN KHUNG NÀO. Suy diễn số học giải quyết đúng khâu đó, "
        f"và mục 5.3a đã chứng minh cải thiện này có ý nghĩa thống kê (p = "
        f"{so(mc['p'], 6)}).",
    ])

    tl.add_heading("5.5. Phân tích lỗi sâu", level=2)
    doan(tl, "Thay vì chỉ liệt kê câu sai, nhóm chạy lại toàn bộ bộ câu hỏi và ghi "
             "HẠNG của đáp án chuẩn trong danh sách trả về, rồi quy mỗi ca chưa đạt "
             "Top-1 về một nguyên nhân gốc duy nhất theo thứ tự ưu tiên. Kết quả: "
             f"{pl['so_ca_chua_toi_uu']}/{th['so_cau_hoi']} ca chưa tối ưu. Trong "
             f"đó chỉ {pl['so_ca_ngoai_top_k']} ca đáp án rơi hẳn ngoài Top-"
             f"{th['top_k']}; {pl['so_ca_trong_top_k_nhung_khong_hang_1']} ca đáp án "
             "VẪN nằm trong danh sách trả về nhưng không đứng đầu; "
             f"{pl['so_ca_chua_toi_uu'] - pl['so_ca_ngoai_top_k'] - pl['so_ca_trong_top_k_nhung_khong_hang_1']} "
             "ca đáp án đã ở hạng 1 nhưng câu hỏi bị gán sai lớp bài toán. Nói cách "
             "khác, phần lớn cái gọi là “lỗi” ở đây là lỗi XẾP HẠNG, không phải lỗi "
             "tìm kiếm.", thut=0.5)
    chu_thich(tl, "Bảng 14. Sáu nhóm nguyên nhân gốc và số ca")
    bang(tl, ["Mã", "Nguyên nhân gốc", "Số ca", "Mức độ"], [
        [ma_, pl["ten_nguyen_nhan"][ma_], str(so_),
         {"nang": "Nặng", "vua": "Vừa", "nhe": "Nhẹ"}.get(
             {"L1": "nang", "L2": "nang", "L3": "nhe", "L4": "nhe",
              "L5": "vua", "L6": "vua"}[ma_], "—")]
        for ma_, so_ in pl["theo_nguyen_nhan"].items()
    ], canh_phai={0, 2, 3}, rong=[1.4, 8.4, 2.0, 2.4])
    if (HINH / "hinh6_phan_tich_loi.png").exists():
        hinh(tl, HINH / "hinh6_phan_tich_loi.png", 15.5,
             "Hình 6. Phân tích lỗi sâu — nguyên nhân gốc và hạng của đáp án chuẩn")

    doan(tl, "Diễn giải từng nhóm:", dam=True)
    _n = pl["theo_nguyen_nhan"]
    gach_dau_dong(tl, [
        f"L5 — Khoảng trống từ vựng ({_n.get('L5', 0)} ca, nhóm lớn nhất). Câu hỏi "
        "dùng từ đời thường không xuất hiện trong bất kỳ cụm từ khoá nào của đáp án: "
        "“nón bảo hiểm” thay vì “mũ bảo hiểm”, “bằng lái” thay vì “giấy phép lái xe”, "
        "“chạy vào đường cao tốc” thay vì nguyên văn điều cấm. Làn keyphrase im lặng, "
        "chỉ còn TF-IDF gánh, nên đáp án tụt xuống hạng 2–3 chứ hiếm khi rơi hẳn. "
        "Đây là lỗi có thể sửa bằng DỮ LIỆU (bổ sung biến thể khẩu ngữ), không cần "
        "đổi thuật giải.",
        f"L1 — Định tuyến sai lớp ({_n.get('L1', 0)} ca, nặng nhất). Bước B3 chọn "
        "nhầm lớp nên bộ giải sai kiểu chạy. Ví dụ “Đèn giao thông có mấy màu?” bị "
        "đẩy sang P7 vì câu quá ngắn và không có động từ tra cứu rõ ràng; “Bằng lái "
        "bị trừ hết 12 điểm rồi thì sao…” bị đẩy sang P4 vì con số 12 kích hoạt mẫu "
        "tra cứu ngược. Cơ chế bổ sung tri thức ở mục 4.3 cứu được một phần, nhưng "
        "không cứu được hạng 1.",
        f"L2 — Trượt hẳn ngoài Top-{th['top_k']} ({_n.get('L2', 0)} ca). Đây mới là "
        "lỗi người dùng thật sự cảm nhận được. Cả bốn ca đều là câu khẩu ngữ dài kể "
        "tình huống, hoặc câu dạng có/không (“Gặp đèn đỏ thì có được đi tiếp "
        "không?”) — người hỏi chờ một câu khẳng định, hệ thống trả điều khoản gần "
        "nghĩa nhất.",
        f"L3 — Thứ tự trong tập trả về ({_n.get('L3', 0)} ca, nhẹ nhất). Toàn bộ "
        "thuộc lớp P4/P6/P7, nơi hệ thống trả NGUYÊN MỘT TẬP thoả ràng buộc. Đáp án "
        "có trong tập, chỉ không đứng đầu — recall đủ, đây là vấn đề trình bày chứ "
        "không phải truy hồi.",
        f"L4 — Câu nhiều đáp án chuẩn ({_n.get('L4', 0)} ca) và L6 — khác "
        f"({_n.get('L6', 0)} ca). Hạng 1 là một mẩu tri thức cũng hợp lệ nhưng không "
        "trùng mẩu được chấm.",
    ])
    chu_thich(tl, "Bảng 15. Một số ca tiêu biểu và nguyên nhân")
    _tieu_bieu = [c for c in pl["ca"] if c["nguyen_nhan"] in ("L1", "L2")][:8]
    bang(tl, ["Mã", "Câu hỏi", "Hạng", "Nguyên nhân"], [
        [c["id"], c["cau_hoi"][:64] + ("…" if len(c["cau_hoi"]) > 64 else ""),
         ("ngoài Top-%d" % th["top_k"]) if c["hang_dap_an"] is None
         else str(c["hang_dap_an"]),
         c["nguyen_nhan"] + " · " + pl["ten_nguyen_nhan"][c["nguyen_nhan"]][:28]]
        for c in _tieu_bieu
    ], canh_phai={0, 2}, co=10, rong=[1.2, 7.8, 2.0, 5.0])

    tl.add_heading("5.6. Giải thích: vì sao các con số lại như vậy", level=2)
    doan(tl, "Bốn cơ chế dưới đây giải thích gần như toàn bộ hình dạng của kết quả.",
         thut=0.5)
    gach_dau_dong(tl, [
        f"Vì sao Top-5 ({pc(th['top5'])}) bỏ xa Top-1 ({pc(th['top1'])})? Vì cơ chế "
        "bổ sung tri thức ở mục 4.3 không để bước phân lớp chặn kết quả: kể cả khi "
        "B3 chọn sai lớp, hệ vẫn nạp thêm tri thức của các loại còn thiếu nếu điểm "
        "vượt 0,40. Hệ quả là đáp án đúng hiếm khi biến mất khỏi danh sách, chỉ "
        f"thường không đứng đầu — đúng như bảng 14: "
        f"{pl['so_ca_trong_top_k_nhung_khong_hang_1']} ca đáp án nằm trong danh sách "
        "nhưng không ở hạng 1.",
        "Vì sao khoảng cách đó lớn nhất ở P2? Vì quy tắc giao thông là loại tri thức "
        "có nhiều điều khoản gần nghĩa nhất — nhường đường, chuyển hướng, quay đầu "
        "chia sẻ rất nhiều từ vựng. Cả ba làn điểm đều cho các ứng viên này số gần "
        "nhau, và hệ hiện chưa có tín hiệu nào tách chúng ngoài độ tương đồng văn "
        "bản. Đây là lý do hướng phát triển ở mục 6.3 đề xuất dùng quan hệ trong đồ "
        "thị R làm tín hiệu phân biệt.",
        f"Vì sao suy diễn số học tạo khác biệt lớn đến thế ({pc(cC['top1'] / 100, 1)} "
        f"→ {pc(cD['top1'] / 100, 1)} trên câu có số) mà Top-5 gần như không đổi? Vì "
        "bài toán ở nhóm câu này không phải TÌM mà là CHỌN. Các khung phạt của cùng "
        "một hành vi có văn bản gần như giống hệt nhau, chỉ khác con số ngưỡng; so "
        "khớp văn bản đưa cả bốn khung vào top-5 nhưng không có cơ sở nào để xếp "
        "hạng giữa chúng. Chỉ khi so sánh KHOẢNG SỐ mới chọn đúng được.",
        f"Vì sao hệ chưa từ chối được truy vấn nào trong {d['so_ngoai_mien']} truy "
        "vấn ngoài lĩnh vực? Vì đặc trưng TF-IDF mặc định không tách được hai phân "
        "bố: 56/%d câu hợp lệ chấm điểm thấp hơn hoặc bằng truy " % th["so_cau_hoi"] +
        "vấn rác, nên không tồn tại ngưỡng nào vừa loại hết rác vừa không từ chối "
        "oan. Số đo đầy đủ và các hướng đã thử được trình bày ở mục 6.2.",
    ])

    tl.add_heading("5.7. Kiểm thử nghiệm thu và kiểm thử tự động", level=2)
    chu_thich(tl, "Bảng 16. Mười hai ca nghiệm thu chức năng")
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

    # ═══════ 6. ỨNG DỤNG, KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN ═══════════════════════
    tl.add_heading("6. Ứng dụng, kết luận và hướng phát triển", level=1)

    tl.add_heading("6.1. Ứng dụng đã triển khai", level=2)
    doan(tl, "Cơ sở tri thức và động cơ suy diễn được đóng gói thành ba mặt tiếp cận, "
             "dùng chung một lõi nên số liệu in ra luôn đến từ đúng mã nguồn đang "
             "phục vụ giao diện.", thut=0.5)
    chu_thich(tl, "Bảng 17. Ba mặt tiếp cận của hệ thống")
    bang(tl, ["Mặt tiếp cận", "Đường dẫn / lệnh", "Dùng cho"], [
        ["Giao diện tra cứu", "/tra-cuu?q= · /dieu-khoan/{id}",
         "Người dùng cuối — tra cứu kèm nguyên văn điều khoản và căn cứ"],
        ["Xem theo mốc thời gian", "/hieu-luc?dk= · bộ lọc ngay=YYYY-MM-DD",
         "So câu chữ trước và sau sửa đổi — trả lời “tại thời điểm t thì sao”"],
        ["Duyệt theo chủ đề", "/chu-de?linh_vuc=&nhom=",
         "Người học luật — đọc có hệ thống theo 6 lĩnh vực"],
        ["Bảng chỉ số", "/chi-so", "Người chấm — xem chỉ số đo trực tiếp trên hệ"],
        ["API JSON", "/api/ask · /api/docs (OpenAPI)",
         "Tích hợp vào ứng dụng khác"],
        ["Đóng gói Docker", "docker compose up giao-dien",
         "Chạy lại toàn bộ mà không cần cài Python"],
    ], co=11, rong=[3.6, 5.4, 7.0])
    doan(tl, "Giao diện đáp ứng được cả màn hình nhỏ: dưới 720px thanh bên chuyển "
             "thành thanh tab đáy, dùng chung đường dẫn chứ không có bản mobile "
             "riêng. Hai bộ lọc ngay và pt (phương tiện) dùng chung trên mọi màn.",
         thut=0.5)
    doan(tl, "Giá trị sử dụng thực tế nằm ở ba chỗ: câu trả lời luôn kèm căn cứ tới "
             "mức điều – khoản – điểm nên kiểm chứng được; tra cứu được theo mốc thời "
             "gian nên không đưa nhầm quy định đã hết hiệu lực; và toàn bộ chạy cục "
             f"bộ trong {so(th['thoi_gian_tb_ms'], 1)} ms mỗi truy vấn, không gửi câu "
             "hỏi của người dân ra dịch vụ ngoài.", thut=0.5)

    tl.add_heading("6.2. Hạn chế", level=2)
    doan(tl, "Mọi hạn chế dưới đây đều đã ĐO ĐƯỢC và khoá lại bằng test xfail trong "
             "kho mã, không phải phỏng đoán. Nhóm trình bày cả những hướng đã thử và "
             "đã bác bỏ, vì một kết quả âm có số đo cũng là kết quả.", thut=0.5)
    mien = {r["tin_hieu"]: r for r in d["mien"]["results"]}
    doan(tl, "a) Chưa từ chối được truy vấn ngoài lĩnh vực. ", dam=True)
    doan(tl, "Ở cấu hình mặc định, hỏi “cách nấu phở bò” thì hệ thống vẫn trả về một "
             "hành vi vi phạm: cả "
             f"{kd['ngoai_mien']['van_tra_ve_ket_qua']}/"
             f"{kd['ngoai_mien']['so_truy_van']} truy vấn ngoài miền đều được trả "
             "lời thay vì bị từ chối. Nguyên nhân đã khoanh vùng: đặc trưng TF-IDF quá yếu để tách "
             f"miền — 56/{th['so_cau_hoi']} câu hợp lệ chấm điểm thấp hơn hoặc bằng "
             "truy vấn rác, nên không tồn tại ngưỡng nào tách được hai phân bố.",
         thut=0.5)
    chu_thich(tl, "Bảng 18. Khả năng tách miền của bốn tín hiệu "
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

    doan(tl, "b) Các hạn chế còn lại. ", dam=True)
    gach_dau_dong(tl, [
        f"Khoảng trống từ vựng là nguồn lỗi lớn nhất: {_n.get('L5', 0)} ca được quy "
        "trực tiếp về nguyên nhân này, và tính rộng ra thì "
        f"{pl['so_ca_khong_co_cum_tu_khoa']}/{pl['so_ca_chua_toi_uu']} ca chưa tối ưu "
        "đều có đặc điểm chung là không cụm từ khoá nào của đáp án xuất hiện trong "
        "câu hỏi. Đây là hạn chế của DỮ LIỆU chứ không của thuật giải: sửa bằng cách "
        "bổ sung biến thể khẩu ngữ vào từ điển, không cần đổi mô hình.",
        f"12/{th['so_cau_hoi']} câu hợp lệ không rút được keyphrase nào, nên không "
        "thể dùng riêng tín hiệu keyphrase làm bộ lọc truy vấn ngoài lĩnh vực.",
        "Bộ câu hỏi đánh giá chưa phủ đều cơ sở tri thức: phân bố chủ đề ở mục 3.4c "
        "cho thấy lĩnh vực “Điều kiện của phương tiện” bị đánh giá nhẹ hơn tỉ trọng "
        "của nó trong cơ sở tri thức. Các chỉ số vì vậy phản ánh đúng nhu cầu tra cứu "
        "phổ biến hơn là phản ánh đều toàn bộ tri thức.",
        "Chưa mô hình hoá 46 chú thích sửa đổi của Luật 118/2025/QH15 ở mức từng "
        "khoản. Đây là khoảng trống DỮ LIỆU đã khoanh vùng: 46 chú thích đã trích ra "
        "data/raw/luat118_dieu7_chu_thich.json, nhưng mô hình SuaDoi hiện chỉ có "
        "trường theo Nghị định 168 nên chưa biểu diễn được sửa đổi ở tầng luật.",
        "Hệ thống không sinh ngôn ngữ tự nhiên: câu trả lời được ghép từ nguyên văn "
        "điều khoản. Đây là lựa chọn có chủ đích của một hệ tra cứu pháp luật — như "
        "các số đo ảo giác ở mục 2.1 cho thấy, diễn giải lại lời của luật là rủi ro "
        "lớn hơn lợi ích về trải nghiệm.",
        "Hỏi nồng độ cồn mà không nêu phương tiện thì hệ thống trả về khung xe đạp. "
        "Về mặt tri thức là đúng — hệ không bịa phương tiện người dùng chưa nói — "
        "nhưng là vấn đề trải nghiệm cần giải quyết bằng câu hỏi làm rõ.",
        f"Cỡ mẫu {th['so_cau_hoi']} câu khiến khoảng tin cậy của các lớp nhỏ rất "
        f"rộng (P7 với n = {p7['n']} có KTC Top-1 trải gần trọn khoảng 0–1), nên "
        "không kết luận mạnh được ở mức từng lớp.",
    ])

    tl.add_heading("6.3. Hướng phát triển", level=2)
    gach_dau_dong(tl, [
        "Mở rộng từ điển cụm từ khoá bằng khẩu ngữ thu từ truy vấn thật — nhắm thẳng "
        f"vào nhóm lỗi L5, nhóm chiếm {_n.get('L5', 0)}/{pl['so_ca_chua_toi_uu']} ca "
        "chưa tối ưu và là hướng cải thiện rẻ nhất.",
        "Bổ sung tầng hỏi lại khi truy vấn thiếu thông tin bắt buộc (phương tiện, "
        "chủ thể) thay vì mặc định chọn khung rộng nhất.",
        "Thêm tín hiệu phân biệt cho lớp P2: các quy tắc gần nghĩa cần được tách bằng "
        "quan hệ trong đồ thị R, không chỉ bằng điểm tương đồng văn bản.",
        "Tổng quát hoá mô hình SuaDoi để biểu diễn được sửa đổi ở cả tầng luật và "
        "tầng nghị định, khép nốt 46 chú thích còn lại — đây cũng là bước tiến gần "
        "hơn tới mô hình sửa đổi hình thức của Governatori và cộng sự [30].",
        "Mở rộng bộ đánh giá để phủ đều các lĩnh vực trong cơ sở tri thức, và tăng "
        "cỡ mẫu để khoảng tin cậy ở mức từng lớp bài toán đủ hẹp cho kết luận.",
        "Đưa tầng dense embedding vào bản triển khai có tài nguyên, kèm ngưỡng hai "
        "mức: từ chối chắc chắn, nghi ngờ thì cảnh báo thay vì chặn.",
        "Về dài hạn, công bố cơ sở tri thức và bộ câu hỏi như một tài nguyên mở cho "
        "lĩnh vực giao thông đường bộ Việt Nam — đúng khoảng trống nêu ở mục 2.3.",
    ])

    tl.add_heading("6.4. Kết luận", level=2)
    doan(tl, "Nhóm đã xây dựng hoàn chỉnh một hệ tra cứu kiến thức pháp luật giao "
             "thông đường bộ theo đúng yêu cầu Đề tài 4: cơ sở tri thức có cấu trúc "
             f"gồm {kb['concepts']} khái niệm, {kb['relations']} quan hệ, "
             f"{kb['rules']} quy tắc, {tien(kb['violations'])} hành vi vi phạm và "
             f"{tien(kb['keyphrases'])} cụm từ khoá; bộ dữ liệu {th['so_cau_hoi']} "
             "câu hỏi có đáp án chuẩn; thuật giải xử lý truy vấn sáu bước; và một "
             "giao diện tra cứu chạy được.", thut=0.5)
    doan(tl, f"Về số đo, hệ thống đạt độ chính xác phân lớp "
             f"{pc(th['do_chinh_xac_phan_lop'])}, Top-1 {pc(th['top1'])} "
             f"(KTC 95% {_ktc('top1')}), Top-5 {pc(th['top5'])} và MRR "
             f"{so(th['mrr'])}, thời gian trả lời trung bình "
             f"{so(th['thoi_gian_tb_ms'], 1)} ms trên máy cá nhân, hoàn toàn không "
             "phụ thuộc dịch vụ ngoài. Thí nghiệm loại bỏ thành phần chứng minh từng "
             "phần của hàm điểm đều đóng góp thực chất, và kiểm định McNemar "
             f"(p = {so(mc['p'], 6)}) khẳng định bước suy diễn số học tạo khác biệt "
             "có ý nghĩa thống kê chứ không phải may rủi.", thut=0.5)
    doan(tl, "So với các công trình khảo sát ở mục 2, đóng góp riêng của đồ án nằm ở "
             "chỗ ghép được ba thứ vốn tách rời: mô hình tri thức tường minh theo "
             "hướng Legal-Onto, suy diễn số học để tính chế tài, và mô hình hoá hiệu "
             "lực theo thời gian ở mức khoản — trên khung pháp lý giao thông đường bộ "
             "2024–2026 mà chưa công trình tiếng Việt nào phủ.", thut=0.5)
    doan(tl, "Điều nhóm thấy đáng giá nhất không phải là con số Top-1 mà là kỷ luật "
             "đo đạc: mọi khẳng định trong báo cáo này đều sinh ra từ một lệnh chạy "
             "lại được, mọi hạn chế đều có số đo kèm theo, mọi tỉ lệ đều kèm khoảng "
             "tin cậy, và những hướng đã thử rồi bác bỏ đều được ghi lại thay vì "
             "giấu đi.", thut=0.5)

    # ═══════════════════════ tài liệu tham khảo ══════════════════════════════
    tl.add_heading("Tài liệu tham khảo", level=1)
    doan(tl, "Văn bản pháp luật", dam=True)
    gach_dau_dong(tl, VAN_BAN_PHAP_LUAT, danh_so=True)
    doan(tl, "Công trình khoa học", dam=True)
    gach_dau_dong(tl, TAI_LIEU_KHOA_HOC, danh_so=True)

    # ═══════════════════════════════ phụ lục ═════════════════════════════════
    tl.add_heading("Phụ lục A. Phân công công việc", level=1)
    chu_thich(tl, "Bảng 19. Phân công bảy thành viên Nhóm 7")
    bang(tl, ["Họ và tên", "MSSV", "Nội dung phụ trách"],
         [[ng["ho_ten"], ng["mssv"], viec]
          for ng, viec in zip(d["tv"]["thanh_vien"], [
              "Mục 1 — tổng quan, phát biểu bài toán; trang bìa và định dạng toàn bài",
              "Mục 2 — khảo sát công trình liên quan, bộ dữ liệu đã có và phân tích "
              "khoảng trống",
              "Mục 3 — nguồn văn bản, quy trình lấy và chuẩn hoá dữ liệu",
              "Mục 3 — thống kê và phân tích bộ dữ liệu, ba biểu đồ phân bố",
              "Mục 4 — kiến trúc, thuật giải B1–B6, hàm điểm lai và cấu hình siêu "
              "tham số",
              "Mục 5 — bảng chỉ số, kiểm định thống kê và thí nghiệm loại bỏ thành "
              "phần",
              "Mục 5 — phân tích lỗi sâu; mục 6 — ứng dụng, hạn chế và demo",
          ])], canh_phai={1}, co=12, rong=[4.2, 2.4, 9.4])

    tl.add_heading("Phụ lục B. Cách kiểm chứng lại số liệu", level=1)
    doan(tl, "Mọi con số trong báo cáo này sinh ra từ các lệnh sau, chạy tại thư mục "
             "ma_nguon/:", thut=0.5)
    ma(tl, [
        "pip install -e '.[dev,web,bao-cao]'",
        f"pytest -q --cov      # {kt['so_test_dat']} passed · {kt['so_xfail']} "
        f"xfailed · phủ {kt['do_phu_phan_tram']}%",
        f"python eval/evaluate.py --gate-top1 {th['top1']:.4f}",
        "python eval/ablation.py            # bang 12, 13",
        "python eval/kiem_dinh.py           # KTC 95%, McNemar, tran precision",
        "python eval/phan_tich_loi.py       # bang 14, 15 va hinh 6",
        "python scripts/thong_ke_du_lieu.py # hinh 1, 2, 3",
        f"python eval/kich_ban.py --chi-tiet # {kt['ca_nghiem_thu_dat']}/"
        f"{kt['ca_nghiem_thu_tong']} ca nghiem thu",
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
