"""Kiểm thử tầng web thay cho Streamlit.

Bản thiết kế bàn giao yêu cầu bảy màn hình với bố cục mà Streamlit không dựng
được. Tầng mới là FastAPI + Jinja: một endpoint JSON cho màn tra cứu, phần còn
lại render phía máy chủ.

Nguyên tắc giữ nguyên từ bản Streamlit: MỌI phép định dạng nằm ở
``presentation.py`` và đã có test riêng — tầng web chỉ gọi xuống, không tự
định dạng lại.
"""
import pytest

pytest.importorskip("fastapi", reason="Cần gói tuỳ chọn 'web'")
from fastapi.testclient import TestClient  # noqa: E402

from traffic_law.api.web import create_app  # noqa: E402

pytestmark = pytest.mark.cham


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


class TestAskEndpoint:
    """POST /api/ask — trả nguyên payload của LawLookup.ask()."""

    def test_returns_the_engine_payload(self, client):
        r = client.post("/api/ask", json={"question": "vượt đèn đỏ xe máy phạt bao nhiêu"})
        assert r.status_code == 200
        d = r.json()
        for k in ("problem_class", "problem_class_name", "not_found",
                  "violations", "rules", "concepts", "related", "analysis"):
            assert k in d, f"Thiếu khoá {k!r}"
        assert d["not_found"] is False
        assert d["violations"], "Phải có ít nhất một hành vi"

    def test_result_carries_formatting_from_presentation_layer(self, client):
        """Frontend không được tự định dạng tiền — máy chủ trả sẵn chuỗi."""
        d = client.post("/api/ask", json={"question": "vượt đèn đỏ xe máy phạt bao nhiêu"}).json()
        card = d["cards"][0]
        assert "đ" in card["fine_text"], card["fine_text"]
        assert card["confidence"] in ("cao", "trung bình", "thấp")
        assert card["citation"], "Thẻ nào cũng phải có căn cứ pháp lý"

    def test_top_k_is_honoured_for_ranked_lookups(self, client):
        d = client.post("/api/ask", json={"question": "vượt đèn đỏ xe máy phạt bao nhiêu",
                                          "top_k": 2}).json()
        assert len(d["violations"]) <= 2

    def test_reverse_lookup_ignores_top_k_on_purpose(self, client):
        """P4 là truy vấn DANH SÁCH — cắt còn top_k sẽ làm câu trả lời sai.

        Hỏi "lỗi nào bị trừ 10 điểm" mà chỉ trả 2 lỗi thì người đọc tưởng chỉ
        có 2. Bộ máy cố ý trả tới 20 (xem ``gh`` trong ``_giai_P4``); tầng web
        không được lặng lẽ cắt bớt.
        """
        d = client.post("/api/ask", json={"question": "lỗi nào bị trừ 10 điểm giấy phép lái xe",
                                          "top_k": 2}).json()
        assert d["problem_class"] == "P4_TRA_CUU_NGUOC"
        assert len(d["violations"]) > 2

    def test_empty_question_is_rejected(self, client):
        assert client.post("/api/ask", json={"question": "   "}).status_code == 422

    def test_out_of_domain_query_does_not_error(self, client):
        r = client.post("/api/ask", json={"question": "cách nấu phở bò"})
        assert r.status_code == 200


class TestScreens:
    """Bảy màn hình của bản thiết kế đều phải render được."""

    @pytest.mark.parametrize("path", [
        "/", "/khong-tim-thay", "/hieu-luc", "/chu-de", "/chi-so", "/mobile",
    ])
    def test_screen_renders(self, client, path):
        r = client.get(path)
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_provision_detail_renders_for_a_real_id(self, client, system):
        vid = system.ask("vượt đèn đỏ xe máy phạt bao nhiêu", top_k=1)["violations"][0]["id"]
        r = client.get(f"/dieu-khoan/{vid}")
        assert r.status_code == 200
        assert "Điều" in r.text

    def test_unknown_provision_returns_404(self, client):
        assert client.get("/dieu-khoan/KHONG_TON_TAI").status_code == 404


class TestDesignContract:
    """Những điểm bản thiết kế nêu tường minh, dễ trôi mất khi sửa về sau."""

    def test_disclaimer_on_every_screen_with_results(self, client):
        """Handoff: miễn trừ phải xuất hiện trên MỌI màn hình có kết quả."""
        for path in ("/", "/khong-tim-thay", "/hieu-luc"):
            assert "không thay thế ý kiến của cơ quan có thẩm quyền" in client.get(path).text, path

    def test_uses_vietnamese_capable_fonts(self, client):
        """Caprasimo/Figtree không có glyph tiếng Việt — phải dùng cặp thay thế."""
        html = client.get("/").text
        assert "Be+Vietnam+Pro" in html and "Baloo+2" in html
        assert "Caprasimo" not in html and "Figtree" not in html

    def test_confidence_thresholds_come_from_presentation_layer(self):
        """Ngưỡng không được gõ cứng lại ở tầng web."""
        from pathlib import Path
        src = Path("src/traffic_law/api/web.py").read_text(encoding="utf-8")
        assert "0.80" not in src and "0.60" not in src
