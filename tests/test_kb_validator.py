"""Kiểm thử tính toàn vẹn của cơ sở tri thức.

Đây là các kiểm tra LIÊN TỆP mà mô hình dữ liệu đơn lẻ không thể phát hiện:
một quan hệ có thể hợp lệ về kiểu nhưng trỏ tới định danh không tồn tại.

Tương ứng yêu cầu của đề bài: *"Đặc tả: các thành phần về khái niệm, dạng luật
trong các quy định."*
"""
import pytest

from tra_cuu_gtdb.kb.validator import MucDo, kiem_tra_toan_ven

pytestmark = pytest.mark.cham


@pytest.fixture(scope="module")
def kq(kb):
    return kiem_tra_toan_ven(kb)


# Khoảng trống dữ liệu đã biết, cần bổ sung bằng công tác thu thập văn bản chứ
# không phải bằng sửa mã nguồn. Liệt kê tường minh để mọi lỗi MỚI vẫn làm đỏ CI.
KHOANG_TRONG_DA_BIET = {"VAN_BAN_SUA_DOI_THIEU"}


class TestKhongCoLoi:
    def test_khong_phat_sinh_loi_moi(self, kq):
        """Chặn mọi lỗi ngoài danh sách khoảng trống dữ liệu đã biết."""
        moi = [v for v in kq.van_de
               if v.muc_do is MucDo.LOI and v.ma not in KHOANG_TRONG_DA_BIET]
        assert moi == [], "\n".join(f"  [{v.ma}] {v.thong_diep}" for v in moi)

    def test_khoang_trong_da_biet_van_duoc_phat_hien(self, kq):
        """Bảo đảm luật kiểm tra chưa bị vô hiệu hoá: nó PHẢI vẫn báo lỗi."""
        assert [v for v in kq.van_de if v.ma == "VAN_BAN_SUA_DOI_THIEU"], (
            "Luật kiểm tra văn bản sửa đổi đã ngừng hoạt động")


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
    @pytest.mark.xfail(strict=True, reason=(
        "Khoảng trống DỮ LIỆU, không phải lỗi mã nguồn: Luật 36/2024 khai bị sửa "
        "đổi bởi Luật 118/2025/QH15 (hiệu lực 01/7/2026) nhưng văn bản đó chưa "
        "được thu thập. Không tạo bản ghi giả vì bịa siêu dữ liệu pháp lý là sai "
        "nghiêm trọng. Cần bổ sung văn bản gốc rồi bỏ dấu xfail này."))
    def test_moi_van_ban_sua_doi_deu_duoc_mo_hinh_hoa(self, kq):
        """Văn bản được khai là sửa đổi phải có mặt trong cơ sở tri thức.

        Nếu thiếu, hệ thống đang phục vụ điều khoản có thể đã hết hiệu lực mà
        không hề biết. Hiện Luật 36/2024 khai bị sửa bởi Luật 118/2025/QH15
        (hiệu lực 01/7/2026) nhưng văn bản đó chưa được mô hình hoá.
        """
        thieu = [v for v in kq.van_de if v.ma == "VAN_BAN_SUA_DOI_THIEU"]
        assert thieu == [], "\n".join(f"  {v.thong_diep}" for v in thieu)


class TestCanhBaoChatLuongDuLieu:
    """Cảnh báo không chặn CI nhưng phải hiện diện, không được im lặng."""

    def test_bao_cao_che_tai_ghi_dang_van_ban_tu_do(self, kq):
        cb = [v for v in kq.van_de if v.ma == "CHE_TAI_PHI_CAU_TRUC"]
        assert cb, "Phải cảnh báo các điều khoản ghi chế tài dưới dạng văn bản tự do"
        assert all(v.muc_do is MucDo.CANH_BAO for v in cb)

    def test_bao_cao_khai_niem_khong_co_dinh_nghia(self, kq):
        cb = [v for v in kq.van_de if v.ma == "KHAI_NIEM_KHONG_DINH_NGHIA"]
        assert cb, "Phải cảnh báo các khái niệm không có định nghĩa trong luật"
