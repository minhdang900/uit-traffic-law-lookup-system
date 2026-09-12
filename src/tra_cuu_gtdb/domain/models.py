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

from tra_cuu_gtdb.domain.temporal import KhoangHieuLuc

ChuoiKhongRong = Annotated[str, Field(min_length=1)]

# Giấy phép lái xe có tổng 12 điểm (Điều 58 Luật 36/2024/QH15).
TONG_DIEM_GPLX = 12


class MoHinhGoc(BaseModel):
    """Lớp cơ sở: cấm trường lạ để phát hiện dữ liệu trôi schema ngay khi nạp."""

    model_config = {"extra": "forbid", "frozen": True}


class CanCu(MoHinhGoc):
    """Căn cứ pháp lý: điều - khoản - điểm của một văn bản.

    Không có căn cứ thì mẩu tri thức không truy nguyên được về văn bản gốc, nên
    ``van_ban`` là bắt buộc và không được rỗng.
    """

    van_ban: ChuoiKhongRong
    dieu: int | None = None
    # Một số nghị định đánh khoản bằng chữ, nên chấp nhận cả int lẫn str.
    khoan: int | str | None = None
    diem: str | None = None

    @field_validator("van_ban")
    @classmethod
    def _van_ban_khong_chi_gom_khoang_trang(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("van_ban không được rỗng hoặc chỉ gồm khoảng trắng")
        return v

    @field_validator("dieu")
    @classmethod
    def _dieu_duong(cls, v: int | None) -> int | None:
        if v is not None and v <= 0:
            raise ValueError("số điều phải là số nguyên dương")
        return v


class MucPhat(MoHinhGoc):
    """Khung tiền phạt. ``min``/``max`` có thể để trống khi điều khoản không phạt tiền."""

    min: int | None = None
    max: int | None = None
    don_vi: str = "VND"
    ghi_chu: str | None = None

    @field_validator("min", "max")
    @classmethod
    def _khong_am(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("mức phạt không được âm")
        return v

    @model_validator(mode="after")
    def _min_khong_vuot_max(self) -> MucPhat:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"mức phạt tối thiểu ({self.min}) vượt tối đa ({self.max})")
        return self

    @property
    def co_phat_tien(self) -> bool:
        """Có áp dụng phạt tiền hay không."""
        return bool(self.max)

    @property
    def co_che_tai_phi_tien(self) -> bool:
        """Chế tài không phải tiền (cảnh cáo, tịch thu phương tiện...).

        8/345 điều khoản của Nghị định 168/2024 không phạt tiền mà áp dụng cảnh
        cáo hoặc tịch thu phương tiện. Dữ liệu hiện ghi các chế tài này dưới dạng
        văn bản tự do trong ``ghi_chu`` thay vì trường có cấu trúc — hợp lệ về nội
        dung nhưng nên được cấu trúc hoá về sau (validator sẽ cảnh báo).
        """
        return bool(self.ghi_chu and self.ghi_chu.strip())


class KhaiNiem(MoHinhGoc):
    """Thành phần C — khái niệm trong miền tri thức."""

    id: ChuoiKhongRong
    ten: ChuoiKhongRong
    loai: str
    # Có thể để trống: không phải khái niệm nào cũng được luật ĐỊNH NGHĨA.
    # Ví dụ "nồng độ cồn" chỉ bị Điều 9 khoản 2 Luật 36/2024 NGHIÊM CẤM chứ không
    # định nghĩa. Với các khái niệm này, nội dung nằm ở ``thuoc_tinh``. Bịa ra một
    # định nghĩa không có trong luật là sai nghiêm trọng với hệ tra cứu pháp luật.
    dinh_nghia: str | None = None
    can_cu: CanCu
    can_cu_text: ChuoiKhongRong
    thuoc_tinh: dict[str, str] = Field(default_factory=dict)
    keyphrases: list[str] = Field(default_factory=list)
    #: Khái niệm cũng bị văn bản sửa đổi chạm tới, y như quy tắc và vi phạm.
    sua_doi_boi: str | None = None
    ghi_chu: str | None = None
    # Trường chỉ mục dựng sẵn lúc build; thuộc về tầng index nhưng lưu kèm dữ liệu.
    text_search: str = ""
    text_search_kd: str = ""

    @model_validator(mode="after")
    def _phai_mang_it_nhat_mot_noi_dung(self) -> KhaiNiem:
        """Cho phép thiếu định nghĩa, nhưng KHÔNG cho phép rỗng hoàn toàn.

        Nới lỏng ``dinh_nghia`` mở ra nguy cơ khái niệm trống trơn lọt vào cơ sở
        tri thức. Ràng buộc này chặn đúng nguy cơ đó: phải có định nghĩa HOẶC
        thuộc tính, nếu không thì khái niệm không mang thông tin gì.
        """
        if not (self.dinh_nghia and self.dinh_nghia.strip()) and not self.thuoc_tinh:
            raise ValueError(
                f"khái niệm {self.id!r} không có cả định nghĩa lẫn thuộc tính")
        return self


class QuanHe(MoHinhGoc):
    """Thành phần R — quan hệ hai ngôi giữa các thực thể tri thức."""

    ten: ChuoiKhongRong
    kieu: ChuoiKhongRong
    nguon: ChuoiKhongRong
    dich: ChuoiKhongRong
    mo_ta: str = ""

    @model_validator(mode="after")
    def _khong_tu_tro(self) -> QuanHe:
        if self.nguon == self.dich:
            raise ValueError(f"quan hệ {self.ten!r} tự trỏ về {self.nguon!r}")
        return self


class QuyTac(MoHinhGoc):
    """Thành phần Rules — quy tắc giao thông và luật dẫn."""

    id: ChuoiKhongRong
    ten: ChuoiKhongRong
    dieu_kien: list[str] = Field(default_factory=list)
    ket_luan: list[str] = Field(default_factory=list)
    nguyen_van: ChuoiKhongRong
    can_cu: CanCu
    can_cu_text: ChuoiKhongRong
    tinh_trang: str | None = None
    sua_doi_boi: str | None = None
    nguyen_van_truoc_sua_doi: str | None = None
    # Khoảng hiệu lực, suy ra tất định từ documents.json bởi
    # scripts/suy_dien_hieu_luc.py. Để trống nếu chưa chạy suy diễn.
    hieu_luc: KhoangHieuLuc | None = None

    nguon: str | None = None
    ghi_chu: str | None = None
    text_search: str = ""
    text_search_kd: str = ""


class ViPham(MoHinhGoc):
    """Thành phần F — hành vi vi phạm kèm chế tài."""

    id: ChuoiKhongRong
    hanh_vi: ChuoiKhongRong
    nhom: ChuoiKhongRong
    ten_nhom: str = ""
    linh_vuc: str = ""
    chu_the: str = ""
    phuong_tien: list[str] = Field(default_factory=list)
    phat_tien: MucPhat = Field(default_factory=MucPhat)
    tru_diem_gplx: int | None = None
    hinh_phat_bo_sung: list[str] = Field(default_factory=list)
    bien_phap_khac_phuc: list[str] = Field(default_factory=list)
    can_cu: CanCu
    can_cu_text: ChuoiKhongRong
    # Các trường sửa đổi để trống khi điều khoản chưa từng bị sửa.
    tinh_trang: str | None = None
    sua_doi_boi: str | None = None
    hanh_vi_truoc_sua_doi: str | None = None
    ghi_chu_sua_doi: str | None = None
    # Khoảng hiệu lực, suy ra tất định từ documents.json bởi
    # scripts/suy_dien_hieu_luc.py. Để trống nếu chưa chạy suy diễn.
    hieu_luc: KhoangHieuLuc | None = None

    keyphrases: list[str] = Field(default_factory=list)
    text_search: str = ""
    text_search_kd: str = ""

    @field_validator("tru_diem_gplx")
    @classmethod
    def _diem_trong_khoang_hop_le(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if not 0 <= v <= TONG_DIEM_GPLX:
            raise ValueError(
                f"số điểm bị trừ phải nằm trong [0, {TONG_DIEM_GPLX}], nhận {v}")
        return v

    @model_validator(mode="after")
    def _phai_co_it_nhat_mot_che_tai(self) -> ViPham:
        """Hành vi không kèm chế tài nào thì không phải hành vi vi phạm."""
        if not (self.phat_tien.co_phat_tien or self.phat_tien.co_che_tai_phi_tien
                or self.tru_diem_gplx or self.hinh_phat_bo_sung
                or self.bien_phap_khac_phuc):
            raise ValueError(f"hành vi {self.id!r} không có chế tài nào")
        return self


class CumTuKhoa(MoHinhGoc):
    """Thành phần Keyphrase — cụm từ khoá dẫn tới tri thức, kèm bản không dấu."""

    cum_tu: ChuoiKhongRong
    khong_dau: ChuoiKhongRong
    so_tu: int = Field(ge=1)
    loai: list[str] = Field(default_factory=list)
    khai_niem: list[str] = Field(default_factory=list)
    quy_tac: list[str] = Field(default_factory=list)
    hanh_vi: list[str] = Field(default_factory=list)
    nhom: list[str] = Field(default_factory=list)
    phuong_tien: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _so_tu_khop_cum_tu(self) -> CumTuKhoa:
        thuc_te = len(self.cum_tu.split())
        if self.so_tu != thuc_te:
            raise ValueError(
                f"so_tu={self.so_tu} không khớp số từ thực tế ({thuc_te}) của {self.cum_tu!r}")
        return self


class SuaDoi(MoHinhGoc):
    """Một khoản sửa đổi do văn bản sửa đổi ban hành."""

    id: ChuoiKhongRong
    loai: Literal["sua_doi", "bo_sung", "bai_bo"]
    # Một số khoản sửa đổi mang tính chung, không gắn với điều cụ thể.
    dieu_nd168: int | None = None
    khoan_nd168: int | str | None = None
    diem_nd168: str | None = None
    noi_dung_moi: str | None = None
    # Sửa đổi có thể chỉ đổi câu chữ, không đụng tới mức phạt hay điểm trừ.
    phat_tien: MucPhat | None = None
    tru_diem_gplx: int | None = None
    ghi_chu: str | None = None
    can_cu: CanCu


class VanBan(MoHinhGoc):
    """Văn bản quy phạm pháp luật, mang ngày hiệu lực."""

    id: ChuoiKhongRong
    ten: ChuoiKhongRong
    ten_vn: ChuoiKhongRong
    so_hieu: ChuoiKhongRong
    ngay_ban_hanh: date
    ngay_hieu_luc: date
    co_quan: str = ""
    vai_tro: str = ""
    hop_nhat: str | None = None
    sua_doi_boi: list[str] = Field(default_factory=list)
    #: Xuất xứ siêu dữ liệu — nêu rõ lấy từ văn bản nào, để kiểm chứng lại được.
    ghi_chu: str | None = None

    @model_validator(mode="after")
    def _hieu_luc_khong_truoc_ban_hanh(self) -> VanBan:
        if self.ngay_hieu_luc < self.ngay_ban_hanh:
            raise ValueError(
                f"{self.so_hieu}: ngày hiệu lực {self.ngay_hieu_luc} "
                f"trước ngày ban hành {self.ngay_ban_hanh}")
        return self
