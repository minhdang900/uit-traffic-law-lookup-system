"""Kiểm thử hiệu lực theo thời gian.

Rủi ro pháp lý nghiêm trọng nhất của một hệ tra cứu pháp luật là trả về mức phạt
đã hết hiệu lực. Các test dưới đây khoá lại hành vi chặn rủi ro đó.

Mốc thời gian trong cơ sở tri thức:
    2025-01-01  Luật 36/2024 và Nghị định 168/2024 có hiệu lực
    2026-08-15  Nghị định 238/2026 có hiệu lực (sửa đổi + bổ sung NĐ 168)
"""
from datetime import date

import pytest
from pydantic import ValidationError

from tra_cuu_gtdb.domain.temporal import KhoangHieuLuc

HL_ND168 = date(2025, 1, 1)
HL_ND238 = date(2026, 8, 15)


class TestKhoangHieuLuc:
    def test_khoang_mo_con_hieu_luc_mai_ve_sau(self):
        k = KhoangHieuLuc(tu=HL_ND168)
        assert k.hieu_luc_tai(HL_ND168)
        assert k.hieu_luc_tai(date(2099, 1, 1))

    def test_truoc_ngay_co_hieu_luc_thi_chua_ap_dung(self):
        k = KhoangHieuLuc(tu=HL_ND168)
        assert not k.hieu_luc_tai(date(2024, 12, 31))

    def test_khoang_dong_bao_gom_ca_ngay_cuoi(self):
        """Điều khoản có hiệu lực trong CẢ ngày hết hiệu lực."""
        k = KhoangHieuLuc(tu=HL_ND168, den=date(2026, 8, 14))
        assert k.hieu_luc_tai(date(2026, 8, 14))
        assert not k.hieu_luc_tai(HL_ND238)

    def test_ngay_het_truoc_ngay_bat_dau_bi_tu_choi(self):
        with pytest.raises(ValidationError):
            KhoangHieuLuc(tu=HL_ND238, den=HL_ND168)


class TestSuyDienHieuLuc:
    pytestmark = pytest.mark.cham

    def test_moi_dieu_khoan_deu_co_khoang_hieu_luc(self, kb):
        thieu = [x.id for tap in (kb.quy_tac, kb.vi_pham) for x in tap if x.hieu_luc is None]
        assert thieu == [], f"{len(thieu)} điều khoản chưa suy diễn hiệu lực: {thieu[:5]}"

    def test_dieu_khoan_nd168_co_hieu_luc_tu_dau_2025(self, kb):
        goc = [v for v in kb.vi_pham if not v.sua_doi_boi]
        assert goc, "Không có điều khoản gốc nào"
        assert all(v.hieu_luc and v.hieu_luc.tu == HL_ND168 for v in goc)

    def test_dieu_khoan_do_nd238_tao_ra_co_hieu_luc_tu_15_8_2026(self, kb):
        sua = [v for v in kb.vi_pham if v.sua_doi_boi]
        assert sua, "Không có điều khoản nào liên quan Nghị định 238"
        assert all(v.hieu_luc and v.hieu_luc.tu == HL_ND238 for v in sua)


class TestTraCuuTheoMocThoiGian:
    pytestmark = pytest.mark.cham

    def test_truoc_2025_chua_co_dieu_khoan_nao(self, kb):
        """Nghị định 168/2024 chưa có hiệu lực ngày 31/12/2024."""
        k = kb.tai_thoi_diem(date(2024, 12, 31))
        assert len(k.vi_pham) == 0
        assert len(k.quy_tac) == 0

    def test_giua_2025_chua_ap_dung_sua_doi_cua_nd238(self, kb):
        k = kb.tai_thoi_diem(date(2025, 6, 1))
        assert 0 < len(k.vi_pham) < len(kb.vi_pham)
        assert all(not v.sua_doi_boi for v in k.vi_pham), (
            "Điều khoản của Nghị định 238 xuất hiện trước ngày 15/8/2026")

    def test_sau_15_8_2026_ap_dung_day_du(self, kb):
        k = kb.tai_thoi_diem(date(2026, 9, 1))
        assert len(k.vi_pham) == len(kb.vi_pham)

    def test_dung_ngay_hieu_luc_da_ap_dung(self, kb):
        """Biên: điều khoản có hiệu lực NGAY trong ngày 15/8/2026."""
        truoc = kb.tai_thoi_diem(date(2026, 8, 14))
        dung_ngay = kb.tai_thoi_diem(HL_ND238)
        assert len(dung_ngay.vi_pham) > len(truoc.vi_pham)

    def test_mac_dinh_la_hom_nay(self, kb):
        assert len(kb.tai_thoi_diem().vi_pham) == len(kb.tai_thoi_diem(date.today()).vi_pham)


class TestSuyDienTatDinh:
    def test_script_idempotent(self):
        """Chạy lại script suy diễn không được tạo thay đổi nào."""
        import sys
        sys.path.insert(0, "scripts")
        from suy_dien_hieu_luc import chay
        assert chay(kiem_tra=True) == 0
