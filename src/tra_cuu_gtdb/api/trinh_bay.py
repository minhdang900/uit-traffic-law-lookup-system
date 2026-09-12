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
NGUONG_CAO = 0.80
NGUONG_TRUNG_BINH = 0.60

#: Thứ tự ưu tiên hiển thị: chế tài trước (thứ người ta hỏi nhiều nhất), rồi
#: quy định, cuối cùng là khái niệm nền.
THU_TU_LOAI = ("hanh_vi", "quy_tac", "khai_niem")

TEN_LOAI = {
    "hanh_vi": "Hành vi vi phạm",
    "quy_tac": "Quy định",
    "khai_niem": "Khái niệm",
}


@dataclass(frozen=True)
class The:
    """Một thẻ kết quả đã sẵn sàng để vẽ."""

    loai: str
    tieu_de: str
    dong: list[str] = field(default_factory=list)
    can_cu: str = ""
    diem: float | None = None
    bo_sung: bool = False

    @property
    def muc_tin_cay(self) -> str:
        return muc_tin_cay(self.diem)


def dinh_dang_tien(n: int | None) -> str:
    """1500000 -> '1.500.000 đồng' (dấu chấm ngăn nghìn, kiểu Việt Nam)."""
    if n is None:
        return "0 đồng"
    return f"{n:,.0f}".replace(",", ".") + " đồng"


def muc_tin_cay(diem: float | None) -> str:
    """Quy điểm thô thành nhãn. Thiếu điểm thì coi là thấp, không nổ lỗi."""
    if diem is None:
        return "thấp"
    if diem >= NGUONG_CAO:
        return "cao"
    if diem >= NGUONG_TRUNG_BINH:
        return "trung bình"
    return "thấp"


def dong_che_tai(v: dict[str, Any]) -> list[str]:
    """Các dòng chế tài của một hành vi vi phạm, đã viết thành câu tiếng Việt."""
    pt = v.get("phat_tien") or {}
    mn, mx = pt.get("min"), pt.get("max")
    dong: list[str] = []

    if mn is None and mx is None:
        dong.append("Không quy định phạt tiền")
    elif mn == mx == 0:
        dong.append("Không phạt tiền (cảnh cáo hoặc hình thức khác)")
    elif mn == mx:
        dong.append(f"Phạt tiền: {dinh_dang_tien(mn)}")
    else:
        dong.append(f"Phạt tiền: từ {dinh_dang_tien(mn)} đến {dinh_dang_tien(mx)}")

    if v.get("tru_diem_gplx"):
        dong.append(f"Trừ {v['tru_diem_gplx']} điểm giấy phép lái xe")
    for x in v.get("hinh_phat_bo_sung") or []:
        dong.append(f"Hình phạt bổ sung: {x}")
    for x in v.get("bien_phap_khac_phuc") or []:
        dong.append(f"Biện pháp khắc phục: {x}")
    return dong


def _the_tu_muc(loai: str, m: dict[str, Any]) -> The:
    if loai == "hanh_vi":
        tieu_de, dong = m.get("hanh_vi", ""), dong_che_tai(m)
    elif loai == "quy_tac":
        tieu_de = m.get("ten", "")
        dong = [m["nguyen_van"]] if m.get("nguyen_van") else []
    else:
        tieu_de = m.get("ten", "")
        dong = [m["dinh_nghia"]] if m.get("dinh_nghia") else [
            f"{k}: {gt}" for k, gt in list((m.get("thuoc_tinh") or {}).items())[:6]]
    return The(loai=loai, tieu_de=tieu_de, dong=dong,
               can_cu=m.get("can_cu_text", ""), diem=m.get("diem"),
               bo_sung=bool(m.get("bo_sung")))


def the_ket_qua(kq: dict[str, Any]) -> list[The]:
    """Gom ba loại tri thức thành một danh sách thẻ theo thứ tự ưu tiên."""
    return [_the_tu_muc(loai, m) for loai in THU_TU_LOAI for m in kq.get(loai) or []]


def tom_tat(kq: dict[str, Any]) -> str:
    """Một dòng tóm tắt đặt ngay dưới ô tìm kiếm."""
    if kq.get("khong_tim_thay"):
        return ("Không tìm thấy quy định phù hợp trong cơ sở tri thức. "
                "Thử diễn đạt lại câu hỏi hoặc nêu rõ loại phương tiện.")
    so = sum(len(kq.get(loai) or []) for loai in THU_TU_LOAI)
    return f"{kq.get('ten_lop_bai_toan', 'Tra cứu')} · {so} mẩu tri thức"
