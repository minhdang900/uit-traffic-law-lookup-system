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


    def test_as_of_date_is_accepted(self, client):
        r = client.post("/api/ask", json={"question": "vượt đèn đỏ xe máy phạt bao nhiêu",
                                          "as_of": "2025-03-01"})
        assert r.status_code == 200


CAU_HOI = "vượt đèn đỏ xe máy phạt bao nhiêu"
#: Truy vấn rác — cấu hình mặc định hiếm khi trả rỗng với câu ngoài miền có
#: nghĩa (xem xfail trong test_confidence_threshold.py), nhưng chắc chắn rỗng ở đây.
VO_NGHIA = "asdfgh qwerty"


class TestScreens:
    """Bản bàn giao: bốn mục điều hướng, mỗi màn hình là một route riêng."""

    @pytest.mark.parametrize("path", [
        "/tra-cuu", f"/tra-cuu?q={CAU_HOI}", f"/tra-cuu?q={VO_NGHIA}", "/hieu-luc",
        "/hieu-luc?ngay=2025-01-01", "/chu-de", "/chu-de?linh_vuc=LV_AN_TOAN&nhom=mu_bao_hiem",
        "/chi-so",
    ])
    def test_screen_renders(self, client, path):
        r = client.get(path)
        assert r.status_code == 200, r.text[:500]
        assert "text/html" in r.headers["content-type"]

    def test_root_redirects_to_search_keeping_the_query(self, client):
        r = client.get("/?q=abc", follow_redirects=False)
        assert r.status_code in (307, 308)
        assert r.headers["location"] == "/tra-cuu?q=abc"

    @pytest.mark.parametrize("path", ["/khong-tim-thay", "/mobile"])
    def test_states_are_not_screens(self, client, path):
        """"Không tìm thấy" là trạng thái của Tra cứu; mobile là bố cục, không phải trang."""
        assert client.get(path).status_code == 404

    def test_provision_detail_renders_for_a_real_id(self, client, system):
        vid = system.ask(CAU_HOI, top_k=1)["violations"][0]["id"]
        r = client.get(f"/dieu-khoan/{vid}")
        assert r.status_code == 200
        assert "Phạm vi áp dụng" in r.text and "Hiệu lực" in r.text

    def test_unknown_provision_returns_404(self, client):
        assert client.get("/dieu-khoan/KHONG_TON_TAI").status_code == 404


class TestSearchBehaviour:
    def test_lead_card_links_to_provision_detail(self, client, system):
        vid = system.ask(CAU_HOI, top_k=1)["violations"][0]["id"]
        assert f"/dieu-khoan/{vid}" in client.get(f"/tra-cuu?q={CAU_HOI}").text

    def test_not_found_state_explains_the_threshold(self, client):
        html = client.get(f"/tra-cuu?q={VO_NGHIA}").text
        assert "Không tìm thấy quy định phù hợp" in html
        assert "0,40" in html, "Phải nêu ngưỡng bổ sung lấy từ tầng suy diễn"

    def test_vehicle_filter_keeps_only_matching_cards(self, client):
        html = client.get(f"/tra-cuu?q={CAU_HOI}&pt=o_to").text
        assert 'data-vehicles="o_to"' in html
        assert 'data-vehicles="mo_to' not in html

    def test_date_before_decree_238_shows_old_wording(self, client):
        """Điều 6 k5 điểm p NĐ 168 bị NĐ 238 sửa từ 15/08/2026."""
        q = "chở người trên nóc xe ô tô phạt bao nhiêu"
        truoc = client.get(f"/tra-cuu?q={q}&ngay=2025-03-01").text
        assert "Chưa áp dụng Nghị định 238/2026/NĐ-CP" in truoc
        assert "chở người trên nóc xe" in truoc, "Phải hiện câu chữ TRƯỚC sửa đổi"


class TestProvisionTruthfulness:
    """Lỗi soát mã phát hiện: màn chi tiết khẳng định điều dữ liệu không nói."""

    def test_detail_viewed_before_amendment_shows_old_wording(self, client):
        html = client.get("/dieu-khoan/VP_OTO_ND168D6_K5P?ngay=2026-01-01").text
        assert "chở người trên nóc xe" in html
        assert "Câu chữ trước sửa đổi" in html
        assert "Phiên bản này đang được áp dụng" not in html

    def test_repealed_clause_is_not_called_untouched(self, client):
        """SD_63 bãi bỏ điểm d–g khoản 17 Điều 32 bằng bản ghi cấp khoản."""
        html = client.get("/dieu-khoan/VP_ND168D32_K17D").text
        assert "không sửa điều khoản này" not in html
        assert "Bãi bỏ" in html and "Hết hiệu lực" in html
        truoc = client.get("/dieu-khoan/VP_ND168D32_K17D?ngay=2026-01-01").text
        assert "Hết hiệu lực từ" not in truoc, "Trước ngày bãi bỏ điều khoản vẫn còn hiệu lực"

    def test_amending_citation_has_no_none(self, client):
        assert "khoản None" not in client.get("/dieu-khoan/VP_ND168D13_K8B").text


