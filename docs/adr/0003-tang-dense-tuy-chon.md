# ADR-0003: Tầng dense embedding là tuỳ chọn, mặc định tắt

**Date**: 2026-09-12 *(ghi lại 2026-09-13)*
**Status**: accepted
**Deciders**: Nhóm 7

## Context

Hệ thống không từ chối được truy vấn ngoài lĩnh vực: hỏi "cách nấu phở bò" vẫn
trả về hành vi vi phạm. Đo trên đặc trưng TF-IDF thô, 56/120 câu hợp lệ chấm điểm
thấp hơn hoặc bằng truy vấn rác — không ngưỡng nào tách được. Dense embedding
nâng AUC từ 0,8746 lên 0,9958 và loại được 92,5% truy vấn rác mà không từ chối oan
câu nào. Nhưng mô hình nặng ~470 MB.

## Decision

`retrieval/dense.py` là gói tuỳ chọn `.[dense]`. Đường đi mặc định của bộ máy suy
diễn **không** gọi tới nó; CI không cài; test của nó tự `skip` khi thiếu gói.

## Alternatives Considered

### Phương án 1: Bật mặc định
- **Pros**: hệ thống từ chối được 92,5% truy vấn rác ngay
- **Cons**: ảnh Docker +470 MB, CI phải tải mô hình mỗi lần chạy
- **Why not**: ảnh nộp bài đang 665 MB (nén 145 MB); thêm 470 MB làm bộ nộp khó
  chuyển. Lợi ích không tương xứng cho phạm vi môn học.

### Phương án 2: Bỏ hẳn, không làm dense
- **Pros**: kho mã gọn
- **Cons**: mất bằng chứng rằng tách miền **là khả thi**
- **Why not**: kết quả đo (AUC 0,9958) là đóng góp có giá trị cho báo cáo, kể cả
  khi không bật trong sản phẩm

## Consequences

### Positive
- Ảnh Docker và CI giữ nhẹ
- Vẫn có bằng chứng đo được để viết vào mục "Hướng phát triển"

### Negative
- Cấu hình mặc định **vẫn trả lời truy vấn ngoài lĩnh vực** — phải chủ động nêu
  khi demo
- Hai đường đi (có/không dense) nghĩa là hai hành vi khác nhau cần giải thích

### Risks
- Hội đồng hỏi "sao không bật". Giảm thiểu: nêu trước, kèm con số 470 MB.

**Tái lập**: `python eval/phat_hien_mien.py --dense --ghi`
