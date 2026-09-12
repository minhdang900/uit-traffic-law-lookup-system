"""Kiểm thử bước phân loại lớp bài toán (P1..P7).

Phân loại sai làm cả pipeline suy diễn đi sai hướng. Báo cáo công bố độ chính
xác phân lớp 95,83% — test này khoá mức đó lại và kiểm từng lớp bằng câu mẫu.
"""
import pytest

from tra_cuu_gtdb.reasoning.engine import (
    P1_KHAI_NIEM,
    P2_QUY_DINH,
    P3_CHE_TAI,
    P4_TRA_CUU_NGUOC,
    P5_TINH_HUONG,
    P6_CAN_CU,
    P7_LIEN_QUAN,
    TEN_LOP_BAI_TOAN,
)

pytestmark = pytest.mark.cham


@pytest.mark.parametrize("cau_hoi,lop_mong_doi", [
    ("Xe cơ giới là gì?",                             P1_KHAI_NIEM),
    ("Gặp đèn đỏ có được đi tiếp không?",             P2_QUY_DINH),
    ("Vượt đèn đỏ xe máy phạt bao nhiêu?",            P3_CHE_TAI),
    ("Lỗi nào bị trừ 10 điểm giấy phép lái xe?",      P4_TRA_CUU_NGUOC),
    ("Điều 6 khoản 9 Nghị định 168 quy định gì?",     P6_CAN_CU),
    ("Cho tôi thông tin về mũ bảo hiểm",              P7_LIEN_QUAN),
])
def test_phan_dung_lop_bai_toan_cho_cau_mau(he_thong, cau_hoi, lop_mong_doi):
    """Mỗi lớp bài toán có một câu hỏi đại diện lấy từ README của đồ án."""
    kq = he_thong.hoi(cau_hoi)
    assert kq["lop_bai_toan"] == lop_mong_doi, (
        f"{cau_hoi!r}\n  mong đợi: {lop_mong_doi}\n  nhận được: {kq['lop_bai_toan']}")


def test_moi_lop_bai_toan_deu_co_ten_hien_thi(he_thong):
    """Giao diện dùng TEN_LOP_BAI_TOAN để hiển thị; thiếu khoá sẽ ném KeyError."""
    for lop in (P1_KHAI_NIEM, P2_QUY_DINH, P3_CHE_TAI, P4_TRA_CUU_NGUOC,
                P5_TINH_HUONG, P6_CAN_CU, P7_LIEN_QUAN):
        assert TEN_LOP_BAI_TOAN.get(lop), f"Thiếu tên hiển thị cho {lop}"


def test_ket_qua_luon_du_khoa_bat_buoc(he_thong):
    """Giao diện và bộ đánh giá đều đọc các khoá này; thiếu một khoá là vỡ."""
    kq = he_thong.hoi("vượt đèn đỏ phạt bao nhiêu")
    for khoa in ("phan_tich", "lop_bai_toan", "ten_lop_bai_toan",
                 "khai_niem", "quy_tac", "hanh_vi", "lien_quan", "can_cu"):
        assert khoa in kq, f"Thiếu khoá bắt buộc: {khoa}"


def test_do_chinh_xac_phan_lop_khong_tut(he_thong, bo_qa):
    """Chạy toàn bộ 120 câu, khoá mức 95,83% đã công bố (cho phép sai số nhỏ)."""
    dung = sum(1 for m in bo_qa
               if he_thong.hoi(m["cau_hoi"])["lop_bai_toan"] == m["lop_bai_toan_dung"])
    acc = dung / len(bo_qa)
    assert acc >= 0.95, f"Độ chính xác phân lớp tụt xuống {acc:.2%} (mức công bố 95,83%)"
