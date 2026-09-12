"""Nạp cơ sở tri thức từ các tệp JSON vào mô hình dữ liệu đã kiểm kiểu.

Cơ sở tri thức để dạng JSON có chủ đích: khi một nghị định thay đổi, diff trên
pull request cho thấy chính xác điều khoản nào đã đổi — điều mà cơ sở dữ liệu
che mất.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from tra_cuu_gtdb.domain.models import (
    CumTuKhoa,
    KhaiNiem,
    QuanHe,
    QuyTac,
    SuaDoi,
    VanBan,
    ViPham,
)


class LoiNapTriThuc(Exception):
    """Nạp cơ sở tri thức thất bại. Thông điệp chỉ rõ tệp và bản ghi gây lỗi."""


@dataclass(frozen=True)
class PhanLoai:
    """Bảng phân loại dùng chung: lĩnh vực, nhóm, phương tiện, chủ thể, đồng nghĩa."""

    linh_vuc: dict[str, str]
    ten_nhom: dict[str, str]
    ten_phuong_tien: dict[str, str]
    ten_chu_the: dict[str, str]
    dong_nghia: dict[str, list[str]]


@dataclass(frozen=True)
class CoSoTriThuc:
    """Cơ sở tri thức K = (C, R, Rules, F, Keyphrase) cùng văn bản và sửa đổi."""

    khai_niem: tuple[KhaiNiem, ...]
    quan_he: tuple[QuanHe, ...]
    quy_tac: tuple[QuyTac, ...]
    vi_pham: tuple[ViPham, ...]
    cum_tu_khoa: tuple[CumTuKhoa, ...]
    van_ban: tuple[VanBan, ...]
    sua_doi: tuple[SuaDoi, ...]
    phan_loai: PhanLoai

    @property
    def dinh_danh_tri_thuc(self) -> frozenset[str]:
        """Tập mọi định danh tri thức có thể được quan hệ hoặc keyphrase trỏ tới."""
        return frozenset(
            [c.id for c in self.khai_niem]
            + [r.id for r in self.quy_tac]
            + [v.id for v in self.vi_pham]
        )

    def tai_thoi_diem(self, moc: date | None = None) -> CoSoTriThuc:
        """Trả về cơ sở tri thức chỉ gồm điều khoản CÓ HIỆU LỰC tại mốc thời gian.

        Điều khoản chưa có khoảng hiệu lực (chưa chạy suy diễn) được giữ lại để
        không âm thầm làm rỗng cơ sở tri thức.
        """
        moc = moc or date.today()

        def con_hieu_luc(x: QuyTac | ViPham) -> bool:
            return x.hieu_luc is None or x.hieu_luc.hieu_luc_tai(moc)

        return replace(
            self,
            quy_tac=tuple(r for r in self.quy_tac if con_hieu_luc(r)),
            vi_pham=tuple(v for v in self.vi_pham if con_hieu_luc(v)),
        )

    def thong_ke(self) -> dict[str, int]:
        return {
            "khai_niem": len(self.khai_niem),
            "quan_he": len(self.quan_he),
            "quy_tac": len(self.quy_tac),
            "vi_pham": len(self.vi_pham),
            "cum_tu_khoa": len(self.cum_tu_khoa),
            "van_ban": len(self.van_ban),
            "sua_doi": len(self.sua_doi),
        }


def _doc_json(duong_dan: Path) -> Any:
    if not duong_dan.is_file():
        raise LoiNapTriThuc(f"Không tìm thấy tệp tri thức: {duong_dan}")
    try:
        with duong_dan.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise LoiNapTriThuc(f"{duong_dan.name} không phải JSON hợp lệ: {e}") from e


def _nap_danh_sach[M: BaseModel](duong_dan: Path, kieu: type[M]) -> tuple[M, ...]:
    """Nạp một tệp JSON dạng danh sách thành tuple các mô hình đã kiểm kiểu.

    Lỗi kiểm kiểu được gói lại kèm tên tệp và chỉ số bản ghi để chẩn đoán nhanh,
    thay vì ném ra một vết ngăn xếp Pydantic thô.
    """
    du_lieu = _doc_json(duong_dan)
    if not isinstance(du_lieu, list):
        raise LoiNapTriThuc(f"{duong_dan.name} phải là danh sách, nhận {type(du_lieu).__name__}")
    ket_qua: list[M] = []
    for i, ban_ghi in enumerate(du_lieu):
        try:
            ket_qua.append(kieu.model_validate(ban_ghi))
        except ValidationError as e:
            dinh_danh = ban_ghi.get("id") or ban_ghi.get("cum_tu") or f"#{i}" \
                if isinstance(ban_ghi, dict) else f"#{i}"
            raise LoiNapTriThuc(
                f"{duong_dan.name} bản ghi {dinh_danh} không hợp lệ:\n{e}") from e
    return tuple(ket_qua)


def _nap_phan_loai(duong_dan: Path) -> PhanLoai:
    d = _doc_json(duong_dan)
    if not isinstance(d, dict):
        raise LoiNapTriThuc(f"{duong_dan.name} phải là đối tượng JSON")
    thieu = {"linh_vuc", "ten_nhom", "ten_phuong_tien", "ten_chu_the", "dong_nghia"} - set(d)
    if thieu:
        raise LoiNapTriThuc(f"{duong_dan.name} thiếu khoá: {sorted(thieu)}")
    return PhanLoai(
        linh_vuc=d["linh_vuc"],
        ten_nhom=d["ten_nhom"],
        ten_phuong_tien=d["ten_phuong_tien"],
        ten_chu_the=d["ten_chu_the"],
        dong_nghia=d["dong_nghia"],
    )


def nap_co_so_tri_thuc(thu_muc: Path) -> CoSoTriThuc:
    """Nạp toàn bộ cơ sở tri thức từ một thư mục chứa các tệp JSON."""
    thu_muc = Path(thu_muc)
    if not thu_muc.is_dir():
        raise LoiNapTriThuc(f"Không tìm thấy thư mục cơ sở tri thức: {thu_muc}")
    return CoSoTriThuc(
        khai_niem=_nap_danh_sach(thu_muc / "concepts.json", KhaiNiem),
        quan_he=_nap_danh_sach(thu_muc / "relations.json", QuanHe),
        quy_tac=_nap_danh_sach(thu_muc / "rules.json", QuyTac),
        vi_pham=_nap_danh_sach(thu_muc / "violations.json", ViPham),
        cum_tu_khoa=_nap_danh_sach(thu_muc / "keyphrases.json", CumTuKhoa),
        van_ban=_nap_danh_sach(thu_muc / "documents.json", VanBan),
        sua_doi=_nap_danh_sach(thu_muc / "amendments.json", SuaDoi),
        phan_loai=_nap_phan_loai(thu_muc / "taxonomy.json"),
    )
