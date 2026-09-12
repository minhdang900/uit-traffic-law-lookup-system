"""Phát hiện miền bằng dense embedding — tầng TUỲ CHỌN.

VÌ SAO CÓ TỆP NÀY
=================
``tests/test_nguong_tin_cay.py`` ghi nhận một hạn chế ĐÃ ĐO ĐƯỢC: với đặc trưng
TF-IDF thưa, không ngưỡng nào tách được truy vấn hợp lệ khỏi truy vấn ngoài
lĩnh vực, vì hai phân bố điểm chồng khít lên nhau. Kết luận khi đó đề xuất thử
dense embedding. Tệp này hiện thực hoá đề xuất đó.

ĐÃ ĐO ĐƯỢC (120 câu hỏi chuẩn, 40 truy vấn ngoài miền phủ 11 chủ đề)
--------------------------------------------------------------------
    tín hiệu          AUC       loại rác khi 0 câu oan
    TF-IDF thô        0.8746     7,5%
    số keyphrase      0.9500     0,0%
    phủ từ vựng KB    0.7243    47,5%   (AUC gần mức ngẫu nhiên: truy vấn rác
                                         dùng toàn từ phổ thông vốn có đầy
                                         trong kho ngữ liệu — tín hiệu vô dụng)
    dense             0.9958    77,5%
    dense + keyphrase    --     92,5%   <- quy tắc đang dùng

Tái lập bằng: ``python eval/phat_hien_mien.py --dense --ghi``

QUY TẮC TỪ CHỐI
---------------
Từ chối khi ĐỒNG THỜI: (a) không rút được keyphrase nào, VÀ (b) điểm dense dưới
ngưỡng. Hai tín hiệu BÙ cho nhau: câu hợp lệ điểm dense thấp thường giàu
keyphrase ("xe gắn máy là gì vậy mọi người" — dense 0.392 nhưng có keyphrase),
còn truy vấn rác không có keyphrase nào.

NGƯỠNG
------
``NGUONG_MIEN_AN_TOAN`` = 0.45 là giá trị LỚN NHẤT còn giữ được hợp đồng "không
từ chối oan câu hợp lệ nào". Đẩy lên 0.52 sẽ loại hết 100% truy vấn rác nhưng
làm oan 3/120 câu — đánh đổi đó bị từ chối, xem test xfail đi kèm.

TÍNH TUỲ CHỌN
-------------
Thiếu gói ``dense`` thì mọi thứ vẫn chạy y như cũ; không hàm nào ở đây được gọi
trên đường đi mặc định của bộ máy suy diễn. Mô hình nặng ~470 MB nên CI mặc
định KHÔNG cài, và cổng chỉ số vẫn đo trên cấu hình mặc định.
"""
from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:  # pragma: no cover - chi phuc vu kiem kieu
    from tra_cuu_gtdb.reasoning.engine import KnowledgeBase

# Mô hình đa ngữ nhẹ, có tiếng Việt. Ghim tên để kết quả đo lặp lại được.
TEN_MO_HINH = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

#: Ngưỡng lớn nhất còn giữ được 0 câu hợp lệ bị từ chối oan (đo trên 120 câu).
NGUONG_MIEN_AN_TOAN = 0.45

#: Ngưỡng loại được 100% truy vấn rác — KHÔNG dùng mặc định vì làm oan 3/120 câu.
NGUONG_LOAI_HET_RAC = 0.52

THU_MUC_CACHE = os.environ.get(
    "TRA_CUU_GTDB_CACHE", os.path.join(os.path.expanduser("~"), ".cache", "tra-cuu-gtdb"))


def dense_kha_dung() -> bool:
    """Gói tuỳ chọn ``dense`` đã cài hay chưa. Không ném lỗi khi thiếu."""
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        return False
    return True


@lru_cache(maxsize=2)
def _nap_mo_hinh(ten: str) -> Any:
    """Nạp mô hình một lần cho cả tiến trình (nạp lại rất tốn thời gian)."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(ten)


class BoLocMien:
    """Chấm điểm "thuộc lĩnh vực giao thông đường bộ" cho một truy vấn.

    Dựng chỉ mục dense cho toàn bộ tri thức (hành vi + khái niệm + quy tắc) rồi
    đo tương đồng cực đại giữa truy vấn và kho đó.
    """

    def __init__(self, kb: KnowledgeBase, ten_mo_hinh: str = TEN_MO_HINH,
                 nguong: float = NGUONG_MIEN_AN_TOAN) -> None:
        if not dense_kha_dung():
            raise RuntimeError(
                "Thiếu gói tuỳ chọn 'dense'. Cài bằng: pip install -e '.[dense]'")
        from tra_cuu_gtdb.reasoning.engine import QueryAnalyzer

        self.kb = kb
        self.nguong = nguong
        self.ten_mo_hinh = ten_mo_hinh
        self.analyzer = QueryAnalyzer(kb)
        self.mo_hinh = _nap_mo_hinh(ten_mo_hinh)
        self.corpus = ([v["text_search"] for v in kb.violations]
                       + [c["text_search"] for c in kb.concepts]
                       + [r["text_search"] for r in kb.rules])
        self.E = self._nhung_corpus()

    # ------------------------------------------------------------- chi muc
    def _duong_dan_cache(self) -> str:
        khoa = hashlib.sha256(
            (self.ten_mo_hinh + "\x00" + "\x00".join(self.corpus)).encode("utf-8")
        ).hexdigest()[:16]
        return os.path.join(THU_MUC_CACHE, f"nhung_{khoa}.npy")

    def _nhung_corpus(self) -> np.ndarray:
        """Nhúng kho tri thức, có nhớ đệm trên đĩa theo nội dung kho."""
        dd = self._duong_dan_cache()
        if os.path.exists(dd):
            try:
                return np.asarray(np.load(dd), dtype=np.float32)
            except (OSError, ValueError):
                pass  # cache hong thi tinh lai, khong lam gay he thong
        E = np.asarray(self.mo_hinh.encode(
            self.corpus, normalize_embeddings=True, batch_size=64,
            show_progress_bar=False), dtype=np.float32)
        try:
            os.makedirs(THU_MUC_CACHE, exist_ok=True)
            np.save(dd, E)
        except OSError:
            pass  # khong ghi duoc cache thi thoi, khong phai loi
        return E

    # -------------------------------------------------------------- cham diem
    def diem_mien(self, truy_van: str) -> float:
        """Tương đồng dense cực đại giữa truy vấn và kho tri thức."""
        q = np.asarray(self.mo_hinh.encode(
            [truy_van], normalize_embeddings=True, show_progress_bar=False),
            dtype=np.float32)
        return float((q @ self.E.T).max())

    def so_keyphrase(self, truy_van: str) -> int:
        # Bo may suy dien la ban port NGUYEN VAN, co y khong gan chu thich kieu
        # (xem ghi chu duong bien kieu trong reasoning/engine.py). Day la cho
        # duy nhat tang retrieval cham vao no.
        kps = self.analyzer.rut_trich_keyphrase(truy_van)  # type: ignore[no-untyped-call]
        return len(kps)

    def ngoai_mien(self, truy_van: str) -> bool:
        """Truy vấn có nằm ngoài lĩnh vực không?

        Chỉ từ chối khi CẢ HAI tín hiệu cùng nói "ngoài miền" — xem ghi chú đầu
        tệp về lý do hai tín hiệu bù cho nhau.
        """
        if self.so_keyphrase(truy_van) > 0:
            return False
        return self.diem_mien(truy_van) < self.nguong
