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

from traffic_law.kb.loader import KnowledgeBase

# Quan hệ có thể trỏ tới nhóm phân loại thay vì một thực thể tri thức cụ thể.
TIEN_TO_NHOM = "NHOM_"


class Severity(Enum):
    LOI = "errors"
    CANH_BAO = "warnings"


@dataclass(frozen=True)
class Issue:
    """Một vấn đề phát hiện được, kèm mã để test bám vào."""

    severity: Severity
    code: str
    message: str


@dataclass
class ValidationReport:
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [v for v in self.issues if v.severity is Severity.LOI]

    @property
    def warnings(self) -> list[Issue]:
        return [v for v in self.issues if v.severity is Severity.CANH_BAO]

    @property
    def ok(self) -> bool:
        """Đạt khi không còn lỗi nghiêm trọng; cảnh báo vẫn cho qua."""
        return not self.errors

    def _them(self, severity: Severity, code: str, message: str) -> None:
        self.issues.append(Issue(severity, code, message))

    def error_(self, code: str, message: str) -> None:
        self._them(Severity.LOI, code, message)

    def warn_(self, code: str, message: str) -> None:
        self._them(Severity.CANH_BAO, code, message)


def _kiem_trung_dinh_danh(kb: KnowledgeBase, kq: ValidationReport) -> None:
    for name, ids in (
        ("khái niệm", [c.id for c in kb.concepts]),
        ("quy tắc", [r.id for r in kb.rules]),
        ("hành vi", [v.id for v in kb.violations]),
    ):
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        if duplicates:
            kq.error_("DINH_DANH_TRUNG", f"Định danh {name} bị trùng: {duplicates[:10]}")


def _kiem_quan_he(kb: KnowledgeBase, kq: ValidationReport) -> None:
    hop_le = kb.knowledge_ids
    treo: list[str] = []
    for q in kb.relations:
        for vai, value in (("nguồn", q.source), ("đích", q.target)):
            if not value.startswith(TIEN_TO_NHOM) and value not in hop_le:
                treo.append(f"{q.name}: {vai}={value}")
    if treo:
        kq.error_("QUAN_HE_TREO",
                f"{len(treo)} quan hệ trỏ tới định danh không tồn tại: {treo[:10]}")


def _kiem_keyphrase(kb: KnowledgeBase, kq: ValidationReport) -> None:
    id_kn = {c.id for c in kb.concepts}
    id_qt = {r.id for r in kb.rules}
    id_vp = {v.id for v in kb.violations}
    treo: list[str] = []
    for k in kb.keyphrases:
        treo += [f"{k.phrase}→{x}" for x in k.concept_ids if x not in id_kn]
        treo += [f"{k.phrase}→{x}" for x in k.rule_ids if x not in id_qt]
        treo += [f"{k.phrase}→{x}" for x in k.violation_ids if x not in id_vp]
    if treo:
        kq.error_("KEYPHRASE_TREO",
                f"{len(treo)} keyphrase trỏ tới định danh không tồn tại: {treo[:10]}")


def _kiem_van_ban_sua_doi(kb: KnowledgeBase, kq: ValidationReport) -> None:
    """Mọi văn bản được khai là sửa đổi phải có mặt trong cơ sở tri thức.

    Thiếu một văn bản sửa đổi nghĩa là hệ thống có thể đang phục vụ điều khoản
    đã hết hiệu lực mà không hề biết — rủi ro pháp lý nghiêm trọng nhất của một
    hệ tra cứu pháp luật.
    """
    so_hieu_da_co = {v.number for v in kb.documents}
    for vb in kb.documents:
        for sd in vb.amended_by:
            if not any(sh in sd for sh in so_hieu_da_co):
                kq.error_(
                    "VAN_BAN_SUA_DOI_THIEU",
                    f"{vb.number} khai bị sửa đổi bởi {sd!r} nhưng văn bản này "
                    f"chưa được mô hình hoá trong documents.json")


def _kiem_nhat_quan_sua_doi(kb: KnowledgeBase, kq: ValidationReport) -> None:
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
    for v in kb.violations:
        danh_dau_sua = v.status == "da_sua_doi"
        co_ban_cu = bool(v.behavior_before_amendment)
        if danh_dau_sua and not co_ban_cu:
            lech.append(f"{v.id}: đánh dấu da_sua_doi nhưng thiếu hanh_vi_truoc_sua_doi")
        elif co_ban_cu and not danh_dau_sua:
            lech.append(f"{v.id}: có hanh_vi_truoc_sua_doi nhưng tinh_trang={v.status!r}")
        elif co_ban_cu and not v.amended_by:
            lech.append(f"{v.id}: có bản trước nhưng không khai sua_doi_boi")
    if lech:
        kq.error_("SUA_DOI_KHONG_NHAT_QUAN",
                f"{len(lech)} điều khoản có dấu hiệu sửa đổi mâu thuẫn: {lech[:10]}")


def _kiem_hieu_luc(kb: KnowledgeBase, kq: ValidationReport) -> None:
    """Mọi điều khoản phải có khoảng hiệu lực (chạy scripts/suy_dien_hieu_luc.py)."""
    missing = [x.id for tap in (kb.rules, kb.violations) for x in tap if x.validity is None]
    if missing:
        kq.error_("THIEU_KHOANG_HIEU_LUC",
                f"{len(missing)} điều khoản chưa có khoảng hiệu lực: {missing[:10]}")


def _canh_bao_chat_luong(kb: KnowledgeBase, kq: ValidationReport) -> None:
    phi_cau_truc = [
        v.id for v in kb.violations
        if not v.fine.has_fine and not v.licence_points
        and not v.extra_penalties and not v.remedies
        and v.fine.has_non_monetary_penalty
    ]
    if phi_cau_truc:
        kq.warn_(
            "CHE_TAI_PHI_CAU_TRUC",
            f"{len(phi_cau_truc)} điều khoản ghi chế tài (cảnh cáo / tịch thu) dưới "
            f"dạng văn bản tự do trong phat_tien.ghi_chu thay vì trường có cấu "
            f"trúc: {phi_cau_truc[:10]}")

    khong_dinh_nghia = [c.id for c in kb.concepts if not c.definition]
    if khong_dinh_nghia:
        kq.warn_(
            "KHAI_NIEM_KHONG_DINH_NGHIA",
            f"{len(khong_dinh_nghia)} khái niệm không có định nghĩa trong luật, chỉ "
            f"có thuộc tính — lớp bài toán P1 phải trả lời bằng thuộc tính và căn "
            f"cứ: {khong_dinh_nghia[:10]}")


def check_integrity(kb: KnowledgeBase) -> ValidationReport:
    """Chạy toàn bộ kiểm tra toàn vẹn và trả về danh sách vấn đề."""
    kq = ValidationReport()
    _kiem_trung_dinh_danh(kb, kq)
    _kiem_quan_he(kb, kq)
    _kiem_keyphrase(kb, kq)
    _kiem_van_ban_sua_doi(kb, kq)
    _kiem_nhat_quan_sua_doi(kb, kq)
    _kiem_hieu_luc(kb, kq)
    _canh_bao_chat_luong(kb, kq)
    return kq
