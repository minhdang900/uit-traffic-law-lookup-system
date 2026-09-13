"""Đối chiếu bản ghi hành vi với CHÍNH văn bản sửa đổi đã lưu trong amendments.json.

VÌ SAO CẦN
==========
Các bản ghi ``VP_BS_*`` (hành vi do Nghị định 238/2026/NĐ-CP bổ sung) được dựng
tay từ văn bản sửa đổi. Soát lại ngày 13/09/2026 bắt được năm chỗ lệch mà không
phép kiểm tra kiểu nào phát hiện được, vì dữ liệu sai vẫn "hợp lệ":

1. SD_16 sửa điểm c khoản 10 Điều 20: hành vi tại "khoản 8, khoản 8a" bị trừ 06
   điểm — nhưng VP_BS_SD_15_1 (khoản 8a) ghi 0 điểm.
2. SD_30 sửa khoản 4 Điều 29: hành vi tại "khoản 3, khoản 3a" bị trừ 02 điểm —
   nhưng VP_BS_SD_29_1/2 (khoản 3a) ghi 0 điểm.
3. SD_31 (khoản 9a Điều 32) xử phạt "tổ chức là CHỦ XE" — bản ghi lại ghi chủ thể
   là người điều khiển.
4. Điểm b khoản 9a Điều 32 chỉ có hiệu lực từ 01/01/2028 (khoản 3 Điều 53 Nghị
   định 168/2024/NĐ-CP) — bản ghi lại tính từ 15/08/2026.
5. SD_63 BÃI BỎ điểm d, đ, e, g khoản 17 Điều 32 — bốn bản ghi vẫn còn hiệu lực
   vô thời hạn.
"""
import re
from datetime import date

import pytest

pytestmark = pytest.mark.cham

HL_ND238 = date(2026, 8, 15)


@pytest.fixture(scope="module")
def vp(kb):
    return {v.id: v for v in kb.violations}

#: "…hành vi (vi phạm) quy định tại khoản 8, khoản 8a Điều này bị trừ điểm giấy
#: phép lái xe 06 điểm" — chỉ dạng tham chiếu CẤP KHOẢN mới đối chiếu tự động được.
_TRU_DIEM_CAP_KHOAN = re.compile(
    r"quy định tại ((?:khoản \d+[a-z]?(?:, )?)+) Điều này bị trừ điểm giấy phép lái xe (\d+) điểm")


def _cap_khoan(noi_dung: str) -> tuple[list[str], int] | None:
    m = _TRU_DIEM_CAP_KHOAN.search(noi_dung)
    if not m:
        return None
    return re.findall(r"khoản (\d+[a-z]?)", m.group(1)), int(m.group(2))


class TestPointsFollowAmendmentText:
    def test_the_two_clause_level_point_amendments_are_recognised(self, kb):
        """Đối chứng dương: bộ đối chiếu phải nhận ra đúng SD_16 và SD_30."""
        nhan = sorted(a.id for a in kb.amendments
                      if a.licence_points and a.new_text and _cap_khoan(a.new_text))
        assert nhan == ["SD_16", "SD_30"]

    def test_added_violations_carry_the_points_their_clause_deducts(self, kb):
        lech = []
        for a in kb.amendments:
            kq = _cap_khoan(a.new_text or "") if a.licence_points else None
            if not kq:
                continue
            khoan, diem = kq
            for v in kb.violations:
                if (v.id.startswith("VP_BS_") and v.citation.article == a.decree_article
                        and str(v.citation.clause) in khoan and v.licence_points != diem):
                    lech.append(f"{v.id}: {v.licence_points} điểm, {a.id} quy định {diem}")
        assert lech == [], "\n".join(lech)


class TestOwnerViolations:
    @pytest.mark.parametrize("vid", ["VP_BS_SD_31_1", "VP_BS_SD_31_2"])
    def test_clause_9a_article_32_penalises_the_vehicle_owner(self, kb, vp, vid):
        sd31 = next(a for a in kb.amendments if a.id == "SD_31")
        assert "chủ xe" in sd31.new_text
        assert vp[vid].subject == "chu_phuong_tien"


class TestDeferredAndRepealedProvisions:
    def test_point_b_clause_9a_article_32_starts_2028(self, vp):
        assert vp["VP_BS_SD_31_2"].validity.start == date(2028, 1, 1)
        assert vp["VP_BS_SD_31_1"].validity.start == HL_ND238

    @pytest.mark.parametrize("diem", ["D", "DD", "E", "G"])
    def test_points_repealed_by_sd63_end_the_day_before_decree_238(self, vp, diem):
        v = vp[f"VP_ND168D32_K17{diem}"]
        assert v.validity.end == date(2026, 8, 14)
        assert not v.validity.in_force_on(HL_ND238)

    def test_phrase_removals_do_not_end_a_provision(self, kb, vp):
        """"Bỏ cụm từ" (SD_58–SD_62) chỉ sửa câu chữ, KHÔNG phải bãi bỏ điều khoản."""
        con = [v.id for v in kb.violations
               if v.citation.article == 32 and str(v.citation.clause) == "7"
               and v.citation.point in ("b", "d")]
        assert con and all(vp[i].validity.end is None for i in con)

    def test_other_points_of_clause_17_are_untouched(self, vp):
        for diem in ("A", "B", "C"):
            assert vp[f"VP_ND168D32_K17{diem}"].validity.end is None
