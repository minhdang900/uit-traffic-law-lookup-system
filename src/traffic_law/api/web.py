"""Tầng web — FastAPI + Jinja, thay cho giao diện Streamlit.

VÌ SAO BỎ STREAMLIT
===================
Bản thiết kế bàn giao yêu cầu bảy màn hình với thanh bên cố định, lưới hai cột
và thẻ kết quả bo 28px — Streamlit không cho kiểm soát bố cục ở mức đó. Bản
bàn giao nói thẳng: thay bằng backend Python bọc ``LawLookup.ask()`` trong một
endpoint JSON, còn giao diện render riêng.

NGUYÊN TẮC GIỮ NGUYÊN
=====================
Mọi phép định dạng vẫn nằm ở ``presentation.py`` và đã có test. Tầng này chỉ
gọi xuống — không tự định dạng tiền, không tự tính ngưỡng tin cậy. Vì vậy
frontend nhận sẵn chuỗi đã định dạng thay vì phải dựng lại luật ở phía client.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator

from traffic_law.api.presentation import (
    KIND_NAMES,
    fine_text,
    penalty_lines,
    result_cards,
    summary_line,
)

GOC = Path(__file__).resolve().parents[3]
THU_MUC = Path(__file__).resolve().parent

#: Bảy màn hình của bản thiết kế, đúng thứ tự trong thanh bên.
NAV = [
    ("/", "Tra cứu", "search"),
    ("/khong-tim-thay", "Không tìm thấy", "alert-circle"),
    ("/dieu-khoan", "Chi tiết điều khoản", "file-text"),
    ("/hieu-luc", "Hiệu lực theo thời gian", "clock"),
    ("/chu-de", "Duyệt chủ đề", "layout-grid"),
    ("/chi-so", "Chỉ số đánh giá", "bar-chart-3"),
    ("/mobile", "Bản mobile", "smartphone"),
]

MIEN_TRU = ("Kết quả tra cứu mang tính tham khảo, không thay thế ý kiến của "
            "cơ quan có thẩm quyền.")

VI_DU_GOI_Y = [
    "Vượt đèn đỏ xe máy phạt bao nhiêu?",
    "Nồng độ cồn 0,3 mg/l phạt thế nào?",
    "Lỗi nào bị trừ 10 điểm giấy phép lái xe?",
]


@lru_cache(maxsize=1)
def he_thong() -> Any:
    """Nạp một lần cho cả tiến trình — dựng chỉ mục TF-IDF mất vài giây."""
    # Bo may suy dien la ban port nguyen van, co y khong gan chu thich kieu.
    from traffic_law.reasoning.engine import LawLookup

    return LawLookup()  # type: ignore[no-untyped-call]


@lru_cache(maxsize=4)
def _doc_json(duong_dan: str) -> Any:
    with (GOC / duong_dan).open(encoding="utf-8") as f:
        return json.load(f)


class CauHoi(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=10)

    @field_validator("question")
    @classmethod
    def _khong_chi_khoang_trang(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("câu hỏi không được để trống")
        return v.strip()


def _the_json(kq: dict[str, Any]) -> list[dict[str, Any]]:
    """Thẻ kết quả đã định dạng sẵn — frontend chỉ việc vẽ."""
    ra = []
    for t in result_cards(kq):
        goc: dict[str, Any] = next(
            (m for m in kq.get(t.kind) or [] if m.get("id") == t.id_), {})
        ra.append({
            "kind": t.kind, "kind_name": KIND_NAMES.get(t.kind, t.kind),
            "title": t.title, "lines": t.lines, "citation": t.citation,
            "score": t.score, "confidence": t.confidence,
            "supplementary": t.supplementary,
            "fine_text": fine_text(goc.get("fine")),
            "licence_points": goc.get("licence_points"),
            "vehicles": goc.get("vehicles") or [],
            "id": t.id_,
        })
    return ra


def _tra_cuu(cau_hoi: str, top_k: int = 5) -> dict[str, Any]:
    kq: dict[str, Any] = he_thong().ask(cau_hoi, top_k=top_k)
    kq["cards"] = _the_json(kq)
    kq["summary_line"] = summary_line(kq)
    return kq


def create_app() -> FastAPI:
    app = FastAPI(title="Tra cứu pháp luật giao thông đường bộ", docs_url="/api/docs")
    app.mount("/static", StaticFiles(directory=THU_MUC / "static"), name="static")
    tpl = Jinja2Templates(directory=str(THU_MUC / "templates"))
    tpl.env.globals.update(NAV=NAV, MIEN_TRU=MIEN_TRU, VI_DU=VI_DU_GOI_Y)

    def trang(request: Request, ten: str, **ctx: Any) -> HTMLResponse:
        return tpl.TemplateResponse(request, ten, {"hom_nay": date.today(), **ctx})

    # ------------------------------------------------------------------ API
    @app.post("/api/ask")
    def api_ask(ch: CauHoi) -> dict[str, Any]:
        return _tra_cuu(ch.question, ch.top_k)

    # -------------------------------------------------------------- màn hình
    @app.get("/", response_class=HTMLResponse)
    def man_tra_cuu(request: Request, q: str = "", top_k: int = 5) -> HTMLResponse:
        kq = _tra_cuu(q, top_k) if q.strip() else None
        return trang(request, "search.html", duong_dan="/", q=q, kq=kq, top_k=top_k)

    @app.get("/khong-tim-thay", response_class=HTMLResponse)
    def man_trong(request: Request) -> HTMLResponse:
        kq = _tra_cuu("cách nấu phở bò")
        return trang(request, "not_found.html", duong_dan="/khong-tim-thay", kq=kq,
                     q="cách nấu phở bò")

    @app.get("/dieu-khoan", response_class=HTMLResponse)
    def man_dieu_khoan_mac_dinh(request: Request) -> HTMLResponse:
        dau = he_thong().ask("vượt đèn đỏ xe máy phạt bao nhiêu", top_k=1)["violations"][0]
        return man_dieu_khoan(request, dau["id"])

    @app.get("/dieu-khoan/{ma}", response_class=HTMLResponse)
    def man_dieu_khoan(request: Request, ma: str) -> HTMLResponse:
        kb = he_thong().kb
        v = kb.by_id.get(ma)
        if v is None:
            raise HTTPException(status_code=404, detail=f"Không có điều khoản {ma}")
        cung_hanh_vi = [x for x in kb.violations
                        if x.behavior == v.behavior and x.id != v.id][:6]
        return trang(request, "provision.html", duong_dan="/dieu-khoan", v=v,
                     fine_text=fine_text, penalty_lines=penalty_lines,
                     cung_hanh_vi=cung_hanh_vi, kb=kb)

    @app.get("/hieu-luc", response_class=HTMLResponse)
    def man_hieu_luc(request: Request) -> HTMLResponse:
        kb = he_thong().kb
        sua = [v for v in kb.violations if v.amended_by][:12]
        return trang(request, "validity.html", duong_dan="/hieu-luc", sua=sua,
                     fine_text=fine_text)

    @app.get("/chu-de", response_class=HTMLResponse)
    def man_chu_de(request: Request, linh_vuc: str = "") -> HTMLResponse:
        kb = he_thong().kb
        dem_lv = Counter(v.field for v in kb.violations)
        nhom_theo_lv: dict[str, Counter[str]] = {}
        for v in kb.violations:
            nhom_theo_lv.setdefault(v.field, Counter())[v.group] += 1
        chon = linh_vuc or max(dem_lv, key=lambda k: dem_lv[k])
        return trang(request, "topics.html", duong_dan="/chu-de", dem_lv=dem_lv,
                     nhom_theo_lv=nhom_theo_lv, chon=chon, kb=kb)

    @app.get("/chi-so", response_class=HTMLResponse)
    def man_chi_so(request: Request) -> HTMLResponse:
        return trang(request, "metrics.html", duong_dan="/chi-so",
                     dg=_doc_json("eval/ket_qua_danh_gia.json")["summary"],
                     ab=_doc_json("eval/ket_qua_ablation.json"))

    @app.get("/mobile", response_class=HTMLResponse)
    def man_mobile(request: Request) -> HTMLResponse:
        return trang(request, "mobile.html", duong_dan="/mobile",
                     kq=_tra_cuu("vượt đèn đỏ xe máy phạt bao nhiêu", top_k=3))

    return app


app = create_app()
