"""Mô hình dữ liệu thuần cho cơ sở tri thức pháp luật giao thông đường bộ.

Tầng này KHÔNG đọc tệp và KHÔNG phụ thuộc tầng nào khác. Nhiệm vụ duy nhất của
nó là làm cho dữ liệu sai không thể tồn tại trong bộ nhớ: mọi ràng buộc về tính
hợp lệ của một mẩu tri thức được phát biểu ngay tại đây, thay vì rải rác trong
các hàm xử lý.

Mô hình tri thức:  K = (C, R, Rules, F, Keyphrase)
    C         → KhaiNiem
    R         → QuanHe
    Rules     → QuyTac
    F         → ViPham
    Keyphrase → CumTuKhoa
"""
from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from traffic_law.domain.field_alias import khoa_json
from traffic_law.domain.temporal import EffectivePeriod

NonEmptyStr = Annotated[str, Field(min_length=1)]

# Giấy phép lái xe có tổng 12 điểm (Điều 58 Luật 36/2024/QH15).
TONG_DIEM_GPLX = 12


class BaseRecord(BaseModel):
    """Lớp cơ sở: cấm trường lạ để phát hiện dữ liệu trôi schema ngay khi nạp.

    ``alias_generator`` cho phép nạp JSON khoá tiếng Việt vào mô hình có tên
    trường tiếng Anh; ``populate_by_name`` cho phép dựng đối tượng trong mã
    bằng chính tên tiếng Anh.
    """

    model_config = {"extra": "forbid", "frozen": True,
                    "alias_generator": khoa_json, "populate_by_name": True}


