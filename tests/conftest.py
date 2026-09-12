"""Cấu hình chung cho bộ kiểm thử."""
from pathlib import Path

import pytest

from tra_cuu_gtdb.kb.loader import CoSoTriThuc, nap_co_so_tri_thuc

THU_MUC_KB = Path(__file__).resolve().parent.parent / "data" / "kb"


@pytest.fixture(scope="session")
def kb() -> CoSoTriThuc:
    """Cơ sở tri thức đã nạp và kiểm kiểu, dùng chung cho cả phiên kiểm thử."""
    return nap_co_so_tri_thuc(THU_MUC_KB)
