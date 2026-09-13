# ADR-0006: Mã nguồn tiếng Anh, dữ liệu tiếng Việt, bắc cầu bằng alias

**Date**: 2026-09-13
**Status**: accepted
**Deciders**: Nhóm 7

## Context

Toàn bộ định danh Python ban đầu bằng tiếng Việt (`nap_co_so_tri_thuc`,
`ViPham`, `hanh_vi`). Cần chuyển sang tiếng Anh cho hợp quy ước. Nhưng
`data/kb/*.json` (1,7 MB) dùng khoá tiếng Việt — đó là **dữ liệu pháp lý**, không
phải mã nguồn.

## Decision

Định danh Python bằng tiếng Anh; khoá JSON giữ tiếng Việt; bắc cầu bằng
`alias_generator` của Pydantic (`domain/field_alias.py`). Chú thích và docstring
giữ nguyên tiếng Việt.

## Alternatives Considered

### Phương án 1: Đổi cả khoá JSON sang tiếng Anh
- **Pros**: nhất quán tuyệt đối
- **Cons**: viết lại 1,7 MB dữ liệu pháp lý, phải chứng minh chỉ số không đổi
- **Why not**: rủi ro cao, lợi ích thấp — dữ liệu pháp lý tiếng Việt có khoá
  tiếng Việt là hợp lý

### Phương án 2: Giữ toàn bộ tiếng Việt
- **Pros**: không phải làm gì
- **Cons**: lệch quy ước
- **Why not**: người dùng yêu cầu tường minh

## Consequences

### Positive
- Việc dịch **làm lộ một nhập nhằng** của tiếng Việt: `hanh_vi` vừa là *danh
  sách vi phạm* trong kết quả, vừa là *trường văn bản* của từng vi phạm; `diem`
  vừa là *điểm số* vừa là *điểm a/b/c* trong căn cứ. Tiếng Anh buộc phải tách:
  `result["violations"]` vs `Violation.behavior`, `"score"` vs `Citation.point`.
  **Mã rõ nghĩa hơn sau khi đổi** — lợi ích ngoài dự tính.

### Negative
- Thêm một lớp gián tiếp (`alias_generator`) mà người đọc mới phải hiểu
- Một tên trường tiếng Anh không thể trỏ tới hai khoá JSON khác nhau — đã va phải
  với `loai`/`kieu`, phải tách thành `kind` và `relation_kind`

### Risks
- Đổi tên bằng regex thô sẽ phá văn xuôi tiếng Việt trong chú thích. Giảm thiểu:
  đổi qua `tokenize`, chỉ chạm token NAME và chuỗi khớp **chính xác**.
