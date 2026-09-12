"""Kiểm thử khói cho vỏ Streamlit.

Không dựng được khung chạy Streamlit trong pytest, nên chỉ kiểm điều duy nhất
có thể hỏng lặng lẽ: tệp app có nhập được không, và nó có thật sự KHÔNG chứa
logic hay không. Phần logic đã kiểm ở ``test_trinh_bay.py``.
"""
import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parent.parent / "src" / "tra_cuu_gtdb" / "api" / "app.py"
streamlit = pytest.importorskip("streamlit", reason="Cần gói tuỳ chọn 'ui'")


def test_nhap_duoc_ma_khong_tu_chay():
    """Nhập module không được vẽ gì — nếu không, pytest sẽ dựng cả giao diện."""
    import tra_cuu_gtdb.api.app as app

    assert callable(app.main)


def test_vo_khong_chua_logic_dinh_dang():
    """Chốt chặn kiến trúc: logic phải ở trinh_bay.py để còn kiểm thử được.

    Nếu ai đó nhét lại phép định dạng tiền vào app.py, test này đỏ.
    """
    nguon = APP.read_text(encoding="utf-8")
    assert 'replace(",", ".")' not in nguon, (
        "Định dạng tiền phải nằm ở trinh_bay.py, không phải trong vỏ giao diện")


def test_moi_ham_ve_deu_duoc_goi_tu_main():
    """Hàm vẽ chết (không ai gọi) là dấu hiệu vỏ đã rữa."""
    cay = ast.parse(APP.read_text(encoding="utf-8"))
    ham = {n.name for n in cay.body if isinstance(n, ast.FunctionDef)}
    goi = {n.func.id for n in ast.walk(cay)
           if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    khong_goi = ham - goi - {"main"}
    assert not khong_goi, f"Hàm không ai gọi: {khong_goi}"
