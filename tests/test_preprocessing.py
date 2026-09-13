"""Kiểm thử tầng tiền xử lý ngôn ngữ của kb_engine.

Đây là tầng thấp nhất của hệ thống: mọi truy vấn đều đi qua đây trước khi được
rút trích keyphrase và phân loại. Sai ở đây thì sai toàn hệ thống.
"""
import pytest

from traffic_law.reasoning.engine import normalise, parse_money, strip_accents


class TestStripAccents:
    """bo_dau() — chuyển tiếng Việt về dạng không dấu, phục vụ so khớp keyphrase."""

    def test_strip_accents_on_accented_vietnamese(self):
        assert strip_accents("Vượt đèn đỏ") == "vuot den do"

    def test_strip_accents_converts_d_with_stroke(self):
        """Chữ 'đ' không phải dấu thanh nên unicodedata không xử lý được, phải thay tay."""
        assert strip_accents("Đường bộ") == "duong bo"
        assert "đ" not in strip_accents("đèn đỏ")

    def test_strip_accents_lowercases(self):
        assert strip_accents("NỒNG ĐỘ CỒN") == "nong do con"

    def test_strip_accents_handles_empty_string(self):
        assert strip_accents("") == ""
        assert strip_accents(None) == ""


class TestNormalise:
    """chuan_hoa() — chuẩn hoá truy vấn người dùng nhập."""

    def test_normalise_collapses_spaces_and_lowercases(self):
        assert normalise("  Phạt   BAO nhiêu?? ") == "phạt bao nhiêu"

    def test_normalise_preserves_vietnamese_accents(self):
        """Khác bo_dau: chuan_hoa PHẢI giữ dấu để so khớp chính xác."""
        assert "ồ" in normalise("Nồng độ cồn")

    def test_normalise_keeps_legally_meaningful_characters(self):
        """Dấu %, /, - mang nghĩa trong văn bản pháp luật (mg/l, 20-35 km/h)."""
        kq = normalise("0,25 miligam/1 lít")
        assert "/" in kq and "," in kq

    def test_normalise_handles_empty_string(self):
        assert normalise("") == ""
        assert normalise(None) == ""


class TestParseMoney:
    """tach_so_tien() — rút trích số tiền, phục vụ lớp P4 (tra cứu ngược theo mức phạt)."""

    @pytest.mark.parametrize("query,expected", [
        ("phạt 2 triệu", [2_000_000]),
        ("5 tỷ", [5_000_000_000]),
        ("800 nghìn", [800_000]),
        ("phạt 500 ngàn đồng", [500_000]),
    ])
    def test_parses_currency_units_correctly(self, query, expected):
        assert parse_money(query) == expected

    def test_returns_empty_when_no_amount(self):
        assert parse_money("vượt đèn đỏ phạt bao nhiêu") == []

    def test_garbage_string_does_not_raise(self):
        """Hàm có khối try/except ValueError nuốt lỗi im lặng (kb_engine.py:77-79).
        Test này khoá lại hành vi đó: nuốt lỗi là CHẤP NHẬN ĐƯỢC ở đây, nhưng
        không được sập chương trình."""
        assert parse_money("abc xyz !!!") == []
        assert parse_money("...,,,") == []

    def test_parses_several_amounts_in_one_query(self):
        """Lớp P4 cần bắt được khoảng: 'từ 2 triệu đến 3 triệu'."""
        kq = parse_money("từ 2 triệu đến 3 triệu")
        assert 2_000_000 in kq and 3_000_000 in kq