class TestValidityScreen:
    def test_lists_every_provision_touched_by_decree_238(self, client, kb):
        n = sum(1 for v in kb.violations if v.amended_by)
        assert f"sửa đổi, bổ sung {n} hành vi vi phạm" in client.get("/hieu-luc").text

    def test_comparison_highlights_the_changed_phrase(self, client):
        html = client.get("/hieu-luc?dk=VP_OTO_ND168D6_K5P").text
        assert '<mark class="diff' in html
        assert "để người nằm, ngồi, đu bám bên ngoài" in html


class TestTopicsScreen:
    def test_selected_group_lists_its_violations(self, client, kb):
        n = sum(1 for v in kb.violations if v.group == "mu_bao_hiem")
        html = client.get("/chu-de?linh_vuc=LV_AN_TOAN&nhom=mu_bao_hiem").text
        assert html.count('class="vrow"') == n


class TestDesignContract:
    """Những điểm bản thiết kế nêu tường minh, dễ trôi mất khi sửa về sau."""

    def test_exactly_four_nav_items_with_current_page_marked(self, client):
        html = client.get("/hieu-luc").text
        nav = html.split('<nav class="nav"', 1)[1].split("</nav>", 1)[0]
        assert nav.count("<a ") == 4
        assert nav.count('aria-current="page"') == 1

    def test_detail_screen_keeps_search_nav_active(self, client, system):
        vid = system.ask(CAU_HOI, top_k=1)["violations"][0]["id"]
        html = client.get(f"/dieu-khoan/{vid}").text
        nav = html.split('<nav class="nav"', 1)[1].split("</nav>", 1)[0]
        assert 'href="/tra-cuu" aria-current="page"' in nav

    def test_mobile_tab_bar_has_four_tabs(self, client):
        html = client.get("/chi-so").text
        tabs = html.split('<nav class="tabbar"', 1)[1].split("</nav>", 1)[0]
        assert tabs.count("<a ") == 4

    def test_disclaimer_on_every_screen_with_results(self, client, system):
        """Handoff: miễn trừ phải xuất hiện trên MỌI màn hình có kết quả."""
        vid = system.ask(CAU_HOI, top_k=1)["violations"][0]["id"]
        for path in (f"/tra-cuu?q={CAU_HOI}", f"/tra-cuu?q={VO_NGHIA}", "/hieu-luc",
                     f"/dieu-khoan/{vid}", "/chu-de?linh_vuc=LV_AN_TOAN&nhom=mu_bao_hiem"):
            assert "không thay thế ý kiến của cơ quan có thẩm quyền" in client.get(path).text, path

    def test_metrics_come_from_the_evaluation_file(self, client):
        html = client.get("/chi-so").text
        assert "95,83%" in html and "0,8384" in html

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


class TestReviewFollowUps:
    """Các điểm còn lại từ lượt soát mã (không đụng dữ liệu tri thức)."""

    def test_result_links_keep_date_and_vehicle_filters(self, client):
        html = client.get(f"/tra-cuu?q={CAU_HOI}&pt=o_to&ngay=2025-03-01").text
        assert "/dieu-khoan/VP_OTO_ND168D6_K9B?ngay=2025-03-01&amp;pt=o_to&amp;q=" in html

    def test_group_rows_and_back_link_keep_filters(self, client):
        html = client.get("/chu-de?nhom=mu_bao_hiem&ngay=2025-03-01").text
        assert "?ngay=2025-03-01" in html.split('class="vlist"', 1)[1]
        detail = client.get("/dieu-khoan/VP_OTO_ND168D6_K9B?ngay=2025-03-01&q=abc").text
        assert 'href="/tra-cuu?ngay=2025-03-01&amp;q=abc"' in detail

    def test_group_decides_its_field_even_if_field_param_disagrees(self, client):
        html = client.get("/chu-de?linh_vuc=LV_QUY_TAC&nhom=mu_bao_hiem").text
        assert "An toàn của người tham gia giao thông · " in html

    def test_unknown_provision_is_an_html_page(self, client):
        r = client.get("/dieu-khoan/KHONG_TON_TAI", headers={"accept": "text/html"})
        assert r.status_code == 404 and "text/html" in r.headers["content-type"]
        assert "Không tìm thấy điều khoản" in r.text

    def test_overlong_question_is_rejected_by_the_api(self, client):
        assert client.post("/api/ask", json={"question": "x" * 501}).status_code == 422

    def test_shared_date_link_is_visible_on_mobile(self, client):
        html = client.get("/chi-so?ngay=2025-03-01").text
        assert 'class="m-date' in html and "01/03/2025" in html
        assert 'class="m-date' not in client.get("/chi-so").text


class TestTeamInfo:
    """Thanh bên ghi thông tin nhóm — đọc từ docs/thanh_vien.json, không gõ tay."""

    def test_sidebar_lists_every_member_from_the_roster(self, client):
        import json
        from pathlib import Path
        ds = json.loads(Path("docs/thanh_vien.json").read_text(encoding="utf-8"))
        foot = client.get("/chi-so").text.split('class="team', 1)[1].split("</aside>", 1)[0]
        assert f"Nhóm {ds['nhom']}" in foot and ds["giang_vien_huong_dan"] in foot
        for tv in ds["thanh_vien"]:
            assert tv["ho_ten"] in foot and tv["mssv"] in foot

    def test_missing_roster_does_not_break_pages(self, client, monkeypatch):
        from traffic_law.api import web
        monkeypatch.setattr(web, "_thong_tin_nhom", lambda: None)
        r = client.get("/chi-so")
        assert r.status_code == 200 and 'class="team' not in r.text
