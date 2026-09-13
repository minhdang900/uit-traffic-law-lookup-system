# ADR-0002: Trọng số hàm điểm lai 0,55 / 0,30 / 0,15

**Date**: 2026-09-12 *(ghi lại 2026-09-13)*
**Status**: accepted
**Deciders**: Nhóm 7

## Context

Xếp hạng tri thức cần kết hợp nhiều tín hiệu: keyphrase trỏ thẳng tới định danh,
tương đồng TF-IDF, và ngữ cảnh (phương tiện, chủ thể, nhóm). Phải quyết tín hiệu
nào nặng ký hơn. Trực giác ban đầu là cho TF-IDF trọng số cao nhất vì nó phủ
được nhiều câu hơn.

## Decision

`score = 0,55·keyphrase + 0,30·ngữ_nghĩa + 0,15·ngữ_cảnh`. Keyphrase nặng nhất.

## Alternatives Considered

### Phương án 1: TF-IDF nặng nhất
- **Pros**: đứng riêng, TF-IDF mạnh hơn keyphrase rõ rệt (Top-1 58,3% vs 35,8%)
- **Cons**: TF-IDF nhiễu — khớp một phần cũng cho điểm cao
- **Why not**: thí nghiệm loại bỏ thành phần cho thấy keyphrase thua về **độ phủ**
  chứ không thua về **độ chính xác**. Khi nó khớp thì gần như luôn đúng; lai lại
  thì TF-IDF lo phần phủ, keyphrase lo phần chuẩn → 66,7%.

### Phương án 2: Chỉ dùng một tín hiệu
- **Pros**: đơn giản, dễ giải thích
- **Cons**: TF-IDF riêng 58,3%, keyphrase riêng 35,8% — đều thua bản lai
- **Why not**: bản lai đạt 66,7%, cao hơn cả hai

## Consequences

### Positive
- Top-1 66,7% từ ba tín hiệu, so với 58,3% của tín hiệu mạnh nhất đứng riêng
- Trọng số có bằng chứng đo được, không phải chỉnh tay theo cảm tính

### Negative
- Ba tín hiệu thì khó gỡ lỗi hơn một
- Trọng số gắn với bộ dữ liệu 120 câu hiện tại; đổi bộ dữ liệu có thể phải đo lại

### Risks
- Quá khớp với 120 câu hỏi chuẩn. Giảm thiểu: cổng chỉ số trong CI (ADR-0009) bắt
  ngay nếu thay đổi làm tụt Top-1.

**Tái lập**: `python eval/ablation.py`
