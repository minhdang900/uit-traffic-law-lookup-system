# Hệ thống tra cứu kiến thức pháp luật giao thông đường bộ

**CS106 — Trí tuệ nhân tạo · Đề tài 4 · Lớp CS106.F31.CN2 · Nhóm 7**
GVHD: PGS.TS. Nguyễn Đình Hiển

---

## Chạy demo trong 1 phút — không cần cài Python

Chỉ cần **Docker Desktop** đang chạy.

| Hệ điều hành | Lệnh |
|---|---|
| macOS / Linux | `cd docker && ./chay_demo.sh` |
| Windows | nháy đúp `docker\chay_demo.bat` |

Script tự nạp ảnh, khởi động, đợi sẵn sàng rồi mở trình duyệt tại
**http://localhost:8000**.

Cổng 8000 bận thì đổi: `PORT=8080 ./chay_demo.sh`
Dừng lại: `./chay_demo.sh dung`

### Bảy màn hình

| Đường dẫn | Nội dung |
|---|---|
| `/` | Tra cứu — gõ câu hỏi tiếng Việt tự nhiên |
| `/khong-tim-thay` | Trạng thái không tìm thấy |
| `/dieu-khoan/{id}` | Chi tiết điều khoản |
| `/hieu-luc` | Hiệu lực theo thời gian |
| `/chu-de` | Duyệt chủ đề |
| `/chi-so` | Chỉ số đánh giá |
| `/api/docs` | Tài liệu API (OpenAPI) |

---

## Nội dung thư mục

```
ma_nguon/     mã nguồn đầy đủ (bản sạch theo git)
docker/       ảnh Docker + script khởi động
bao_cao/      khung báo cáo Word + 2 tài liệu nội dung
so_lieu/      số liệu đo được, dán thẳng vào báo cáo
```

- `HUONG_DAN_BAO_CAO.md` — cách hoàn thiện báo cáo Word, phân công, checklist
- `KICH_BAN_DEMO.md` — kịch bản trình bày buổi 10

---

## Chạy từ mã nguồn (nếu muốn sửa)

```bash
cd ma_nguon
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev,web,bao-cao]'

pytest -q                                    # 179 passed, 6 xfailed
python eval/evaluate.py --gate-top1 0.7667   # cổng chỉ số
python eval/kich_ban.py --chi-tiet           # 12 ca nghiệm thu
uvicorn traffic_law.api.web:app --reload     # giao diện
```

---

## Kết quả chính

| Chỉ số | Giá trị |
|---|---|
| Độ chính xác phân lớp | 95,83% |
| Top-1 · Top-5 | 76,67% · 95,00% |
| MRR | 0,8384 |
| Thời gian trả lời | 6,2 ms |
| Kiểm thử tự động | 179 đạt · 6 xfail có số đo · phủ 90% |
| Ca nghiệm thu | 12/12 đạt |

Cơ sở tri thức `K = (C, R, Rules, F, Keyphrase)`: 73 khái niệm · 482 quan hệ ·
109 quy tắc · 345 hành vi vi phạm · 1.674 cụm từ khoá.

Nguồn: Luật 36/2024/QH15 và Nghị định 168/2024/NĐ-CP, đối chiếu Văn bản hợp
nhất **55/VBHN-VPQH ngày 23/3/2026** — tức bản **sau** sửa đổi.

> Kết quả tra cứu mang tính tham khảo, không thay thế ý kiến của cơ quan có
> thẩm quyền.
