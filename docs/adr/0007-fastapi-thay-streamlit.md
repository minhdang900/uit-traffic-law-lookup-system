# ADR-0007: FastAPI + Jinja thay cho Streamlit

**Date**: 2026-09-13
**Status**: accepted
**Deciders**: Nhóm 7

## Context

Giao diện ban đầu là một trang Streamlit mỏng. Bản bàn giao thiết kế yêu cầu
nhiều màn hình với thanh bên cố định 252px, lưới hai cột và thẻ bo 28px —
Streamlit không cho kiểm soát bố cục ở mức đó. Bản bàn giao sau đó mở rộng lên
12 màn hình, responsive từ 402 px tới 2560 px.

## Decision

Bọc `LawLookup.ask()` bằng endpoint JSON của FastAPI, render giao diện bằng Jinja
template. Xoá `app.py` của Streamlit thay vì để hai giao diện song song.

## Alternatives Considered

### Phương án 1: Giữ Streamlit, chèn CSS tuỳ biến
- **Pros**: không phải viết tầng web mới, test hiện có giữ nguyên
- **Cons**: Streamlit sinh DOM riêng, CSS chèn vào rất dễ vỡ khi nâng phiên bản
- **Why not**: bản bàn giao nói thẳng rằng bố cục này Streamlit không dựng được

### Phương án 2: React + Vite
- **Pros**: toàn quyền về giao diện, hệ sinh thái lớn
- **Cons**: thêm toolchain Node vào dự án thuần Python, Docker phức tạp hơn
- **Why not**: Jinja đủ cho giao diện render phía máy chủ; giữ stack một ngôn ngữ

## Consequences

### Positive
- Dựng đúng bản thiết kế, có API JSON dùng lại được
- Mở rộng từ bản 7 màn hình lên bản 12 màn hình responsive mà **không phải đổi
  kiến trúc** — chỉ thêm route và template
- Ảnh Docker đơn giản, không cần bước build frontend

### Negative
- Mất tiện lợi của Streamlit (widget sẵn, tự rerun)
- Phải tự viết tầng trình bày và test cho nó

### Risks
- Lỗi giao diện không test nào bắt được. Đã gặp thật: 3/4 lỗi (ô chỉ số xếp
  ngang, biểu đồ rỗng, thanh vô hình) chỉ lộ khi **mở trình duyệt xem**.
  Giảm thiểu: bắt buộc xem bằng mắt trước khi merge thay đổi giao diện.
