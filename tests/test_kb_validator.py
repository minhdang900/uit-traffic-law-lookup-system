"""Kiểm thử tính toàn vẹn của cơ sở tri thức.

Đây là các kiểm tra LIÊN TỆP mà mô hình dữ liệu đơn lẻ không thể phát hiện:
một quan hệ có thể hợp lệ về kiểu nhưng trỏ tới định danh không tồn tại.

Tương ứng yêu cầu của đề bài: *"Đặc tả: các thành phần về khái niệm, dạng luật
trong các quy định."*
"""
from dataclasses import replace
from datetime import date

import pytest

from traffic_law.domain.models import Document
from traffic_law.kb.validator import Severity, check_integrity

pytestmark = pytest.mark.cham


@pytest.fixture(scope="module")
def kq(kb):
    return check_integrity(kb)


# Danh sách rỗng: mọi khoảng trống dữ liệu từng biết đều đã được bịt. Giữ hằng
# số này để lần sau có khoảng trống mới thì khai báo tường minh ở đây, thay vì
# nới lỏng phép kiểm tra.
KHOANG_TRONG_DA_BIET: set[str] = set()


class TestNoErrors:
    def test_no_new_errors(self, kq):
        """Chặn mọi lỗi ngoài danh sách khoảng trống dữ liệu đã biết."""
        moi = [v for v in kq.issues
               if v.severity is Severity.LOI and v.code not in KHOANG_TRONG_DA_BIET]
        assert moi == [], "\n".join(f"  [{v.code}] {v.message}" for v in moi)

    def test_amending_document_check_still_works(self, kb):
        """Đối chứng dương: luật kiểm tra phải BẮT được văn bản sửa đổi bị thiếu.

        Trước đây bài kiểm tra này dựa vào một khoảng trống CÓ THẬT trong dữ
        liệu. Khoảng trống đó đã bịt, nên nếu chỉ xoá bài kiểm tra thì luật này
        có thể hỏng mà không ai biết. Thay bằng đối chứng dựng sẵn: bịa ra một
        văn bản khai bị sửa bởi một số hiệu không tồn tại, rồi đòi hỏi luật
        kiểm tra phải báo lỗi.
        """
        gia = replace(kb, documents=(
            *kb.documents,
            Document(id="VB_DOI_CHUNG", name="Van ban doi chung",
                   name_vn="Văn bản đối chứng", number="999/9999/QH99",
                   issued_on=date(2099, 1, 1), effective_from=date(2099, 1, 2),
                   amended_by=["Luật 000/0000/QH00 (không tồn tại)"]),
        ))
        errors = [v for v in check_integrity(gia).issues
               if v.code == "VAN_BAN_SUA_DOI_THIEU"]
        assert errors, "Luật kiểm tra văn bản sửa đổi đã ngừng hoạt động"

    def test_law_118_2025_is_modelled(self, kb):
        """Văn bản sửa đổi Luật 36/2024 phải có mặt, kèm xuất xứ kiểm chứng được."""
        vb = next((v for v in kb.documents if v.number == "118/2025/QH15"), None)
        assert vb is not None, "Thiếu Luật 118/2025/QH15 trong documents.json"
        assert vb.effective_from == date(2026, 7, 1)
        assert vb.issued_on == date(2025, 12, 10)
        assert vb.note and "55/VBHN-VPQH" in vb.note, (
            "Phải ghi rõ xuất xứ siêu dữ liệu để kiểm chứng lại được")


class TestIdentifiers:
    def test_no_duplicate_identifiers(self, kb):
        for name, tap in (("khái niệm", kb.concepts), ("quy tắc", kb.rules),
                         ("hành vi", kb.violations)):
            ids = [x.id for x in tap]
            duplicates = {i for i in ids if ids.count(i) > 1}
            assert not duplicates, f"Định danh {name} trùng: {sorted(duplicates)[:5]}"

    def test_relation_points_to_existing_entities(self, kb):
        hop_le = kb.knowledge_ids
        broken = [f"{q.name}: {q.source}→{q.target}" for q in kb.relations
                if not (q.source.startswith("NHOM_") or q.source in hop_le)
                or not (q.target.startswith("NHOM_") or q.target in hop_le)]
        assert broken == [], f"{len(broken)} quan hệ treo: {broken[:5]}"

    def test_keyphrase_points_to_existing_entities(self, kb):
        id_vp = {v.id for v in kb.violations}
        id_kn = {c.id for c in kb.concepts}
        id_qt = {r.id for r in kb.rules}
        broken = []
        for k in kb.keyphrases:
            broken += [(k.phrase, x) for x in k.violation_ids if x not in id_vp]
            broken += [(k.phrase, x) for x in k.concept_ids if x not in id_kn]
            broken += [(k.phrase, x) for x in k.rule_ids if x not in id_qt]
        assert broken == [], f"{len(broken)} keyphrase treo: {broken[:5]}"


