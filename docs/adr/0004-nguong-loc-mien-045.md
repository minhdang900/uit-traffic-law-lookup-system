# ADR-0004: Ngưỡng lọc miền 0,45 thay vì 0,52

**Date**: 2026-09-12 *(ghi lại 2026-09-13)*
**Status**: accepted
**Deciders**: Nhóm 7

## Context

Với tầng dense bật, ngưỡng quyết định truy vấn nào bị từ chối. Đo trên 120 câu hợp
lệ và 40 truy vấn ngoài miền: trần điểm dense của truy vấn rác là **0,516**, còn
sàn của câu hợp lệ không có keyphrase là **0,464**. Hai phân bố **chồng lấn** —
không có ngưỡng nào vừa loại hết rác vừa không làm oan câu hợp lệ.

## Decision

Ngưỡng 0,45 — giá trị **lớn nhất** còn giữ được hợp đồng "không từ chối oan câu
hợp lệ nào". Loại được 92,5% truy vấn rác.

## Alternatives Considered

### Phương án 1: Ngưỡng 0,52
- **Pros**: loại **100%** truy vấn rác
- **Cons**: từ chối oan 3/120 câu hợp lệ
- **Why not**: từ chối oan người hỏi thật tệ hơn nhiều so với lỡ trả lời một câu
  vớ vẩn. Một người tra mức phạt mà bị bảo "không tìm thấy" sẽ bỏ đi; một người
  hỏi về nấu ăn mà nhận được luật giao thông chỉ thấy buồn cười.

### Phương án 2: Không lọc gì cả
- **Pros**: chắc chắn không oan ai
- **Cons**: mọi truy vấn rác đều được trả lời
- **Why not**: đã có sẵn tín hiệu tách được 92,5%, bỏ đi là lãng phí

## Consequences

### Positive
- Hợp đồng "0 câu oan" được giữ, có test khoá lại
- Vẫn loại được phần lớn truy vấn rác

### Negative
- Biên rất mỏng: rút ngắn câu rác ("cách nấu phở bò" thay vì "cách nấu phở bò
  ngon tại nhà") thì điểm lên 0,452 và **lọt** qua ngưỡng 0,45

### Risks
- Ngưỡng gắn chặt với 40 truy vấn rác hiện có. Giảm thiểu: ghi rõ phần chồng lấn
  bằng `xfail(strict=True)` kèm số đo, để nếu ngày nào nó bất ngờ đạt thì CI báo.
