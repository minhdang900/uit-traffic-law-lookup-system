"""Kiểm thử truy vấn gõ KHÔNG DẤU ở hai bộ nhận dạng cấu trúc.

Bỏ dấu toàn bộ 120 câu hỏi làm Top-1 tụt 76,67% -> 66,67%, và mức tụt dồn hết
vào hai lớp: P6 (tra theo căn cứ) 7/8 -> 0/8, P4 (tra ngược) 8/12 -> 3/12.
Nguyên nhân: ``detect_citation`` và ``detect_constraints`` dò mẫu có dấu
("điều", "khoản", "trừ ... điểm") trên chuỗi chưa bỏ dấu. Phần so khớp
TF-IDF và keyphrase vốn đã chịu được mất dấu.

Nhánh không dấu chỉ bật khi CẢ câu không có dấu, nên câu có dấu đi đúng đường
cũ — cổng chỉ số trên 120 câu có dấu không đổi.
"""
import pytest

from traffic_law.kb.text import strip_accents
from traffic_law.reasoning.engine import P4_TRA_CUU_NGUOC, P6_CAN_CU

pytestmark = pytest.mark.cham


class TestCitationWithoutAccents:
    def test_unaccented_citation_is_recognised(self, system):
        """Cùng một câu hỏi theo căn cứ, có dấu hay không dấu phải ra cùng căn cứ."""
        co_dau = system.engine.analyzer.detect_citation(
            "Điều 6 khoản 9 điểm a Nghị định 168/2024/NĐ-CP nói về lỗi gì?")
        khong_dau = system.engine.analyzer.detect_citation(
            "Dieu 6 khoan 9 diem a Nghi dinh 168/2024/ND-CP noi ve loi gi?")
        assert co_dau, "bản có dấu phải nhận ra căn cứ, nếu không phép so sánh vô nghĩa"
        assert khong_dau == co_dau

    @pytest.mark.parametrize("question", [
        "Dieu 6 khoan 9 diem a Nghi dinh 168/2024/NĐ-CP noi ve loi gi?",  # dan "NĐ-CP"
        "Điều 6 khoan 9 diem a nghi dinh 168",
    ])
    def test_mixed_accent_citation_is_recognised(self, system, question):
        """Gõ không dấu nhưng dán số hiệu văn bản có dấu: một chữ "Đ" không được làm hỏng cả câu."""
        cc = system.engine.analyzer.detect_citation(question)
        assert cc is not None
        assert (cc["article"], cc["clause"], cc["point"]) == (6, "9", "a")

    def test_mixed_accent_keeps_accented_point_letter(self, system):
        cc = system.engine.analyzer.detect_citation("dieu 7 khoan 2 điểm đ nghi dinh 168")
        assert cc is not None and cc["point"] == "đ"

    def test_unaccented_citation_question_hits_the_right_violation(self, system):
        kq = system.ask("Dieu 6 khoan 9 diem a Nghi dinh 168/2024/ND-CP noi ve loi gi?")
        assert kq["problem_class"] == P6_CAN_CU
        assert kq["violations"][0]["id"] == "VP_OTO_ND168D6_K9A"

    def test_telex_dd_is_read_as_letter_dd(self, system):
        """Người gõ không dấu viết điểm "đ" là "dd" (kiểu Telex)."""
        cc = system.engine.analyzer.detect_citation("dieu 7 khoan 2 diem dd nghi dinh 168")
        assert cc is not None and cc["point"] == "đ"

    def test_words_that_merely_look_like_dieu_are_not_citations(self, system):
        """"dieu kien" (điều kiện) không có số điều theo sau -> không phải căn cứ."""
        assert system.engine.analyzer.detect_citation("dieu kien de lai xe o to") is None


