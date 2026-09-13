"""Kiểm thử tầng mô hình dữ liệu thuần (domain).

Tầng này không đọc tệp, không phụ thuộc thư viện ngoài nào ngoài Pydantic.
Nhiệm vụ của nó là làm cho dữ liệu sai KHÔNG THỂ tồn tại trong bộ nhớ.
"""
import pytest
from pydantic import ValidationError

from traffic_law.domain.models import Citation, Concept, Fine, Relation, Violation


class TestCitation:
    def test_citation_requires_a_document(self):
        cc = Citation(documents="Nghị định 168/2024/NĐ-CP", article=6, clause=1, point="a")
        assert cc.documents and cc.article == 6

    def test_missing_document_is_rejected(self):
        with pytest.raises(ValidationError):
            Citation(article=6)

    def test_blank_text_is_rejected(self):
        """Căn cứ pháp lý rỗng nghĩa là không truy được về văn bản gốc."""
        with pytest.raises(ValidationError):
            Citation(documents="   ")


class TestFine:
    def test_valid_fine(self):
        mp = Fine(min=400_000, max=600_000, unit="VND")
        assert mp.min <= mp.max

    def test_min_above_max_is_rejected(self):
        with pytest.raises(ValidationError):
            Fine(min=600_000, max=400_000, unit="VND")

    def test_negative_fine_is_rejected(self):
        with pytest.raises(ValidationError):
            Fine(min=-1, max=100, unit="VND")


class TestConcept:
    def test_valid_concept(self):
        kn = Concept(
            id="KN_XE_CO_GIOI", name="Xe cơ giới", kind="concepts",
            definition="Xe cơ giới bao gồm ô tô, mô tô...",
            citation=Citation(documents="Luật 36/2024/QH15", article=34, clause=1),
            citation_text="Điều 34 khoản 1 Luật 36/2024/QH15",
        )
        assert kn.id.startswith("KN_")

    def test_allows_missing_definition_when_attributes_exist(self):
        """9/73 khái niệm không được luật định nghĩa (vd "nồng độ cồn" chỉ bị cấm
        tại Điều 9 khoản 2, không được định nghĩa). Nội dung nằm ở thuoc_tinh."""
        kn = Concept(
            id="KN_NONG_DO_CON", name="Nồng độ cồn", kind="concepts",
            definition=None,
            attributes={"threshold": "Luật cấm tuyệt đối, không quy định ngưỡng cho phép"},
            citation=Citation(documents="Luật 36/2024/QH15", article=9, clause=2),
            citation_text="Điều 9 khoản 2 Luật 36/2024/QH15",
        )
        assert kn.definition is None and kn.attributes

    def test_wholly_empty_concept_is_rejected(self):
        """Không có định nghĩa VÀ không có thuộc tính = không mang thông tin gì."""
        with pytest.raises(ValidationError):
            Concept(
                id="KN_X", name="X", kind="concepts", definition=None, attributes={},
                citation=Citation(documents="Luật 36/2024/QH15"), citation_text="Điều 1",
            )


class TestViolation:
    def _vp(self, **kw):
        mac_dinh = dict(
            id="VP_TEST", behavior="Vượt đèn đỏ", group="den_tin_hieu",
            subject="nguoi_dieu_khien", vehicles=["xe_may"],
            fine=Fine(min=4_000_000, max=6_000_000, unit="VND"),
            licence_points=6, field="LV_QUY_TAC", group_name="Đèn tín hiệu",
            citation=Citation(documents="Nghị định 168/2024/NĐ-CP", article=7, clause=9),
            citation_text="Điều 7 khoản 9 Nghị định 168/2024/NĐ-CP",
        )
        mac_dinh.update(kw)
        return Violation(**mac_dinh)

    def test_valid_violation(self):
        assert self._vp().licence_points == 6

    def test_negative_licence_points_rejected(self):
        with pytest.raises(ValidationError):
            self._vp(licence_points=-1)

    def test_licence_points_above_12_rejected(self):
        """Giấy phép lái xe chỉ có 12 điểm; trừ quá 12 là dữ liệu sai."""
        with pytest.raises(ValidationError):
            self._vp(licence_points=13)

    def test_requires_at_least_one_penalty(self):
        """Hành vi vi phạm không có chế tài nào thì không phải hành vi vi phạm."""
        with pytest.raises(ValidationError):
            self._vp(fine=Fine(min=0, max=0, unit="VND"),
                     licence_points=0, extra_penalties=[], remedies=[])


class TestRelation:
    def test_valid_relation(self):
        qh = Relation(name="la_loai_cua", relation_kind="phan_cap",
                    source="KN_XE_O_TO", target="KN_XE_CO_GIOI", description="...")
        assert qh.source != qh.target

    def test_self_referencing_relation_is_rejected(self):
        """Quan hệ trỏ về chính nó tạo vòng lặp vô hạn khi duyệt đồ thị tri thức."""
        with pytest.raises(ValidationError):
            Relation(name="la_loai_cua", relation_kind="phan_cap",
                   source="KN_X", target="KN_X", description="...")
