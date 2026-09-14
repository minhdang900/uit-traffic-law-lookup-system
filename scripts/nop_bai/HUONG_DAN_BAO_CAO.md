# Hoàn thiện và nộp báo cáo Đề tài 4

Báo cáo chính thức **duy nhất** là `bao_cao/BaoCao_Nhom7_CS106.pdf`, biên dịch từ
mã nguồn LaTeX trong `bao_cao/bao-cao-latex/`. Không còn bản Word — đừng tìm.
Tài liệu này ghi lại **định dạng bắt buộc**, **cách sửa và biên dịch lại** và
**checklist trước khi nộp**.

---

## A. Định dạng bắt buộc — đã cài sẵn trong `main.tex`

Rút từ 7 ảnh trong `De_bai/Huong_dan_viet_bao_cao_Word/`. Sai định dạng bị trừ
điểm trình bày dù nội dung tốt.

| Hạng mục | Giá trị | Ở đâu trong `main.tex` |
|---|---|---|
| Font | Times New Roman, cỡ 14 | `\documentclass[14pt]{extarticle}` · `\setmainfont{Times New Roman}` |
| Lề | Top 2 · Bottom 2 · **Left 3** · Right 2 (cm) | gói `geometry` |
| Hướng trang | Portrait, toàn bộ tài liệu | `a4paper` |
| Viền trang bìa | Box, cách chữ 1 pt trên/dưới, 4 pt trái/phải | khối `tikzpicture` trong `titlepage` — **chỉ** trang bìa |

Lề trái 3 cm là để chừa chỗ đóng gáy — đừng đặt 2 cm cho "cân".

---

## B. Sửa nội dung và biên dịch lại

Mỗi mục của báo cáo là một tệp trong `bao-cao-latex/chapters/`:

| Tệp | Nội dung |
|---|---|
| `00_front.tex` | Lời cảm ơn, tóm tắt, mục lục, danh sách hình/bảng, từ viết tắt |
| `01_tong_quan.tex` … `06_ung_dung_ket_luan.tex` | Mục 1 – 6 |
| `07_tai_lieu_tham_khao.tex` | 37 tài liệu tham khảo (trích bằng `\cite{khoa}`) |
| `08_phu_luc.tex` | Phụ lục A (phân công), B (lệnh kiểm chứng số liệu) |

Biên dịch (cần TeX Live có XeLaTeX):

```bash
cd bao_cao/bao-cao-latex
latexmk -xelatex main.tex     # tự chạy 2–3 lượt để mục lục và trích dẫn đúng
latexmk -c                    # dọn tệp trung gian
```

Mục lục, số hình, số bảng và số trích dẫn **tự cập nhật** — không có bước
"Update Field" nào phải làm tay.

> **Đừng sửa trực tiếp trong thư mục nộp bài.** Nguồn gốc nằm ở
> `ma_nguon/docs/bao-cao-latex/`; `scripts/dong_goi_nop_bai.sh` chép từ đó sang
> và biên dịch lại. Sửa ở thư mục nộp thì lần đóng gói sau sẽ mất.

Hình vẽ sinh lại bằng `scripts/ve_so_do.py` và `scripts/thong_ke_du_lieu.py`
(ra `docs/so_do/`); script đóng gói tự chép `hinh*.png` mới nhất vào `figures/`.
Ba ảnh `ui_*.png` là ảnh chụp giao diện thật, chụp lại bằng tay khi giao diện đổi.

---

## C. Ba chỗ dễ bị trừ điểm oan — đã xử lý sẵn trong báo cáo

**1. Đề ghi "01 văn bản", dự án dùng 4.** Mục 3.1 của báo cáo mở đầu bằng đoạn
giải trình:

> Luật 36/2024/QH15 quy định **hành vi**, còn Nghị định 168/2024/NĐ-CP mới quy
> định **mức phạt**. Chỉ dùng luật gốc thì không trả lời được câu hỏi phổ biến
> nhất là *"phạt bao nhiêu tiền"*. Hai văn bản sửa đổi (Luật 118/2025/QH15,
> NĐ 238/2026/NĐ-CP) được đưa vào để hệ thống trả lời đúng **theo mốc thời gian**.

