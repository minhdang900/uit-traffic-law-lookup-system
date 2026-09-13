"""Kiểm thử bộ kịch bản nghiệm thu.

``eval/evaluate.py`` đo 120 câu bằng chỉ số tổng hợp — tốt cho việc theo dõi
hồi quy, nhưng đọc một con số 76,67% thì không biết hệ thống LÀM ĐƯỢC GÌ.

Bộ kịch bản này ngược lại: ít ca, mỗi ca nêu rõ KỲ VỌNG CỤ THỂ và đạt hay
không đạt thấy ngay. Dùng khi demo, khi nghiệm thu, và khi cần biết một thay
đổi vừa làm hỏng đúng cái gì.
"""
import pytest

from traffic_law.acceptance.scenarios import SCENARIOS, Scenario, check_scenario

pytestmark = pytest.mark.cham


class TestChecker:
    """Bản thân bộ kiểm tra phải bắt được lỗi — nếu không thì mọi ca đều 'đạt'."""

    def test_passes_when_every_expectation_matches(self):
        kq = {"problem_class": "P3_TRA_CUU_CHE_TAI", "not_found": False,
              "violations": [{"id": "VP_X", "citation_text": "Điều 7 khoản 7",
                           "fine": {"min": 4000000, "max": 6000000},
                           "licence_points": 4}],
              "concepts": [], "rules": []}
        ca = Scenario(code="TC00", group="thu", question="x",
                     lop="P3_TRA_CUU_CHE_TAI", chua_id="VP_X",
                     can_cu_chua="Điều 7", tien=(4000000, 6000000), tru_diem=4)
        assert check_scenario(kq, ca) == []

    def test_catches_wrong_problem_class(self):
        kq = {"problem_class": "P1_TRA_CUU_KHAI_NIEM", "not_found": False,
              "violations": [], "concepts": [], "rules": []}
        errors = check_scenario(kq, Scenario(code="TC00", group="thu", question="x",
                                      lop="P3_TRA_CUU_CHE_TAI"))
        assert any("lớp" in x for x in errors), errors

    def test_catches_missing_knowledge_id(self):
        kq = {"problem_class": "P3_TRA_CUU_CHE_TAI", "not_found": False,
              "violations": [{"id": "VP_KHAC", "citation_text": "", "fine": {},
                           "licence_points": None}], "concepts": [], "rules": []}
        errors = check_scenario(kq, Scenario(code="TC00", group="thu", question="x",
                                      chua_id="VP_CAN_TIM"))
        assert any("VP_CAN_TIM" in x for x in errors), errors

    def test_catches_wrong_fine_range(self):
        kq = {"problem_class": "P3_TRA_CUU_CHE_TAI", "not_found": False,
              "violations": [{"id": "VP_X", "citation_text": "",
                           "fine": {"min": 100000, "max": 200000},
                           "licence_points": None}], "concepts": [], "rules": []}
        errors = check_scenario(kq, Scenario(code="TC00", group="thu", question="x",
                                      tien=(4000000, 6000000)))
        assert any("phạt tiền" in x for x in errors), errors

    def test_can_check_rejection_expectation(self):
        kq = {"problem_class": "P7_TRA_CUU_LIEN_QUAN", "not_found": False,
              "violations": [], "concepts": [], "rules": []}
        errors = check_scenario(kq, Scenario(code="TC00", group="thu", question="x",
                                      not_found=True))
        assert errors, "Kỳ vọng bị từ chối nhưng hệ thống trả lời — phải báo lỗi"


class TestScenarioSet:
    def test_scenario_codes_are_unique(self):
        code = [c.code for c in SCENARIOS]
        assert len(set(code)) == len(code), "Mã ca kiểm thử bị trùng"

    def test_covers_all_seven_problem_classes(self):
        lop = {c.lop for c in SCENARIOS if c.lop}
        assert len(lop) >= 7, f"Mới phủ {len(lop)} lớp: {sorted(lop)}"

    def test_every_scenario_states_an_expectation(self):
        """Ca không có kỳ vọng nào thì luôn 'đạt' — vô nghĩa."""
        rong = [c.code for c in SCENARIOS if not c.has_expectation()]
        assert rong == [], f"Ca không nêu kỳ vọng: {rong}"

    @pytest.mark.parametrize("code", [c.code for c in SCENARIOS])
    def test_every_scenario_passes_on_real_system(self, system, code):
        ca = next(c for c in SCENARIOS if c.code == code)
        errors = check_scenario(system.ask(ca.question, top_k=5), ca)
        assert errors == [], f"{ca.code} ({ca.question!r}): " + "; ".join(errors)
