"""Kiểm thử tầng mô hình dữ liệu thuần (domain).

Tầng này không đọc tệp, không phụ thuộc thư viện ngoài nào ngoài Pydantic.
Nhiệm vụ của nó là làm cho dữ liệu sai KHÔNG THỂ tồn tại trong bộ nhớ.
"""
import pytest
from pydantic import ValidationError

from tra_cuu_gtdb.domain.models import CanCu, KhaiNiem, MucPhat, QuanHe, ViPham


class TestCanCu:
    def test_can_cu_toi_thieu_phai_co_van_ban(self):
        cc = CanCu(van_ban="Nghị định 168/2024/NĐ-CP", dieu=6, khoan=1, diem="a")
        assert cc.van_ban and cc.dieu == 6

    def test_thieu_van_ban_bi_tu_choi(self):
        with pytest.raises(ValidationError):
            CanCu(dieu=6)

    def test_van_ban_rong_bi_tu_choi(self):
        """Căn cứ pháp lý rỗng nghĩa là không truy được về văn bản gốc."""
        with pytest.raises(ValidationError):
            CanCu(van_ban="   ")


class TestMucPhat:
    def test_muc_phat_hop_le(self):
        mp = MucPhat(min=400_000, max=600_000, don_vi="VND")
        assert mp.min <= mp.max

    def test_min_lon_hon_max_bi_tu_choi(self):
        with pytest.raises(ValidationError):
            MucPhat(min=600_000, max=400_000, don_vi="VND")

    def test_muc_phat_am_bi_tu_choi(self):
        with pytest.raises(ValidationError):
            MucPhat(min=-1, max=100, don_vi="VND")


class TestKhaiNiem:
    def test_khai_niem_hop_le(self):
        kn = KhaiNiem(
            id="KN_XE_CO_GIOI", ten="Xe cơ giới", loai="khai_niem",
            dinh_nghia="Xe cơ giới bao gồm ô tô, mô tô...",
            can_cu=CanCu(van_ban="Luật 36/2024/QH15", dieu=34, khoan=1),
            can_cu_text="Điều 34 khoản 1 Luật 36/2024/QH15",
        )
        assert kn.id.startswith("KN_")

    def test_cho_phep_thieu_dinh_nghia_neu_co_thuoc_tinh(self):
        """9/73 khái niệm không được luật định nghĩa (vd "nồng độ cồn" chỉ bị cấm
        tại Điều 9 khoản 2, không được định nghĩa). Nội dung nằm ở thuoc_tinh."""
        kn = KhaiNiem(
            id="KN_NONG_DO_CON", ten="Nồng độ cồn", loai="khai_niem",
            dinh_nghia=None,
            thuoc_tinh={"nguong": "Luật cấm tuyệt đối, không quy định ngưỡng cho phép"},
            can_cu=CanCu(van_ban="Luật 36/2024/QH15", dieu=9, khoan=2),
            can_cu_text="Điều 9 khoản 2 Luật 36/2024/QH15",
        )
        assert kn.dinh_nghia is None and kn.thuoc_tinh

    def test_khai_niem_rong_hoan_toan_bi_tu_choi(self):
        """Không có định nghĩa VÀ không có thuộc tính = không mang thông tin gì."""
        with pytest.raises(ValidationError):
            KhaiNiem(
                id="KN_X", ten="X", loai="khai_niem", dinh_nghia=None, thuoc_tinh={},
                can_cu=CanCu(van_ban="Luật 36/2024/QH15"), can_cu_text="Điều 1",
            )


class TestViPham:
    def _vp(self, **kw):
        mac_dinh = dict(
            id="VP_TEST", hanh_vi="Vượt đèn đỏ", nhom="den_tin_hieu",
            chu_the="nguoi_dieu_khien", phuong_tien=["xe_may"],
            phat_tien=MucPhat(min=4_000_000, max=6_000_000, don_vi="VND"),
            tru_diem_gplx=6, linh_vuc="LV_QUY_TAC", ten_nhom="Đèn tín hiệu",
            can_cu=CanCu(van_ban="Nghị định 168/2024/NĐ-CP", dieu=7, khoan=9),
            can_cu_text="Điều 7 khoản 9 Nghị định 168/2024/NĐ-CP",
        )
        mac_dinh.update(kw)
        return ViPham(**mac_dinh)

    def test_vi_pham_hop_le(self):
        assert self._vp().tru_diem_gplx == 6

    def test_tru_diem_am_bi_tu_choi(self):
        with pytest.raises(ValidationError):
            self._vp(tru_diem_gplx=-1)

    def test_tru_diem_qua_12_bi_tu_choi(self):
        """Giấy phép lái xe chỉ có 12 điểm; trừ quá 12 là dữ liệu sai."""
        with pytest.raises(ValidationError):
            self._vp(tru_diem_gplx=13)

    def test_phai_co_it_nhat_mot_che_tai(self):
        """Hành vi vi phạm không có chế tài nào thì không phải hành vi vi phạm."""
        with pytest.raises(ValidationError):
            self._vp(phat_tien=MucPhat(min=0, max=0, don_vi="VND"),
                     tru_diem_gplx=0, hinh_phat_bo_sung=[], bien_phap_khac_phuc=[])


class TestQuanHe:
    def test_quan_he_hop_le(self):
        qh = QuanHe(ten="la_loai_cua", kieu="phan_cap",
                    nguon="KN_XE_O_TO", dich="KN_XE_CO_GIOI", mo_ta="...")
        assert qh.nguon != qh.dich

    def test_quan_he_tu_tro_bi_tu_choi(self):
        """Quan hệ trỏ về chính nó tạo vòng lặp vô hạn khi duyệt đồ thị tri thức."""
        with pytest.raises(ValidationError):
            QuanHe(ten="la_loai_cua", kieu="phan_cap",
                   nguon="KN_X", dich="KN_X", mo_ta="...")