**2. Mục "Hạn chế" là điểm cộng.** Mọi hạn chế ở mục 6.2 đều kèm số đo. Có nêu
cả kết quả **âm**: phủ từ vựng KB là tín hiệu vô dụng để tách miền (AUC 0,7243)
— đã thử và đã bác bỏ.

**3. Trích dẫn chuẩn.** Mọi mục tri thức đều dẫn Văn bản hợp nhất
**55/VBHN-VPQH ngày 23/3/2026** — chứng tỏ dữ liệu là bản **sau** sửa đổi.

---

## D. Hai con số dễ nhầm khi bị hỏi

Cả hai đều đúng, nhưng **đo hai thứ khác nhau** — đừng nói lẫn:

| Con số | Nghĩa |
|---|---|
| **77,5%** | Tỷ lệ truy vấn rác bị loại **chỉ bằng điểm dense**, ở ngưỡng ép buộc 0 câu hợp lệ bị từ chối oan (`so_lieu/ket_qua_phat_hien_mien.json`, khoá `loai_rac_khi_0_oan`) |
| **92,5%** | Tỷ lệ truy vấn rác bị loại bởi **bộ lọc kết hợp** keyphrase + dense (`tests/test_domain_detection.py::test_rejects_most_junk_queries`) |

Bảng 18 (mục 6.2.1) dùng 77,5% vì đang so sánh **từng tín hiệu** trong cùng một
bảng; đoạn văn ngay dưới bảng nêu 92,5% của bộ lọc kết hợp.

---

## E. Phân công 7 thành viên

Theo **Phụ lục A** của báo cáo:

| # | Thành viên | Việc |
|---|---|---|
| 1 | Nguyễn Quang Lâm | Mục 1 — tổng quan, phát biểu bài toán; trang bìa và định dạng toàn bài |
| 2 | Trần Trọng Tấn | Mục 2 — công trình liên quan, bộ dữ liệu đã có, khoảng trống |
| 3 | Lê Quang Thi | Mục 3 — nguồn văn bản, quy trình lấy và chuẩn hoá dữ liệu |
| 4 | Vỏ Cẩm Thu | Mục 3 — thống kê và phân tích bộ dữ liệu, ba biểu đồ phân bố |
| 5 | Nguyễn Trí Toàn | Mục 4 — kiến trúc, thuật giải B1–B6, hàm điểm lai, siêu tham số |
| 6 | Nguyễn Văn Thái | Mục 5 — bảng chỉ số, kiểm định thống kê, ablation |
| 7 | Đỗ Quốc Hoàng | Mục 5 — phân tích lỗi sâu; mục 6 — ứng dụng, hạn chế và demo (xem `KICH_BAN_DEMO.md`) |

---

## F. Checklist trước khi nộp

- [ ] Mở `bao_cao/BaoCao_Nhom7_CS106.pdf`: 46 trang, mục lục có số trang, không có `??`
- [ ] Trang bìa đủ: trường, khoa, CS106, tên đề tài, lĩnh vực, GVHD
      **PGS.TS. Nguyễn Đình Hiển**, lớp **CS106.F31.CN2**, **Nhóm 7**,
      bảng 7 thành viên (họ tên + MSSV), địa điểm và thời gian — viền Box chỉ ở trang bìa
- [ ] Mọi bảng và hình có số thứ tự + chú thích (Bảng 1., Hình 1.)
- [ ] Thập phân dùng **dấu phẩy** (0,8384), tiền dùng **dấu chấm** (4.000.000 đồng)
- [ ] Đã chạy lại `pytest -q --cov`, `python eval/evaluate.py` và `python eval/kiem_dinh.py`
      để số liệu khớp thực tế
- [ ] Mở thử `slide/Slide_Nhom7_CS106.pptx`, chạy Slide Show kiểm tra
- [ ] Chạy thử `docker/chay_demo.sh` **trước buổi báo cáo ít nhất 5 phút**
