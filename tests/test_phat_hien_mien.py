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

from tra_cuu_gtdb.retrieval.dense import (
    NGUONG_MIEN_AN_TOAN,
    BoLocMien,
    dense_kha_dung,
)

pytestmark = pytest.mark.cham

GOC = Path(__file__).resolve().parent.parent
can_dense = pytest.mark.skipif(
    not dense_kha_dung(), reason="Cần gói tuỳ chọn 'dense' (pip install -e '.[dense]')")


@pytest.fixture(scope="session")
def ngoai_mien():
    with (GOC / "eval" / "truy_van_ngoai_mien.json").open(encoding="utf-8") as f:
        return [t["cau_hoi"] for t in json.load(f)["truy_van"]]


@pytest.fixture(scope="session")
def bo_loc(he_thong):
    return BoLocMien(he_thong.kb)


class TestHopDongTuyChon:
    """Tầng dense là TUỲ CHỌN — vắng nó hệ thống không được đổi hành vi."""

    def test_bao_duoc_minh_co_kha_dung_hay_khong(self):
        assert isinstance(dense_kha_dung(), bool)

    def test_thieu_dense_thi_khong_tu_choi_cau_nao(self, he_thong, bo_qa):
        """Đường cơ sở phải giữ nguyên: mặc định không bật lọc miền."""
        bi_tu_choi = [m["id"] for m in bo_qa
                      if he_thong.hoi(m["cau_hoi"])["khong_tim_thay"]]
        assert bi_tu_choi == []

    def test_nguong_an_toan_nam_trong_khoang_do_duoc(self):
        """0.45 là ngưỡng lớn nhất giữ được 0 câu hợp lệ bị từ chối oan."""
        assert 0.40 <= NGUONG_MIEN_AN_TOAN <= 0.50


@can_dense
class TestDenseTachDuocMien:
    """Điều mà TF-IDF KHÔNG làm được, dense LÀM ĐƯỢC — đo bằng số."""

    def test_khong_tu_choi_oan_cau_hop_le_nao(self, bo_loc, bo_qa):
        """Ràng buộc cứng: giữ nguyên hợp đồng 0 câu hợp lệ bị loại."""
        oan = [m["id"] for m in bo_qa if bo_loc.ngoai_mien(m["cau_hoi"])]
        assert oan == [], f"{len(oan)}/120 câu hợp lệ bị từ chối oan: {oan[:10]}"

    def test_loai_duoc_phan_lon_truy_van_rac(self, bo_loc, ngoai_mien):
        """Đường cơ sở TF-IDF loại được 7,5%. Quy tắc kết hợp đo được 92,5%."""
        loai = [q for q in ngoai_mien if bo_loc.ngoai_mien(q)]
        ty_le = len(loai) / len(ngoai_mien)
        assert ty_le >= 0.90, f"Chỉ loại được {ty_le:.1%} truy vấn rác"

    def test_auc_vuot_troi_so_voi_tfidf(self, bo_loc, bo_qa, ngoai_mien):
        """AUC dense (0.9958) phải vượt TF-IDF thô (0.8746) và keyphrase (0.9500)."""
        trong = [bo_loc.diem_mien(m["cau_hoi"]) for m in bo_qa]
        ngoai = [bo_loc.diem_mien(q) for q in ngoai_mien]
        auc = sum((a > b) + 0.5 * (a == b) for a in trong for b in ngoai)
        auc /= len(trong) * len(ngoai)
        assert auc >= 0.97, f"AUC dense chỉ đạt {auc:.4f}"


@can_dense
class TestDanhDoiConLai:
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
    def test_nen_loai_duoc_toan_bo_truy_van_rac(self, bo_loc, ngoai_mien):
        con_lai = [q for q in ngoai_mien if not bo_loc.ngoai_mien(q)]
        assert con_lai == [], f"{len(con_lai)}/40 truy vấn rác vẫn lọt: {con_lai}"
