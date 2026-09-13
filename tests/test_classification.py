"""Kiểm thử bước phân loại lớp bài toán (P1..P7).

Phân loại sai làm cả pipeline suy diễn đi sai hướng. Báo cáo công bố độ chính
xác phân lớp 95,83% — test này khoá mức đó lại và kiểm từng lớp bằng câu mẫu.
"""
import pytest

from traffic_law.reasoning.engine import (
    P1_KHAI_NIEM,
    P2_QUY_DINH,
    P3_CHE_TAI,
    P4_TRA_CUU_NGUOC,
    P5_TINH_HUONG,
    P6_CAN_CU,
    P7_LIEN_QUAN,
    PROBLEM_CLASS_NAMES,
)

pytestmark = pytest.mark.cham


@pytest.mark.parametrize("question,expected_class", [
    ("Xe cơ giới là gì?",                             P1_KHAI_NIEM),
    ("Gặp đèn đỏ có được đi tiếp không?",             P2_QUY_DINH),
    ("Vượt đèn đỏ xe máy phạt bao nhiêu?",            P3_CHE_TAI),
    ("Lỗi nào bị trừ 10 điểm giấy phép lái xe?",      P4_TRA_CUU_NGUOC),
    ("Điều 6 khoản 9 Nghị định 168 quy định gì?",     P6_CAN_CU),
    ("Cho tôi thông tin về mũ bảo hiểm",              P7_LIEN_QUAN),
])
def test_classifies_sample_questions_correctly(system, question, expected_class):
    """Mỗi lớp bài toán có một câu hỏi đại diện lấy từ README của đồ án."""
    kq = system.ask(question)
    assert kq["problem_class"] == expected_class, (
        f"{question!r}\n  mong đợi: {expected_class}\n  nhận được: {kq['problem_class']}")


def test_every_problem_class_has_a_display_name(system):
    """Giao diện dùng TEN_LOP_BAI_TOAN để hiển thị; thiếu khoá sẽ ném KeyError."""
    for lop in (P1_KHAI_NIEM, P2_QUY_DINH, P3_CHE_TAI, P4_TRA_CUU_NGUOC,
                P5_TINH_HUONG, P6_CAN_CU, P7_LIEN_QUAN):
        assert PROBLEM_CLASS_NAMES.get(lop), f"Thiếu tên hiển thị cho {lop}"


def test_result_always_has_required_keys(system):
    """Giao diện và bộ đánh giá đều đọc các khoá này; thiếu một khoá là vỡ."""
    kq = system.ask("vượt đèn đỏ phạt bao nhiêu")
    for khoa in ("analysis", "problem_class", "problem_class_name",
                 "concepts", "rules", "violations", "related", "citation"):
        assert khoa in kq, f"Thiếu khoá bắt buộc: {khoa}"


def test_classification_accuracy_does_not_regress(system, qa_set):
    """Chạy toàn bộ 120 câu, khoá mức 95,83% đã công bố (cho phép sai số nhỏ)."""
    dung = sum(1 for m in qa_set
               if system.ask(m["cau_hoi"])["problem_class"] == m["lop_bai_toan_dung"])
    acc = dung / len(qa_set)
    assert acc >= 0.95, f"Độ chính xác phân lớp tụt xuống {acc:.2%} (mức công bố 95,83%)"
