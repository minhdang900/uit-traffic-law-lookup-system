# ADR-0001: Dùng 4 văn bản pháp luật thay vì 01 như đề bài ghi

**Date**: 2026-09-12 *(ghi lại 2026-09-13)*
**Status**: accepted
**Deciders**: Nhóm 7

## Context

Đề bài yêu cầu "chọn 1 trong các lĩnh vực và **01 văn bản pháp luật** tương ứng".
Nhưng trong pháp luật giao thông Việt Nam, **luật quy định hành vi còn nghị định
quy định mức phạt** — hai thứ nằm ở hai văn bản khác nhau. Câu hỏi phổ biến nhất
của người dùng là "phạt bao nhiêu tiền", mà chỉ có luật gốc thì không trả lời được.

## Decision

Cơ sở tri thức dùng 4 văn bản: Luật 36/2024/QH15 (hành vi), Nghị định
168/2024/NĐ-CP (chế tài), cùng hai văn bản sửa đổi Luật 118/2025/QH15 và Nghị
định 238/2026/NĐ-CP.

## Alternatives Considered

### Phương án 1: Chỉ Luật 36/2024/QH15
- **Pros**: đúng nguyên văn đề bài, phạm vi gọn
- **Cons**: không có mức phạt nào trong cơ sở tri thức
- **Why not**: mọi hành vi vi phạm có chế tài đều dẫn Nghị định 168 — bỏ nghị định
  thì lớp bài toán P3 (tra cứu chế tài, 40/120 câu hỏi) mất sạch

### Phương án 2: Luật + Nghị định, bỏ hai văn bản sửa đổi
- **Pros**: đơn giản hơn, không cần mô hình hiệu lực theo thời gian
- **Cons**: phục vụ điều khoản đã bị sửa mà không biết
- **Why not**: cả hai văn bản sửa đổi đều đã có hiệu lực trước ngày báo cáo
  (01/7/2026 và 15/8/2026)

## Consequences

### Positive
- Trả lời được câu hỏi "phạt bao nhiêu" — giá trị thực tế của hệ thống
- Trả lời đúng theo mốc thời gian

### Negative
- Lệch chữ nghĩa của đề bài, **bắt buộc phải giải trình trong báo cáo**
- Cơ sở tri thức phức tạp hơn: cần mô hình văn bản và khoảng hiệu lực

### Risks
- Bị đọc là làm sai đề. Giảm thiểu: đặt đoạn giải trình sớm trong mục 2 báo cáo.
