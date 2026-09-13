"""Tầng trình bày — biến kết quả suy diễn thành thứ vẽ được lên màn hình.

Toàn bộ phần CÓ THỂ SAI nằm ở đây dưới dạng hàm thuần: định dạng tiền, gom kết
quả, xếp mức tin cậy. ``app.py`` chỉ là vỏ Streamlit mỏng gọi xuống, nhờ vậy
kiểm thử được mà không cần dựng khung chạy Streamlit.

Không import ``streamlit`` trong tệp này.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

#: Ngưỡng quy điểm thô thành nhãn đọc được. Điểm 0.9816 không nói gì với người
#: tra luật; "độ tin cậy cao" thì có.
HIGH_CONFIDENCE = 0.80
MEDIUM_CONFIDENCE = 0.60

#: Thứ tự ưu tiên hiển thị: chế tài trước (thứ người ta hỏi nhiều nhất), rồi
#: quy định, cuối cùng là khái niệm nền.
KIND_ORDER = ("violations", "rules", "concepts")

KIND_NAMES = {
    "violations": "Hành vi vi phạm",
    "rules": "Quy định",
    "concepts": "Khái niệm",
}


@dataclass(frozen=True)
class Card:
    """Một thẻ kết quả đã sẵn sàng để vẽ."""

    kind: str
    #: Định danh tri thức — giao diện cần nó để trỏ tới màn Chi tiết điều khoản.
    id_: str
    title: str
    lines: list[str] = field(default_factory=list)
    citation: str = ""
    score: float | None = None
    supplementary: bool = False

    @property
    def confidence(self) -> str:
        return confidence(self.score)


def format_money(n: int | None) -> str:
    """1500000 -> '1.500.000 đồng' (dấu chấm ngăn nghìn, kiểu Việt Nam)."""
    if n is None:
        return "0 đồng"
    return f"{n:,.0f}".replace(",", ".") + " đồng"


def confidence(point: float | None) -> str:
    """Quy điểm thô thành nhãn. Thiếu điểm thì coi là thấp, không nổ lỗi."""
    if point is None:
        return "thấp"
    if point >= HIGH_CONFIDENCE:
        return "cao"
    if point >= MEDIUM_CONFIDENCE:
        return "trung bình"
    return "thấp"


def penalty_lines(v: dict[str, Any]) -> list[str]:
    """Các dòng chế tài của một hành vi vi phạm, đã viết thành câu tiếng Việt."""
    pt = v.get("fine") or {}
    mn, mx = pt.get("min"), pt.get("max")
    lines: list[str] = []

    if mn is None and mx is None:
        lines.append("Không quy định phạt tiền")
    elif mn == mx == 0:
        lines.append("Không phạt tiền (cảnh cáo hoặc hình thức khác)")
    elif mn == mx:
        lines.append(f"Phạt tiền: {format_money(mn)}")
    else:
        lines.append(f"Phạt tiền: từ {format_money(mn)} đến {format_money(mx)}")

    if v.get("licence_points"):
        lines.append(f"Trừ {v['licence_points']} điểm giấy phép lái xe")
    for x in v.get("extra_penalties") or []:
        lines.append(f"Hình phạt bổ sung: {x}")
    for x in v.get("remedies") or []:
        lines.append(f"Biện pháp khắc phục: {x}")
    return lines


def _card_from_item(kind: str, m: dict[str, Any]) -> Card:
    if kind == "violations":
        title, lines = m.get("behavior", ""), penalty_lines(m)
    elif kind == "rules":
        title = m.get("name", "")
        lines = [m["text"]] if m.get("text") else []
    else:
        title = m.get("name", "")
        lines = [m["definition"]] if m.get("definition") else [
            f"{k}: {gt}" for k, gt in list((m.get("attributes") or {}).items())[:6]]
    return Card(kind=kind, id_=m.get("id", ""), title=title, lines=lines,
               citation=m.get("citation_text", ""), score=m.get("score"),
               supplementary=bool(m.get("supplementary")))


def result_cards(kq: dict[str, Any]) -> list[Card]:
    """Gom ba loại tri thức thành một danh sách thẻ theo thứ tự ưu tiên."""
    return [_card_from_item(kind, m) for kind in KIND_ORDER for m in kq.get(kind) or []]


def summary_line(kq: dict[str, Any]) -> str:
    """Một dòng tóm tắt đặt ngay dưới ô tìm kiếm."""
    if kq.get("not_found"):
        return ("Không tìm thấy quy định phù hợp trong cơ sở tri thức. "
                "Thử diễn đạt lại câu hỏi hoặc nêu rõ loại phương tiện.")
    so = sum(len(kq.get(kind) or []) for kind in KIND_ORDER)
    return f"{kq.get('problem_class_name', 'Tra cứu')} · {so} mẩu tri thức"


def fine_text(fine: dict[str, Any] | None) -> str:
    """Khung phạt tiền viết gọn cho giao diện web.

    Khác ``penalty_lines``: bản thiết kế rút hậu tố "đồng" thành "đ" và dùng
    en dash cho khoảng, để số liệu vừa trong ô chỉ rộng 210px.
    """
    fine = fine or {}
    lo, hi = fine.get("min"), fine.get("max")
    if lo is None and hi is None:
        return "Không quy định phạt tiền"
    if lo == hi == 0:
        return "Không phạt tiền (cảnh cáo hoặc hình thức khác)"
    if lo == hi:
        return f"{format_money(lo)}".replace(" đồng", "") + " đ"
    return (f"{format_money(lo)}".replace(" đồng", "") + " – "
            + f"{format_money(hi)}".replace(" đồng", "") + " đ")


# ---------------------------------------------------------------------------
# Các hàm dưới đây phục vụ bản bàn giao thiết kế 12 màn hình. Cùng nguyên tắc:
# định dạng nằm ở đây, template chỉ việc in ra.
# ---------------------------------------------------------------------------

def vi_decimal(x: float, digits: int) -> str:
    """0.8384 -> '0,8384': số thập phân kiểu Việt Nam dùng dấu phẩy."""
    return f"{x:.{digits}f}".replace(".", ",")


def vi_percent(ratio: float) -> str:
    """0.9583 -> '95,83%'. Đúng 100% thì ghi gọn '100%' như bản thiết kế."""
    if round(ratio * 100, 2) == 100:
        return "100%"
    return vi_decimal(ratio * 100, 2) + "%"


#: Tên ngắn dùng trên pill — tên đầy đủ trong taxonomy ("Xe mô tô") quá dài để
#: ghép hai ba phương tiện vào một pill 11px.
VEHICLE_SHORT_NAMES = {
    "mo_to": "mô tô", "xe_gan_may": "xe gắn máy", "o_to": "ô tô",
    "xe_dap": "xe đạp", "xe_tho_so": "xe thô sơ",
    "xe_may_chuyen_dung": "xe máy chuyên dùng",
}

SUBJECT_NAMES = {
    "nguoi_dieu_khien": "người điều khiển", "chu_phuong_tien": "chủ phương tiện",
    "nguoi_di_bo": "người đi bộ", "hanh_khach": "hành khách", "ca_nhan": "cá nhân, tổ chức",
}


def _capitalise(s: str) -> str:
    return s[:1].upper() + s[1:]


def vehicle_label(codes: list[str], subject: str = "") -> str:
    """['mo_to', 'xe_gan_may'] -> 'Mô tô, xe gắn máy'.

    Lỗi không gắn phương tiện (người đi bộ, chủ xe là tổ chức...) lấy chủ thể làm
    nhãn, để pill luôn trả lời được câu "áp dụng cho ai".
    """
    names = [VEHICLE_SHORT_NAMES[c] for c in codes if c in VEHICLE_SHORT_NAMES]
    if not names and subject:
        names = [SUBJECT_NAMES.get(subject, subject.replace("_", " "))]
    return _capitalise(", ".join(names))


def short_citation(citation: dict[str, Any]) -> str:
    """Căn cứ viết gọn cho bảng và bản mobile: 'Điều 6 k9 điểm b'."""
    parts = [f"Điều {citation.get('article')}"]
    if citation.get("clause") is not None:
        parts.append(f"k{citation['clause']}")
    if citation.get("point"):
        parts.append(f"điểm {citation['point']}")
    return " ".join(parts)


def position_label(citation: dict[str, Any]) -> str:
    """Vị trí điều khoản cho pill: 'Điều 7 · khoản 7 · điểm c'."""
    parts = [f"Điều {citation.get('article')}"]
    if citation.get("clause") is not None:
        parts.append(f"khoản {citation['clause']}")
    if citation.get("point"):
        parts.append(f"điểm {citation['point']}")
    return " · ".join(parts)


def points_tail(points: int | None) -> str:
    """Đuôi mức phạt trên thẻ phụ. Không trừ điểm cũng phải nói ra."""
    return f"trừ {points} điểm giấy phép lái xe" if points else "không trừ điểm"


#: Nhãn lớp bài toán cho bảng chỉ số và bản mobile (dạng dài, dạng ngắn).
#: Tên đầy đủ nằm ở ``PROBLEM_CLASS_NAMES`` của tầng suy diễn.
PROBLEM_CLASS_LABELS = {
    "P1": ("Tra cứu khái niệm", "Khái niệm"),
    "P2": ("Tra cứu quy định", "Quy định"),
    "P3": ("Tra cứu chế tài", "Chế tài"),
    "P4": ("Tra cứu ngược", "Tra ngược"),
    "P5": ("Suy diễn tình huống", "Tình huống"),
    "P6": ("Tra cứu theo căn cứ", "Căn cứ"),
    "P7": ("Tra cứu liên quan", "Liên quan"),
}


def problem_class_label(code: str, short: bool = False) -> str:
    """'P3_TRA_CUU_CHE_TAI' -> 'P3 · Tra cứu chế tài' (hoặc 'P3 · Chế tài')."""
    ma = code[:2]
    names = PROBLEM_CLASS_LABELS.get(ma)
    return f"{ma} · {names[1 if short else 0]}" if names else ma


@dataclass(frozen=True)
class Diff:
    """Hai phiên bản câu chữ tách thành phần chung và phần khác nhau."""

    prefix: str
    before: str
    after: str
    suffix: str


_TOKEN = re.compile(r"\w+|\s+|[^\w\s]")


def diff_segments(before: str, after: str) -> Diff:
    """Tách phần chung đầu/cuối theo ranh giới từ để tô nền phần bị sửa.

    Cố ý chỉ tách MỘT đoạn khác nhau thay vì dò từng từ: sửa đổi của nghị định là
    "thay thế cụm từ A bằng cụm từ B", nên một đoạn liền đọc đúng ý văn bản hơn
    một loạt mảnh vụn tô nền xen kẽ.
    """
    a, b = _TOKEN.findall(before), _TOKEN.findall(after)
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    j = 0
    while j < min(len(a), len(b)) - i and a[-1 - j] == b[-1 - j]:
        j += 1
    return Diff(prefix="".join(a[:i]), before="".join(a[i:len(a) - j]),
                after="".join(b[i:len(b) - j]), suffix="".join(a[len(a) - j:]))


@dataclass(frozen=True)
class VehicleFilter:
    """Một chip lọc ở thanh bên: nhãn, mã phương tiện và chủ thể khớp."""

    key: str
    label: str
    vehicles: frozenset[str]
    subjects: frozenset[str] = frozenset()


VEHICLE_FILTERS = (
    VehicleFilter("mo_to", "Mô tô, xe gắn máy", frozenset({"mo_to", "xe_gan_may"})),
    VehicleFilter("o_to", "Ô tô", frozenset({"o_to"})),
    VehicleFilter("xe_dap", "Xe đạp", frozenset({"xe_dap", "xe_tho_so"})),
    VehicleFilter("di_bo", "Người đi bộ", frozenset(), frozenset({"nguoi_di_bo"})),
)


def filter_vehicles(items: list[dict[str, Any]], selected: list[str]) -> list[dict[str, Any]]:
    """Giữ hành vi khớp BẤT KỲ chip nào đang chọn. Không chọn gì thì giữ nguyên."""
    chosen = [f for f in VEHICLE_FILTERS if f.key in selected]
    if not chosen:
        return list(items)
    return [x for x in items
            if any(f.vehicles & set(x.get("vehicles") or []) or x.get("subject") in f.subjects
                   for f in chosen)]


def as_of(items: list[dict[str, Any]], moc: date, text_key: str = "behavior",
          before_key: str = "behavior_before_amendment") -> list[dict[str, Any]]:
    """Kết quả tra cứu nhìn tại mốc thời gian ``moc``.

    Cơ sở tri thức chỉ lưu bản HIỆN HÀNH của điều khoản bị sửa, kèm câu chữ cũ.
    Nên trước ngày sửa đổi: điều khoản có câu chữ cũ thì hiện lại câu chữ cũ,
    điều khoản bổ sung (không có câu chữ cũ) thì chưa tồn tại. Không sửa payload
    gốc của bộ máy. Quy tắc lưu câu chữ ở ``text``/``text_before_amendment``.
    """
    ra: list[dict[str, Any]] = []
    for x in items:
        hl = x.get("validity")
        if not hl:
            ra.append(x)
            continue
        start = date.fromisoformat(hl["start"])
        end = date.fromisoformat(hl["end"]) if hl.get("end") else None
        if end is not None and moc > end:
            continue
        if moc >= start:
            ra.append(x)
        elif x.get(before_key):
            ra.append({**x, text_key: x[before_key], "shown_before_amendment": True})
    return ra


@dataclass(frozen=True)
class Milestone:
    """Một mốc trên timeline hiệu lực; ``reached`` = đã tới tính đến mốc tra cứu."""

    date_text: str
    caption: str
    reached: bool


_THIEU_CAN_CU = re.compile(r" (khoản|điểm) None\b")


def clean_citation_text(s: str) -> str:
    """'... Điều 3 khoản None' -> '... Điều 3': dữ liệu nguồn ghép cả trường rỗng."""
    return _THIEU_CAN_CU.sub("", s)


AMENDMENT_KIND_NAMES = {"sua_doi": "Sửa đổi", "bo_sung": "Bổ sung", "bai_bo": "Bãi bỏ"}


def amendments_touching(amendments: list[dict[str, Any]],
                        citation: dict[str, Any]) -> list[dict[str, Any]]:
    """Bản ghi sửa đổi có PHẠM VI bao trùm điều–khoản–điểm ``citation``.

    Bản ghi cấp khoản (không ghi điểm) hay cấp điều (không ghi khoản) chạm tới mọi
    điểm bên dưới — ví dụ SD_63 bãi bỏ điểm d–g khoản 17 Điều 32 nhưng chỉ ghi tới
    khoản. Không khớp được thì KHÔNG được suy ra "không bị sửa".
    """
    def khop(gt: Any, muc: Any) -> bool:
        return gt is None or str(gt) == str(muc)

    return [a for a in amendments
            if a.get("decree_article") == citation.get("article")
            and khop(a.get("decree_clause"), citation.get("clause"))
            and khop(a.get("decree_point"), citation.get("point"))]


def validity_timeline(start: date, end: date | None, origin: date, origin_doc: str,
                      amended_by: str | None, has_before: bool, amending_docs: list[str],
                      moc: date, touching: list[str] | None = None) -> list[Milestone]:
    """Các mốc hiệu lực của một điều khoản, suy từ dữ liệu thay vì gõ tay.

    ``origin`` là ngày văn bản gốc có hiệu lực; ``start`` là đầu khoảng hiệu lực
    của phiên bản hiện hành (trùng ``origin`` nếu chưa từng bị sửa). ``touching``
    là mô tả các bản ghi sửa đổi có phạm vi bao trùm điều khoản nhưng chưa gắn vào
    nó — khi có, tuyệt đối không khẳng định "không sửa".
    """
    def m(d: date, caption: str) -> Milestone:
        return Milestone(f"{d:%d/%m/%Y}", caption, d <= moc)

    if amended_by:
        amended_by = clean_citation_text(amended_by)
    if amended_by and has_before:
        mocs = [m(origin, f"{origin_doc} có hiệu lực"), m(start, f"Sửa đổi bởi {amended_by}")]
    elif amended_by:
        mocs = [m(start, f"Bổ sung bởi {amended_by}")]
    else:
        mocs = [m(start, f"{origin_doc} có hiệu lực")]

    if end is not None:
        mocs.append(m(end, "Hết hiệu lực" + (" — " + "; ".join(touching) if touching else "")))
    elif moc < start:
        mocs.append(Milestone(
            "Chưa có mốc kết thúc",
            f"Tại {moc:%d/%m/%Y} câu chữ trước sửa đổi đang được áp dụng" if has_before
            else f"Chưa có hiệu lực tại {moc:%d/%m/%Y}", False))
    elif amended_by:
        mocs.append(Milestone("Chưa có mốc kết thúc", "Phiên bản này đang được áp dụng", False))
    elif touching:
        mocs.append(Milestone("Chưa có mốc kết thúc",
                              "Có văn bản sửa đổi chạm tới khoản này, cần đối chiếu: "
                              + "; ".join(touching), False))
    elif amending_docs:
        # "Nghị định 238/2026/NĐ-CP (hiệu lực 15/8/2026)" -> bỏ phần ngoặc.
        ten = amending_docs[0].split(" (", 1)[0]
        mocs.append(Milestone("Chưa có mốc kết thúc", f"{ten} không sửa điều khoản này", False))
    else:
        mocs.append(Milestone("Chưa có mốc kết thúc", "Chưa có văn bản sửa đổi", False))
    return mocs
