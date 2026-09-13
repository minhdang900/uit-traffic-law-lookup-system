"""Khoá HỢP ĐỒNG ĐẦU RA của tầng suy diễn bằng ảnh chụp vàng (golden file).

VÌ SAO CẦN
==========
Tầng suy diễn sắp được chuyển từ truy cập ``dict`` sang mô hình có kiểu. Cổng
chỉ số trong CI chỉ canh các con số tổng hợp (Top-1, MRR...) nên vẫn có thể bỏ
lọt thay đổi cục bộ: sai thứ tự trong một lớp bài toán, thiếu một trường trong
dict trả về, điểm lệch ở chữ số thứ tư. Tệp này khoá TỪNG truy vấn một.

Ảnh chụp được sinh từ hành vi TRƯỚC khi refactor:

    python -m tests.test_hop_dong_dau_ra --ghi-lai

Nếu một thay đổi làm ảnh chụp lệch, đó là tín hiệu phải DỪNG và xem xét, không
phải lý do để chạy lại lệnh ghi đè.
"""
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.cham

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "tests" / "data" / "snapshot_output.json"

#: Phủ đủ 7 lớp bài toán P1..P7 cùng vài truy vấn biên.
QUERIES = [
    "xe cơ giới là gì",
    "nồng độ cồn là gì",
    "người lái xe phải mang theo giấy tờ gì",
    "quy tắc nhường đường tại nơi giao nhau",
    "vượt đèn đỏ xe máy phạt bao nhiêu",
    "không đội mũ bảo hiểm phạt bao nhiêu",
    "nồng độ cồn 0,3 mg/l phạt thế nào",
    "lỗi nào bị trừ 10 điểm giấy phép lái xe",
    "những lỗi nào bị phạt trên 30 triệu đồng",
    "Điều 6 khoản 9 điểm a Nghị định 168/2024/NĐ-CP nói về lỗi gì?",
    "tôi vừa vượt đèn đỏ vừa không có giấy phép lái xe thì bị phạt bao nhiêu",
    "Xe ưu tiên.",
    "cách nấu phở bò",
]


def _digest(kq):
    """Rút gọn kết quả thành phần quan sát được, đủ chặt để bắt mọi sai lệch."""
    def item(ds):
        return [{"id": x["id"], "score": x.get("score"),
                 "supplementary": x.get("supplementary", False)}
                for x in ds]
    return {
        "problem_class": kq.get("problem_class"),
        "not_found": kq["not_found"],
        "concepts": item(kq["concepts"]),
        "rules": item(kq["rules"]),
        "violations": item(kq["violations"]),
        # Khoa ca BO TRUONG cua mau dau tien: doi hinh dang dict la pha hop dong.
        "violation_fields": sorted(kq["violations"][0]) if kq["violations"] else [],
        "concept_fields": sorted(kq["concepts"][0]) if kq["concepts"] else [],
    }


def build_snapshot(system):
    return {q: _digest(system.ask(q, top_k=5)) for q in QUERIES}


@pytest.fixture(scope="session")
def baseline_snapshot():
    if not SNAPSHOT.exists():
        pytest.skip(f"Chưa có ảnh chụp {SNAPSHOT}; sinh bằng --ghi-lai")
    with SNAPSHOT.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("query", QUERIES)
def test_output_matches_snapshot(system, baseline_snapshot, query):
    """Từng truy vấn phải cho ra ĐÚNG kết quả như trước khi refactor."""
    assert _digest(system.ask(query, top_k=5)) == baseline_snapshot[query]


def test_snapshot_covers_all_seven_problem_classes(baseline_snapshot):
    """Ảnh chụp mất giá trị nếu không phủ hết các lớp bài toán."""
    lop = {v["problem_class"] for v in baseline_snapshot.values() if v["problem_class"]}
    assert len(lop) >= 7, f"Ảnh chụp chỉ phủ {len(lop)} lớp: {sorted(lop)}"


if __name__ == "__main__":
    import sys

    if "--ghi-lai" not in sys.argv:
        raise SystemExit("Dùng: python -m tests.test_hop_dong_dau_ra --ghi-lai")
    sys.path.insert(0, str(ROOT / "src"))
    from traffic_law.reasoning.engine import LawLookup

    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    with SNAPSHOT.open("w", encoding="utf-8") as f:
        json.dump(build_snapshot(LawLookup()), f, ensure_ascii=False, indent=1)
    print(f"Đã ghi {SNAPSHOT.relative_to(ROOT)} ({len(QUERIES)} truy vấn)")
