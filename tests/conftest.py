"""Cấu hình chung cho bộ kiểm thử."""
from pathlib import Path

import pytest

from tra_cuu_gtdb.kb.loader import CoSoTriThuc, nap_co_so_tri_thuc

THU_MUC_KB = Path(__file__).resolve().parent.parent / "data" / "kb"


@pytest.fixture(scope="session")
def kb() -> CoSoTriThuc:
    """Cơ sở tri thức đã nạp và kiểm kiểu, dùng chung cho cả phiên kiểm thử."""
    return nap_co_so_tri_thuc(THU_MUC_KB)


@pytest.fixture(scope="session")
def he_thong():
    """Hệ thống tra cứu đầy đủ (nạp KB + dựng chỉ mục TF-IDF) — dùng chung cả phiên."""
    from tra_cuu_gtdb.reasoning.engine import TraCuuPhapLuat
    return TraCuuPhapLuat()


@pytest.fixture(scope="session")
def kb_da_lap_chi_muc(he_thong):
    """Cơ sở tri thức ĐÃ LẬP CHỈ MỤC mà tầng suy diễn dùng.

    Từ bước chuyển sang mô hình có kiểu, các bộ sưu tập ở đây (``keyphrases``,
    ``violations``...) chứa mô hình Pydantic chứ không còn ``dict``; chỉ đầu ra
    của ``hoi()`` mới là dict.
    """
    return he_thong.kb


@pytest.fixture(scope="session")
def bo_qa():
    """Bộ 120 câu hỏi kiểm thử có đáp án chuẩn."""
    import json
    with (Path(__file__).resolve().parent.parent / "eval" / "qa_dataset.json").open(
            encoding="utf-8") as f:
        return json.load(f)
