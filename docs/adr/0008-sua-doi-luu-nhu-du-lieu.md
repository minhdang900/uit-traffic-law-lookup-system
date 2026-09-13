# ADR-0008: Sửa đổi lưu như dữ liệu, không hợp nhất lúc dựng KB

**Date**: 2026-09-12 *(ghi lại 2026-09-13)*
**Status**: accepted
**Deciders**: Nhóm 7

## Context

Luật 36/2024 bị Luật 118/2025 sửa (hiệu lực 01/7/2026); Nghị định 168/2024 bị
Nghị định 238/2026 sửa (15/8/2026). Một hệ tra cứu pháp luật trả về mức phạt đã
hết hiệu lực còn nguy hiểm hơn hệ trả lời "không tìm thấy".

## Decision

Mỗi điều khoản mang một **khoảng hiệu lực** `[tu, den]`. Sửa đổi lưu như **dữ
liệu**, không ghi đè bản gốc. Mọi truy vấn giải theo một **mốc thời gian** (mặc
định hôm nay).

## Alternatives Considered

### Phương án 1: Hợp nhất sẵn lúc dựng cơ sở tri thức
- **Pros**: đơn giản, truy vấn nhanh hơn
- **Cons**: mất khả năng trả lời "mức phạt tại ngày X là bao nhiêu"
- **Why not**: người bị phạt tháng trước cần biết mức phạt **tại thời điểm đó**,
  không phải mức hiện hành

### Phương án 2: Chỉ lưu bản hiện hành
- **Pros**: gọn nhất
- **Cons**: như trên, cộng thêm không kiểm chứng được đã cập nhật hay chưa
- **Why not**: validator cần phát hiện văn bản sửa đổi bị thiếu

## Consequences

### Positive
- Trả lời được theo mốc thời gian — điểm khác biệt của hệ thống
- R15 (chở trẻ em) tự động hiệu lực từ 01/7/2026, không phải sửa tay

### Negative
- Mô hình dữ liệu phức tạp hơn: thêm `EffectivePeriod`, `Amendment`, `as_of()`
- Cần script suy diễn hiệu lực, và script đó phải **bất biến** (chạy lại không đổi)

### Risks
- Suy diễn hiệu lực sai thì sai âm thầm. Giảm thiểu: CI chạy
  `scripts/suy_dien_hieu_luc.py --kiem-tra` mỗi lần.
