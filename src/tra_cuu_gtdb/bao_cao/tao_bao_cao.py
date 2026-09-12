"""Sinh khung báo cáo Word đúng định dạng đề bài yêu cầu.

VÌ SAO SINH BẰNG MÃ
===================
Đề bài kèm 7 ảnh hướng dẫn định dạng rất cụ thể. Gõ tay thì (a) sai lề không ai
phát hiện cho tới lúc nộp, và (b) mỗi lần chỉ số thay đổi lại phải sửa tay
khắp báo cáo. Sinh bằng mã thì định dạng được KIỂM THỬ, còn số liệu LẤY THẲNG
từ ``eval/ket_qua_danh_gia.json`` nên không bao giờ lệch với thực đo.

Đây là KHUNG, không phải bài nộp: các mục phân tích, nhận xét và hình minh hoạ
vẫn phải người viết. Chỗ nào cần viết thêm đều đánh dấu rõ trong tài liệu.

Chạy:
    pip install -e '.[bao-cao]'
    python -m tra_cuu_gtdb.bao_cao.tao_bao_cao
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from docx import Document as _mo_tai_lieu
from docx.document import Document  # kieu that; docx.Document la HAM tao, khong phai lop
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

#: Rút từ 7 ảnh trong Huong_dan_viet_bao_cao_Word/ của đề bài.
DINH_DANG: dict[str, Any] = {
    "font": "Times New Roman",
    "co_chu": 14,
    "le_cm": {"tren": 2, "duoi": 2, "trai": 3, "phai": 2},
}

TRUONG = "ĐẠI HỌC QUỐC GIA THÀNH PHỐ HỒ CHÍ MINH"
KHOA = "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN"
MON = "CS106 — TRÍ TUỆ NHÂN TẠO"
DE_TAI = "Đề tài 4: Xây dựng hệ thống tra cứu kiến thức pháp luật"
LINH_VUC = "Lĩnh vực: Giao thông đường bộ"
GVHD = "PGS.TS. Nguyễn Đình Hiển"
LOP = "CS106.F31.CN2"
NHOM = "Nhóm 7"

#: Mục nào cần người viết thêm thì ghi rõ, đừng để người đọc tưởng đã xong.
CAN_VIET_THEM = "[Cần viết thêm]"


def _dem(duong_dan: Path) -> int:
    """Số bản ghi trong một tệp JSON của cơ sở tri thức."""
    with duong_dan.open(encoding="utf-8") as f:
        return len(json.load(f))


def _phan_tram(x: float) -> str:
    return f"{x:.2%}".replace(".", ",")


def _so(x: float, chu_so: int = 4) -> str:
    return f"{x:.{chu_so}f}".replace(".", ",")


def _dat_dinh_dang(tl: Document) -> None:
    """Áp bốn thiết lập rút từ ảnh hướng dẫn."""
    kieu = tl.styles["Normal"].font
    kieu.name = DINH_DANG["font"]
    kieu.size = Pt(DINH_DANG["co_chu"])
    le = DINH_DANG["le_cm"]
    for khu in tl.sections:
        khu.orientation = WD_ORIENT.PORTRAIT
        khu.top_margin = Cm(le["tren"])
        khu.bottom_margin = Cm(le["duoi"])
        khu.left_margin = Cm(le["trai"])
        khu.right_margin = Cm(le["phai"])


def _giua(tl: Document, chu: str, dam: bool = False, co: int | None = None) -> None:
    d = tl.add_paragraph()
    d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = d.add_run(chu)
    r.bold = dam
    if co:
        r.font.size = Pt(co)


def _trang_bia(tl: Document, thanh_vien: list[dict[str, str]]) -> None:
    _giua(tl, TRUONG, dam=True)
    _giua(tl, KHOA, dam=True)
    _giua(tl, "")
    _giua(tl, "")
    _giua(tl, MON, dam=True, co=16)
    _giua(tl, "")
    _giua(tl, DE_TAI, dam=True, co=20)
    _giua(tl, LINH_VUC, co=16)
    _giua(tl, "")
    _giua(tl, f"Giảng viên hướng dẫn: {GVHD}")
    _giua(tl, f"Lớp: {LOP}   ·   {NHOM}")
    _giua(tl, "")

    bang = tl.add_table(rows=1, cols=3)
    bang.style = "Table Grid"
    for o, nhan in zip(bang.rows[0].cells, ("STT", "Họ và tên", "MSSV"), strict=True):
        o.paragraphs[0].add_run(nhan).bold = True
    for i, nguoi in enumerate(thanh_vien, 1):
        h = bang.add_row().cells
        h[0].text, h[1].text, h[2].text = str(i), nguoi["ho_ten"], nguoi["mssv"]

    _giua(tl, "")
    _giua(tl, "Thành phố Hồ Chí Minh, tháng 9 năm 2026")
    # python-docx chua gan chu thich kieu cho ham nay
    tl.add_page_break()  # type: ignore[no-untyped-call]


def _bang(tl: Document, tieu_de: list[str], hang: list[list[str]]) -> None:
    b = tl.add_table(rows=1, cols=len(tieu_de))
    b.style = "Table Grid"
    for o, nhan in zip(b.rows[0].cells, tieu_de, strict=True):
        o.paragraphs[0].add_run(nhan).bold = True
    for d in hang:
        for o, gt in zip(b.add_row().cells, d, strict=True):
            o.text = gt


def _muc(tl: Document, so: str, ten: str) -> None:
    tl.add_heading(f"{so}. {ten}", level=1)


def dung_bao_cao(goc: Path) -> Document:
    """Dựng tài liệu báo cáo từ dữ liệu thật trong kho."""
    with (goc / "docs" / "thanh_vien.json").open(encoding="utf-8") as f:
        thanh_vien = json.load(f)["thanh_vien"]
    with (goc / "eval" / "ket_qua_danh_gia.json").open(encoding="utf-8") as f:
        dg = json.load(f)
    th = dg["tong_hop"]

    tl = _mo_tai_lieu()
    _dat_dinh_dang(tl)
    _trang_bia(tl, thanh_vien)

    _muc(tl, "1", "Giới thiệu")
    tl.add_paragraph(
        "Hệ thống tra cứu kiến thức pháp luật giao thông đường bộ Việt Nam, xây dựng "
        "trên mô hình tri thức K = (C, R, Rules, F, Keyphrase). Người dùng đặt câu hỏi "
        "bằng ngôn ngữ tự nhiên; hệ thống phân loại câu hỏi vào một trong bảy lớp bài "
        "toán, truy hồi tri thức phù hợp và trả lời kèm căn cứ pháp lý.")
    tl.add_paragraph(f"{CAN_VIET_THEM} Bối cảnh thực tiễn và lý do chọn đề tài.")

    _muc(tl, "2", "Cơ sở tri thức")
    tl.add_paragraph("Nguồn: Luật 36/2024/QH15 và Nghị định 168/2024/NĐ-CP, đối chiếu "
                     "bản hợp nhất tới năm 2026.")
    _bang(tl, ["Thành phần", "Ký hiệu", "Số lượng"], [
        [ten, ky_hieu, str(_dem(goc / "data" / "kb" / tep))]
        for ten, ky_hieu, tep in [
            ("Khái niệm", "C", "concepts.json"),
            ("Quan hệ", "R", "relations.json"),
            ("Quy tắc", "Rules", "rules.json"),
            ("Hành vi vi phạm", "F", "violations.json"),
            ("Keyphrase", "Keyphrase", "keyphrases.json"),
        ]
    ])
    tl.add_paragraph(f"{CAN_VIET_THEM} Cách thu thập và chuẩn hoá dữ liệu; ví dụ minh hoạ "
                     "một bản ghi khái niệm và một bản ghi hành vi vi phạm.")

    _muc(tl, "3", "Thiết kế giải pháp")
    tl.add_paragraph("Thuật giải xử lý truy vấn gồm sáu bước B1–B6: chuẩn hoá truy vấn; "
                     "rút trích keyphrase theo cụm dài nhất; phân loại lớp bài toán; dựng "
                     "biểu diễn hình thức Q; suy diễn và truy hồi; sinh câu trả lời kèm căn cứ.")
    tl.add_paragraph("Hàm điểm lai: score = 0,55·keyphrase + 0,30·ngữ nghĩa + 0,15·ngữ cảnh.")
    tl.add_paragraph(f"{CAN_VIET_THEM} Chèn sơ đồ kiến trúc và sơ đồ luồng B1–B6. "
                     "Nội dung chi tiết xem docs/thiet_ke_giai_phap.md.")

    _muc(tl, "4", "Thực nghiệm và đánh giá")
    tl.add_paragraph(f"Bộ dữ liệu kiểm thử: {th['so_cau_hoi']} câu hỏi có đáp án chuẩn "
                     f"và căn cứ pháp lý, k = {th['top_k']}.")
    _bang(tl, ["Chỉ số", "Giá trị"], [
        ["Độ chính xác phân lớp", _phan_tram(th["do_chinh_xac_phan_lop"])],
        ["Top-1", _phan_tram(th["top1"])],
        ["Top-3", _phan_tram(th["top3"])],
        ["Top-5", _phan_tram(th["top5"])],
        ["MRR", _so(th["mrr"])],
        ["Precision (macro)", _so(th["precision_macro"])],
        ["Recall (macro)", _so(th["recall_macro"])],
        ["F1 (macro)", _so(th["f1_macro"])],
    ])
    tl.add_paragraph("")
    tl.add_paragraph("Kết quả theo từng lớp bài toán:")
    _bang(tl, ["Lớp bài toán", "n", "Phân lớp", "Top-1", "Top-5"], [
        [lop, str(g["n"]), _phan_tram(g["acc_phan_lop"]),
         _phan_tram(g["top1"]), _phan_tram(g["top5"])]
        for lop, g in th["theo_lop_bai_toan"].items()
    ])
    tl.add_paragraph(f"{CAN_VIET_THEM} Nhận xét từng lớp bài toán, đặc biệt các lớp có "
                     "Top-1 thấp, và phân tích những câu trả lời sai.")

    _muc(tl, "5", "Hạn chế và hướng phát triển")
    tl.add_paragraph("Các hạn chế dưới đây đều đã ĐO ĐƯỢC và ghi nhận bằng test xfail "
                     "trong kho mã, không phải phỏng đoán:")
    for y in [
        "Chưa từ chối được truy vấn ngoài lĩnh vực ở cấu hình mặc định: đặc trưng "
        "TF-IDF quá yếu để tách miền.",
        "Dense embedding nâng AUC từ 0,8746 lên 0,9958 và loại được 92,5% truy vấn "
        "rác mà không từ chối oan câu hợp lệ nào, nhưng hai phân bố vẫn chồng lấn.",
        "Hệ thống không sinh ngôn ngữ tự nhiên: câu trả lời ghép từ nguyên văn điều "
        "khoản. Đây là lựa chọn có chủ đích của một hệ tra cứu pháp luật.",
        "Chưa mô hình hoá 46 khoản sửa đổi của Luật 118/2025/QH15 ở mức từng khoản.",
    ]:
        tl.add_paragraph(y, style="List Bullet")

    _muc(tl, "6", "Kết luận")
    tl.add_paragraph(f"{CAN_VIET_THEM} Tóm tắt kết quả đạt được và đóng góp của nhóm.")

    _muc(tl, "7", "Tài liệu tham khảo")
    for x in ["Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15.",
              "Nghị định 168/2024/NĐ-CP.",
              "Luật 118/2025/QH15 sửa đổi, bổ sung một số điều của 10 luật liên quan "
              "đến an ninh, trật tự.",
              "Văn bản hợp nhất 55/VBHN-VPQH ngày 23/3/2026, Văn phòng Quốc hội.",
              "Thư viện pháp luật — https://thuvienphapluat.vn/"]:
        tl.add_paragraph(x, style="List Number")

    return tl


def main() -> int:
    goc = Path(__file__).resolve().parents[3]
    dd = goc / "docs" / "bao_cao_de_tai_4_khung.docx"
    dung_bao_cao(goc).save(str(dd))
    print(f"Da ghi {dd.relative_to(goc)}")
    print(f"Cac muc danh dau {CAN_VIET_THEM} van can nguoi viet.")
    print("Day la KHUNG duoc sinh lai moi lan chay. Hay Save As sang ten khac")
    print("truoc khi dien noi dung, keo lan chay sau ghi de mat bai.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
