# Architecture Decision Records

Quyết định kiến trúc của hệ thống tra cứu pháp luật giao thông đường bộ
(CS106 · Đề tài 4 · Nhóm 7).

Toàn bộ 10 ADR dưới đây được **ghi lại sau** (backfilled) vào 13/9/2026 — quyết
định đã có từ trước, mỗi tệp ghi rõ ngày quyết định gốc. Vì ghi sau nên phần
"Alternatives Considered" lấy từ số đo thật đã có, không phải dựng lại từ trí nhớ.

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-bon-van-ban-thay-vi-mot.md) | Dùng 4 văn bản pháp luật thay vì 01 như đề bài ghi | accepted | 2026-09-12 |
| [0002](0002-trong-so-ham-diem-lai.md) | Trọng số hàm điểm lai 0,55 / 0,30 / 0,15 | accepted | 2026-09-12 |
| [0003](0003-tang-dense-tuy-chon.md) | Tầng dense embedding là tuỳ chọn, mặc định tắt | accepted | 2026-09-12 |
| [0004](0004-nguong-loc-mien-045.md) | Ngưỡng lọc miền 0,45 thay vì 0,52 | accepted | 2026-09-12 |
| [0005](0005-mo-hinh-co-kieu-trong-suy-dien.md) | Mô hình có kiểu trong tầng suy diễn, dict chỉ ở đường biên | accepted | 2026-09-12 |
| [0006](0006-ma-tieng-anh-du-lieu-tieng-viet.md) | Mã nguồn tiếng Anh, dữ liệu tiếng Việt, bắc cầu bằng alias | accepted | 2026-09-13 |
| [0007](0007-fastapi-thay-streamlit.md) | FastAPI + Jinja thay cho Streamlit | accepted | 2026-09-13 |
| [0008](0008-sua-doi-luu-nhu-du-lieu.md) | Sửa đổi lưu như dữ liệu, không hợp nhất lúc dựng KB | accepted | 2026-09-12 |
| [0009](0009-cong-chi-so-trong-ci.md) | Cổng chỉ số Top-1 trong CI | accepted | 2026-09-12 |
| [0010](0010-khong-sinh-ngon-ngu-tu-nhien.md) | Không sinh ngôn ngữ tự nhiên | accepted | 2026-09-12 |

Sơ đồ kiến trúc và đánh giá theo Clean Architecture / DDD:
[`docs/kien_truc.md`](../kien_truc.md).