class Citation(BaseRecord):
    """Căn cứ pháp lý: điều - khoản - điểm của một văn bản.

    Không có căn cứ thì mẩu tri thức không truy nguyên được về văn bản gốc, nên
    ``van_ban`` là bắt buộc và không được rỗng.
    """

    documents: NonEmptyStr
    article: int | None = None
    # Một số nghị định đánh khoản bằng chữ, nên chấp nhận cả int lẫn str.
    clause: int | str | None = None
    point: str | None = None

    @field_validator("documents")
    @classmethod
    def _van_ban_khong_chi_gom_khoang_trang(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("van_ban không được rỗng hoặc chỉ gồm khoảng trắng")
        return v

    @field_validator("article")
    @classmethod
    def _dieu_duong(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("số điều phải là số nguyên dương")
        return v


class Fine(BaseRecord):
    """Khung tiền phạt. ``min``/``max`` có thể để trống khi điều khoản không phạt tiền."""

    min: int | None = None
    max: int | None = None
    unit: str = "VND"
    note: str | None = None

    @field_validator("min", "max")
    @classmethod
    def _khong_am(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("mức phạt không được âm")
        return v

    @model_validator(mode="after")
    def _min_khong_vuot_max(self) -> Fine:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"mức phạt tối thiểu ({self.min}) vượt tối đa ({self.max})")
        return self

    @property
    def has_fine(self) -> bool:
        """Có áp dụng phạt tiền hay không."""
        return bool(self.max)

    @property
    def has_non_monetary_penalty(self) -> bool:
        """Chế tài không phải tiền (cảnh cáo, tịch thu phương tiện...).

        8/345 điều khoản của Nghị định 168/2024 không phạt tiền mà áp dụng cảnh
        cáo hoặc tịch thu phương tiện. Dữ liệu hiện ghi các chế tài này dưới dạng
        văn bản tự do trong ``ghi_chu`` thay vì trường có cấu trúc — hợp lệ về nội
        dung nhưng nên được cấu trúc hoá về sau (validator sẽ cảnh báo).
        """
        return bool(self.note and self.note.strip())


class Concept(BaseRecord):
    """Thành phần C — khái niệm trong miền tri thức."""

    id: NonEmptyStr
    name: NonEmptyStr
    kind: str
    # Có thể để trống: không phải khái niệm nào cũng được luật ĐỊNH NGHĨA.
    # Ví dụ "nồng độ cồn" chỉ bị Điều 9 khoản 2 Luật 36/2024 NGHIÊM CẤM chứ không
    # định nghĩa. Với các khái niệm này, nội dung nằm ở ``thuoc_tinh``. Bịa ra một
    # định nghĩa không có trong luật là sai nghiêm trọng với hệ tra cứu pháp luật.
    definition: str | None = None
    citation: Citation
    citation_text: NonEmptyStr
    attributes: dict[str, str] = Field(default_factory=dict)
    keyphrases: list[str] = Field(default_factory=list)
    #: Khái niệm cũng bị văn bản sửa đổi chạm tới, y như quy tắc và vi phạm.
    amended_by: str | None = None
    note: str | None = None
    # Trường chỉ mục dựng sẵn lúc build; thuộc về tầng index nhưng lưu kèm dữ liệu.
    text_search: str = ""
    text_search_kd: str = ""

    @model_validator(mode="after")
    def _phai_mang_it_nhat_mot_noi_dung(self) -> Concept:
        """Cho phép thiếu định nghĩa, nhưng KHÔNG cho phép rỗng hoàn toàn.

        Nới lỏng ``dinh_nghia`` mở ra nguy cơ khái niệm trống trơn lọt vào cơ sở
        tri thức. Ràng buộc này chặn đúng nguy cơ đó: phải có định nghĩa HOẶC
        thuộc tính, nếu không thì khái niệm không mang thông tin gì.
        """
        if not (self.definition and self.definition.strip()) and not self.attributes:
            raise ValueError(
                f"khái niệm {self.id!r} không có cả định nghĩa lẫn thuộc tính")
        return self


class Relation(BaseRecord):
    """Thành phần R — quan hệ hai ngôi giữa các thực thể tri thức."""

    name: NonEmptyStr
    # Ten khac 'kind' cua Concept vi hai truong nay anh xa toi hai khoa JSON
    # khac nhau ("kieu" va "loai"), ma alias_generator la ham DUNG CHUNG.
    relation_kind: NonEmptyStr
    source: NonEmptyStr
    target: NonEmptyStr
    description: str = ""

    @model_validator(mode="after")
    def _khong_tu_tro(self) -> Relation:
        if self.source == self.target:
            raise ValueError(f"quan hệ {self.name!r} tự trỏ về {self.source!r}")
        return self


class Rule(BaseRecord):
    """Thành phần Rules — quy tắc giao thông và luật dẫn."""

    id: NonEmptyStr
    name: NonEmptyStr
    conditions: list[str] = Field(default_factory=list)
    conclusions: list[str] = Field(default_factory=list)
    text: NonEmptyStr
    citation: Citation
    citation_text: NonEmptyStr
    status: str | None = None
    amended_by: str | None = None
    text_before_amendment: str | None = None
    # Khoảng hiệu lực, suy ra tất định từ documents.json bởi
    # scripts/suy_dien_hieu_luc.py. Để trống nếu chưa chạy suy diễn.
    validity: EffectivePeriod | None = None

    source: str | None = None
    note: str | None = None
    text_search: str = ""
    text_search_kd: str = ""


class Violation(BaseRecord):
    """Thành phần F — hành vi vi phạm kèm chế tài."""

    id: NonEmptyStr
    behavior: NonEmptyStr
    group: NonEmptyStr
    group_name: str = ""
    field: str = ""
    subject: str = ""
    vehicles: list[str] = Field(default_factory=list)
    fine: Fine = Field(default_factory=Fine)
    licence_points: int | None = None
    extra_penalties: list[str] = Field(default_factory=list)
    remedies: list[str] = Field(default_factory=list)
    citation: Citation
    citation_text: NonEmptyStr
    # Các trường sửa đổi để trống khi điều khoản chưa từng bị sửa.
    status: str | None = None
    amended_by: str | None = None
    behavior_before_amendment: str | None = None
    amendment_note: str | None = None
    # Khoảng hiệu lực, suy ra tất định từ documents.json bởi
    # scripts/suy_dien_hieu_luc.py. Để trống nếu chưa chạy suy diễn.
    validity: EffectivePeriod | None = None

    keyphrases: list[str] = Field(default_factory=list)
    text_search: str = ""
    text_search_kd: str = ""

    @field_validator("licence_points")
    @classmethod
    def _diem_trong_khoang_hop_le(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if not 0 <= v <= TONG_DIEM_GPLX:
            raise ValueError(
                f"số điểm bị trừ phải nằm trong [0, {TONG_DIEM_GPLX}], nhận {v}")
        return v

    @model_validator(mode="after")
    def _phai_co_it_nhat_mot_che_tai(self) -> Violation:
        """Hành vi không kèm chế tài nào thì không phải hành vi vi phạm."""
        if not (self.fine.has_fine or self.fine.has_non_monetary_penalty
                or self.licence_points or self.extra_penalties
                or self.remedies):
            raise ValueError(f"hành vi {self.id!r} không có chế tài nào")
        return self


class Keyphrase(BaseRecord):
    """Thành phần Keyphrase — cụm từ khoá dẫn tới tri thức, kèm bản không dấu."""

    phrase: NonEmptyStr
    unaccented: NonEmptyStr
    word_count: int = Field(ge=1)
    # Hau to _ids: day la DANH SACH DINH DANH tro toi tri thuc, khong phai ban
    # than tri thuc — va cung tranh trung ten voi cac bo suu tap cua KnowledgeBase.
    kind: list[str] = Field(default_factory=list)
    concept_ids: list[str] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    violation_ids: list[str] = Field(default_factory=list)
    group: list[str] = Field(default_factory=list)
    vehicles: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _so_tu_khop_cum_tu(self) -> Keyphrase:
        actual = len(self.phrase.split())
        if self.word_count != actual:
            raise ValueError(
                f"so_tu={self.word_count} không khớp số từ thực tế ({actual}) của {self.phrase!r}")
        return self


class Amendment(BaseRecord):
    """Một khoản sửa đổi do văn bản sửa đổi ban hành."""

    id: NonEmptyStr
    # Gia tri DU LIEU trong amendments.json — giu nguyen tieng Viet.
    kind: Literal["sua_doi", "bo_sung", "bai_bo"]
    # Một số khoản sửa đổi mang tính chung, không gắn với điều cụ thể.
    decree_article: int | None = None
    decree_clause: int | str | None = None
    decree_point: str | None = None
    new_text: str | None = None
    # Sửa đổi có thể chỉ đổi câu chữ, không đụng tới mức phạt hay điểm trừ.
    fine: Fine | None = None
    licence_points: int | None = None
    note: str | None = None
    citation: Citation


class Document(BaseRecord):
    """Văn bản quy phạm pháp luật, mang ngày hiệu lực."""

    id: NonEmptyStr
    name: NonEmptyStr
    name_vn: NonEmptyStr
    number: NonEmptyStr
    issued_on: date
    effective_from: date
    authority: str = ""
    role: str = ""
    consolidated_in: str | None = None
    amended_by: list[str] = Field(default_factory=list)
    #: Xuất xứ siêu dữ liệu — nêu rõ lấy từ văn bản nào, để kiểm chứng lại được.
    note: str | None = None

    @model_validator(mode="after")
    def _hieu_luc_khong_truoc_ban_hanh(self) -> Document:
        if self.effective_from < self.issued_on:
            raise ValueError(
                f"{self.number}: ngày hiệu lực {self.effective_from} "
                f"trước ngày ban hành {self.issued_on}")
        return self
