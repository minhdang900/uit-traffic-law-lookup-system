"""Kiểm tra toàn vẹn liên tệp của cơ sở tri thức.

Mô hình dữ liệu (``domain.models``) bảo đảm từng bản ghi hợp lệ khi đứng một
mình. Tầng này kiểm những ràng buộc chỉ thấy được khi nhìn toàn bộ cơ sở tri
thức: quan hệ trỏ tới đâu, keyphrase dẫn tới đâu, văn bản sửa đổi đã được mô
hình hoá chưa.

Hai mức độ:
    LOI       — chặn CI. Cơ sở tri thức không dùng được.
    CANH_BAO  — không chặn, nhưng phải hiện diện để không bị bỏ quên.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tra_cuu_gtdb.kb.loader import CoSoTriThuc

# Quan hệ có thể trỏ tới nhóm phân loại thay vì một thực thể tri thức cụ thể.
TIEN_TO_NHOM = "NHOM_"


class MucDo(Enum):
    LOI = "loi"
    CANH_BAO = "canh_bao"


@dataclass(frozen=True)
class VanDe:
    """Một vấn đề phát hiện được, kèm mã để test bám vào."""

    muc_do: MucDo
    ma: str
    thong_diep: str


@dataclass
class KetQuaKiemTra:
    van_de: list[VanDe] = field(default_factory=list)

    @property
    def loi(self) -> list[VanDe]:
        return [v for v in self.van_de if v.muc_do is MucDo.LOI]

    @property
    def canh_bao(self) -> list[VanDe]:
        return [v for v in self.van_de if v.muc_do is MucDo.CANH_BAO]

    @property
    def dat(self) -> bool:
        """Đạt khi không còn lỗi nghiêm trọng; cảnh báo vẫn cho qua."""
        return not self.loi

    def _them(self, muc_do: MucDo, ma: str, thong_diep: str) -> None:
        self.van_de.append(VanDe(muc_do, ma, thong_diep))

    def loi_(self, ma: str, thong_diep: str) -> None:
        self._them(MucDo.LOI, ma, thong_diep)

    def canh_bao_(self, ma: str, thong_diep: str) -> None:
        self._them(MucDo.CANH_BAO, ma, thong_diep)


def _kiem_trung_dinh_danh(kb: CoSoTriThuc, kq: KetQuaKiemTra) -> None:
    for ten, ids in (
        ("khái niệm", [c.id for c in kb.khai_niem]),
        ("quy tắc", [r.id for r in kb.quy_tac]),
        ("hành vi", [v.id for v in kb.vi_pham]),
    ):
        trung = sorted({i for i in ids if ids.count(i) > 1})
        if trung:
            kq.loi_("DINH_DANH_TRUNG", f"Định danh {ten} bị trùng: {trung[:10]}")


def _kiem_quan_he(kb: CoSoTriThuc, kq: KetQuaKiemTra) -> None:
    hop_le = kb.dinh_danh_tri_thuc
    treo: list[str] = []
    for q in kb.quan_he:
        for vai, gia_tri in (("nguồn", q.nguon), ("đích", q.dich)):
            if not gia_tri.startswith(TIEN_TO_NHOM) and gia_tri not in hop_le:
                treo.append(f"{q.ten}: {vai}={gia_tri}")
    if treo:
        kq.loi_("QUAN_HE_TREO",
                f"{len(treo)} quan hệ trỏ tới định danh không tồn tại: {treo[:10]}")


def _kiem_keyphrase(kb: CoSoTriThuc, kq: KetQuaKiemTra) -> None:
    id_kn = {c.id for c in kb.khai_niem}
    id_qt = {r.id for r in kb.quy_tac}
    id_vp = {v.id for v in kb.vi_pham}
    treo: list[str] = []
    for k in kb.cum_tu_khoa:
        treo += [f"{k.cum_tu}→{x}" for x in k.khai_niem if x not in id_kn]
        treo += [f"{k.cum_tu}→{x}" for x in k.quy_tac if x not in id_qt]
        treo += [f"{k.cum_tu}→{x}" for x in k.hanh_vi if x not in id_vp]
    if treo:
        kq.loi_("KEYPHRASE_TREO",
                f"{len(treo)} keyphrase trỏ tới định danh không tồn tại: {treo[:10]}")


def _kiem_van_ban_sua_doi(kb: CoSoTriThuc, kq: KetQuaKiemTra) -> None:
    """Mọi văn bản được khai là sửa đổi phải có mặt trong cơ sở tri thức.

    Thiếu một văn bản sửa đổi nghĩa là hệ thống có thể đang phục vụ điều khoản
    đã hết hiệu lực mà không hề biết — rủi ro pháp lý nghiêm trọng nhất của một
    hệ tra cứu pháp luật.
    """
    so_hieu_da_co = {v.so_hieu for v in kb.van_ban}
    for vb in kb.van_ban:
        for sd in vb.sua_doi_boi:
            if not any(sh in sd for sh in so_hieu_da_co):
                kq.loi_(
                    "VAN_BAN_SUA_DOI_THIEU",
                    f"{vb.so_hieu} khai bị sửa đổi bởi {sd!r} nhưng văn bản này "
                    f"chưa được mô hình hoá trong documents.json")


def _kiem_nhat_quan_sua_doi(kb: CoSoTriThuc, kq: KetQuaKiemTra) -> None:
    """Dấu hiệu sửa đổi phải nhất quán, có phân biệt BỔ SUNG với SỬA ĐỔI.

    Một văn bản sửa đổi vừa có thể SỬA điều khoản cũ, vừa có thể BỔ SUNG điều
    khoản mới. Hai trường hợp này có dấu hiệu khác nhau và đều hợp lệ:

    - **Bổ sung**: ``sua_doi_boi`` trỏ tới văn bản đã tạo ra nó, ``tinh_trang``
      là ``hien_hanh``, KHÔNG có bản trước (vì chưa từng tồn tại).
    - **Sửa đổi**: ``sua_doi_boi`` trỏ tới văn bản đã sửa nó, ``tinh_trang`` là
      ``da_sua_doi``, CÓ ``hanh_vi_truoc_sua_doi``.

    Chỉ báo lỗi khi hai dấu hiệu mâu thuẫn thực sự — lúc đó không xác định được
    bản ghi đang lưu nội dung trước hay sau sửa đổi, dẫn thẳng tới mức phạt sai.
    """
    lech: list[str] = []
    for v in kb.vi_pham:
        danh_dau_sua = v.tinh_trang == "da_sua_doi"
        co_ban_cu = bool(v.hanh_vi_truoc_sua_doi)
        if danh_dau_sua and not co_ban_cu:
            lech.append(f"{v.id}: đánh dấu da_sua_doi nhưng thiếu hanh_vi_truoc_sua_doi")
        elif co_ban_cu and not danh_dau_sua:
            lech.append(f"{v.id}: có hanh_vi_truoc_sua_doi nhưng tinh_trang={v.tinh_trang!r}")
        elif co_ban_cu and not v.sua_doi_boi:
            lech.append(f"{v.id}: có bản trước nhưng không khai sua_doi_boi")
    if lech:
        kq.loi_("SUA_DOI_KHONG_NHAT_QUAN",
                f"{len(lech)} điều khoản có dấu hiệu sửa đổi mâu thuẫn: {lech[:10]}")


def _kiem_hieu_luc(kb: CoSoTriThuc, kq: KetQuaKiemTra) -> None:
    """Mọi điều khoản phải có khoảng hiệu lực (chạy scripts/suy_dien_hieu_luc.py)."""
    thieu = [x.id for tap in (kb.quy_tac, kb.vi_pham) for x in tap if x.hieu_luc is None]
    if thieu:
        kq.loi_("THIEU_KHOANG_HIEU_LUC",
                f"{len(thieu)} điều khoản chưa có khoảng hiệu lực: {thieu[:10]}")


def _canh_bao_chat_luong(kb: CoSoTriThuc, kq: KetQuaKiemTra) -> None:
    phi_cau_truc = [
        v.id for v in kb.vi_pham
        if not v.phat_tien.co_phat_tien and not v.tru_diem_gplx
        and not v.hinh_phat_bo_sung and not v.bien_phap_khac_phuc
        and v.phat_tien.co_che_tai_phi_tien
    ]
    if phi_cau_truc:
        kq.canh_bao_(
            "CHE_TAI_PHI_CAU_TRUC",
            f"{len(phi_cau_truc)} điều khoản ghi chế tài (cảnh cáo / tịch thu) dưới "
            f"dạng văn bản tự do trong phat_tien.ghi_chu thay vì trường có cấu "
            f"trúc: {phi_cau_truc[:10]}")

    khong_dinh_nghia = [c.id for c in kb.khai_niem if not c.dinh_nghia]
    if khong_dinh_nghia:
        kq.canh_bao_(
            "KHAI_NIEM_KHONG_DINH_NGHIA",
            f"{len(khong_dinh_nghia)} khái niệm không có định nghĩa trong luật, chỉ "
            f"có thuộc tính — lớp bài toán P1 phải trả lời bằng thuộc tính và căn "
            f"cứ: {khong_dinh_nghia[:10]}")


def kiem_tra_toan_ven(kb: CoSoTriThuc) -> KetQuaKiemTra:
    """Chạy toàn bộ kiểm tra toàn vẹn và trả về danh sách vấn đề."""
    kq = KetQuaKiemTra()
    _kiem_trung_dinh_danh(kb, kq)
    _kiem_quan_he(kb, kq)
    _kiem_keyphrase(kb, kq)
    _kiem_van_ban_sua_doi(kb, kq)
    _kiem_nhat_quan_sua_doi(kb, kq)
    _kiem_hieu_luc(kb, kq)
    _canh_bao_chat_luong(kb, kq)
    return kq