class TestLegalBasis:
    def test_every_knowledge_item_is_traceable(self, kb):
        """Không có căn cứ thì người dùng không kiểm chứng được câu trả lời."""
        missing = [x.id for tap in (kb.concepts, kb.rules, kb.violations)
                 for x in tap if not x.citation_text.strip()]
        assert missing == []


class TestAmendingDocument:
    def test_every_amending_document_is_modelled(self, kq):
        """Văn bản được khai là sửa đổi phải có mặt trong cơ sở tri thức.

        Nếu thiếu, hệ thống đang phục vụ điều khoản có thể đã hết hiệu lực mà
        không hề biết.
        """
        missing = [v for v in kq.issues if v.code == "VAN_BAN_SUA_DOI_THIEU"]
        assert missing == [], "\n".join(f"  {v.message}" for v in missing)


class TestLaw118AmendmentScope:
    """Luật 118/2025/QH15 đã mô hình hoá tới đâu — và CHƯA tới đâu."""

    def test_every_law36_citation_uses_consolidated_text(self, kb):
        """Không phục vụ luật cũ: mọi mục đều trích từ bản hợp nhất sau sửa đổi.

        Đây mới là điều thực sự chặn rủi ro "trả lời bằng điều khoản đã hết
        hiệu lực" — quan trọng hơn việc có bản ghi văn bản sửa đổi hay không.
        """
        dan_luat = [x for tap in (kb.rules, kb.concepts)
                    for x in tap if "Luật" in x.citation.documents]
        missing = [x.id for x in dan_luat if "hợp nhất" not in x.citation_text]
        assert missing == [], f"{len(missing)}/{len(dan_luat)} mục không dẫn bản hợp nhất"

    def test_amended_provisions_record_provenance(self, kb):
        """Mục rơi đúng vào khoản bị Luật 118 sửa phải khai sua_doi_boi."""
        can_khai = {"R15", "R87", "KN_PHUONG_TIEN_GIAO_THONG_THONG_MINH"}
        missing = [x.id for tap in (kb.rules, kb.concepts) for x in tap
                 if x.id in can_khai and not x.amended_by]
        assert missing == [], f"Thiếu khai báo sửa đổi: {missing}"

    def test_validity_follows_amending_law_date(self, kb):
        """R15 mang nguyên văn SAU sửa đổi nên chỉ có hiệu lực từ 01/7/2026."""
        r15 = next(r for r in kb.rules if r.id == "R15")
        assert r15.validity is not None
        assert r15.validity.start == date(2026, 7, 1), (
            f"R15 phải hiệu lực từ 01/7/2026, đang là {r15.validity.start}")

    @pytest.mark.xfail(strict=True, reason=(
        "Khoảng trống DỮ LIỆU còn lại, đã khoanh vùng chứ không bỏ ngỏ: Điều 7 "
        "Luật 118/2025/QH15 gồm 23 khoản, ứng với 46 chú thích trong Văn bản "
        "hợp nhất 55/VBHN-VPQH (đã trích ra data/raw/luat118_dieu7_chu_thich."
        "json). Chưa mô hình hoá chúng thành bản ghi SuaDoi vì mô hình SuaDoi "
        "hiện chỉ có trường dieu_nd168/khoan_nd168 — đóng khung theo Nghị định "
        "168, không biểu diễn được sửa đổi ở tầng LUẬT. Cần tổng quát hoá mô "
        "hình trước, đó là việc riêng."))
    def test_every_law118_amendment_has_a_record(self, kb):
        sd = [s for s in kb.amendments if "118/2025" in s.citation.documents]
        assert len(sd) == 46, f"Mới mô hình hoá {len(sd)}/46 chú thích sửa đổi"


class TestDataQualityWarnings:
    """Cảnh báo không chặn CI nhưng phải hiện diện, không được im lặng."""

    def test_warns_on_free_text_penalties(self, kq):
        cb = [v for v in kq.issues if v.code == "CHE_TAI_PHI_CAU_TRUC"]
        assert cb, "Phải cảnh báo các điều khoản ghi chế tài dưới dạng văn bản tự do"
        assert all(v.severity is Severity.CANH_BAO for v in cb)

    def test_warns_on_concepts_without_definition(self, kq):
        cb = [v for v in kq.issues if v.code == "KHAI_NIEM_KHONG_DINH_NGHIA"]
        assert cb, "Phải cảnh báo các khái niệm không có định nghĩa trong luật"
