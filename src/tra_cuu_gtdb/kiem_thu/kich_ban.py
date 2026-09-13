"""Bộ kịch bản nghiệm thu — ít ca, mỗi ca nêu rõ kỳ vọng cụ thể.

KHÁC GÌ ``eval/evaluate.py``
============================
``evaluate.py`` chấm 120 câu và trả về chỉ số tổng hợp — tốt để canh hồi quy,
nhưng đọc "Top-1 76,67%" thì không biết hệ thống LÀM ĐƯỢC GÌ và HỎNG Ở ĐÂU.

Bộ này ngược lại: mỗi ca nêu một kỳ vọng kiểm chứng được bằng chính văn bản
luật (đúng khung tiền, đúng số điểm trừ, đúng điều khoản), đạt hay không thấy
ngay. Dùng khi demo, khi nghiệm thu, và khi cần biết một thay đổi vừa làm
hỏng đúng cái gì.

VÌ SAO KHÔNG CÓ CA "PHẢI TỪ CHỐI TRUY VẤN RÁC"
Phép kiểm ``khong_tim_thay`` có sẵn và đã được kiểm thử, nhưng cấu hình mặc
định KHÔNG từ chối được truy vấn ngoài lĩnh vực — đây là hạn chế đã đo và ghi
bằng xfail trong ``tests/test_nguong_tin_cay.py``. Thêm một ca chắc chắn hỏng
vào bộ nghiệm thu chỉ làm nhiễu; muốn kiểm khả năng từ chối thì chạy
``eval/phat_hien_mien.py --dense``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class KichBan:
    """Một ca nghiệm thu. Trường nào để ``None`` thì không kiểm trường đó."""

    ma: str
    nhom: str
    cau_hoi: str
    lop: str | None = None
    chua_id: str | None = None
    can_cu_chua: str | None = None
    tien: tuple[int, int] | None = None
    tru_diem: int | None = None
    khong_tim_thay: bool | None = None
    ghi_chu: str = ""

    def co_ky_vong(self) -> bool:
        """Ca không nêu kỳ vọng nào thì luôn 'đạt' — vô nghĩa, phải chặn."""
        return any(x is not None for x in
                   (self.lop, self.chua_id, self.can_cu_chua, self.tien,
                    self.tru_diem, self.khong_tim_thay))


def _moi_muc(kq: dict[str, Any]) -> list[dict[str, Any]]:
    return [m for loai in ("hanh_vi", "quy_tac", "khai_niem") for m in kq.get(loai) or []]


def kiem_mot_ca(kq: dict[str, Any], ca: KichBan) -> list[str]:
    """Trả về danh sách điểm KHÔNG khớp. Rỗng nghĩa là đạt."""
    loi: list[str] = []

    if ca.khong_tim_thay is not None and kq["khong_tim_thay"] != ca.khong_tim_thay:
        loi.append(f"khong_tim_thay: cần {ca.khong_tim_thay}, thực {kq['khong_tim_thay']}")

    if ca.lop is not None and kq.get("lop_bai_toan") != ca.lop:
        loi.append(f"sai lớp bài toán: cần {ca.lop}, thực {kq.get('lop_bai_toan')}")

    if ca.chua_id is not None and ca.chua_id not in {m["id"] for m in _moi_muc(kq)}:
        loi.append(f"không thấy {ca.chua_id} trong kết quả")

    dau = (kq.get("hanh_vi") or [None])[0]

    if ca.can_cu_chua is not None:
        co = any(ca.can_cu_chua in (m.get("can_cu_text") or "") for m in _moi_muc(kq))
        if not co:
            loi.append(f"không mẩu nào dẫn căn cứ chứa {ca.can_cu_chua!r}")

    if ca.tien is not None:
        if dau is None:
            loi.append("cần khung phạt tiền nhưng không có hành vi nào")
        else:
            pt = dau.get("phat_tien") or {}
            thuc = (pt.get("min"), pt.get("max"))
            if thuc != ca.tien:
                loi.append(f"sai khung phạt tiền: cần {ca.tien}, thực {thuc}")

    if ca.tru_diem is not None:
        if dau is None:
            loi.append("cần số điểm trừ nhưng không có hành vi nào")
        elif dau.get("tru_diem_gplx") != ca.tru_diem:
            loi.append(f"sai điểm trừ: cần {ca.tru_diem}, thực {dau.get('tru_diem_gplx')}")

    return loi


#: Kỳ vọng của mỗi ca đối chiếu được với chính văn bản luật, không phải chép
#: lại kết quả hệ thống in ra.
KICH_BAN: list[KichBan] = [
    # --- bảy lớp bài toán ---
    KichBan("TC01", "Lớp bài toán", "Xe cơ giới là gì?",
            lop="P1_TRA_CUU_KHAI_NIEM", chua_id="KN_XE_CO_GIOI",
            can_cu_chua="Điều 34", ghi_chu="Định nghĩa tại Điều 34 khoản 1 Luật 36/2024"),
    KichBan("TC02", "Lớp bài toán", "Người lái xe phải mang theo giấy tờ gì?",
            lop="P2_TRA_CUU_QUY_DINH"),
    KichBan("TC03", "Lớp bài toán", "Vượt đèn đỏ xe máy phạt bao nhiêu?",
            lop="P3_TRA_CUU_CHE_TAI", tien=(4_000_000, 6_000_000), tru_diem=4,
            can_cu_chua="Điều 7", ghi_chu="Điều 7 khoản 7 điểm c NĐ 168/2024"),
    KichBan("TC04", "Lớp bài toán", "Lỗi nào bị trừ 10 điểm giấy phép lái xe?",
            lop="P4_TRA_CUU_NGUOC", tru_diem=10),
    KichBan("TC05", "Lớp bài toán",
            "Tôi vừa vượt đèn đỏ vừa không có giấy phép lái xe thì bị phạt bao nhiêu?",
            lop="P5_SUY_DIEN_TINH_HUONG"),
    KichBan("TC06", "Lớp bài toán",
            "Điều 6 khoản 9 điểm a Nghị định 168/2024/NĐ-CP nói về lỗi gì?",
            lop="P6_TRA_CUU_CAN_CU", can_cu_chua="Điều 6 khoản 9 điểm a",
            ghi_chu="Tra theo căn cứ phải trúng đúng điều khoản được hỏi"),
    KichBan("TC07", "Lớp bài toán", "Cho tôi thông tin về điểm của giấy phép lái xe.",
            lop="P7_TRA_CUU_LIEN_QUAN"),

    # --- suy diễn số học: cùng câu hỏi, giá trị khác nhau -> khung khác nhau ---
    KichBan("TC08", "Suy diễn số học", "xe máy nồng độ cồn 0,3 mg/l phạt bao nhiêu",
            lop="P3_TRA_CUU_CHE_TAI", tien=(6_000_000, 8_000_000), tru_diem=10,
            ghi_chu="0,3 thuộc khung 'vượt quá 0,25 đến 0,4 mg/l'"),
    KichBan("TC09", "Suy diễn số học", "ô tô nồng độ cồn 0,5 mg/l phạt bao nhiêu",
            lop="P3_TRA_CUU_CHE_TAI", tien=(30_000_000, 40_000_000),
            ghi_chu="Khung cao nhất với ô tô, vượt quá 0,4 mg/l"),

    # --- tra cứu ngữ nghĩa: khẩu ngữ, không dấu ---
    KichBan("TC10", "Ngữ nghĩa", "nhậu xong lái xe máy bị phạt nhiêu tiền",
            lop="P3_TRA_CUU_CHE_TAI",
            ghi_chu="Chữ 'nhậu' không có trong bất kỳ văn bản luật nào"),
    KichBan("TC11", "Ngữ nghĩa", "khong doi mu bao hiem phat bao nhieu",
            lop="P3_TRA_CUU_CHE_TAI", ghi_chu="Truy vấn không dấu"),
    KichBan("TC12", "Ngữ nghĩa", "chạy quá tốc độ 25 km/h thì sao",
            lop="P3_TRA_CUU_CHE_TAI",
            ghi_chu="Chọn đúng khung 'trên 20 km/h đến 35 km/h'"),
]
