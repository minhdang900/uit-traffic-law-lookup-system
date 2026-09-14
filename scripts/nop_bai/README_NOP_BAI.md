# Hệ thống tra cứu kiến thức pháp luật giao thông đường bộ

**CS106 — Trí tuệ nhân tạo · Đề tài 4 · Lớp CS106.F31.CN2 · Nhóm 7**
GVHD: PGS.TS. Nguyễn Đình Hiển

---

## Nộp những gì

| Tệp | Nội dung |
|---|---|
| `bao_cao/BaoCao_Nhom7_CS106.pdf` | **Báo cáo chính thức** — 46 trang, 6 mục, 2 phụ lục, 19 bảng, 9 hình |
| `bao_cao/bao-cao-latex/` | Mã nguồn LaTeX của báo cáo (`latexmk -xelatex main.tex`) |
| `slide/Slide_Nhom7_CS106.pptx` | **Slide trình chiếu** 21 trang cho buổi báo cáo (kèm bản PDF) |
| `slide/index.html` | Bản slide chạy trên trình duyệt, dùng đúng token của giao diện |
| `bao_cao/thiet_ke_giai_phap.md` | Tài liệu thiết kế — nguồn chữ cho mục 3 |
| `bao_cao/kien_truc.md` | Kiến trúc thực tế đang chạy, kèm đánh giá theo Clean Architecture |
| `bao_cao/doi_chieu_de_tai_4.md` | Soát từng dòng yêu cầu đề bài với bằng chứng đo được |
| `bao_cao/bao_cao_du_lieu.md` | Báo cáo về bộ dữ liệu |
| `bao_cao/adr/` | Các quyết định kiến trúc và lý do chọn |
| `ma_nguon/` | Mã nguồn đầy đủ (bản sạch theo git) |
| `docker/` | Ảnh Docker + script khởi động demo |
| `so_lieu/` | Số liệu đo được — nguồn của mọi con số trong báo cáo |
| `KICH_BAN_DEMO.md` | Kịch bản trình bày 5 bước, kèm phương án dự phòng |
| `HUONG_DAN_BAO_CAO.md` | Định dạng bắt buộc, phân công, checklist trước khi nộp |

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

### Các màn hình

Thu hẹp cửa sổ dưới 720px để xem bản mobile (thanh tab đáy) — cùng các đường dẫn.

| Đường dẫn | Nội dung |
|---|---|
| `/tra-cuu` | Tra cứu — gõ câu hỏi tiếng Việt tự nhiên (gồm trạng thái không tìm thấy) |
| `/dieu-khoan/{id}` | Chi tiết điều khoản |
| `/hieu-luc` | Hiệu lực theo thời gian |
| `/chu-de` | Duyệt chủ đề |
| `/chi-so` | Chỉ số đánh giá |
| `/api/docs` | Tài liệu API (OpenAPI) |

---

## Kết quả chính

| Chỉ số | Giá trị |
|---|---|
| Độ chính xác phân lớp | 95,83% |
| Top-1 · Top-3 · Top-5 | 76,67% · 90,83% · 95,00% |
| MRR | 0,8384 |
| Precision · Recall · F1 (macro) | 0,3373 · 0,9306 · 0,4399 |
| Thời gian trả lời | 6,2 ms |
| Kiểm thử tự động | **286 đạt · 5 xfail có số đo · 4 bỏ qua (gói `dense` tuỳ chọn) · phủ 90%** |
| Ca nghiệm thu | 12/12 đạt |

Cơ sở tri thức `K = (C, R, Rules, F, Keyphrase)`: 73 khái niệm · 482 quan hệ ·
109 quy tắc · 345 hành vi vi phạm · 1.674 cụm từ khoá, cùng 4 bản ghi văn bản
nguồn và 63 bản ghi sửa đổi.

Nguồn: Luật 36/2024/QH15 và Nghị định 168/2024/NĐ-CP, đối chiếu Văn bản hợp
nhất **55/VBHN-VPQH ngày 23/3/2026** — tức bản **sau** sửa đổi.

> Kết quả tra cứu mang tính tham khảo, không thay thế ý kiến của cơ quan có
> thẩm quyền.

---

## Chạy từ mã nguồn (nếu muốn sửa)

Cần Python **3.12** trở lên.

```bash
cd ma_nguon
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev,web,bao-cao]'

pytest -q --cov                              # 286 passed · 5 xfailed · 4 skipped · phủ 90%
python eval/evaluate.py --gate-top1 0.7667   # cổng chỉ số
python eval/ablation.py                      # thí nghiệm loại bỏ thành phần
python eval/kich_ban.py --chi-tiet           # 12 ca nghiệm thu
python eval/phat_hien_mien.py                # bảng AUC tách miền
python eval/kiem_dinh.py                     # KTC 95%, McNemar, trần precision, bỏ dấu
uvicorn traffic_law.api.web:app --reload     # giao diện
```

4 test bỏ qua là các test cần gói tuỳ chọn `dense` (sentence-transformers, ~470 MB).
Cài thêm `pip install -e '.[dense]'` thì một trong số đó chuyển thành **xfail có số đo**,
tổng cộng 6 hạn chế đã đo.

### Sinh lại báo cáo và slide

Chạy trong `ma_nguon/`:

```bash
python scripts/ve_so_do.py             # sơ đồ kiến trúc + luồng B1–B6 → docs/so_do/
python scripts/thong_ke_du_lieu.py     # biểu đồ phân bố + phân tích lỗi → docs/so_do/
cd docs/bao-cao-latex && latexmk -xelatex main.tex   # báo cáo → main.pdf
node   scripts/lam_slide.js            # slide → docs/Slide_Nhom7_CS106.pptx
```

Sau khi vẽ lại hình, chép `docs/so_do/hinh*.png` sang `docs/bao-cao-latex/figures/`
rồi biên dịch lại. `scripts/dong_goi_nop_bai.sh` làm sẵn toàn bộ các bước này.
