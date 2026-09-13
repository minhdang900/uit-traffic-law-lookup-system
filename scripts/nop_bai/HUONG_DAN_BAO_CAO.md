# Hoàn thiện báo cáo Đề tài 4

## A. Định dạng bắt buộc

Rút từ 7 ảnh trong `De_bai/Huong_dan_viet_bao_cao_Word/`. Sai định dạng bị trừ
điểm trình bày dù nội dung tốt.

| Hạng mục | Giá trị |
|---|---|
| Font | Times New Roman, cỡ 14, bấm **Set As Default** |
| Lề | Top 2 · Bottom 2 · **Left 3** · Right 2 (cm), Gutter 0 |
| Hướng trang | Portrait, Apply to **Whole document** |
| Viền trang bìa | Box; Options: trên/dưới **1 pt**, trái/phải **4 pt**, từ **Text** |

Lề trái 3 cm là để chừa chỗ đóng gáy — đừng đặt 2 cm cho "cân".

**Cách nhanh nhất:** dùng sẵn `bao_cao/bao_cao_de_tai_4_khung.docx`. Khung đã áp
đúng cả 4 thiết lập (có test khoá lại), đã dựng trang bìa, 7 mục và 4 bảng số
liệu tự điền từ dữ liệu thật.

> **Cảnh báo:** nếu sinh lại khung bằng `python -m traffic_law.report.builder`
> thì tệp bị **ghi đè**. Hãy **Save As** sang tên khác (ví dụ
> `BaoCao_Nhom7_CS106.docx`) **trước khi** gõ chữ nào.

---

## B. Bảy mục — lấy nội dung ở đâu

| Mục | Trạng thái | Nguồn |
|---|---|---|
| 1. Giới thiệu | cần viết | Tự viết: bối cảnh, lý do chọn lĩnh vực |
| 2. Cơ sở tri thức | bảng đã có | `bao_cao/doi_chieu_de_tai_4.md` mục a) |
| 3. Thiết kế giải pháp | cần 2 sơ đồ | **Toàn bộ chữ đã có** trong `bao_cao/thiet_ke_giai_phap.md` |
| 4. Thực nghiệm | bảng đã điền | `so_lieu/*.json`; cần viết **nhận xét** |
| 5. Hạn chế | **đã đủ** | 4 gạch đầu dòng từ các xfail đã đo |
| 6. Kết luận | cần viết | Tự viết |
| 7. Tài liệu tham khảo | **đã đủ 5 mục** | — |

Hai sơ đồ cần vẽ (draw.io hoặc PowerPoint rồi chèn ảnh):

- **Kiến trúc**: Câu hỏi → `QueryAnalyzer` → `Q` → `InferenceEngine` (điều phối
  P1–P7) ↔ `IndexedKnowledgeBase` (chỉ mục + TF-IDF + `NumericReasoner`) →
  `render_answer`
- **Luồng B1–B6**: chuẩn hoá → rút keyphrase (cụm dài nhất) → phân lớp bài toán
  → dựng `Q` → suy diễn/truy hồi → sinh câu trả lời kèm căn cứ

---

## C. Nhận xét cần viết cho mục 4

Đừng để trống — đây là phần thể hiện nhóm *hiểu* số liệu chứ không chỉ chép.

- **P2 chỉ 55% Top-1** nhưng Top-5 đạt 85%: quy định có nhiều điều khoản gần
  nghĩa, đáp án đúng **có** trong danh sách nhưng chưa xếp đầu.
- **P7 chỉ 40%** nhưng Top-5 đạt 100%: lớp "kiến thức liên quan" vốn không có
  một đáp án duy nhất — chỉ số Top-1 không phản ánh đúng chất lượng ở lớp này.
- **9/120 câu sai hoàn toàn**: danh sách trong `so_lieu/ket_qua_danh_gia.json`,
  khoá `cau_sai`.
- **Precision 0,3375 không phải khiếm khuyết**: trả k=5 kết quả cho đáp án 1 mẩu
  → trần precision toán học là 0,20/câu. Con số 0,3375 đã **cao hơn** mức đó.

