# Hoàn thiện và nộp báo cáo Đề tài 4

Báo cáo đã được viết đủ bảy mục trong `bao_cao/BaoCao_Nhom7_CS106.docx`.
Tài liệu này ghi lại **định dạng bắt buộc**, **việc còn phải làm bằng tay** và
**checklist trước khi nộp**.

---

## A. Định dạng bắt buộc

Rút từ 7 ảnh trong `De_bai/Huong_dan_viet_bao_cao_Word/`. Sai định dạng bị trừ
điểm trình bày dù nội dung tốt.

| Hạng mục | Giá trị | Trạng thái |
|---|---|---|
| Font | Times New Roman, cỡ 14 | đã áp trong tệp .docx |
| Lề | Top 2 · Bottom 2 · **Left 3** · Right 2 (cm), Gutter 0 | đã áp |
| Hướng trang | Portrait, Apply to **Whole document** | đã áp |
| Viền trang bìa | Box; Options: trên/dưới **1 pt**, trái/phải **4 pt**, từ **Text** | đã áp, chỉ trang bìa |

Lề trái 3 cm là để chừa chỗ đóng gáy — đừng đặt 2 cm cho "cân".

Khi mở tệp trong Word, hãy bấm **Set As Default** cho font nếu định gõ thêm,
để phần gõ thêm không nhảy về Calibri.

---

## B. Ba việc phải làm bằng tay trong Word

Bốn thiết lập định dạng đã đúng, nội dung đã đủ. Còn ba việc Word phải tự làm:

1. **Cập nhật mục lục.** Nhấn chuột phải vào khối mục lục ở trang 2 →
   **Update Field** → *Update entire table*. Trước khi in thì cập nhật lại lần nữa.
2. **Kiểm tra ngắt trang.** Sau khi mục lục giãn ra, xem lại các hình và bảng
   có bị tách khỏi chú thích không.
3. **Xuất PDF** để kiểm tra lại lề, font và viền trang bìa.

Không còn chuỗi `[Cần viết thêm]` nào trong tệp — tìm bằng Ctrl+F để xác nhận.

---

## C. Sinh lại báo cáo khi số liệu thay đổi

Ba script nằm trong `ma_nguon/scripts/`, chạy tại `ma_nguon/`:

```bash
python scripts/ve_so_do.py             # vẽ lại 2 sơ đồ  → docs/so_do/
python scripts/tao_bao_cao_day_du.py   # dựng lại .docx  → docs/
node   scripts/lam_slide.js            # dựng lại .pptx  → docs/
```

> **Cảnh báo:** các lệnh trên **ghi đè** tệp cũ. Nếu đã gõ thêm gì vào bản Word
> thì **Save As** sang tên khác trước khi chạy lại.

`scripts/dong_goi_nop_bai.sh` chạy cả ba rồi chép kết quả sang thư mục nộp bài —
nên **đừng sửa trực tiếp trong thư mục nộp bài**, lần đóng gói sau sẽ ghi đè.
Sửa ở `ma_nguon/` rồi đóng gói lại.

`ma_nguon/src/traffic_law/report/builder.py` là bộ sinh **khung rỗng** đời cũ
(`bao_cao/bao_cao_de_tai_4_khung.docx`), giữ lại vì có test khoá định dạng.
Đừng nhầm hai bộ sinh này với nhau.

---

## D. Ba chỗ dễ bị trừ điểm oan — đã xử lý sẵn trong báo cáo

**1. Đề ghi "01 văn bản", dự án dùng 4.** Mục 2.1 của báo cáo mở đầu bằng đoạn
giải trình:

> Luật 36/2024/QH15 quy định **hành vi**, còn Nghị định 168/2024/NĐ-CP mới quy
> định **mức phạt**. Chỉ dùng luật gốc thì không trả lời được câu hỏi phổ biến
> nhất là *"phạt bao nhiêu tiền"*. Hai văn bản sửa đổi (Luật 118/2025/QH15,
> NĐ 238/2026/NĐ-CP) được đưa vào để hệ thống trả lời đúng **theo mốc thời gian**.

