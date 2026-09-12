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

GOC = Path(__file__).resolve().parent.parent
ANH_CHUP = GOC / "tests" / "du_lieu" / "anh_chup_dau_ra.json"

#: Phủ đủ 7 lớp bài toán P1..P7 cùng vài truy vấn biên.
TRUY_VAN = [
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


def _tom_tat(kq):
    """Rút gọn kết quả thành phần quan sát được, đủ chặt để bắt mọi sai lệch."""
    def muc(ds):
        return [{"id": x["id"], "diem": x.get("diem"), "bo_sung": x.get("bo_sung", False)}
                for x in ds]
    return {
        "lop_bai_toan": kq.get("lop_bai_toan"),
        "khong_tim_thay": kq["khong_tim_thay"],
        "khai_niem": muc(kq["khai_niem"]),
        "quy_tac": muc(kq["quy_tac"]),
        "hanh_vi": muc(kq["hanh_vi"]),
        # Khoa ca BO TRUONG cua mau dau tien: doi hinh dang dict la pha hop dong.
        "truong_hanh_vi": sorted(kq["hanh_vi"][0]) if kq["hanh_vi"] else [],
        "truong_khai_niem": sorted(kq["khai_niem"][0]) if kq["khai_niem"] else [],
    }


def sinh_anh_chup(he_thong):
    return {q: _tom_tat(he_thong.hoi(q, top_k=5)) for q in TRUY_VAN}


@pytest.fixture(scope="session")
def anh_chup_goc():
    if not ANH_CHUP.exists():
        pytest.skip(f"Chưa có ảnh chụp {ANH_CHUP}; sinh bằng --ghi-lai")
    with ANH_CHUP.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("truy_van", TRUY_VAN)
def test_dau_ra_khop_anh_chup(he_thong, anh_chup_goc, truy_van):
    """Từng truy vấn phải cho ra ĐÚNG kết quả như trước khi refactor."""
    assert _tom_tat(he_thong.hoi(truy_van, top_k=5)) == anh_chup_goc[truy_van]


def test_anh_chup_phu_du_bay_lop_bai_toan(anh_chup_goc):
    """Ảnh chụp mất giá trị nếu không phủ hết các lớp bài toán."""
    lop = {v["lop_bai_toan"] for v in anh_chup_goc.values() if v["lop_bai_toan"]}
    assert len(lop) >= 7, f"Ảnh chụp chỉ phủ {len(lop)} lớp: {sorted(lop)}"


if __name__ == "__main__":
    import sys

    if "--ghi-lai" not in sys.argv:
        raise SystemExit("Dùng: python -m tests.test_hop_dong_dau_ra --ghi-lai")
    sys.path.insert(0, str(GOC / "src"))
    from tra_cuu_gtdb.reasoning.engine import TraCuuPhapLuat

    ANH_CHUP.parent.mkdir(parents=True, exist_ok=True)
    with ANH_CHUP.open("w", encoding="utf-8") as f:
        json.dump(sinh_anh_chup(TraCuuPhapLuat()), f, ensure_ascii=False, indent=1)
    print(f"Đã ghi {ANH_CHUP.relative_to(GOC)} ({len(TRUY_VAN)} truy vấn)")
