"""Kiểm thử việc nạp cơ sở tri thức từ JSON."""
from pathlib import Path

import pytest

from tra_cuu_gtdb.kb.loader import LoiNapTriThuc, nap_co_so_tri_thuc

pytestmark = pytest.mark.cham


class TestNapThanhCong:
    def test_nap_du_quy_mo_da_cong_bo(self, kb):
        """Khoá mức sàn theo số liệu trong báo cáo đồ án.
        Dùng >= để còn mở rộng cơ sở tri thức mà không làm đỏ test."""
        tk = kb.thong_ke()
        assert tk["khai_niem"] >= 73
        assert tk["quan_he"] >= 482
        assert tk["quy_tac"] >= 109
        assert tk["vi_pham"] >= 345
        assert tk["cum_tu_khoa"] >= 1674
        assert tk["van_ban"] >= 3
        assert tk["sua_doi"] >= 63

    def test_phan_loai_day_du(self, kb):
        pl = kb.phan_loai
        assert pl.linh_vuc and pl.ten_nhom and pl.ten_phuong_tien
        assert pl.ten_chu_the and pl.dong_nghia

    def test_van_ban_co_ngay_hieu_luc(self, kb):
        """Ngày hiệu lực là nền tảng cho việc mô hình hoá hiệu lực theo thời gian."""
        for vb in kb.van_ban:
            assert vb.ngay_hieu_luc >= vb.ngay_ban_hanh

    def test_co_so_tri_thuc_bat_bien(self, kb):
        """Dữ liệu nạp xong là bất biến — tránh sửa nhầm giữa các truy vấn."""
        with pytest.raises((AttributeError, TypeError, ValueError)):
            kb.khai_niem[0].ten = "đổi tên"  # type: ignore[misc]


class TestBaoLoiRoRang:
    def test_thu_muc_khong_ton_tai(self):
        with pytest.raises(LoiNapTriThuc, match="Không tìm thấy thư mục"):
            nap_co_so_tri_thuc(Path("/khong/ton/tai"))

    def test_thieu_tep_bao_ro_ten_tep(self, tmp_path):
        with pytest.raises(LoiNapTriThuc, match="concepts.json"):
            nap_co_so_tri_thuc(tmp_path)

    def test_json_hong_bao_ro_ten_tep(self, tmp_path):
        (tmp_path / "concepts.json").write_text("{khong phai json", encoding="utf-8")
        with pytest.raises(LoiNapTriThuc, match="không phải JSON hợp lệ"):
            nap_co_so_tri_thuc(tmp_path)

    def test_ban_ghi_sai_bao_ro_dinh_danh(self, tmp_path):
        """Thông điệp lỗi phải chỉ đúng bản ghi nào sai, không ném vết ngăn xếp thô."""
        (tmp_path / "concepts.json").write_text(
            '[{"id": "KN_X", "ten": "X", "loai": "kn", "dinh_nghia": "d", '
            '"can_cu": {"van_ban": ""}, "can_cu_text": "Điều 1"}]', encoding="utf-8")
        with pytest.raises(LoiNapTriThuc, match="KN_X"):
            nap_co_so_tri_thuc(tmp_path)
