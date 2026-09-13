"""Tầng trình bày — biến kết quả suy diễn thành thứ vẽ được lên màn hình.

Toàn bộ phần CÓ THỂ SAI nằm ở đây dưới dạng hàm thuần: định dạng tiền, gom kết
quả, xếp mức tin cậy. ``app.py`` chỉ là vỏ Streamlit mỏng gọi xuống, nhờ vậy
kiểm thử được mà không cần dựng khung chạy Streamlit.

Không import ``streamlit`` trong tệp này.
"""
from __future__ import annotations

from dataclasses import dataclass, field
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
