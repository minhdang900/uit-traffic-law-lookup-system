"""Kiểm thử tính toàn vẹn của cơ sở tri thức.

Đây là các kiểm tra LIÊN TỆP mà mô hình dữ liệu đơn lẻ không thể phát hiện:
một quan hệ có thể hợp lệ về kiểu nhưng trỏ tới định danh không tồn tại.

Tương ứng yêu cầu của đề bài: *"Đặc tả: các thành phần về khái niệm, dạng luật
trong các quy định."*
"""
from dataclasses import replace
from datetime import date

import pytest

from tra_cuu_gtdb.domain.models import VanBan
from tra_cuu_gtdb.kb.validator import MucDo, kiem_tra_toan_ven

pytestmark = pytest.mark.cham


@pytest.fixture(scope="module")
def kq(kb):
    return kiem_tra_toan_ven(kb)


# Danh sách rỗng: mọi khoảng trống dữ liệu từng biết đều đã được bịt. Giữ hằng
# số này để lần sau có khoảng trống mới thì khai báo tường minh ở đây, thay vì
# nới lỏng phép kiểm tra.
KHOANG_TRONG_DA_BIET: set[str] = set()


class TestKhongCoLoi:
    def test_khong_phat_sinh_loi_moi(self, kq):
        """Chặn mọi lỗi ngoài danh sách khoảng trống dữ liệu đã biết."""
        moi = [v for v in kq.van_de
               if v.muc_do is MucDo.LOI and v.ma not in KHOANG_TRONG_DA_BIET]
        assert moi == [], "\n".join(f"  [{v.ma}] {v.thong_diep}" for v in moi)

    def test_luat_kiem_tra_van_ban_sua_doi_van_con_hieu_luc(self, kb):
        """Đối chứng dương: luật kiểm tra phải BẮT được văn bản sửa đổi bị thiếu.

        Trước đây bài kiểm tra này dựa vào một khoảng trống CÓ THẬT trong dữ
        liệu. Khoảng trống đó đã bịt, nên nếu chỉ xoá bài kiểm tra thì luật này
        có thể hỏng mà không ai biết. Thay bằng đối chứng dựng sẵn: bịa ra một
        văn bản khai bị sửa bởi một số hiệu không tồn tại, rồi đòi hỏi luật
        kiểm tra phải báo lỗi.
        """
        gia = replace(kb, van_ban=(
            *kb.van_ban,
            VanBan(id="VB_DOI_CHUNG", ten="Van ban doi chung",
                   ten_vn="Văn bản đối chứng", so_hieu="999/9999/QH99",
                   ngay_ban_hanh=date(2099, 1, 1), ngay_hieu_luc=date(2099, 1, 2),
                   sua_doi_boi=["Luật 000/0000/QH00 (không tồn tại)"]),
        ))
        loi = [v for v in kiem_tra_toan_ven(gia).van_de
               if v.ma == "VAN_BAN_SUA_DOI_THIEU"]
        assert loi, "Luật kiểm tra văn bản sửa đổi đã ngừng hoạt động"

    def test_luat_118_2025_da_duoc_mo_hinh_hoa(self, kb):
        """Văn bản sửa đổi Luật 36/2024 phải có mặt, kèm xuất xứ kiểm chứng được."""
        vb = next((v for v in kb.van_ban if v.so_hieu == "118/2025/QH15"), None)
        assert vb is not None, "Thiếu Luật 118/2025/QH15 trong documents.json"
        assert vb.ngay_hieu_luc == date(2026, 7, 1)
        assert vb.ngay_ban_hanh == date(2025, 12, 10)
        assert vb.ghi_chu and "55/VBHN-VPQH" in vb.ghi_chu, (
            "Phải ghi rõ xuất xứ siêu dữ liệu để kiểm chứng lại được")


class TestDinhDanh:
    def test_khong_trung_dinh_danh(self, kb):
        for ten, tap in (("khái niệm", kb.khai_niem), ("quy tắc", kb.quy_tac),
                         ("hành vi", kb.vi_pham)):
            ids = [x.id for x in tap]
            trung = {i for i in ids if ids.count(i) > 1}
            assert not trung, f"Định danh {ten} trùng: {sorted(trung)[:5]}"

    def test_quan_he_tro_toi_thuc_the_co_that(self, kb):
        hop_le = kb.dinh_danh_tri_thuc
        hong = [f"{q.ten}: {q.nguon}→{q.dich}" for q in kb.quan_he
                if not (q.nguon.startswith("NHOM_") or q.nguon in hop_le)
                or not (q.dich.startswith("NHOM_") or q.dich in hop_le)]
        assert hong == [], f"{len(hong)} quan hệ treo: {hong[:5]}"

    def test_keyphrase_tro_toi_thuc_the_co_that(self, kb):
        id_vp = {v.id for v in kb.vi_pham}
        id_kn = {c.id for c in kb.khai_niem}
        id_qt = {r.id for r in kb.quy_tac}
        hong = []
        for k in kb.cum_tu_khoa:
            hong += [(k.cum_tu, x) for x in k.hanh_vi if x not in id_vp]
            hong += [(k.cum_tu, x) for x in k.khai_niem if x not in id_kn]
            hong += [(k.cum_tu, x) for x in k.quy_tac if x not in id_qt]
        assert hong == [], f"{len(hong)} keyphrase treo: {hong[:5]}"