**Đoạn đáng viết nhất** — từ `so_lieu/ket_qua_ablation.json`:

keyphrase đứng riêng (35,8%) **yếu hơn** TF-IDF (58,3%), nhưng vẫn xứng trọng số
cao nhất 0,55 vì nó thua về *độ phủ*, không thua về *độ chính xác*. Lai lại,
TF-IDF lo phần phủ còn keyphrase lo phần chuẩn → 66,7%. Thêm suy diễn số học →
76,7%. Riêng 22 câu có giá trị số, Top-1 nhảy **40,9% → 95,5%** trong khi Top-5
gần như không đổi: so khớp từ khoá vẫn *tìm ra* đủ khung phạt, nó chỉ không biết
**chọn khung nào**.

---

## D. Ba chỗ dễ bị trừ điểm oan

**1. Đề ghi "01 văn bản", dự án dùng 4.** Đặt đoạn giải trình sớm trong mục 2:

> Luật 36/2024/QH15 quy định **hành vi**, còn Nghị định 168/2024/NĐ-CP mới quy
> định **mức phạt**. Chỉ dùng luật gốc thì không trả lời được câu hỏi phổ biến
> nhất là *"phạt bao nhiêu tiền"*. Hai văn bản sửa đổi (Luật 118/2025/QH15,
> NĐ 238/2026/NĐ-CP) được đưa vào để hệ thống trả lời đúng **theo mốc thời gian**.

**2. Mục "Hạn chế" là điểm cộng.** 6 xfail đều kèm số đo. Nêu cả kết quả **âm**:
phủ từ vựng KB là tín hiệu vô dụng (AUC 0,72) — đã thử và đã bác bỏ.

**3. Trích dẫn chuẩn.** Mọi mục tri thức đều dẫn Văn bản hợp nhất
**55/VBHN-VPQH ngày 23/3/2026** — chứng tỏ dữ liệu là bản **sau** sửa đổi.

---

## E. Phân công 7 thành viên

| # | Việc |
|---|---|
| 1 | Mục 1 + trang bìa + định dạng toàn bài + rà soát cuối |
| 2 | Mục 2 + ví dụ bản ghi + đoạn giải trình "01 văn bản" |
| 3 | Mục 3 — vẽ sơ đồ kiến trúc và sơ đồ luồng B1–B6 |
| 4 | Mục 3 — phần chữ: hàm điểm lai, trọng số, ablation |
| 5 | Mục 4 — bảng chỉ số + nhận xét từng lớp bài toán |
| 6 | Mục 4 — phân tích 9 câu sai + bảng 12 ca nghiệm thu |
| 7 | Mục 5, 6 + chuẩn bị demo (xem `KICH_BAN_DEMO.md`) |

---

## F. Checklist trước khi nộp

- [ ] Times New Roman 14 toàn bài, đã Set As Default
- [ ] Lề 2–2–3–2 cm, Portrait, Whole document
- [ ] Trang bìa có viền Box (1 pt trên/dưới, 4 pt trái/phải, từ Text)
- [ ] Trang bìa đủ: trường, khoa, CS106, tên đề tài, lĩnh vực, GVHD
      **PGS.TS. Nguyễn Đình Hiển**, lớp **CS106.F31.CN2**, **Nhóm 7**,
      bảng 7 thành viên (họ tên + MSSV), địa điểm và thời gian
- [ ] Mục lục tự động, cập nhật lại trước khi in
- [ ] **Không còn chuỗi `[Cần viết thêm]`** — tìm bằng Ctrl+F
- [ ] Mọi bảng và hình có số thứ tự + chú thích (Bảng 1., Hình 1.)
- [ ] Thập phân dùng **dấu phẩy** (0,8384), tiền dùng **dấu chấm** (4.000.000 đồng)
- [ ] Đã có đoạn giải trình "01 văn bản"
- [ ] Đã chạy lại `pytest -q` và `python eval/evaluate.py` để số liệu khớp thực tế
- [ ] Xuất PDF kiểm tra lại lề và font
