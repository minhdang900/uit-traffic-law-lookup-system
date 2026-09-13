"""Kiểm thử các hàm trình bày mà bản bàn giao thiết kế (bản 12 màn hình) cần.

Cùng nguyên tắc với ``test_presentation.py``: mọi phép định dạng CÓ THỂ SAI nằm
ở tầng trình bày dưới dạng hàm thuần, tầng web chỉ gọi xuống. Tệp này khoá
những quy ước bản bàn giao nêu tường minh — dấu phẩy thập phân, nhãn phương
tiện, căn cứ viết gọn — cùng hai hành vi mới: lọc theo phương tiện và xem cơ sở
tri thức tại một thời điểm.
"""
from datetime import date

import pytest

from traffic_law.api.presentation import (
    VEHICLE_FILTERS,
    amendments_touching,
    as_of,
    clean_citation_text,
    diff_segments,
    filter_vehicles,
    points_tail,
    position_label,
    problem_class_label,
    short_citation,
    validity_timeline,
    vehicle_label,
    vi_decimal,
    vi_percent,
)


class TestVietnameseNumbers:
    """Bản bàn giao: số thập phân dùng dấu phẩy — 0,8384, 95,83%."""

    def test_decimal_uses_comma(self):
        assert vi_decimal(0.8384, 4) == "0,8384"
        assert vi_decimal(6.1, 1) == "6,1"

    @pytest.mark.parametrize("ratio,expected", [
        (0.9583, "95,83%"), (0.95, "95,00%"), (0.6667, "66,67%"), (1.0, "100%"),
    ])
    def test_percent_from_ratio(self, ratio, expected):
        """Thiết kế ghi "100%" gọn, nhưng "95,00%" giữ hai chữ số cho thẳng cột."""
        assert vi_percent(ratio) == expected


class TestVehicleLabel:
    """Nhãn pill phương tiện trên thẻ kết quả: "Mô tô, xe gắn máy", "Ô tô"."""

    @pytest.mark.parametrize("codes,expected", [
        (["mo_to", "xe_gan_may"], "Mô tô, xe gắn máy"),
        (["o_to"], "Ô tô"),
        (["xe_dap", "xe_tho_so"], "Xe đạp, xe thô sơ"),
        (["xe_may_chuyen_dung"], "Xe máy chuyên dùng"),
    ])
    def test_joins_short_names_and_capitalises_once(self, codes, expected):
        assert vehicle_label(codes) == expected

    def test_falls_back_to_subject_when_not_tied_to_a_vehicle(self):
        """Lỗi của người đi bộ gắn "khong_ap_dung" — nhãn phải nói ai vi phạm."""
        assert vehicle_label(["khong_ap_dung"], "nguoi_di_bo") == "Người đi bộ"

    def test_empty_is_empty(self):
        assert vehicle_label([]) == ""


class TestCitationLabels:
    CIT = {"documents": "Nghị định 168/2024/NĐ-CP", "article": 6, "clause": 9, "point": "b"}

    def test_short_citation_for_tables(self):
        """Bảng "Cùng hành vi, phương tiện khác": "Điều 6 k9 điểm b"."""
        assert short_citation(self.CIT) == "Điều 6 k9 điểm b"

    def test_short_citation_with_lettered_clause_and_no_point(self):
        assert short_citation({"article": 20, "clause": "8a", "point": None}) == "Điều 20 k8a"

    def test_position_label_for_pills(self):
        """Pill vị trí ở màn Chi tiết: "Điều 7 · khoản 7 · điểm c"."""
        assert position_label({"article": 7, "clause": 7, "point": "c"}) == \
            "Điều 7 · khoản 7 · điểm c"


class TestPointsTail:
    """Đuôi mức phạt trên thẻ phụ — không bao giờ để trống gây hiểu nhầm."""

    def test_points(self):
        assert points_tail(4) == "trừ 4 điểm giấy phép lái xe"

    @pytest.mark.parametrize("p", [0, None])
    def test_no_points_is_said_out_loud(self, p):
        assert points_tail(p) == "không trừ điểm"


