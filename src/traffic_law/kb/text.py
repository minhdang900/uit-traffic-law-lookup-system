"""Tiền xử lý ngôn ngữ tiếng Việt cho truy vấn và văn bản tri thức."""
from __future__ import annotations

import re
import unicodedata

# Đơn vị tiền tệ xuất hiện trong truy vấn người dùng và hệ số quy đổi ra đồng.
_HE_SO_TIEN: dict[str, int] = {
    "tỷ": 1_000_000_000, "tỉ": 1_000_000_000,
    "triệu": 1_000_000,
    "nghìn": 1_000, "ngàn": 1_000, "k": 1_000,
    "đồng": 1, "vnđ": 1, "vnd": 1,
}


def strip_accents(s: str | None) -> str:
    """Chuyển chuỗi tiếng Việt về dạng không dấu, viết thường.

    Chữ "đ" không phải dấu thanh nên ``unicodedata`` không tách được, phải thay tay.
    """
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def normalise(s: str | None) -> str:
    """Chuẩn hoá truy vấn: viết thường, bỏ ký tự lạ, gộp khoảng trắng.

    Giữ lại ``% / , . - +`` vì chúng mang nghĩa trong văn bản pháp luật
    (ví dụ "0,25 miligam/1 lít", "20-35 km/h").
    """
    s = unicodedata.normalize("NFC", s or "").lower()
    s = re.sub(r"[\"'`“”‘’?!]", " ", s)
    s = re.sub(r"[^\w\s%/,.\-+]", " ", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def parse_money(s: str) -> list[int]:
    """Rút trích các số tiền (VND) trong truy vấn, phục vụ lớp bài toán P4.

    Số không kèm đơn vị tiền tệ bị bỏ qua để tránh bắt nhầm số điều, số khoản.
    """
    out: list[int] = []
    for m in re.finditer(r"(\d[\d.,]*)\s*(tỷ|tỉ|triệu|nghìn|ngàn|k|đồng|vnđ|vnd)?", s):
        raw, unit = m.group(1), (m.group(2) or "")
        if unit not in _HE_SO_TIEN:
            continue
        try:
            value = float(raw.replace(".", "").replace(",", "."))
        except ValueError:
            continue
        out.append(int(value * _HE_SO_TIEN[unit]))
    return out
