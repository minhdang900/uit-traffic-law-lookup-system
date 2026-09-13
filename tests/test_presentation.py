"""Kiểm thử tầng trình bày của giao diện tra cứu.

VÌ SAO TÁCH RIÊNG KHỎI STREAMLIT
=================================
Mã Streamlit gần như không kiểm thử được: nó vẽ thẳng ra khung chạy của nó.
Nên toàn bộ phần CÓ THỂ SAI — định dạng tiền, gom kết quả, xếp mức tin cậy —
nằm ở ``api/trinh_bay.py`` dưới dạng hàm thuần, còn ``api/app.py`` chỉ là vỏ
mỏng gọi xuống. Tệp này kiểm phần hàm thuần đó.
"""
import pytest

from traffic_law.api.presentation import (
    confidence,
    fine_text,
    penalty_lines,
    result_cards,
    summary_line,
)


class TestConfidence:
    """Điểm số thô vô nghĩa với người dùng; phải quy thành nhãn đọc được."""

    @pytest.mark.parametrize("point,expected", [
        (0.95, "cao"), (0.80, "cao"),
        (0.79, "trung bình"), (0.60, "trung bình"),
        (0.59, "thấp"), (0.0, "thấp"),
    ])
    def test_bands_are_assigned_correctly(self, point, expected):
        assert confidence(point) == expected

    def test_missing_score_counts_as_low(self):
        """Kết quả tra theo căn cứ không có điểm — không được nổ lỗi."""
        assert confidence(None) == "thấp"


class TestPenaltyLines:
    """Chế tài phải đọc được như người Việt viết, không phải như JSON."""

    def test_formats_money_the_vietnamese_way(self):
        v = {"fine": {"min": 4000000, "max": 6000000}, "licence_points": None,
             "extra_penalties": [], "remedies": []}
        assert penalty_lines(v) == ["Phạt tiền: từ 4.000.000 đồng đến 6.000.000 đồng"]

    def test_fixed_fine_omits_from_to(self):
        v = {"fine": {"min": 500000, "max": 500000}, "licence_points": None,
             "extra_penalties": [], "remedies": []}
        assert penalty_lines(v) == ["Phạt tiền: 500.000 đồng"]

    def test_no_fine_is_stated_explicitly(self):
        """Im lặng ở đây khiến người đọc tưởng chưa tra ra chế tài."""
        v = {"fine": {"min": None, "max": None}, "licence_points": None,
             "extra_penalties": [], "remedies": []}
        assert penalty_lines(v) == ["Không quy định phạt tiền"]

    def test_includes_every_kind_of_penalty(self):
        v = {"fine": {"min": 6000000, "max": 8000000}, "licence_points": 10,
             "extra_penalties": ["Tịch thu phương tiện"],
             "remedies": ["Buộc khôi phục lại tình trạng ban đầu"]}
        assert penalty_lines(v) == [
            "Phạt tiền: từ 6.000.000 đồng đến 8.000.000 đồng",
            "Trừ 10 điểm giấy phép lái xe",
            "Hình phạt bổ sung: Tịch thu phương tiện",
            "Biện pháp khắc phục: Buộc khôi phục lại tình trạng ban đầu",
        ]


class TestResultCards:
    """Gom ba loại tri thức thành danh sách thẻ để giao diện chỉ việc vẽ."""

    def test_groups_all_three_kinds_in_priority_order(self, system):
        kq = system.ask("vượt đèn đỏ xe máy phạt bao nhiêu", top_k=2)
        the = result_cards(kq)
        assert the, "Phải có ít nhất một thẻ"
        kind = [t.kind for t in the]
        assert kind == sorted(kind, key=["violations", "rules", "concepts"].index), (
            f"Sai thứ tự ưu tiên: {kind}")

    def test_every_card_has_a_legal_citation(self, system):
        """Không có căn cứ thì người dùng không kiểm chứng được — vô dụng."""
        for t in result_cards(system.ask("xe cơ giới là gì", top_k=3)):
            assert t.citation.strip(), f"Thẻ {t.title!r} thiếu căn cứ"

    def test_card_carries_the_knowledge_id(self, system):
        """Bản thiết kế có link "Xem điều khoản →" nên thẻ phải mang định danh."""
        for t in result_cards(system.ask("vượt đèn đỏ xe máy phạt bao nhiêu", top_k=2)):
            assert t.id_, f"Thẻ {t.title!r} không mang id"

    def test_marks_supplementary_knowledge(self, system):
        """Người dùng cần biết mẩu nào là trả lời chính, mẩu nào chỉ gợi thêm."""
        the = result_cards(system.ask("xe cơ giới là gì", top_k=3))
        assert any(t.kind == "concepts" and not t.supplementary for t in the)

    def test_out_of_domain_query_does_not_raise(self, system):
        result_cards(system.ask("cách nấu phở bò"))  # khong duoc nem ngoai le


class TestSummaryLine:
    def test_states_the_problem_class_name(self, system):
        assert "chế tài" in summary_line(system.ask("vượt đèn đỏ phạt bao nhiêu")).lower()

    def test_says_so_when_nothing_found(self):
        kq = {"not_found": True, "problem_class_name": "Tra cứu kiến thức liên quan",
              "concepts": [], "rules": [], "violations": []}
        assert "không tìm thấy" in summary_line(kq).lower()


class TestFineText:
    """Bản thiết kế rút hậu tố thành "đ" và dùng en dash cho khoảng."""

    def test_khoang_dung_en_dash_va_hau_to_ngan(self):
        assert fine_text({"min": 4_000_000, "max": 6_000_000}) == "4.000.000 – 6.000.000 đ"

    def test_muc_co_dinh_chi_mot_so(self):
        assert fine_text({"min": 1_500_000, "max": 1_500_000}) == "1.500.000 đ"

    def test_bang_khong_la_canh_cao_chu_khong_phai_0_dong(self):
        assert fine_text({"min": 0, "max": 0}) == "Không phạt tiền (cảnh cáo hoặc hình thức khác)"

    def test_khong_quy_dinh_phat_tien(self):
        assert fine_text({"min": None, "max": None}) == "Không quy định phạt tiền"
