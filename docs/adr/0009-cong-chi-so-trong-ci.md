# ADR-0009: Cổng chỉ số Top-1 trong CI

**Date**: 2026-09-12 *(ghi lại 2026-09-13)*
**Status**: accepted
**Deciders**: Nhóm 7

## Context

Bảy người cùng sửa một kho mã, và chất lượng truy hồi là thứ **dễ tụt âm thầm**:
đổi một trọng số, thêm một heuristic, refactor một hàm — test đơn vị vẫn xanh mà
Top-1 rơi vài phần trăm không ai biết.

## Decision

`eval/evaluate.py --gate-top1 0.7667` chạy trong CI và thoát mã 1 nếu Top-1 tụt
dưới đường cơ sở.

## Alternatives Considered

### Phương án 1: Chỉ đo thủ công khi nhớ
- **Pros**: không tốn thời gian CI
- **Cons**: không ai nhớ; phát hiện muộn thì khó truy nguyên commit nào gây ra
- **Why not**: đã có 14 PR trong dự án — không thể trông vào trí nhớ

### Phương án 2: Test đơn vị khoá từng câu hỏi
- **Pros**: chỉ rõ câu nào hỏng
- **Cons**: 120 test giòn, đổi thứ hạng hợp lệ cũng làm đỏ
- **Why not**: quá chặt; cái cần khoá là **chỉ số tổng hợp**, không phải từng câu

## Consequences

### Positive
- Refactor lớn (ADR-0005, ADR-0006) làm được **an toàn** — cổng chứng minh không đổi
- Đường cơ sở thành con số công khai, ai cũng thấy

### Negative
- CI chậm hơn (~30 giây cho bước đánh giá)
- Đường cơ sở phải cập nhật tay khi cải thiện thật

### Risks
- Ngưỡng đặt bằng đúng giá trị hiện tại (0,7667) nên **mọi** dao động đều đỏ.
  Chấp nhận: hệ thống tất định, không có yếu tố ngẫu nhiên.
