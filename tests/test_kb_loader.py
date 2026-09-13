"""Kiểm thử việc nạp cơ sở tri thức từ JSON."""
from pathlib import Path

import pytest

from traffic_law.kb.loader import KnowledgeLoadError, load_knowledge_base

pytestmark = pytest.mark.cham


class TestLoadsSuccessfully:
    def test_loads_the_published_scale(self, kb):
        """Khoá mức sàn theo số liệu trong báo cáo đồ án.
        Dùng >= để còn mở rộng cơ sở tri thức mà không làm đỏ test."""
        tk = kb.stats()
        assert tk["concepts"] >= 73
        assert tk["relations"] >= 482
        assert tk["rules"] >= 109
        assert tk["violations"] >= 345
        assert tk["keyphrases"] >= 1674
        assert tk["documents"] >= 3
        assert tk["amendments"] >= 63

    def test_taxonomy_is_complete(self, kb):
        pl = kb.taxonomy
        assert pl.field and pl.group_name and pl.vehicle_names
        assert pl.subject_names and pl.synonyms

    def test_document_has_effective_date(self, kb):
        """Ngày hiệu lực là nền tảng cho việc mô hình hoá hiệu lực theo thời gian."""
        for vb in kb.documents:
            assert vb.effective_from >= vb.issued_on

    def test_knowledge_base_is_immutable(self, kb):
        """Dữ liệu nạp xong là bất biến — tránh sửa nhầm giữa các truy vấn."""
        with pytest.raises((AttributeError, TypeError, ValueError)):
            kb.concepts[0].name = "đổi tên"  # type: ignore[misc]


class TestClearErrors:
    def test_missing_directory(self):
        with pytest.raises(KnowledgeLoadError, match="Không tìm thấy thư mục"):
            load_knowledge_base(Path("/khong/ton/tai"))

    def test_missing_file_names_the_file(self, tmp_path):
        with pytest.raises(KnowledgeLoadError, match="concepts.json"):
            load_knowledge_base(tmp_path)

    def test_broken_json_names_the_file(self, tmp_path):
        (tmp_path / "concepts.json").write_text("{khong phai json", encoding="utf-8")
        with pytest.raises(KnowledgeLoadError, match="không phải JSON hợp lệ"):
            load_knowledge_base(tmp_path)

    def test_bad_record_names_the_identifier(self, tmp_path):
        """Thông điệp lỗi phải chỉ đúng bản ghi nào sai, không ném vết ngăn xếp thô."""
        (tmp_path / "concepts.json").write_text(
            '[{"id": "KN_X", "ten": "X", "loai": "kn", "dinh_nghia": "d", '
            '"can_cu": {"van_ban": ""}, "can_cu_text": "Điều 1"}]', encoding="utf-8")
        with pytest.raises(KnowledgeLoadError, match="KN_X"):
            load_knowledge_base(tmp_path)
