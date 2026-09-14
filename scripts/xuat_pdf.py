# -*- coding: utf-8 -*-
"""Xuất .docx/.pptx ra PDF bằng LibreOffice — CÓ cập nhật mục lục.

VÌ SAO KHÔNG DÙNG THẲNG `soffice --convert-to pdf`
Lệnh đó nạp tài liệu rồi xuất ngay, KHÔNG cập nhật trường (field). Mục lục trong
báo cáo là một trường TOC, nên bản PDF xuất theo cách đó có trang MỤC LỤC trống,
chỉ còn dòng nhắc "Nhấn chuột phải… Update Field". Script này điều khiển
LibreOffice qua UNO để cập nhật chỉ mục trước khi lưu.

    python scripts/xuat_pdf.py docs/Slide_Nhom7_CS106.pptx
    python scripts/xuat_pdf.py --ra-thu-muc /duong/dan/khac tep1.docx tep2.pptx

Cần LibreOffice. Mô-đun `uno` nằm trong bản cài LibreOffice chứ không phải trên
PyPI, nên nếu python đang chạy không có `uno`, script tự chạy lại bằng python đi
kèm LibreOffice. Không tìm thấy thì lùi về `--convert-to` và CẢNH BÁO rằng mục
lục sẽ trống — im lặng xuất bản thiếu mục lục còn tệ hơn là báo lỗi.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

CONG = "2002"

#: Nơi LibreOffice hay nằm, theo thứ tự ưu tiên. macOS cài dạng .app nên không
#: có trong PATH; Linux thì thường có sẵn.
UNG_VIEN_SOFFICE = [
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/bin/soffice",
    "/usr/lib/libreoffice/program/soffice",
    "/opt/libreoffice/program/soffice",
]
#: Python có thể import được `uno`. macOS: bản đi kèm LibreOffice. Linux: gói
#: python3-uno cài vào python hệ thống, nên `python3` trên PATH thường có — còn
#: python của môi trường ảo (.venv, uv) thì KHÔNG. Vì vậy phải thử chứ không
#: đoán: mỗi ứng viên được chạy thử `-c "import uno"`.
UNG_VIEN_PYTHON = [
    "/Applications/LibreOffice.app/Contents/Resources/python",
    "/Applications/LibreOffice.app/Contents/MacOS/python",
    "/usr/lib/libreoffice/program/python",
    "/opt/libreoffice/program/python",
    "python3",
    "/usr/bin/python3",
]


def tim_python_co_uno() -> str | None:
    """Ứng viên đầu tiên thật sự import được `uno` (bỏ qua chính python đang chạy)."""
    dang_chay = os.path.realpath(sys.executable)
    for c in UNG_VIEN_PYTHON:
        duong_dan = shutil.which(c) if not os.path.isabs(c) else c
        if not duong_dan or not os.access(duong_dan, os.X_OK):
            continue
        if os.path.realpath(duong_dan) == dang_chay:
            continue
        try:
            r = subprocess.run([duong_dan, "-c", "import uno"], check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            continue
        if r.returncode == 0:
            return duong_dan
    return None


def tim_soffice() -> str | None:
    return shutil.which("soffice") or next(
        (c for c in UNG_VIEN_SOFFICE if os.access(c, os.X_OK)), None)


def bo_loc(tep: Path) -> str:
    if tep.suffix.lower() in (".pptx", ".ppt", ".odp"):
        return "impress_pdf_Export"
    if tep.suffix.lower() in (".xlsx", ".xls", ".ods"):
        return "calc_pdf_Export"
    return "writer_pdf_Export"


# ─────────────────────────── đường chính: qua UNO ────────────────────────────
def xuat_qua_uno(cac_tep: list[Path], ra_thu_muc: Path | None) -> int:
    import uno  # noqa: PLC0415  (chỉ có khi chạy bằng python của LibreOffice)
    from com.sun.star.beans import PropertyValue  # noqa: PLC0415

    def pv(ten, gt):
        p = PropertyValue()
        p.Name, p.Value = ten, gt
        return p

    soffice = tim_soffice()
    tien_trinh = subprocess.Popen([
        soffice, "--headless", "--norestore", "--invisible",
        f"--accept=socket,host=127.0.0.1,port={CONG};urp;"])
    try:
        ctx_local = uno.getComponentContext()
        giai = ctx_local.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", ctx_local)
        url = (f"uno:socket,host=127.0.0.1,port={CONG};urp;"
               "StarOffice.ComponentContext")
        ctx = None
        for _ in range(60):                       # chờ tối đa 30 giây
            try:
                ctx = giai.resolve(url)
                break
            except Exception:
                time.sleep(0.5)
        if ctx is None:
            raise RuntimeError("khong ket noi duoc LibreOffice qua UNO")

        desktop = ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", ctx)
        for tep in cac_tep:
            doc = desktop.loadComponentFromURL(
                uno.systemPathToFileUrl(str(tep.resolve())), "_blank", 0,
                (pv("Hidden", True), pv("ReadOnly", False)))
            # ĐÂY là bước mà --convert-to bỏ qua: cập nhật mục lục và trường.
            for cap_nhat in (
                lambda: doc.refresh(),
                lambda: [doc.getDocumentIndexes().getByIndex(i).update()
                         for i in range(doc.getDocumentIndexes().getCount())],
                lambda: doc.getTextFields().refresh(),
            ):
                try:
                    cap_nhat()
                except Exception:
                    pass                          # tài liệu không có mục lục
            ra = (ra_thu_muc or tep.parent) / (tep.stem + ".pdf")
            ra.parent.mkdir(parents=True, exist_ok=True)
            doc.storeToURL(uno.systemPathToFileUrl(str(ra.resolve())),
                           (pv("FilterName", bo_loc(tep)),
                            pv("Overwrite", True)))
            doc.close(False)
            print(f"    {ra.name} — co cap nhat muc luc")
        try:
            desktop.terminate()
        except Exception:
            pass
    finally:
        time.sleep(2)
        tien_trinh.terminate()
    return 0


# ─────────────────── đường lùi: --convert-to, mục lục trống ──────────────────
def xuat_du_phong(cac_tep: list[Path], ra_thu_muc: Path | None) -> int:
    soffice = tim_soffice()
    if not soffice:
        print("BO QUA xuat PDF: khong tim thay LibreOffice.", file=sys.stderr)
        return 1
    print("CANH BAO: khong dung duoc UNO nen muc luc trong PDF se TRONG.",
          file=sys.stderr)
    for tep in cac_tep:
        dich = ra_thu_muc or tep.parent
        dich.mkdir(parents=True, exist_ok=True)
        subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                        "--outdir", str(dich), str(tep)],
                       check=False, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        print(f"    {tep.stem}.pdf — MUC LUC TRONG", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tep", nargs="+", help="tệp .docx/.pptx cần xuất PDF")
    ap.add_argument("--ra-thu-muc", default=None,
                    help="thư mục ghi PDF (mặc định: cạnh tệp gốc)")
    a = ap.parse_args()

    cac_tep = [Path(t) for t in a.tep]
    thieu = [t for t in cac_tep if not t.is_file()]
    if thieu:
        print("Khong tim thay: " + ", ".join(map(str, thieu)), file=sys.stderr)
        return 2
    ra = Path(a.ra_thu_muc) if a.ra_thu_muc else None

    try:
        import uno  # noqa: F401,PLC0415
    except ImportError:
        # Chạy lại bằng một python khác có sẵn mô-đun uno.
        py_lo = tim_python_co_uno()
        if py_lo and os.environ.get("_XUAT_PDF_DA_THU") != "1":
            moi = dict(os.environ, _XUAT_PDF_DA_THU="1")
            return subprocess.run([py_lo, os.path.abspath(__file__), *sys.argv[1:]],
                                  env=moi, check=False).returncode
        return xuat_du_phong(cac_tep, ra)

    if not tim_soffice():
        print("BO QUA xuat PDF: khong tim thay LibreOffice.", file=sys.stderr)
        return 1
    try:
        return xuat_qua_uno(cac_tep, ra)
    except Exception as e:                        # noqa: BLE001
        print(f"UNO that bai ({e}) — lui ve --convert-to.", file=sys.stderr)
        return xuat_du_phong(cac_tep, ra)


if __name__ == "__main__":
    raise SystemExit(main())
