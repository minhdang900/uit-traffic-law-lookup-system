# ADR-0010: Không sinh ngôn ngữ tự nhiên

**Date**: 2026-09-12 *(ghi lại 2026-09-13)*
**Status**: accepted
**Deciders**: Nhóm 7

## Context

Xu hướng hiện nay là bọc cơ sở tri thức bằng một mô hình sinh để trả lời trôi
chảy. Với tra cứu pháp luật, điều đó nghĩa là **diễn giải lại lời của luật** —
và người đọc không phân biệt được đâu là nguyên văn điều khoản, đâu là câu do máy
viết ra.

## Decision

Câu trả lời **ghép từ nguyên văn điều khoản**, luôn kèm căn cứ điều–khoản–điểm.
Không có tầng sinh ngôn ngữ nào.

## Alternatives Considered

### Phương án 1: Thêm mô hình sinh tóm tắt câu trả lời
- **Pros**: câu trả lời trôi chảy, thân thiện hơn
- **Cons**: có thể bịa; người đọc không biết chỗ nào là luật thật
- **Why not**: sai một con số tiền phạt là gây thiệt hại thật cho người đọc.
  Nguyên văn có thể khô nhưng **kiểm chứng được**.

### Phương án 2: Sinh nhưng kèm trích dẫn
- **Pros**: vừa trôi chảy vừa truy nguyên được
- **Cons**: vẫn không ngăn được việc diễn giải lệch trong phần văn xuôi
- **Why not**: ngoài phạm vi môn học; và lợi ích không bù được rủi ro

## Consequences

### Positive
- Mọi chữ hiển thị đều truy nguyên được về một điều khoản cụ thể
- Không cần GPU, không phụ thuộc dịch vụ ngoài, chạy 6,2 ms

### Negative
- Câu trả lời đọc khô, đúng giọng văn bản pháp quy
- Không trả lời được câu hỏi cần suy luận tổng hợp nhiều điều khoản

### Risks
- Bị coi là "không dùng AI hiện đại". Giảm thiểu: nêu rõ đây là **lựa chọn có
  chủ đích** của một hệ tra cứu pháp luật, kèm miễn trừ trách nhiệm trên mọi màn
  hình có kết quả.
