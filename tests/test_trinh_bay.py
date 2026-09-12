"""Kiểm thử tầng trình bày của giao diện tra cứu.

VÌ SAO TÁCH RIÊNG KHỎI STREAMLIT
=================================
Mã Streamlit gần như không kiểm thử được: nó vẽ thẳng ra khung chạy của nó.
Nên toàn bộ phần CÓ THỂ SAI — định dạng tiền, gom kết quả, xếp mức tin cậy —
nằm ở ``api/trinh_bay.py`` dưới dạng hàm thuần, còn ``api/app.py`` chỉ là vỏ
mỏng gọi xuống. Tệp này kiểm phần hàm thuần đó.
"""
import pytest

from tra_cuu_gtdb.api.trinh_bay import (
    dong_che_tai,
    muc_tin_cay,
    the_ket_qua,
    tom_tat,
)


class TestMucTinCay:
    """Điểm số thô vô nghĩa với người dùng; phải quy thành nhãn đọc được."""

    @pytest.mark.parametrize("diem,mong_doi", [
        (0.95, "cao"), (0.80, "cao"),
        (0.79, "trung bình"), (0.60, "trung bình"),
        (0.59, "thấp"), (0.0, "thấp"),
    ])
    def test_xep_dung_dai(self, diem, mong_doi):
        assert muc_tin_cay(diem) == mong_doi

    def test_diem_thieu_thi_coi_la_thap(self):
        """Kết quả tra theo căn cứ không có điểm — không được nổ lỗi."""
        assert muc_tin_cay(None) == "thấp"


class TestDongCheTai:
    """Chế tài phải đọc được như người Việt viết, không phải như JSON."""

    def test_dinh_dang_tien_theo_kieu_viet_nam(self):
        v = {"phat_tien": {"min": 4000000, "max": 6000000}, "tru_diem_gplx": None,
             "hinh_phat_bo_sung": [], "bien_phap_khac_phuc": []}
        assert dong_che_tai(v) == ["Phạt tiền: từ 4.000.000 đồng đến 6.000.000 đồng"]

    def test_muc_phat_co_dinh_khong_ghi_tu_den(self):
        v = {"phat_tien": {"min": 500000, "max": 500000}, "tru_diem_gplx": None,
             "hinh_phat_bo_sung": [], "bien_phap_khac_phuc": []}
        assert dong_che_tai(v) == ["Phạt tiền: 500.000 đồng"]

    def test_khong_phat_tien_van_phai_noi_ro(self):
        """Im lặng ở đây khiến người đọc tưởng chưa tra ra chế tài."""
        v = {"phat_tien": {"min": None, "max": None}, "tru_diem_gplx": None,
             "hinh_phat_bo_sung": [], "bien_phap_khac_phuc": []}
        assert dong_che_tai(v) == ["Không quy định phạt tiền"]

    def test_gop_du_moi_loai_che_tai(self):
        v = {"phat_tien": {"min": 6000000, "max": 8000000}, "tru_diem_gplx": 10,
             "hinh_phat_bo_sung": ["Tịch thu phương tiện"],
             "bien_phap_khac_phuc": ["Buộc khôi phục lại tình trạng ban đầu"]}
        assert dong_che_tai(v) == [
            "Phạt tiền: từ 6.000.000 đồng đến 8.000.000 đồng",
            "Trừ 10 điểm giấy phép lái xe",
            "Hình phạt bổ sung: Tịch thu phương tiện",
            "Biện pháp khắc phục: Buộc khôi phục lại tình trạng ban đầu",
        ]


class TestTheKetQua:
    """Gom ba loại tri thức thành danh sách thẻ để giao diện chỉ việc vẽ."""

    def test_gom_du_ba_loai_theo_dung_thu_tu(self, he_thong):
        kq = he_thong.hoi("vượt đèn đỏ xe máy phạt bao nhiêu", top_k=2)
        the = the_ket_qua(kq)
        assert the, "Phải có ít nhất một thẻ"
        loai = [t.loai for t in the]
        assert loai == sorted(loai, key=["hanh_vi", "quy_tac", "khai_niem"].index), (
            f"Sai thứ tự ưu tiên: {loai}")

    def test_moi_the_deu_co_can_cu_phap_ly(self, he_thong):
        """Không có căn cứ thì người dùng không kiểm chứng được — vô dụng."""
        for t in the_ket_qua(he_thong.hoi("xe cơ giới là gì", top_k=3)):
            assert t.can_cu.strip(), f"Thẻ {t.tieu_de!r} thiếu căn cứ"

    def test_danh_dau_tri_thuc_bo_sung(self, he_thong):
        """Người dùng cần biết mẩu nào là trả lời chính, mẩu nào chỉ gợi thêm."""
        the = the_ket_qua(he_thong.hoi("xe cơ giới là gì", top_k=3))
        assert any(t.loai == "khai_niem" and not t.bo_sung for t in the)

    def test_truy_van_ngoai_linh_vuc_khong_gay_loi(self, he_thong):
        the_ket_qua(he_thong.hoi("cách nấu phở bò"))  # khong duoc nem ngoai le


class TestTomTat:
    def test_neu_ten_lop_bai_toan(self, he_thong):
        assert "chế tài" in tom_tat(he_thong.hoi("vượt đèn đỏ phạt bao nhiêu")).lower()

    def test_noi_ro_khi_khong_tim_thay(self):
        kq = {"khong_tim_thay": True, "ten_lop_bai_toan": "Tra cứu kiến thức liên quan",
              "khai_niem": [], "quy_tac": [], "hanh_vi": []}
        assert "không tìm thấy" in tom_tat(kq).lower()