class TestConstraintsWithoutAccents:
    def test_unaccented_point_deduction_is_recognised(self, system):
        rb = system.engine.analyzer.detect_constraints("loi nao bi tru 10 diem giay phep lai xe")
        assert rb.get("tru_diem") == 10

    def test_unaccented_reverse_lookup_matches_accented_one(self, system):
        co_dau = system.ask("Lỗi nào bị trừ 10 điểm giấy phép lái xe?")
        khong_dau = system.ask("Loi nao bi tru 10 diem giay phep lai xe?")
        assert co_dau["violations"], "bản có dấu phải trả về danh sách lỗi"
        assert khong_dau["problem_class"] == P4_TRA_CUU_NGUOC
        assert ({v["id"] for v in khong_dau["violations"]}
                == {v["id"] for v in co_dau["violations"]})

    def test_unaccented_money_range_is_recognised(self, system):
        rb = system.engine.analyzer.detect_constraints(
            "nhung loi bi phat tu 1 trieu den 2 trieu dong")
        assert rb.get("tien_khoang") == (1_000_000, 2_000_000)

    def test_unaccented_licence_suspension_range_is_recognised(self, system):
        rb = system.engine.analyzer.detect_constraints("loi nao bi tuoc bang tu 2 den 4 thang")
        assert rb.get("extra_penalties") == "2 tháng đến 4 tháng"

    @pytest.mark.parametrize("question,key", [
        ("loi nao chi bi canh cao", "chi_canh_cao"),
        ("loi nao phat cao nhat", "sap_xep"),
        ("hanh vi nao bi tich thu xe", "extra_penalties"),
    ])
    def test_unaccented_keywords_are_recognised(self, system, question, key):
        assert key in system.engine.analyzer.detect_constraints(question)

    def test_den_do_is_not_read_as_upper_bound(self, system):
        """Không dấu, "đèn" và "đến" cùng viết "den": "vuot den do" không phải cận trên."""
        rb = system.engine.analyzer.detect_constraints("vuot den do xe may phat 4 trieu a")
        assert "tien_max" not in rb

    @pytest.mark.parametrize("question", [
        "Toi bi phat 4 trieu vi xe khong qua kiem dinh, co dung khong?",  # không qua ≠ không quá
        "Bi CSGT duoi theo vi khong dung xe, phat 5 trieu dung khong?",   # đuổi ≠ dưới
        "Dua xe gay hon loan bi phat 10 trieu a?",                         # hỗn ≠ hơn
    ])
    def test_colliding_words_are_not_read_as_money_bounds(self, system, question):
        """Mất dấu làm vài từ trùng mặt chữ với từ so sánh; chỉ tính khi đứng ngay trước số."""
        rb = system.engine.analyzer.detect_constraints(question)
        assert "tien_min" not in rb and "tien_max" not in rb, rb

    @pytest.mark.parametrize("question,key,value", [
        ("nhung loi phat duoi 1 trieu", "tien_max", 1_000_000),
        ("loi nao phat khong qua 2 trieu", "tien_max", 2_000_000),
        ("loi nao phat hon 5 trieu", "tien_min", 5_000_000),
        ("loi nao phat tren 5 trieu", "tien_min", 5_000_000),
    ])
    def test_real_money_bounds_are_still_recognised(self, system, question, key, value):
        assert system.engine.analyzer.detect_constraints(question).get(key) == value

    def test_mixed_accent_point_deduction_is_recognised(self, system):
        rb = system.engine.analyzer.detect_constraints(
            "Loi nao bi tru 10 diem GPLX, phat bao nhieu vnđ?")
        assert rb.get("tru_diem") == 10


@pytest.mark.benchmark
def test_stripping_accents_no_longer_breaks_p4_and_p6(system, qa_set):
    """Bỏ dấu toàn bộ bộ câu hỏi: P6 và P4 phải giữ được mức Top-1 như bản có dấu."""
    from collections import Counter

    dung, tong = Counter(), Counter()
    for m in qa_set:
        lop = m["lop_bai_toan_dung"]
        if lop not in (P4_TRA_CUU_NGUOC, P6_CAN_CU):
            continue
        kq = system.ask(strip_accents(m["cau_hoi"]), top_k=5)
        loai = {"concept": "concepts", "rule": "rules"}.get(m["loai_tri_thuc"], "violations")
        ids = [x["id"] for x in kq[loai]]
        tong[lop] += 1
        dung[lop] += bool(ids) and ids[0] in set(m["id_tri_thuc_dung"])
    assert dung[P6_CAN_CU] >= 7, f"P6 không dấu: {dung[P6_CAN_CU]}/{tong[P6_CAN_CU]}"
    assert dung[P4_TRA_CUU_NGUOC] >= 8, (
        f"P4 không dấu: {dung[P4_TRA_CUU_NGUOC]}/{tong[P4_TRA_CUU_NGUOC]}")
