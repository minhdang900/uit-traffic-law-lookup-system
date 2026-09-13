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

from traffic_law.api import app  # noqa: E402
from traffic_law.api.presentation import result_cards  # noqa: E402

NGUON = Path(app.__file__).read_text(encoding="utf-8")

pytestmark = pytest.mark.cham


class TestExampleQuestions:
    """Nút ví dụ là thứ giám khảo bấm đầu tiên. Không được ra tay trắng."""

    def test_has_at_least_four_examples(self):
        assert len(app.EXAMPLES) >= 4

    @pytest.mark.parametrize("i", range(6))
    def test_every_example_returns_a_result(self, system, i):
        if i >= len(app.EXAMPLES):
            pytest.skip("ít ví dụ hơn")
        question = app.EXAMPLES[i]
        kq = system.ask(question, top_k=5)
        assert not kq["not_found"], f"Ví dụ {question!r} ra 'không tìm thấy'"
        assert result_cards(kq), f"Ví dụ {question!r} không sinh được thẻ nào"

    def test_examples_cover_several_problem_classes(self, system):
        """Một dãy ví dụ cùng một lớp thì không cho thấy hệ thống làm được gì."""
        lop = {system.ask(q)["problem_class"] for q in app.EXAMPLES}
        assert len(lop) >= 3, f"Ví dụ chỉ phủ {len(lop)} lớp bài toán: {lop}"

    def test_no_duplicate_examples(self):
        assert len(set(app.EXAMPLES)) == len(app.EXAMPLES)


class TestShellHasNoSideEffects:
    def test_importing_module_renders_nothing(self):
        """Nếu main() bị gọi ở mức module, chỉ riêng việc nhập đã dựng giao diện."""
        cay = ast.parse(NGUON)
        goi_muc_module = [n for n in cay.body if isinstance(n, ast.Expr)
                          and isinstance(n.value, ast.Call)]
        assert not goi_muc_module, (
            "Có lệnh gọi ở mức module; main() phải nằm dưới if __name__")

    def test_has_main_entry_point(self):
        assert callable(app.main)


class TestArchitectureBoundary:
    """Chốt chặn để vỏ không rữa thành nơi chứa logic."""

    def test_no_money_formatting_in_shell(self):
        assert 'replace(",", ".")' not in NGUON, (
            "Định dạng tiền phải ở trinh_bay.py, không phải trong vỏ")

    def test_no_confidence_thresholds_in_shell(self):
        for dau_hieu in [">= 0.8", ">= 0.6", "> 0.8", "> 0.6"]:
            assert dau_hieu not in NGUON, (
                f"Ngưỡng tin cậy {dau_hieu!r} phải ở trinh_bay.py")

    def test_no_dead_render_functions(self):
        cay = ast.parse(NGUON)
        ham = {n.name for n in cay.body if isinstance(n, ast.FunctionDef)}
        goi = {n.func.id for n in ast.walk(cay)
               if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert not (ham - goi - {"main"}), f"Hàm không ai gọi: {ham - goi - {'main'}}"
