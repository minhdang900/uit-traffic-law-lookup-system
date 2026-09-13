"""Cầu nối giữa tên trường tiếng Anh trong mã và khoá tiếng Việt trong dữ liệu.

Tách riêng khỏi ``models.py`` để ``temporal.py`` cũng dùng được mà không tạo
vòng nhập lẫn nhau.
"""
from __future__ import annotations

#: Cầu nối giữa TÊN TRƯỜNG tiếng Anh trong mã và KHOÁ tiếng Việt trong
#: ``data/kb/*.json``. Dữ liệu tri thức giữ nguyên tiếng Việt vì đó là dữ liệu
#: pháp lý, không phải mã nguồn; chỉ tầng mã đổi sang tiếng Anh.
BI_DANH_TRUONG: dict[str, str] = {
    "amended_by": "sua_doi_boi",
    "amendment_note": "ghi_chu_sua_doi",
    "article": "dieu",
    "attributes": "thuoc_tinh",
    "authority": "co_quan",
    "behavior": "hanh_vi",
    "behavior_before_amendment": "hanh_vi_truoc_sua_doi",
    "citation": "can_cu",
    "citation_text": "can_cu_text",
    "clause": "khoan",
    "concepts": "khai_niem",
    "conclusions": "ket_luan",
    "conditions": "dieu_kien",
    "consolidated_in": "hop_nhat",
    "decree_article": "dieu_nd168",
    "decree_clause": "khoan_nd168",
    "decree_point": "diem_nd168",
    "definition": "dinh_nghia",
    "description": "mo_ta",
    "documents": "van_ban",
    "effective_from": "ngay_hieu_luc",
    "end": "den",
    "extra_penalties": "hinh_phat_bo_sung",
    "field": "linh_vuc",
    "fine": "phat_tien",
    "group": "nhom",
    "group_name": "ten_nhom",
    "issued_on": "ngay_ban_hanh",
    "kind": "loai",
    "relation_kind": "kieu",
    "concept_ids": "khai_niem",
    "rule_ids": "quy_tac",
    "violation_ids": "hanh_vi",
    "licence_points": "tru_diem_gplx",
    "name": "ten",
    "name_vn": "ten_vn",
    "new_text": "noi_dung_moi",
    "note": "ghi_chu",
    "number": "so_hieu",
    "phrase": "cum_tu",
    "point": "diem",
    "remedies": "bien_phap_khac_phuc",
    "role": "vai_tro",
    "rules": "quy_tac",
    "source": "nguon",
    "start": "tu",
    "status": "tinh_trang",
    "subject": "chu_the",
    "subject_names": "ten_chu_the",
    "synonyms": "dong_nghia",
    "target": "dich",
    "text": "nguyen_van",
    "text_before_amendment": "nguyen_van_truoc_sua_doi",
    "unaccented": "khong_dau",
    "unit": "don_vi",
    "validity": "hieu_luc",
    "vehicle_names": "ten_phuong_tien",
    "vehicles": "phuong_tien",
    "word_count": "so_tu"
}


def khoa_json(ten_truong: str) -> str:
    """Tên trường tiếng Anh -> khoá tương ứng trong tệp JSON tri thức."""
    return BI_DANH_TRUONG.get(ten_truong, ten_truong)
