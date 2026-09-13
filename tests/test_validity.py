"""Kiểm thử hiệu lực theo thời gian.

Rủi ro pháp lý nghiêm trọng nhất của một hệ tra cứu pháp luật là trả về mức phạt
đã hết hiệu lực. Các test dưới đây khoá lại hành vi chặn rủi ro đó.

Mốc thời gian trong cơ sở tri thức:
    2025-01-01  Luật 36/2024 và Nghị định 168/2024 có hiệu lực
    2026-08-15  Nghị định 238/2026 có hiệu lực (sửa đổi + bổ sung NĐ 168)
"""
from datetime import date

import pytest
from pydantic import ValidationError

from traffic_law.domain.temporal import EffectivePeriod

HL_ND168 = date(2025, 1, 1)
HL_ND238 = date(2026, 8, 15)


class TestEffectivePeriod:
    def test_open_period_stays_in_force(self):
        k = EffectivePeriod(start=HL_ND168)
        assert k.in_force_on(HL_ND168)
        assert k.in_force_on(date(2099, 1, 1))

    def test_not_applied_before_effective_date(self):
        k = EffectivePeriod(start=HL_ND168)
        assert not k.in_force_on(date(2024, 12, 31))

    def test_closed_period_includes_last_day(self):
        """Điều khoản có hiệu lực trong CẢ ngày hết hiệu lực."""
        k = EffectivePeriod(start=HL_ND168, end=date(2026, 8, 14))
        assert k.in_force_on(date(2026, 8, 14))
        assert not k.in_force_on(HL_ND238)

    def test_end_before_start_is_rejected(self):
        with pytest.raises(ValidationError):
            EffectivePeriod(start=HL_ND238, end=HL_ND168)


class TestValidityInference:
    pytestmark = pytest.mark.cham

    def test_every_provision_has_a_validity_period(self, kb):
        missing = [x.id for tap in (kb.rules, kb.violations) for x in tap if x.validity is None]
        assert missing == [], f"{len(missing)} điều khoản chưa suy diễn hiệu lực: {missing[:5]}"

    def test_decree168_provisions_start_2025_01_01(self, kb):
        goc = [v for v in kb.violations if not v.amended_by]
        assert goc, "Không có điều khoản gốc nào"
        assert all(v.validity and v.validity.start == HL_ND168 for v in goc)

    def test_provisions_created_by_decree238_start_2026_08_15(self, kb):
        sua = [v for v in kb.violations if v.amended_by]
        assert sua, "Không có điều khoản nào liên quan Nghị định 238"
        assert all(v.validity and v.validity.start == HL_ND238 for v in sua)


class TestLookupAtPointInTime:
    pytestmark = pytest.mark.cham

    def test_before_2025_no_provision_applies(self, kb):
        """Nghị định 168/2024 chưa có hiệu lực ngày 31/12/2024."""
        k = kb.as_of(date(2024, 12, 31))
        assert len(k.violations) == 0
        assert len(k.rules) == 0

    def test_mid_2025_excludes_decree238_amendments(self, kb):
        k = kb.as_of(date(2025, 6, 1))
        assert 0 < len(k.violations) < len(kb.violations)
        assert all(not v.amended_by for v in k.violations), (
            "Điều khoản của Nghị định 238 xuất hiện trước ngày 15/8/2026")

    def test_after_2026_08_15_everything_applies(self, kb):
        k = kb.as_of(date(2026, 9, 1))
        assert len(k.violations) == len(kb.violations)

    def test_applies_on_the_effective_date_itself(self, kb):
        """Biên: điều khoản có hiệu lực NGAY trong ngày 15/8/2026."""
        truoc = kb.as_of(date(2026, 8, 14))
        dung_ngay = kb.as_of(HL_ND238)
        assert len(dung_ngay.violations) > len(truoc.violations)

    def test_defaults_to_today(self, kb):
        assert len(kb.as_of().violations) == len(kb.as_of(date.today()).violations)


class TestDeterministicInference:
    def test_script_is_idempotent(self):
        """Chạy lại script suy diễn không được tạo thay đổi nào."""
        import sys
        sys.path.insert(0, "scripts")
        from suy_dien_hieu_luc import chay
        assert chay(kiem_tra=True) == 0
