"""Kiểm thử tầng phát hiện miền (trong/ngoài lĩnh vực giao thông đường bộ).

BỐI CẢNH
========
Pha trước đã ĐO ĐƯỢC và ghi nhận: với đặc trưng TF-IDF thưa, không tồn tại
ngưỡng nào tách được truy vấn hợp lệ khỏi truy vấn rác (xem
``tests/test_nguong_tin_cay.py``). Kết luận khi đó đề xuất thử "dense embedding
hoặc bộ phân lớp miền riêng".

Pha này KIỂM CHỨNG đề xuất đó bằng đo đạc, trên 120 câu hỏi chuẩn và 40 truy
vấn ngoài miền (``eval/truy_van_ngoai_mien.json``, phủ 11 chủ đề).

KẾT QUẢ: dense embedding CẢI THIỆN RÕ RỆT nhưng KHÔNG xoá sạch đánh đổi.
Vì vậy tầng này là TUỲ CHỌN: thiếu gói ``dense`` thì hệ thống chạy y như cũ.
"""
import json
from pathlib import Path

import pytest

from traffic_law.retrieval.dense import (
    SAFE_DOMAIN_THRESHOLD,
    DomainFilter,
    dense_available,
)

pytestmark = pytest.mark.cham

ROOT = Path(__file__).resolve().parent.parent
can_dense = pytest.mark.skipif(
    not dense_available(), reason="Cần gói tuỳ chọn 'dense' (pip install -e '.[dense]')")


@pytest.fixture(scope="session")
def is_out_of_domain():
    with (ROOT / "eval" / "truy_van_ngoai_mien.json").open(encoding="utf-8") as f:
        return [t["cau_hoi"] for t in json.load(f)["truy_van"]]


@pytest.fixture(scope="session")
def filter_(system):
    return DomainFilter(system.kb)


class TestOptionalContract:
    """Tầng dense là TUỲ CHỌN — vắng nó hệ thống không được đổi hành vi."""

    def test_reports_whether_it_is_available(self):
        assert isinstance(dense_available(), bool)

    def test_without_dense_nothing_is_rejected(self, system, qa_set):
        """Đường cơ sở phải giữ nguyên: mặc định không bật lọc miền."""
        rejected = [m["id"] for m in qa_set
                      if system.ask(m["cau_hoi"])["not_found"]]
        assert rejected == []

    def test_safe_threshold_lies_in_measured_range(self):
        """0.45 là ngưỡng lớn nhất giữ được 0 câu hợp lệ bị từ chối oan."""
        assert 0.40 <= SAFE_DOMAIN_THRESHOLD <= 0.50


@can_dense
class TestDenseSeparatesDomain:
    """Điều mà TF-IDF KHÔNG làm được, dense LÀM ĐƯỢC — đo bằng số."""

    def test_rejects_no_valid_question(self, filter_, qa_set):
        """Ràng buộc cứng: giữ nguyên hợp đồng 0 câu hợp lệ bị loại."""
        oan = [m["id"] for m in qa_set if filter_.is_out_of_domain(m["cau_hoi"])]
        assert oan == [], f"{len(oan)}/120 câu hợp lệ bị từ chối oan: {oan[:10]}"

    def test_rejects_most_junk_queries(self, filter_, is_out_of_domain):
        """Đường cơ sở TF-IDF loại được 7,5%. Quy tắc kết hợp đo được 92,5%."""
        kind = [q for q in is_out_of_domain if filter_.is_out_of_domain(q)]
        ty_le = len(kind) / len(is_out_of_domain)
        assert ty_le >= 0.90, f"Chỉ loại được {ty_le:.1%} truy vấn rác"

    def test_auc_clearly_beats_tfidf(self, filter_, qa_set, is_out_of_domain):
        """AUC dense (0.9958) phải vượt TF-IDF thô (0.8746) và keyphrase (0.9500)."""
        trong = [filter_.domain_score(m["cau_hoi"]) for m in qa_set]
        ngoai = [filter_.domain_score(q) for q in is_out_of_domain]
        auc = sum((a > b) + 0.5 * (a == b) for a in trong for b in ngoai)
        auc /= len(trong) * len(ngoai)
        assert auc >= 0.97, f"AUC dense chỉ đạt {auc:.4f}"


@can_dense
class TestRemainingTradeoff:
    """Dense KHÔNG xoá hết đánh đổi. Ghi nhận phần còn lại, không giấu."""

    @pytest.mark.xfail(strict=True, reason=(
        "Đã ĐO: trần điểm dense của truy vấn rác là 0.516 ('điện thoại nào "
        "chụp ảnh đẹp') NẰM TRÊN sàn 0.464 của câu hợp lệ không có keyphrase "
        "('Có lỗi nào chỉ bị phạt cảnh cáo?'; kế đó 'Ra đường phải mang giấy "
        "tờ gì?' 0.476). Muốn loại 100% rác phải đẩy ngưỡng lên 0.52, khi đó "
        "3/120 câu hợp lệ bị oan — vi phạm hợp đồng 0 câu oan. Dense nâng AUC "
        "0.9500 -> 0.9958 nhưng hai phân bố VẪN chồng lấn. "
        "Muốn đóng nốt khoảng này cần mô hình tinh chỉnh trên miền pháp luật "
        "tiếng Việt, không phải chỉnh ngưỡng."))
    def test_should_reject_every_junk_query(self, filter_, is_out_of_domain):
        remaining = [q for q in is_out_of_domain if not filter_.is_out_of_domain(q)]
        assert remaining == [], f"{len(remaining)}/40 truy vấn rác vẫn lọt: {remaining}"
