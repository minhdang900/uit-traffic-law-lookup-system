"""Cấu hình chung cho bộ kiểm thử."""
from pathlib import Path

import pytest

from traffic_law.kb.loader import KnowledgeBase, load_knowledge_base

THU_MUC_KB = Path(__file__).resolve().parent.parent / "data" / "kb"


@pytest.fixture(scope="session")
def kb() -> KnowledgeBase:
    """Cơ sở tri thức đã nạp và kiểm kiểu, dùng chung cho cả phiên kiểm thử."""
    return load_knowledge_base(THU_MUC_KB)


@pytest.fixture(scope="session")
def system():
    """Hệ thống tra cứu đầy đủ (nạp KB + dựng chỉ mục TF-IDF) — dùng chung cả phiên."""
    from traffic_law.reasoning.engine import LawLookup
    return LawLookup()


@pytest.fixture(scope="session")
def indexed_kb(system):
    """Cơ sở tri thức ĐÃ LẬP CHỈ MỤC mà tầng suy diễn dùng.

    Từ bước chuyển sang mô hình có kiểu, các bộ sưu tập ở đây (``keyphrases``,
    ``violations``...) chứa mô hình Pydantic chứ không còn ``dict``; chỉ đầu ra
    của ``hoi()`` mới là dict.
    """
    return system.kb


@pytest.fixture(scope="session")
def qa_set():
    """Bộ 120 câu hỏi kiểm thử có đáp án chuẩn."""
    import json
    with (Path(__file__).resolve().parent.parent / "eval" / "qa_dataset.json").open(
            encoding="utf-8") as f:
        return json.load(f)
