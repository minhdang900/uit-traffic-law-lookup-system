"""Kiểm thử tầng tiền xử lý ngôn ngữ của kb_engine.

Đây là tầng thấp nhất của hệ thống: mọi truy vấn đều đi qua đây trước khi được
rút trích keyphrase và phân loại. Sai ở đây thì sai toàn hệ thống.
"""
import pytest

from tra_cuu_gtdb.reasoning.engine import bo_dau, chuan_hoa, tach_so_tien


class TestBoDau:
    """bo_dau() — chuyển tiếng Việt về dạng không dấu, phục vụ so khớp keyphrase."""

    def test_bo_dau_tieng_viet_co_dau(self):
        assert bo_dau("Vượt đèn đỏ") == "vuot den do"

    def test_bo_dau_chuyen_chu_d_gach_ngang(self):
        """Chữ 'đ' không phải dấu thanh nên unicodedata không xử lý được, phải thay tay."""
        assert bo_dau("Đường bộ") == "duong bo"
        assert "đ" not in bo_dau("đèn đỏ")

    def test_bo_dau_viet_thuong_hoa(self):
        assert bo_dau("NỒNG ĐỘ CỒN") == "nong do con"

    def test_bo_dau_chuoi_rong_khong_ne_loi(self):
        assert bo_dau("") == ""
        assert bo_dau(None) == ""


class TestChuanHoa:
    """chuan_hoa() — chuẩn hoá truy vấn người dùng nhập."""

    def test_chuan_hoa_gop_khoang_trang_va_viet_thuong(self):
        assert chuan_hoa("  Phạt   BAO nhiêu?? ") == "phạt bao nhiêu"

    def test_chuan_hoa_giu_nguyen_dau_tieng_viet(self):
        """Khác bo_dau: chuan_hoa PHẢI giữ dấu để so khớp chính xác."""
        assert "ồ" in chuan_hoa("Nồng độ cồn")

    def test_chuan_hoa_giu_ky_tu_co_nghia_trong_van_ban_luat(self):
        """Dấu %, /, - mang nghĩa trong văn bản pháp luật (mg/l, 20-35 km/h)."""
        kq = chuan_hoa("0,25 miligam/1 lít")
        assert "/" in kq and "," in kq

    def test_chuan_hoa_chuoi_rong_khong_ne_loi(self):
        assert chuan_hoa("") == ""
        assert chuan_hoa(None) == ""


class TestTachSoTien:
    """tach_so_tien() — rút trích số tiền, phục vụ lớp P4 (tra cứu ngược theo mức phạt)."""

    @pytest.mark.parametrize("truy_van,mong_doi", [
        ("phạt 2 triệu", [2_000_000]),
        ("5 tỷ", [5_000_000_000]),
        ("800 nghìn", [800_000]),
        ("phạt 500 ngàn đồng", [500_000]),
    ])
    def test_tach_dung_don_vi_tien_te(self, truy_van, mong_doi):
        assert tach_so_tien(truy_van) == mong_doi

    def test_khong_co_so_tien_thi_tra_ve_rong(self):
        assert tach_so_tien("vượt đèn đỏ phạt bao nhiêu") == []

    def test_chuoi_rac_khong_nem_loi(self):
        """Hàm có khối try/except ValueError nuốt lỗi im lặng (kb_engine.py:77-79).
        Test này khoá lại hành vi đó: nuốt lỗi là CHẤP NHẬN ĐƯỢC ở đây, nhưng
        không được sập chương trình."""
        assert tach_so_tien("abc xyz !!!") == []
        assert tach_so_tien("...,,,") == []

    def test_tach_nhieu_so_tien_trong_mot_truy_van(self):
        """Lớp P4 cần bắt được khoảng: 'từ 2 triệu đến 3 triệu'."""
        kq = tach_so_tien("từ 2 triệu đến 3 triệu")
        assert 2_000_000 in kq and 3_000_000 in kq