class TestCanCuPhapLy:
    def test_moi_tri_thuc_deu_truy_nguyen_duoc(self, kb):
        """Không có căn cứ thì người dùng không kiểm chứng được câu trả lời."""
        thieu = [x.id for tap in (kb.khai_niem, kb.quy_tac, kb.vi_pham)
                 for x in tap if not x.can_cu_text.strip()]
        assert thieu == []


class TestVanBanSuaDoi:
    def test_moi_van_ban_sua_doi_deu_duoc_mo_hinh_hoa(self, kq):
        """Văn bản được khai là sửa đổi phải có mặt trong cơ sở tri thức.

        Nếu thiếu, hệ thống đang phục vụ điều khoản có thể đã hết hiệu lực mà
        không hề biết.
        """
        thieu = [v for v in kq.van_de if v.ma == "VAN_BAN_SUA_DOI_THIEU"]
        assert thieu == [], "\n".join(f"  {v.thong_diep}" for v in thieu)


class TestPhamViSuaDoiCuaLuat118:
    """Luật 118/2025/QH15 đã mô hình hoá tới đâu — và CHƯA tới đâu."""

    def test_moi_muc_dan_luat_36_deu_dung_ban_hop_nhat(self, kb):
        """Không phục vụ luật cũ: mọi mục đều trích từ bản hợp nhất sau sửa đổi.

        Đây mới là điều thực sự chặn rủi ro "trả lời bằng điều khoản đã hết
        hiệu lực" — quan trọng hơn việc có bản ghi văn bản sửa đổi hay không.
        """
        dan_luat = [x for tap in (kb.quy_tac, kb.khai_niem)
                    for x in tap if "Luật" in x.can_cu.van_ban]
        thieu = [x.id for x in dan_luat if "hợp nhất" not in x.can_cu_text]
        assert thieu == [], f"{len(thieu)}/{len(dan_luat)} mục không dẫn bản hợp nhất"

    def test_dieu_khoan_bi_sua_doi_co_ghi_xuat_xu(self, kb):
        """Mục rơi đúng vào khoản bị Luật 118 sửa phải khai sua_doi_boi."""
        can_khai = {"R15", "R87", "KN_PHUONG_TIEN_GIAO_THONG_THONG_MINH"}
        thieu = [x.id for tap in (kb.quy_tac, kb.khai_niem) for x in tap
                 if x.id in can_khai and not x.sua_doi_boi]
        assert thieu == [], f"Thiếu khai báo sửa đổi: {thieu}"

    def test_hieu_luc_theo_dung_moc_cua_luat_sua_doi(self, kb):
        """R15 mang nguyên văn SAU sửa đổi nên chỉ có hiệu lực từ 01/7/2026."""
        r15 = next(r for r in kb.quy_tac if r.id == "R15")
        assert r15.hieu_luc is not None
        assert r15.hieu_luc.tu == date(2026, 7, 1), (
            f"R15 phải hiệu lực từ 01/7/2026, đang là {r15.hieu_luc.tu}")

    @pytest.mark.xfail(strict=True, reason=(
        "Khoảng trống DỮ LIỆU còn lại, đã khoanh vùng chứ không bỏ ngỏ: Điều 7 "
        "Luật 118/2025/QH15 gồm 23 khoản, ứng với 46 chú thích trong Văn bản "
        "hợp nhất 55/VBHN-VPQH (đã trích ra data/raw/luat118_dieu7_chu_thich."
        "json). Chưa mô hình hoá chúng thành bản ghi SuaDoi vì mô hình SuaDoi "
        "hiện chỉ có trường dieu_nd168/khoan_nd168 — đóng khung theo Nghị định "
        "168, không biểu diễn được sửa đổi ở tầng LUẬT. Cần tổng quát hoá mô "
        "hình trước, đó là việc riêng."))
    def test_moi_khoan_sua_doi_cua_luat_118_deu_co_ban_ghi(self, kb):
        sd = [s for s in kb.sua_doi if "118/2025" in s.can_cu.van_ban]
        assert len(sd) == 46, f"Mới mô hình hoá {len(sd)}/46 chú thích sửa đổi"


class TestCanhBaoChatLuongDuLieu:
    """Cảnh báo không chặn CI nhưng phải hiện diện, không được im lặng."""

    def test_bao_cao_che_tai_ghi_dang_van_ban_tu_do(self, kq):
        cb = [v for v in kq.van_de if v.ma == "CHE_TAI_PHI_CAU_TRUC"]
        assert cb, "Phải cảnh báo các điều khoản ghi chế tài dưới dạng văn bản tự do"
        assert all(v.muc_do is MucDo.CANH_BAO for v in cb)

    def test_bao_cao_khai_niem_khong_co_dinh_nghia(self, kq):
        cb = [v for v in kq.van_de if v.ma == "KHAI_NIEM_KHONG_DINH_NGHIA"]
        assert cb, "Phải cảnh báo các khái niệm không có định nghĩa trong luật"
