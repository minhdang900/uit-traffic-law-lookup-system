"""Kiểm thử bộ kịch bản nghiệm thu.

``eval/evaluate.py`` đo 120 câu bằng chỉ số tổng hợp — tốt cho việc theo dõi
hồi quy, nhưng đọc một con số 76,67% thì không biết hệ thống LÀM ĐƯỢC GÌ.

Bộ kịch bản này ngược lại: ít ca, mỗi ca nêu rõ KỲ VỌNG CỤ THỂ và đạt hay
không đạt thấy ngay. Dùng khi demo, khi nghiệm thu, và khi cần biết một thay
đổi vừa làm hỏng đúng cái gì.
"""
import pytest

from tra_cuu_gtdb.kiem_thu.kich_ban import KICH_BAN, KichBan, kiem_mot_ca

pytestmark = pytest.mark.cham


class TestBoKiemTra:
    """Bản thân bộ kiểm tra phải bắt được lỗi — nếu không thì mọi ca đều 'đạt'."""

    def test_bao_dat_khi_moi_ky_vong_deu_khop(self):
        kq = {"lop_bai_toan": "P3_TRA_CUU_CHE_TAI", "khong_tim_thay": False,
              "hanh_vi": [{"id": "VP_X", "can_cu_text": "Điều 7 khoản 7",
                           "phat_tien": {"min": 4000000, "max": 6000000},
                           "tru_diem_gplx": 4}],
              "khai_niem": [], "quy_tac": []}
        ca = KichBan(ma="TC00", nhom="thu", cau_hoi="x",
                     lop="P3_TRA_CUU_CHE_TAI", chua_id="VP_X",
                     can_cu_chua="Điều 7", tien=(4000000, 6000000), tru_diem=4)
        assert kiem_mot_ca(kq, ca) == []

    def test_bat_duoc_sai_lop_bai_toan(self):
        kq = {"lop_bai_toan": "P1_TRA_CUU_KHAI_NIEM", "khong_tim_thay": False,
              "hanh_vi": [], "khai_niem": [], "quy_tac": []}
        loi = kiem_mot_ca(kq, KichBan(ma="TC00", nhom="thu", cau_hoi="x",
                                      lop="P3_TRA_CUU_CHE_TAI"))
        assert any("lớp" in x for x in loi), loi

    def test_bat_duoc_thieu_id_tri_thuc(self):
        kq = {"lop_bai_toan": "P3_TRA_CUU_CHE_TAI", "khong_tim_thay": False,
              "hanh_vi": [{"id": "VP_KHAC", "can_cu_text": "", "phat_tien": {},
                           "tru_diem_gplx": None}], "khai_niem": [], "quy_tac": []}
        loi = kiem_mot_ca(kq, KichBan(ma="TC00", nhom="thu", cau_hoi="x",
                                      chua_id="VP_CAN_TIM"))
        assert any("VP_CAN_TIM" in x for x in loi), loi

    def test_bat_duoc_sai_khung_tien(self):
        kq = {"lop_bai_toan": "P3_TRA_CUU_CHE_TAI", "khong_tim_thay": False,
              "hanh_vi": [{"id": "VP_X", "can_cu_text": "",
                           "phat_tien": {"min": 100000, "max": 200000},
                           "tru_diem_gplx": None}], "khai_niem": [], "quy_tac": []}
        loi = kiem_mot_ca(kq, KichBan(ma="TC00", nhom="thu", cau_hoi="x",
                                      tien=(4000000, 6000000)))
        assert any("phạt tiền" in x for x in loi), loi

    def test_kiem_duoc_ky_vong_tu_choi(self):
        kq = {"lop_bai_toan": "P7_TRA_CUU_LIEN_QUAN", "khong_tim_thay": False,
              "hanh_vi": [], "khai_niem": [], "quy_tac": []}
        loi = kiem_mot_ca(kq, KichBan(ma="TC00", nhom="thu", cau_hoi="x",
                                      khong_tim_thay=True))
        assert loi, "Kỳ vọng bị từ chối nhưng hệ thống trả lời — phải báo lỗi"


class TestBoKichBan:
    def test_ma_ca_khong_trung(self):
        ma = [c.ma for c in KICH_BAN]
        assert len(set(ma)) == len(ma), "Mã ca kiểm thử bị trùng"

    def test_phu_du_bay_lop_bai_toan(self):
        lop = {c.lop for c in KICH_BAN if c.lop}
        assert len(lop) >= 7, f"Mới phủ {len(lop)} lớp: {sorted(lop)}"

    def test_moi_ca_deu_neu_it_nhat_mot_ky_vong(self):
        """Ca không có kỳ vọng nào thì luôn 'đạt' — vô nghĩa."""
        rong = [c.ma for c in KICH_BAN if not c.co_ky_vong()]
        assert rong == [], f"Ca không nêu kỳ vọng: {rong}"

    @pytest.mark.parametrize("ma", [c.ma for c in KICH_BAN])
    def test_moi_ca_deu_dat_tren_he_thong_that(self, he_thong, ma):
        ca = next(c for c in KICH_BAN if c.ma == ma)
        loi = kiem_mot_ca(he_thong.hoi(ca.cau_hoi, top_k=5), ca)
        assert loi == [], f"{ca.ma} ({ca.cau_hoi!r}): " + "; ".join(loi)
