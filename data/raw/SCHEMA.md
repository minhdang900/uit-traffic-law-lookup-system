# Schema cơ sở tri thức - Hệ thống tra cứu pháp luật giao thông đường bộ

## 1. concepts.json  (tập khái niệm C)
[
 {
  "id": "KN_<MA>",                       // chữ HOA không dấu, ví dụ KN_NONG_DO_CON
  "ten": "Nồng độ cồn",
  "loai": "khai_niem|phuong_tien|chu_the|hanh_vi|giay_to|che_tai|ha_tang",
  "dinh_nghia": "nguyên văn định nghĩa trong luật (nếu có)",
  "thuoc_tinh": {"ten_thuoc_tinh": "giá trị"},
  "keyphrases": ["cụm từ khoá 1", "cụm từ khoá 2"],
  "can_cu": {"van_ban": "Luật 36/2024/QH15", "dieu": 2, "khoan": 1, "diem": null}
 }
]

## 2. relations.json  (tập quan hệ R)
[
 {"ten": "la_loai_cua|thuoc_ve|bi_dieu_chinh_boi|co_che_tai|lien_quan",
  "nguon": "KN_XE_MAY", "dich": "KN_XE_CO_GIOI",
  "mo_ta": "...", "can_cu": {...}}
]

## 3. rules.json  (tập luật Rules)
[
 {"id": "R<nn>",
  "ten": "...",
  "dieu_kien": ["mệnh đề điều kiện 1", "..."],
  "ket_luan": ["mệnh đề kết luận"],
  "can_cu": {...}}
]

## 4. violations.json  (sự kiện: hành vi vi phạm + chế tài)
[
 {
  "id": "VP_<PHUONGTIEN>_<MA>_<n>",
  "hanh_vi": "NGUYÊN VĂN mô tả hành vi trong nghị định",
  "nhom": "nong_do_con|toc_do|den_tin_hieu|mu_bao_hiem|lan_duong|nguoc_chieu|dien_thoai|giay_to|dung_do|cho_qua_so_nguoi|khac|...",
  "chu_the": "nguoi_dieu_khien|chu_phuong_tien|nguoi_di_bo|hanh_khach|to_chuc",
  "phuong_tien": ["o_to","mo_to","xe_gan_may","xe_dap","xe_may_chuyen_dung","xe_tho_so","khong_ap_dung"],
  "phat_tien": {"min": 6000000, "max": 8000000, "don_vi": "VND", "ghi_chu": null},
  "hinh_phat_bo_sung": ["tước quyền sử dụng GPLX từ 22 tháng đến 24 tháng"],
  "tru_diem_gplx": 4,                    // 0 nếu không trừ điểm, null nếu không áp dụng
  "bien_phap_khac_phuc": [],
  "can_cu": {"van_ban": "Nghị định 168/2024/NĐ-CP", "dieu": 6, "khoan": 6, "diem": "a"},
  "tinh_trang": "hien_hanh|da_sua_doi|da_bai_bo",
  "sua_doi_boi": "Nghị định 238/2026/NĐ-CP Điều ... khoản ...",   // null nếu không
  "keyphrases": ["nồng độ cồn", "ô tô", "rượu bia", "0,25 mg/l khí thở"]
 }
]

QUY TẮC BẮT BUỘC:
- Trường "hanh_vi" phải là NGUYÊN VĂN của văn bản, không diễn giải lại.
- Không bịa số tiền phạt. Nếu văn bản ghi khoảng thì lấy đúng khoảng đó.
- "can_cu" phải đầy đủ điều/khoản/điểm.
- Tiền viết dạng số nguyên VND (6.000.000 -> 6000000).