class TestProblemClassLabel:
    def test_long_and_short_forms(self):
        assert problem_class_label("P3_TRA_CUU_CHE_TAI") == "P3 · Tra cứu chế tài"
        assert problem_class_label("P3_TRA_CUU_CHE_TAI", short=True) == "P3 · Chế tài"

    def test_unknown_code_does_not_raise(self):
        assert problem_class_label("P9_LA") == "P9"


class TestDiffSegments:
    """Màn Hiệu lực tô nền phần chữ khác nhau giữa bản trước và bản sau."""

    def test_isolates_the_replaced_phrase_at_word_boundaries(self):
        truoc = ("Chở người trên thùng xe trái quy định; chở người trên nóc xe; "
                 "để người đu bám ở cửa xe, bên ngoài thành xe khi xe đang chạy")
        sau = ("Chở người trên thùng xe trái quy định; để người nằm, ngồi, đu bám "
               "bên ngoài xe khi xe đang chạy")
        d = diff_segments(truoc, sau)
        assert d.prefix == "Chở người trên thùng xe trái quy định; "
        assert d.suffix == " xe khi xe đang chạy"
        assert d.prefix + d.before + d.suffix == truoc
        assert d.prefix + d.after + d.suffix == sau
        assert d.before.startswith("chở người trên nóc xe")
        assert d.after == "để người nằm, ngồi, đu bám bên ngoài"

    def test_pure_addition_leaves_before_side_empty(self):
        sau = "không nối chắc chắn khi kéo nhau, trừ điểm b khoản 3a"
        d = diff_segments("không nối chắc chắn khi kéo nhau", sau)
        assert d.before == ""
        assert d.after == ", trừ điểm b khoản 3a"
        assert d.prefix + d.after + d.suffix == sau

    def test_identical_texts_have_no_change(self):
        d = diff_segments("giống hệt", "giống hệt")
        assert (d.before, d.after) == ("", "")
        assert d.prefix + d.suffix == "giống hệt"


def _vp(id_, vehicles, start, before=None, subject="nguoi_dieu_khien", end=None):
    return {"id": id_, "behavior": f"hành vi {id_}", "vehicles": vehicles,
            "subject": subject, "behavior_before_amendment": before,
            "validity": {"start": start, "end": end}}


class TestFilterVehicles:
    ITEMS = [_vp("A", ["mo_to", "xe_gan_may"], "2025-01-01"),
             _vp("B", ["o_to"], "2025-01-01"),
             _vp("C", ["khong_ap_dung"], "2025-01-01", subject="nguoi_di_bo")]

    def test_no_selection_keeps_everything(self):
        assert [x["id"] for x in filter_vehicles(self.ITEMS, [])] == ["A", "B", "C"]

    def test_keeps_items_matching_any_selected_filter(self):
        kept = filter_vehicles(self.ITEMS, ["o_to", "di_bo"])
        assert [x["id"] for x in kept] == ["B", "C"]

    def test_unknown_filter_key_is_ignored_not_fatal(self):
        assert [x["id"] for x in filter_vehicles(self.ITEMS, ["xe_bay"])] == ["A", "B", "C"]

    def test_the_four_sidebar_filters_of_the_design(self):
        assert [f.label for f in VEHICLE_FILTERS] == [
            "Mô tô, xe gắn máy", "Ô tô", "Xe đạp", "Người đi bộ"]


