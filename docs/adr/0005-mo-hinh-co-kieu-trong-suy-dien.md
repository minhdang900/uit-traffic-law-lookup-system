# ADR-0005: Mô hình có kiểu trong tầng suy diễn, dict chỉ ở đường biên

**Date**: 2026-09-12 *(ghi lại 2026-09-13)*
**Status**: accepted
**Deciders**: Nhóm 7

## Context

Bộ máy suy diễn ban đầu là bản **port nguyên văn** từ `kb_engine.py`, dùng `dict`
xuyên suốt (`v["hanh_vi"]`). Giữ nguyên văn để tái lập chính xác Top-1 76,67%.
Nhưng dict không bắt được lỗi gõ sai tên trường, và mypy không kiểm được gì.

## Decision

Tri thức đi suốt tầng suy diễn dưới dạng **mô hình Pydantic có kiểu**. Chỉ đúng
một chỗ chuyển ngược về `dict` — hàm `_to_dict()`, gọi khi trả kết quả ra ngoài.

## Alternatives Considered

### Phương án 1: Giữ dict nguyên bản port
- **Pros**: không rủi ro, tái lập được với bản gốc
- **Cons**: không kiểm kiểu được; gõ sai tên trường chỉ lộ lúc chạy
- **Why not**: `pyproject.toml` đã hẹn từ trước rằng dọn dẹp sẽ làm khi có cổng
  chỉ số canh giữ. Cổng đó đã có.

### Phương án 2: Đổi cả hình dạng dict trả về
- **Pros**: nhất quán hoàn toàn
- **Cons**: phá hợp đồng công khai mà giao diện, bộ đánh giá và test đang đọc
- **Why not**: đó là thay đổi phá vỡ tương thích, khác hẳn dọn dẹp nội bộ

## Consequences

### Positive
- 5/6 nhóm cảnh báo ruff bị chặn trước đây **tự hết** sau khi đổi kiểu
- mypy strict phủ được thêm nhiều tệp

### Negative
- Diff lớn (~200 chỗ), khó soát
- Mất tính "nguyên văn" so với bản gốc — khó đối chiếu về sau

### Risks
- Đổi sai làm tụt chỉ số. Giảm thiểu: ảnh chụp vàng 13 truy vấn khoá cả **bộ
  trường** của dict trả về, sinh **trước** khi sửa. Kết quả: `eval/ket_qua_danh_gia.json`
  giống **từng byte** sau refactor.
