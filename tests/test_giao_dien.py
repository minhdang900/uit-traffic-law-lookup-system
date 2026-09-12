"""Kiểm thử vỏ giao diện Streamlit.

Khung chạy Streamlit không dựng được trong pytest, nên tệp này KHÔNG cố kiểm
việc vẽ. Nó kiểm bốn thứ có thể hỏng lặng lẽ mà vẫn kiểm được bằng mã thật:

1. Câu hỏi ví dụ có thật sự trả lời được không — hỏng cái này thì buổi báo cáo
   bấm nút ra "không tìm thấy".
2. Nhập module có vẽ gì ra không — nếu có, pytest sẽ dựng cả giao diện.
3. Vỏ có lẫn logic vào không — logic phải ở trinh_bay.py để còn kiểm thử được.
4. Có hàm vẽ chết không.

Phần logic trình bày kiểm ở ``test_trinh_bay.py``.
"""
import ast
from pathlib import Path

import pytest

pytest.importorskip("streamlit", reason="Cần gói tuỳ chọn 'ui'")

from tra_cuu_gtdb.api import app  # noqa: E402
from tra_cuu_gtdb.api.trinh_bay import the_ket_qua  # noqa: E402

NGUON = Path(app.__file__).read_text(encoding="utf-8")

pytestmark = pytest.mark.cham


class TestCauHoiViDu:
    """Nút ví dụ là thứ giám khảo bấm đầu tiên. Không được ra tay trắng."""

    def test_co_it_nhat_bon_vi_du(self):
        assert len(app.VI_DU) >= 4

    @pytest.mark.parametrize("i", range(6))
    def test_moi_vi_du_deu_tra_ve_ket_qua(self, he_thong, i):
        if i >= len(app.VI_DU):
            pytest.skip("ít ví dụ hơn")
        cau_hoi = app.VI_DU[i]
        kq = he_thong.hoi(cau_hoi, top_k=5)
        assert not kq["khong_tim_thay"], f"Ví dụ {cau_hoi!r} ra 'không tìm thấy'"
        assert the_ket_qua(kq), f"Ví dụ {cau_hoi!r} không sinh được thẻ nào"

    def test_vi_du_phu_nhieu_lop_bai_toan(self, he_thong):
        """Một dãy ví dụ cùng một lớp thì không cho thấy hệ thống làm được gì."""
        lop = {he_thong.hoi(q)["lop_bai_toan"] for q in app.VI_DU}
        assert len(lop) >= 3, f"Ví dụ chỉ phủ {len(lop)} lớp bài toán: {lop}"

    def test_khong_co_vi_du_trung_nhau(self):
        assert len(set(app.VI_DU)) == len(app.VI_DU)


class TestVoKhongCoTacDungPhu:
    def test_nhap_module_khong_ve_gi(self):
        """Nếu main() bị gọi ở mức module, chỉ riêng việc nhập đã dựng giao diện."""
        cay = ast.parse(NGUON)
        goi_muc_module = [n for n in cay.body if isinstance(n, ast.Expr)
                          and isinstance(n.value, ast.Call)]
        assert not goi_muc_module, (
            "Có lệnh gọi ở mức module; main() phải nằm dưới if __name__")

    def test_co_diem_vao_main(self):
        assert callable(app.main)


class TestRanhGioiKienTruc:
    """Chốt chặn để vỏ không rữa thành nơi chứa logic."""

    def test_khong_dinh_dang_tien_trong_vo(self):
        assert 'replace(",", ".")' not in NGUON, (
            "Định dạng tiền phải ở trinh_bay.py, không phải trong vỏ")

    def test_khong_tinh_muc_tin_cay_trong_vo(self):
        for dau_hieu in [">= 0.8", ">= 0.6", "> 0.8", "> 0.6"]:
            assert dau_hieu not in NGUON, (
                f"Ngưỡng tin cậy {dau_hieu!r} phải ở trinh_bay.py")

    def test_khong_ham_ve_chet(self):
        cay = ast.parse(NGUON)
        ham = {n.name for n in cay.body if isinstance(n, ast.FunctionDef)}
        goi = {n.func.id for n in ast.walk(cay)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert not (ham - goi - {"main"}), f"Hàm không ai gọi: {ham - goi - {'main'}}"
