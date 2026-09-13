"""Tầng web — FastAPI + Jinja, dựng theo bản bàn giao thiết kế 12 màn hình.

VÌ SAO KHÔNG DÙNG STREAMLIT
===========================
Bản thiết kế yêu cầu thanh bên cố định 252px, lưới hai cột, thẻ bo 28px và bản
mobile có thanh tab đáy — Streamlit không cho kiểm soát bố cục ở mức đó. Bản
bàn giao đề xuất bọc ``LawLookup.ask()`` trong một endpoint JSON và render riêng.

NGUYÊN TẮC GIỮ NGUYÊN
=====================
Mọi phép định dạng nằm ở ``presentation.py`` và đã có test. Tầng này chỉ gọi
xuống — không tự định dạng tiền, không tự tính ngưỡng tin cậy. Tầng suy diễn
KHÔNG bị sửa: lọc phương tiện và xem theo thời điểm là phép hậu xử lý trên
payload, nên chỉ số đánh giá (Top-1 76,67%) không thể bị ảnh hưởng.

ĐIỀU HƯỚNG
==========
Bản bàn giao chỉ có bốn mục: Tra cứu · Hiệu lực theo thời gian · Duyệt chủ đề ·
Chỉ số đánh giá. "Không tìm thấy" là một TRẠNG THÁI của Tra cứu, "Chi tiết điều
khoản" là màn con của Tra cứu; bản mobile là cùng các route ấy ở bề rộng hẹp.
"""
from __future__ import annotations

import json
import math
import time
from collections import Counter
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

from traffic_law.api.presentation import (
    AMENDMENT_KIND_NAMES,
    KIND_NAMES,
    MEDIUM_CONFIDENCE,
    VEHICLE_FILTERS,
    amendments_touching,
    as_of,
    clean_citation_text,
    confidence,
    diff_segments,
    filter_vehicles,
    fine_text,
    points_tail,
    position_label,
    problem_class_label,
    result_cards,
    short_citation,
    validity_timeline,
    vehicle_label,
    vi_decimal,
    vi_percent,
)

GOC = Path(__file__).resolve().parents[3]
THU_MUC = Path(__file__).resolve().parent


@dataclass(frozen=True)
class NavItem:
    href: str
    label: str
    short: str
    icon: str


#: Thứ tự thanh bên desktop.
NAV = (
    NavItem("/tra-cuu", "Tra cứu", "Tra cứu", "search"),
    NavItem("/hieu-luc", "Hiệu lực theo thời gian", "Hiệu lực", "clock"),
    NavItem("/chu-de", "Duyệt chủ đề", "Chủ đề", "layout-grid"),
    NavItem("/chi-so", "Chỉ số đánh giá", "Chỉ số", "bar-chart"),
)
#: Thanh tab đáy mobile dùng thứ tự khác — đúng như màn 07–12 của bản thiết kế.
TABS = (NAV[0], NAV[2], NAV[1], NAV[3])

MIEN_TRU = ("Kết quả tra cứu mang tính tham khảo, không thay thế ý kiến của "
            "cơ quan có thẩm quyền.")

#: Câu gợi ý lấy nguyên văn từ bộ 120 câu hỏi đánh giá (eval/qa_dataset.json).
VI_DU_GOI_Y = (
    "Vượt đèn đỏ xe máy phạt bao nhiêu?",
    "Nồng độ cồn 0,3 mg/l phạt thế nào?",
    "Lỗi nào bị trừ 10 điểm giấy phép lái xe?",
)

#: Tên ngắn của lĩnh vực cho hàng chip cuộn ngang trên mobile.
TEN_NGAN_LINH_VUC = {
    "LV_QUY_TAC": "Quy tắc", "LV_AN_TOAN": "An toàn", "LV_NGUOI_LAI": "Người lái",
    "LV_PHUONG_TIEN": "Phương tiện", "LV_VAN_TAI": "Vận tải", "LV_KHAC": "Khác",
}