**2. Mục "Hạn chế" là điểm cộng.** Mọi hạn chế trong mục 5 đều kèm số đo và đều
được khoá bằng `xfail(strict=True)`. Có nêu cả kết quả **âm**: phủ từ vựng KB là
tín hiệu vô dụng để tách miền (AUC 0,7243) — đã thử và đã bác bỏ.

**3. Trích dẫn chuẩn.** Mọi mục tri thức đều dẫn Văn bản hợp nhất
**55/VBHN-VPQH ngày 23/3/2026** — chứng tỏ dữ liệu là bản **sau** sửa đổi.

---

## E. Hai con số dễ nhầm khi bị hỏi

Cả hai đều đúng, nhưng **đo hai thứ khác nhau** — đừng nói lẫn:

| Con số | Nghĩa |
|---|---|
| **77,5%** | Tỷ lệ truy vấn rác bị loại **chỉ bằng điểm dense**, ở ngưỡng ép buộc 0 câu hợp lệ bị từ chối oan (`so_lieu/ket_qua_phat_hien_mien.json`, khoá `loai_rac_khi_0_oan`) |
| **92,5%** | Tỷ lệ truy vấn rác bị loại bởi **bộ lọc kết hợp** keyphrase + dense (`tests/test_domain_detection.py::test_rejects_most_junk_queries`) |

Báo cáo dùng 77,5% ở mục 5.1 vì đang so sánh **từng tín hiệu** trong cùng một bảng.

---

## F. Phân công 7 thành viên

Xem **Phụ lục A** của báo cáo. Tóm tắt:

| # | Thành viên | Việc |
|---|---|---|
| 1 | Nguyễn Quang Lâm | Mục 1 + trang bìa + định dạng toàn bài + rà soát cuối |
| 2 | Trần Trọng Tấn | Mục 2 + ví dụ bản ghi + đoạn giải trình "01 văn bản" |
| 3 | Lê Quang Thi | Mục 3 — hai sơ đồ |
| 4 | Vỏ Cẩm Thu | Mục 3 — hàm điểm lai, trọng số, ablation |
| 5 | Nguyễn Trí Toàn | Mục 4 — bảng chỉ số + nhận xét từng lớp bài toán |
| 6 | Nguyễn Văn Thái | Mục 4 — phân tích 9 câu sai + bảng 12 ca nghiệm thu |
| 7 | Đỗ Quốc Hoàng | Mục 5, 6 + chuẩn bị demo (xem `KICH_BAN_DEMO.md`) |

---

## G. Checklist trước khi nộp

- [ ] Mở `bao_cao/BaoCao_Nhom7_CS106.docx`, **Update Field** cho mục lục
- [ ] Times New Roman 14 toàn bài (bấm Set As Default nếu gõ thêm)
- [ ] Lề 2–2–3–2 cm, Portrait, Whole document
- [ ] Trang bìa có viền Box (1 pt trên/dưới, 4 pt trái/phải, từ Text) — và **chỉ** trang bìa
- [ ] Trang bìa đủ: trường, khoa, CS106, tên đề tài, lĩnh vực, GVHD
      **PGS.TS. Nguyễn Đình Hiển**, lớp **CS106.F31.CN2**, **Nhóm 7**,
      bảng 7 thành viên (họ tên + MSSV), địa điểm và thời gian
- [ ] Ctrl+F `[Cần viết thêm]` — phải không còn kết quả nào
- [ ] Mọi bảng và hình có số thứ tự + chú thích (Bảng 1., Hình 1.)
- [ ] Thập phân dùng **dấu phẩy** (0,8384), tiền dùng **dấu chấm** (4.000.000 đồng)
- [ ] Đã chạy lại `pytest -q --cov` và `python eval/evaluate.py` để số liệu khớp thực tế
- [ ] Mở thử `slide/Slide_Nhom7_CS106.pptx`, chạy Slide Show kiểm tra 11 trang
- [ ] Chạy thử `docker/chay_demo.sh` **trước buổi báo cáo ít nhất 5 phút**
- [ ] Xuất PDF kiểm tra lại lề, font và viền
