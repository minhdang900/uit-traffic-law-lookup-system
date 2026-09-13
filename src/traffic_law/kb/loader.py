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

from traffic_law.domain.models import (
    Amendment,
    Concept,
    Document,
    Keyphrase,
    Relation,
    Rule,
    Violation,
)


class KnowledgeLoadError(Exception):
    """Nạp cơ sở tri thức thất bại. Thông điệp chỉ rõ tệp và bản ghi gây lỗi."""


@dataclass(frozen=True)
class Taxonomy:
    """Bảng phân loại dùng chung: lĩnh vực, nhóm, phương tiện, chủ thể, đồng nghĩa."""

    field: dict[str, str]
    group_name: dict[str, str]
    vehicle_names: dict[str, str]
    subject_names: dict[str, str]
    synonyms: dict[str, list[str]]


@dataclass(frozen=True)
class KnowledgeBase:
    """Cơ sở tri thức K = (C, R, Rules, F, Keyphrase) cùng văn bản và sửa đổi."""

    concepts: tuple[Concept, ...]
    relations: tuple[Relation, ...]
    rules: tuple[Rule, ...]
    violations: tuple[Violation, ...]
    keyphrases: tuple[Keyphrase, ...]
    documents: tuple[Document, ...]
    amendments: tuple[Amendment, ...]
    taxonomy: Taxonomy

    @property
    def knowledge_ids(self) -> frozenset[str]:
        """Tập mọi định danh tri thức có thể được quan hệ hoặc keyphrase trỏ tới."""
        return frozenset(
            [c.id for c in self.concepts]
            + [r.id for r in self.rules]
            + [v.id for v in self.violations]
        )

    def as_of(self, moc: date | None = None) -> KnowledgeBase:
        """Trả về cơ sở tri thức chỉ gồm điều khoản CÓ HIỆU LỰC tại mốc thời gian.

        Điều khoản chưa có khoảng hiệu lực (chưa chạy suy diễn) được giữ lại để
        không âm thầm làm rỗng cơ sở tri thức.
        """
        moc = moc or date.today()

        def is_in_force(x: Rule | Violation) -> bool:
            return x.validity is None or x.validity.in_force_on(moc)

        return replace(
            self,
            rules=tuple(r for r in self.rules if is_in_force(r)),
            violations=tuple(v for v in self.violations if is_in_force(v)),
        )

    def stats(self) -> dict[str, int]:
        return {
            "concepts": len(self.concepts),
            "relations": len(self.relations),
            "rules": len(self.rules),
            "violations": len(self.violations),
            "keyphrases": len(self.keyphrases),
            "documents": len(self.documents),
            "amendments": len(self.amendments),
        }


def _read_json(duong_dan: Path) -> Any:
    if not duong_dan.is_file():
        raise KnowledgeLoadError(f"Không tìm thấy tệp tri thức: {duong_dan}")
    try:
        with duong_dan.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise KnowledgeLoadError(f"{duong_dan.name} không phải JSON hợp lệ: {e}") from e


def _load_list[M: BaseModel](duong_dan: Path, kind: type[M]) -> tuple[M, ...]:
    """Nạp một tệp JSON dạng danh sách thành tuple các mô hình đã kiểm kiểu.

    Lỗi kiểm kiểu được gói lại kèm tên tệp và chỉ số bản ghi để chẩn đoán nhanh,
    thay vì ném ra một vết ngăn xếp Pydantic thô.
    """
    data = _read_json(duong_dan)
    if not isinstance(data, list):
        raise KnowledgeLoadError(f"{duong_dan.name} phải là danh sách, nhận {type(data).__name__}")
    results: list[M] = []
    for i, ban_ghi in enumerate(data):
        try:
            results.append(kind.model_validate(ban_ghi))
        except ValidationError as e:
            dinh_danh = ban_ghi.get("id") or ban_ghi.get("phrase") or f"#{i}" \
                if isinstance(ban_ghi, dict) else f"#{i}"
            raise KnowledgeLoadError(
                f"{duong_dan.name} bản ghi {dinh_danh} không hợp lệ:\n{e}") from e
    return tuple(results)


def _load_taxonomy(duong_dan: Path) -> Taxonomy:
    d = _read_json(duong_dan)
    if not isinstance(d, dict):
        raise KnowledgeLoadError(f"{duong_dan.name} phải là đối tượng JSON")
    # taxonomy.json dung KHOA TIENG VIET (du lieu, khong phai ma nguon).
    missing = {"linh_vuc", "ten_nhom", "ten_phuong_tien",
               "ten_chu_the", "dong_nghia"} - set(d)
    if missing:
        raise KnowledgeLoadError(f"{duong_dan.name} thiếu khoá: {sorted(missing)}")
    return Taxonomy(
        field=d["linh_vuc"],
        group_name=d["ten_nhom"],
        vehicle_names=d["ten_phuong_tien"],
        subject_names=d["ten_chu_the"],
        synonyms=d["dong_nghia"],
    )


def load_knowledge_base(thu_muc: Path) -> KnowledgeBase:
    """Nạp toàn bộ cơ sở tri thức từ một thư mục chứa các tệp JSON."""
    thu_muc = Path(thu_muc)
    if not thu_muc.is_dir():
        raise KnowledgeLoadError(f"Không tìm thấy thư mục cơ sở tri thức: {thu_muc}")
    return KnowledgeBase(
        concepts=_load_list(thu_muc / "concepts.json", Concept),
        relations=_load_list(thu_muc / "relations.json", Relation),
        rules=_load_list(thu_muc / "rules.json", Rule),
        violations=_load_list(thu_muc / "violations.json", Violation),
        keyphrases=_load_list(thu_muc / "keyphrases.json", Keyphrase),
        documents=_load_list(thu_muc / "documents.json", Document),
        amendments=_load_list(thu_muc / "amendments.json", Amendment),
        taxonomy=_load_taxonomy(thu_muc / "taxonomy.json"),
    )