VAN_BAN_GOC = "168/2024/NĐ-CP"
VAN_BAN_SUA_DOI = "Nghị định 238/2026/NĐ-CP"


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


def _thong_tin_nhom() -> dict[str, Any] | None:
    """Thông tin nhóm cho chân thanh bên, đọc từ ``docs/thanh_vien.json``.

    Thiếu tệp (ví dụ bản cài không kèm thư mục docs) thì bỏ khối này, không làm hỏng trang.
    """
    try:
        gt = _doc_json("docs/thanh_vien.json")
    except (OSError, ValueError):
        return None
    return gt if isinstance(gt, dict) else None


class CauHoi(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=10)
    as_of: date | None = None

    @field_validator("question")
    @classmethod
    def _khong_chi_khoang_trang(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("câu hỏi không được để trống")
        return v.strip()


# --------------------------------------------------------------------- dữ liệu
def _van_ban(ten: str) -> Any:
    """Văn bản trong documents.json có số hiệu nằm trong chuỗi căn cứ."""
    return next((d for d in he_thong().kb.documents if d.number in ten), None)


def _ngay_hieu_luc(ten: str) -> date:
    vb = _van_ban(ten)
    return vb.effective_from if vb else date.max


def _ten_linh_vuc(ma: str) -> str:
    gt: Any = he_thong().kb.field.get(ma)
    return str(gt.get("ten", ma)) if isinstance(gt, dict) else str(gt or ma)


def _nhom_cua_linh_vuc(ma: str) -> list[str]:
    gt: Any = he_thong().kb.field.get(ma)
    return list(gt.get("nhom", [])) if isinstance(gt, dict) else []


def _ten_nhom(ma: str) -> str:
    return str(he_thong().kb.group_name.get(ma, ma.replace("_", " ")))


def _linh_vuc_cua_nhom(ma: str) -> str:
    return next((lv for lv in he_thong().kb.field if ma in _nhom_cua_linh_vuc(lv)), "")


def _ngay(d: str | None) -> str:
    return f"{date.fromisoformat(d):%d/%m/%Y}" if d else ""


#: Việt Nam không đổi giờ theo mùa nên độ lệch cố định đủ dùng, và không phụ thuộc
#: gói tzdata (ảnh Docker slim không có).
GIO_VIET_NAM = timezone(timedelta(hours=7), "ICT")


def hom_nay() -> date:
    """"Hôm nay" theo giờ Việt Nam, không theo đồng hồ máy chủ (thường là UTC)."""
    return datetime.now(GIO_VIET_NAM).date()


def _giu_ngay(moc: date) -> list[tuple[str, str]]:
    """Tham số ``ngay`` chỉ xuất hiện khi khác hôm nay — URL mặc định gọn."""
    return [("ngay", moc.isoformat())] if moc != hom_nay() else []


def _url(path: str, keep: list[tuple[str, str]], **params: Any) -> str:
    """URL nội bộ giữ bộ lọc ``keep`` (thời điểm, phương tiện) cộng tham số riêng."""
    ts = [*keep, *[(k, v) for k, v in params.items() if v not in (None, "")]]
    return path + ("?" + urlencode(ts) if ts else "")


# ----------------------------------------------------------------- view model
def _the(kind: str, m: dict[str, Any], q: str,
         keep: list[tuple[str, str]] | None = None) -> dict[str, Any]:
    """Một thẻ kết quả đã định dạng sẵn — template chỉ việc vẽ."""
    diem = m.get("score")
    hl = m.get("validity") or {}
    href = _url(f"/dieu-khoan/{m.get('id')}", keep or [], q=q)
    return {
        "kind": kind, "kind_name": KIND_NAMES.get(kind, kind), "id": m.get("id", ""),
        "title": m.get("behavior") or m.get("name", ""),
        "body": m.get("definition") or m.get("text") or "",
        "attributes": list((m.get("attributes") or {}).items())[:4],
        "citation": m.get("citation_text", ""),
        "short_citation": short_citation(m.get("citation") or {}),
        "score": diem, "score_text": vi_decimal(diem, 2) if diem is not None else "",
        "confidence": confidence(diem),
        "supplementary": bool(m.get("supplementary")),
        "before_amendment": bool(m.get("shown_before_amendment")),
        "vehicles": m.get("vehicles") or [],
        "vehicle_label": vehicle_label(m.get("vehicles") or [], m.get("subject") or ""),
        "fine_text": fine_text(m.get("fine")),
        # Ví dụ mức phạt riêng cho tổ chức — không được giấu sau khoảng của cá nhân.
        "fine_note": (m.get("fine") or {}).get("note") or "",
        "licence_points": m.get("licence_points"),
        "points_tail": points_tail(m.get("licence_points")),
        "valid_from": _ngay(hl.get("start")),
        "href": href if kind == "violations" else "",
    }


def _diem_cao_nhat(phan_tich: dict[str, Any]) -> float:
    """Điểm tốt nhất trên cả ba loại tri thức — để giải thích VÌ SAO không tìm thấy.

    Gọi lại bộ xếp hạng của tầng suy diễn chỉ để ĐỌC điểm; không đổi kết quả.
    """
    eng, kb = he_thong().engine, he_thong().kb
    diem = [sc for sc, _, _ in eng._rank_violations(phan_tich, top_k=1)]
    diem += [sc for sc, _ in eng._rank(phan_tich, "concept", kb.concepts, 1)]
    diem += [sc for sc, _ in eng._rank(phan_tich, "rule", kb.rules, 1)]
    return math.floor(float(max(diem, default=0.0)) * 100) / 100


def _tra_cuu(cau_hoi: str, top_k: int, moc: date, phuong_tien: list[str]) -> dict[str, Any]:
    """Gọi bộ máy rồi hậu xử lý: xem tại thời điểm ``moc``, lọc phương tiện."""
    bat_dau = time.perf_counter()
    kq: dict[str, Any] = he_thong().ask(cau_hoi, top_k=top_k)
    kq["elapsed_ms"] = (time.perf_counter() - bat_dau) * 1000

    loai = ("violations", "rules", "concepts")
    tong_truoc_loc = sum(len(kq[k]) for k in loai)
    kq["violations"] = filter_vehicles(as_of(kq["violations"], moc), phuong_tien)
    kq["rules"] = as_of(kq["rules"], moc, text_key="text", before_key="text_before_amendment")
    kq["knowledge_count"] = sum(len(kq[k]) for k in loai)
    kq["filtered_out"] = (not kq["not_found"] and kq["knowledge_count"] == 0
                          and tong_truoc_loc > 0)
    return kq


def _ket_qua_view(kq: dict[str, Any], q: str,
                  keep: list[tuple[str, str]] | None = None) -> dict[str, Any]:
    from traffic_law.reasoning.engine import SUPPLEMENT_THRESHOLD

    kb = he_thong().kb
    phan_tich = kq["analysis"]
    the = [_the(t.kind, next(m for m in kq[t.kind] if m.get("id") == t.id_), q, keep)
           for t in result_cards(kq)]
    diem_dau = the[0]["score"] if the else None
    nhom = phan_tich["group"] or phan_tich["inferred_groups"]
    return {
        "cards": the,
        "class_label": f"{kq['problem_class'][:2]} · {kq['problem_class_name']}",
        "class_short": problem_class_label(kq["problem_class"]),
        "elapsed": vi_decimal(kq["elapsed_ms"], 1) + " ms",
        "low_confidence": diem_dau is not None and diem_dau < MEDIUM_CONFIDENCE,
        "analysis": [
            ("Cụm từ khoá", ", ".join(k["phrase"] for k in phan_tich["keyphrase"]) or "—"),
            ("Phương tiện nhận diện",
             ", ".join(kb.vehicle_names.get(p, p).lower() for p in phan_tich["vehicles"])
             or "—"),
            ("Nhóm", ", ".join(_ten_nhom(n) for n in nhom) or "—"),
            ("Chủ thể", kb.subject_names.get(phan_tich["subject"], "—")
             if phan_tich["subject"] else "—"),
        ],
        "related": [{"name": g["name"], "count": g["so_quy_dinh"],
                     "href": _url("/chu-de", keep or [], linh_vuc=_linh_vuc_cua_nhom(g["code"]),
                                  nhom=g["code"])}
                    for g in kq["related"]],
        "threshold": vi_decimal(SUPPLEMENT_THRESHOLD, 2),
        "best_score": vi_decimal(_diem_cao_nhat(phan_tich), 2) if kq["not_found"] else "",
    }


def _hang_vi_pham(v: Any) -> dict[str, Any]:
    """Một dòng hành vi cho danh sách nhóm và các bảng — từ mô hình có kiểu."""
    return {
        "id": v.id, "behavior": v.behavior, "vehicles": v.vehicles,
        "vehicle_label": vehicle_label(v.vehicles, v.subject),
        "fine_text": fine_text(v.fine.model_dump()),
        "points": f"{v.licence_points} điểm" if v.licence_points else "—",
        "short_citation": short_citation(v.citation.model_dump()),
        "citation": v.citation_text,
    }


def _nhan_sua_doi(v: Any) -> tuple[str, str]:
    """(nhãn, sắc thái pill) của điều khoản bị văn bản sửa đổi chạm tới."""
    return ("Sửa đổi", "neutral") if v.behavior_before_amendment else ("Bổ sung", "green")


# ------------------------------------------------------------------------ app
@asynccontextmanager
async def _nap_truoc(_: FastAPI) -> AsyncIterator[None]:
    """Nạp cơ sở tri thức lúc khởi động, để lượt tra đầu tiên không gánh vài giây
    dựng chỉ mục — nếu không, số "ms" trên dải phân lớp sẽ đo sai."""
    he_thong()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Tra cứu pháp luật giao thông đường bộ", docs_url="/api/docs",
                  lifespan=_nap_truoc)
    app.mount("/static", StaticFiles(directory=THU_MUC / "static"), name="static")
    tpl = Jinja2Templates(directory=str(THU_MUC / "templates"))
    tpl.env.globals.update(NAV=NAV, TABS=TABS, MIEN_TRU=MIEN_TRU, VI_DU=VI_DU_GOI_Y)
    # Ô số liệu hẹp: khi khoảng phạt phải xuống dòng, đừng để "đ" rơi một mình.
    tpl.env.filters["giu_don_vi"] = lambda s: str(s).replace(" đ", "\u00a0đ")

    def trang_thai(request: Request) -> tuple[date, list[str]]:
        """Bộ lọc dùng chung ở thanh bên: ``ngay`` (ISO) và ``pt`` (lặp lại)."""
        try:
            moc = date.fromisoformat(request.query_params.get("ngay", ""))
        except ValueError:
            moc = hom_nay()
        hop_le = {f.key for f in VEHICLE_FILTERS}
        return moc, [p for p in request.query_params.getlist("pt") if p in hop_le]

    def trang(request: Request, ten: str, section: str, status_code: int = 200,
              **ctx: Any) -> HTMLResponse:
        moc, pt = trang_thai(request)
        giu = _giu_ngay(moc)
        khac = [(k, v) for k, v in request.query_params.multi_items() if k not in ("pt", "ngay")]

        def href(path: str, **params: Any) -> str:
            """Link nội bộ giữ nguyên thời điểm tra cứu và bộ lọc phương tiện."""
            return _url(path, [*giu, *[("pt", p) for p in pt]], **params)

        chips = []
        for f in VEHICLE_FILTERS:
            bat = f.key in pt
            moi = [p for p in pt if p != f.key] if bat else [*pt, f.key]
            ts = [*khac, *giu, *[("pt", p) for p in moi]]
            chips.append({"label": f.label, "on": bat,
                          "href": request.url.path + ("?" + urlencode(ts) if ts else "")})

        return tpl.TemplateResponse(request, ten, {
            "section": section, "href": href, "chips": chips,
            "moc": moc, "moc_text": f"{moc:%d/%m/%Y}", "pt": pt, "custom_date": bool(giu),
            "keep_params": [*giu, *[("pt", p) for p in pt]],
            "hidden_params": [(k, v) for k, v in request.query_params.multi_items()
                              if k != "ngay"],
            "amendment_applied": moc >= _ngay_hieu_luc(VAN_BAN_SUA_DOI),
            "amending_doc": VAN_BAN_SUA_DOI,
            "team": _thong_tin_nhom(),
            "stats": {k: f"{n:,}".replace(",", ".") for k, n in he_thong().stats().items()},
            **ctx,
        }, status_code=status_code)

    @app.exception_handler(StarletteHTTPException)
    async def loi_http(request: Request, exc: StarletteHTTPException) -> Response:
        """Trình duyệt gặp 404 thì nhận trang HTML có điều hướng, API vẫn nhận JSON."""
        if exc.status_code == 404 and "text/html" in request.headers.get("accept", ""):
            dieu_khoan = request.url.path.startswith("/dieu-khoan/")
            return trang(request, "error.html", "/tra-cuu" if dieu_khoan else "", status_code=404,
                         heading="Không tìm thấy điều khoản" if dieu_khoan
                         else "Không tìm thấy trang",
                         message="Mã tri thức này không có trong cơ sở tri thức." if dieu_khoan
                         else "Đường dẫn không tồn tại.")
        return await http_exception_handler(request, exc)

    # ------------------------------------------------------------------ API
    @app.post("/api/ask")
    def api_ask(ch: CauHoi) -> dict[str, Any]:
        """Payload nguyên của ``LawLookup.ask()`` kèm thẻ đã định dạng sẵn."""
        kq = _tra_cuu(ch.question, ch.top_k, ch.as_of or hom_nay(), [])
        kq["cards"] = _ket_qua_view(kq, ch.question)["cards"]
        return kq

    # -------------------------------------------------------------- màn hình
    @app.get("/")
    def goc(request: Request) -> RedirectResponse:
        qs = request.url.query
        return RedirectResponse("/tra-cuu" + (f"?{qs}" if qs else ""), status_code=307)

    @app.get("/tra-cuu", response_class=HTMLResponse)
    def man_tra_cuu(request: Request, q: str = "", top_k: int = 5) -> HTMLResponse:
        moc, pt = trang_thai(request)
        q = q[:500]
        keep = [*_giu_ngay(moc), *[("pt", p) for p in pt]]
        kq = _tra_cuu(q.strip(), min(max(top_k, 1), 10), moc, pt) if q.strip() else None
        return trang(request, "search.html", "/tra-cuu", q=q, kq=kq,
                     view=_ket_qua_view(kq, q, keep) if kq else None)

    @app.get("/dieu-khoan/{ma}", response_class=HTMLResponse)
    def man_dieu_khoan(request: Request, ma: str, q: str = "") -> HTMLResponse:
        moc, _ = trang_thai(request)
        kb = he_thong().kb
        v = kb.by_id.get(ma)
        if v is None:
            raise HTTPException(status_code=404, detail=f"Không có điều khoản {ma}")

        vb_goc = _van_ban(v.citation.documents)
        goc_hl = vb_goc.effective_from if vb_goc else None
        start = v.validity.start if v.validity else (goc_hl or moc)
        # Bản ghi sửa đổi có phạm vi bao trùm điều khoản nhưng chưa gắn vào nó (ví dụ
        # bãi bỏ ghi ở cấp khoản) — chỉ khi KHÔNG có mới được nói "không sửa".
        cham = [] if v.amended_by else [
            f"{AMENDMENT_KIND_NAMES.get(a['kind'], a['kind'])}"
            f"{': ' + a['note'] if a.get('note') else ''}"
            for a in amendments_touching([a.model_dump() for a in kb.amendments],
                                         v.citation.model_dump())]
        timeline = validity_timeline(
            start=start, end=v.validity.end if v.validity else None, origin=goc_hl or start,
            origin_doc=v.citation.documents, amended_by=v.amended_by,
            has_before=bool(v.behavior_before_amendment),
            amending_docs=vb_goc.amended_by if vb_goc else [], moc=moc, touching=cham)

        # Xem tại mốc trước khi phiên bản hiện hành có hiệu lực: hiện câu chữ lúc ấy.
        truoc_hieu_luc = moc < start
        het_hieu_luc = v.validity is not None and v.validity.end is not None \
            and moc > v.validity.end
        if het_hieu_luc:
            tieu_de, tinh_trang = v.behavior, ("Hết hiệu lực", "neutral")
        elif truoc_hieu_luc and v.behavior_before_amendment:
            tieu_de, tinh_trang = v.behavior_before_amendment, ("Câu chữ trước sửa đổi", "neutral")
        elif truoc_hieu_luc:
            tieu_de, tinh_trang = v.behavior, ("Chưa có hiệu lực", "neutral")
        elif v.amended_by:
            tieu_de, tinh_trang = v.behavior, _nhan_sua_doi(v)
        elif cham:
            tieu_de, tinh_trang = v.behavior, ("Cần đối chiếu sửa đổi", "neutral")
        else:
            tieu_de, tinh_trang = v.behavior, ("Hiện hành", "green")

        cung = sorted((x for x in kb.violations if x.behavior == v.behavior),
                      key=lambda x: (x.citation.article or 0, str(x.citation.clause)))
        return trang(
            request, "provision.html", "/tra-cuu", q=q,
            v=v, row=_hang_vi_pham(v), timeline=timeline, title=tieu_de,
            viewing_past=truoc_hieu_luc, valid_from=f"{start:%d/%m/%Y}",
            expired=het_hieu_luc,
            valid_until=f"{v.validity.end:%d/%m/%Y}" if v.validity and v.validity.end else "",
            status=tinh_trang,
            position=position_label(v.citation.model_dump()),
            field_name=_ten_linh_vuc(v.field), group_name=v.group_name or _ten_nhom(v.group),
            scope_vehicles=", ".join(kb.vehicle_names.get(p, p).lower()
                                     for p in v.vehicles).capitalize() or "—",
            subject=kb.subject_names.get(v.subject, "—") if v.subject else "—",
            extra=", ".join(v.extra_penalties) or "Không có",
            same_behaviour=[{**_hang_vi_pham(x), "current": x.id == v.id} for x in cung]
            if len(cung) > 1 else [],
        )

    @app.get("/hieu-luc", response_class=HTMLResponse)
    def man_hieu_luc(request: Request, dk: str = "") -> HTMLResponse:
        moc, _ = trang_thai(request)
        kb = he_thong().kb
        ngay_sua = _ngay_hieu_luc(VAN_BAN_SUA_DOI)
        ngay_goc = _ngay_hieu_luc(VAN_BAN_GOC)

        cham = sorted((v for v in kb.violations if v.amended_by),
                      key=lambda v: (v.citation.article or 0, str(v.citation.clause),
                                     v.citation.point or ""))
        rows = [{**_hang_vi_pham(v), "kind": _nhan_sua_doi(v), "selected": False,
                 # Điều khoản bổ sung chưa tồn tại trước ngày sửa đổi có hiệu lực.
                 "in_force": bool(v.behavior_before_amendment) or v.validity is None
                             or v.validity.in_force_on(moc),
                 "href": "/hieu-luc?" + urlencode([*_giu_ngay(moc), ("dk", v.id)]) + "#so-sanh"}
                for v in cham]

        # Mặc định chọn điều khoản bị SỬA có câu chữ ngắn nhất — dễ đọc nhất.
        co_truoc = [v for v in cham if v.behavior_before_amendment]
        chon = next((v for v in cham if v.id == dk), None) or min(
            co_truoc, key=lambda v: len(v.behavior) + len(v.behavior_before_amendment),
            default=None)

        so_sanh = None
        if chon is not None:
            for r in rows:
                r["selected"] = r["id"] == chon.id
            bat_dau = chon.validity.start if chon.validity else ngay_sua
            khop = [a for a in kb.amendments
                    if (a.decree_article, str(a.decree_clause), a.decree_point)
                    == (chon.citation.article, str(chon.citation.clause), chon.citation.point)]
            # Chỉ ghi "không đổi" khi MỌI bản ghi sửa đổi khớp đều không đụng tới chế tài.
            khong_doi = " · không đổi" if khop and all(
                a.fine is None and a.licence_points is None for a in khop) else ""
            so_sanh = {
                "citation": chon.citation_text, "status": _nhan_sua_doi(chon),
                "text": chon.behavior,
                "diff": diff_segments(chon.behavior_before_amendment, chon.behavior)
                if chon.behavior_before_amendment else None,
                "before_label": f"{ngay_goc:%d/%m/%Y} – {bat_dau - timedelta(days=1):%d/%m/%Y}",
                "after_label": f"Từ {bat_dau:%d/%m/%Y}",
                "after_active": moc >= bat_dau,
                "fine": fine_text(chon.fine.model_dump()) + khong_doi,
                "points": (f"{chon.licence_points} điểm" if chon.licence_points
                           else "Không trừ điểm") + khong_doi,
                "amended_by": clean_citation_text(chon.amended_by),
            }

        return trang(
            request, "validity.html", "/hieu-luc", rows=rows, compare=so_sanh,
            moc_options=[{"text": f"{d:%d/%m/%Y}", "on": d == moc,
                          "href": "/hieu-luc?" + urlencode(
                              [*_giu_ngay(d), *([("dk", dk)] if dk else [])])}
                         for d in sorted({ngay_goc, moc, hom_nay()})],
            notes=sorted({f"{r['short_citation']}: {v.fine.note}"
                          for r, v in zip(rows, cham, strict=True) if v.fine.note}),
        )

    @app.get("/chu-de", response_class=HTMLResponse)
    def man_chu_de(request: Request, linh_vuc: str = "", nhom: str = "") -> HTMLResponse:
        moc, pt = trang_thai(request)
        kb = he_thong().kb
        dem_lv = Counter(v.field for v in kb.violations)
        dem_nhom = Counter(v.group for v in kb.violations)
        if nhom in dem_nhom:
            # Nhóm quyết định lĩnh vực: tránh chip của lĩnh vực này đè danh sách nhóm khác.
            linh_vuc = _linh_vuc_cua_nhom(nhom)
        keep = [*_giu_ngay(moc), *[("pt", p) for p in pt]]
        chon = linh_vuc if linh_vuc in dem_lv else max(dem_lv, key=lambda k: dem_lv[k])

        # Đếm nhóm CÓ hành vi: taxonomy khai báo cả nhóm rỗng ("via_he"), mà tiêu đề
        # "N nhóm" phải khớp số chip hiện bên dưới.
        def so_nhom(lv: str) -> int:
            return sum(1 for g in _nhom_cua_linh_vuc(lv) if dem_nhom[g])

        fields = [{"code": lv, "name": _ten_linh_vuc(lv), "short": TEN_NGAN_LINH_VUC.get(lv, lv),
                   "count": n, "groups": so_nhom(lv), "on": lv == chon,
                   "href": _url("/chu-de", keep, linh_vuc=lv)}
                  for lv, n in dem_lv.most_common()]
        groups = [{"code": g, "name": _ten_nhom(g), "count": dem_nhom[g], "on": g == nhom,
                   "href": _url("/chu-de", keep, linh_vuc=chon, nhom=g) + "#nhom"}
                  for g in sorted(_nhom_cua_linh_vuc(chon), key=lambda g: -dem_nhom[g])
                  if dem_nhom[g]]

        hanh_vi: list[dict[str, Any]] = []
        if nhom in dem_nhom:
            items = [v.model_dump(mode="json") for v in kb.by_nhom[nhom]]
            giu = {x["id"] for x in filter_vehicles(as_of(items, moc), pt)}
            hanh_vi = [_hang_vi_pham(v) for v in kb.by_nhom[nhom] if v.id in giu]
        return trang(
            request, "topics.html", "/chu-de", fields=fields, groups=groups,
            field=next(f for f in fields if f["on"]), group=nhom if nhom in dem_nhom else "",
            group_name=_ten_nhom(nhom) if nhom in dem_nhom else "",
            group_total=dem_nhom.get(nhom, 0), violations=hanh_vi,
            total=len(kb.violations),
            total_groups=len(dem_nhom),
        )

    @app.get("/chi-so", response_class=HTMLResponse)
    def man_chi_so(request: Request) -> HTMLResponse:
        dg = _doc_json("eval/ket_qua_danh_gia.json")["summary"]
        ab = _doc_json("eval/ket_qua_ablation.json")
        so = list(ab.get("cau_hoi_co_gia_tri_so", {}).values())
        numeric = ({"n": ab.get("so_cau_hoi_co_so"), "before": vi_decimal(so[0]["top1"], 2),
                    "after": vi_decimal(so[-1]["top1"], 2)} if len(so) >= 2 else None)
        toan_bo = list(ab.get("toan_bo", {}).values())
        buoc_so = (vi_decimal(toan_bo[-1]["top1"] - toan_bo[-2]["top1"], 2)
                   if len(toan_bo) >= 2 else "")
        return trang(
            request, "metrics.html", "/chi-so", dg=dg, numeric=numeric, numeric_gain=buoc_so,
            boxes=[("Phân lớp bài toán", "Phân lớp bài toán",
                    vi_percent(dg["do_chinh_xac_phan_lop"]), "dark"),
                   ("Truy hồi Top-1", "Top-1", vi_percent(dg["top1"]), ""),
                   ("Truy hồi Top-5", "Top-5", vi_percent(dg["top5"]), ""),
                   ("MRR", "MRR", vi_decimal(dg["mrr"], 4), "green"),
                   ("Thời gian trả lời", "Trả lời",
                    vi_decimal(dg["thoi_gian_tb_ms"], 1) + " ms", "")],
            classes=[{"label": problem_class_label(lop), "short": problem_class_label(lop, True),
                      "n": g["n"], "pl": vi_percent(g["acc_phan_lop"]),
                      "t1": vi_percent(g["top1"]), "t5": vi_percent(g["top5"]),
                      "t5_width": round(g["top5"] * 100, 2),
                      "t5_short": "100" if g["top5"] >= 1 else vi_decimal(g["top5"] * 100, 1)}
                     for lop, g in dg["theo_lop_bai_toan"].items()],
            ablation=[{"label": ten.replace(". ", " · ", 1), "width": round(g["top1"], 2),
                       "value": vi_decimal(g["top1"], 2) + "%"}
                      for ten, g in ab.get("toan_bo", {}).items()],
            precision=vi_decimal(dg["precision_macro"], 4),
            precision_cap=vi_decimal(1 / dg["top_k"], 2),
        )

    return app


app = create_app()
