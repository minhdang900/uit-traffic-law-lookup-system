"""Hiệu lực theo thời gian của điều khoản pháp luật.

Một hệ tra cứu pháp luật trả về mức phạt đã hết hiệu lực còn nguy hiểm hơn hệ
trả lời "không tìm thấy". Vì vậy hiệu lực được mô hình hoá như một khái niệm
hạng nhất chứ không phải bước hợp nhất lúc dựng cơ sở tri thức:

- Mỗi điều khoản mang một **khoảng hiệu lực** ``[hieu_luc_tu, hieu_luc_den]``.
- Sửa đổi được lưu như **dữ liệu**, không ghi đè bản gốc.
- Mọi truy vấn giải theo một **mốc thời gian** (mặc định là hôm nay).

Nhờ đó trả lời được "mức phạt tại ngày X là bao nhiêu", chứ không chỉ biết bản
hiện hành.
"""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, model_validator

from traffic_law.domain.field_alias import khoa_json


class EffectivePeriod(BaseModel):
    """Khoảng thời gian một điều khoản có hiệu lực.

    ``den`` để trống nghĩa là điều khoản còn hiệu lực đến hiện tại. Khoảng được
    hiểu là **đóng hai đầu**: điều khoản có hiệu lực trong cả ngày ``den``.
    """

    model_config = {"extra": "forbid", "frozen": True,
                    "alias_generator": khoa_json, "populate_by_name": True}

    start: date
    end: date | None = None

    @model_validator(mode="after")
    def _den_khong_truoc_tu(self) -> EffectivePeriod:
        if self.end is not None and self.end < self.start:
            raise ValueError(f"ngày hết hiệu lực {self.end} trước ngày có hiệu lực {self.start}")
        return self

    @property
    def is_in_force(self) -> bool:
        """Điều khoản còn hiệu lực tính đến hôm nay."""
        return self.in_force_on(date.today())

    def in_force_on(self, moc: date) -> bool:
        """Điều khoản có hiệu lực tại mốc thời gian ``moc`` hay không."""
        if moc < self.start:
            return False
        return self.end is None or moc <= self.end

    def __str__(self) -> str:
        return f"từ {self.start:%d/%m/%Y}" + (
            f" đến {self.end:%d/%m/%Y}" if self.end else " (còn hiệu lực)")