class TestAsOf:
    """Xem cơ sở tri thức tại một thời điểm — điểm khác biệt của hệ.

    Điều khoản bị Nghị định 238/2026 sửa CHỈ lưu bản mới kèm câu chữ cũ, nên
    trước ngày sửa đổi phải hiện lại câu chữ cũ, còn điều khoản BỔ SUNG (không
    có câu chữ cũ) thì chưa tồn tại.
    """

    ITEMS = [_vp("HIEN_HANH", ["o_to"], "2025-01-01"),
             _vp("SUA_DOI", ["o_to"], "2026-08-15", before="câu chữ cũ"),
             _vp("BO_SUNG", ["o_to"], "2026-08-15"),
             _vp("HET_HIEU_LUC", ["o_to"], "2025-01-01", end="2025-06-30")]

    def test_today_shows_the_amended_wording_and_drops_expired(self):
        kept = as_of(self.ITEMS, date(2026, 9, 13))
        assert [x["id"] for x in kept] == ["HIEN_HANH", "SUA_DOI", "BO_SUNG"]
        assert kept[1]["behavior"] == "hành vi SUA_DOI"
        assert not kept[1].get("shown_before_amendment")

    def test_before_the_amendment_restores_old_wording_and_hides_additions(self):
        kept = as_of(self.ITEMS, date(2025, 3, 1))
        assert [x["id"] for x in kept] == ["HIEN_HANH", "SUA_DOI", "HET_HIEU_LUC"]
        assert kept[1]["behavior"] == "câu chữ cũ"
        assert kept[1]["shown_before_amendment"] is True

    def test_does_not_mutate_the_engine_payload(self):
        items = [dict(x) for x in self.ITEMS]
        as_of(items, date(2025, 3, 1))
        assert items[1]["behavior"] == "hành vi SUA_DOI"

    def test_items_without_validity_are_kept(self):
        """Khái niệm không mang hiệu lực — không được lặng lẽ biến mất."""
        assert as_of([{"id": "KN", "name": "x"}], date(2020, 1, 1)) == [{"id": "KN", "name": "x"}]


class TestAsOfRules:
    def test_rules_restore_their_own_before_text(self):
        """Quy tắc R98 lưu câu chữ cũ ở ``text_before_amendment``, không phải ``behavior``."""
        r = {"id": "R98", "text": "mới", "text_before_amendment": "cũ",
             "validity": {"start": "2026-08-15", "end": None}}
        kept = as_of([r], date(2025, 3, 1), text_key="text", before_key="text_before_amendment")
        assert kept[0]["text"] == "cũ" and kept[0]["shown_before_amendment"] is True


class TestValidityTimeline:
    """Timeline dọc ở màn Chi tiết điều khoản — suy từ dữ liệu, không gõ tay."""

    ND168 = "Nghị định 168/2024/NĐ-CP"
    ND238 = ["Nghị định 238/2026/NĐ-CP (hiệu lực 15/8/2026)"]

    def test_untouched_provision(self):
        t = validity_timeline(start=date(2025, 1, 1), end=None, origin=date(2025, 1, 1),
                              origin_doc=self.ND168, amended_by=None, has_before=False,
                              amending_docs=self.ND238, moc=date(2026, 9, 13))
        assert [(m.date_text, m.caption, m.reached) for m in t] == [
            ("01/01/2025", "Nghị định 168/2024/NĐ-CP có hiệu lực", True),
            ("Chưa có mốc kết thúc", "Nghị định 238/2026/NĐ-CP không sửa điều khoản này", False),
        ]

    def test_amended_provision_shows_both_versions(self):
        t = validity_timeline(start=date(2026, 8, 15), end=None, origin=date(2025, 1, 1),
                              origin_doc=self.ND168,
                              amended_by="Nghị định 238/2026/NĐ-CP Điều 19 khoản 10",
                              has_before=True, amending_docs=self.ND238, moc=date(2025, 3, 1))
        assert [m.date_text for m in t] == ["01/01/2025", "15/08/2026", "Chưa có mốc kết thúc"]
        assert t[1].caption == "Sửa đổi bởi Nghị định 238/2026/NĐ-CP Điều 19 khoản 10"
        assert [m.reached for m in t] == [True, False, False], "Mốc chưa tới thì chấm rỗng"

    def test_added_provision_starts_at_the_amendment(self):
        t = validity_timeline(start=date(2026, 8, 15), end=None, origin=date(2025, 1, 1),
                              origin_doc=self.ND168, amended_by="Nghị định 238/2026/NĐ-CP Điều 7",
                              has_before=False, amending_docs=self.ND238, moc=date(2026, 9, 13))
        assert t[0].caption == "Bổ sung bởi Nghị định 238/2026/NĐ-CP Điều 7"
        assert len(t) == 2


class TestTimelineTruthfulness:
    """Hai lỗi phát hiện khi soát mã: hệ không được khẳng định điều dữ liệu không nói."""

    ND168 = "Nghị định 168/2024/NĐ-CP"
    ND238 = ["Nghị định 238/2026/NĐ-CP (hiệu lực 15/8/2026)"]

    def test_amended_provision_viewed_before_amendment_is_not_called_current(self):
        t = validity_timeline(start=date(2026, 8, 15), end=None, origin=date(2025, 1, 1),
                              origin_doc=self.ND168, amended_by="NĐ 238 Điều 19 khoản 10",
                              has_before=True, amending_docs=self.ND238, moc=date(2026, 1, 1))
        assert "Phiên bản này" not in t[-1].caption
        assert t[-1].caption == "Tại 01/01/2026 câu chữ trước sửa đổi đang được áp dụng"

    def test_added_provision_viewed_before_it_exists(self):
        t = validity_timeline(start=date(2026, 8, 15), end=None, origin=date(2025, 1, 1),
                              origin_doc=self.ND168, amended_by="NĐ 238 Điều 7",
                              has_before=False, amending_docs=self.ND238, moc=date(2026, 1, 1))
        assert t[-1].caption == "Chưa có hiệu lực tại 01/01/2026"

    def test_never_claims_untouched_when_an_amendment_record_touches_the_clause(self):
        """NĐ 238 BÃI BỎ điểm d–g khoản 17 Điều 32 bằng một bản ghi cấp khoản (SD_63)."""
        t = validity_timeline(start=date(2025, 1, 1), end=None, origin=date(2025, 1, 1),
                              origin_doc=self.ND168, amended_by=None, has_before=False,
                              amending_docs=self.ND238, moc=date(2026, 9, 13),
                              touching=["Bãi bỏ: BÃI BỎ điểm d, điểm đ, điểm e, điểm g khoản 17"])
        assert "không sửa" not in t[-1].caption
        assert "Bãi bỏ" in t[-1].caption


class TestAmendmentsTouching:
    AM = [{"kind": "bai_bo", "decree_article": 32, "decree_clause": 17, "decree_point": None,
           "note": "BÃI BỎ điểm d khoản 17"},
          {"kind": "sua_doi", "decree_article": 6, "decree_clause": 5, "decree_point": "p",
           "note": "Thay thế cụm từ"},
          {"kind": "bai_bo", "decree_article": 32, "decree_clause": None, "decree_point": None,
           "note": "Bỏ cụm từ tại điểm b khoản 7"}]

    def test_clause_level_record_touches_every_point_of_that_clause(self):
        hit = amendments_touching(self.AM, {"article": 32, "clause": 17, "point": "d"})
        assert [a["note"] for a in hit] == [
            "BÃI BỎ điểm d khoản 17", "Bỏ cụm từ tại điểm b khoản 7"]

    def test_point_level_record_does_not_touch_sibling_points(self):
        assert amendments_touching(self.AM, {"article": 6, "clause": 5, "point": "q"}) == []


def test_clean_citation_text_drops_missing_parts():
    assert clean_citation_text("Nghị định 238/2026/NĐ-CP Điều 3 khoản None") == \
        "Nghị định 238/2026/NĐ-CP Điều 3"
    assert clean_citation_text("NĐ 238 Điều 19 khoản 10") == "NĐ 238 Điều 19 khoản 10"
