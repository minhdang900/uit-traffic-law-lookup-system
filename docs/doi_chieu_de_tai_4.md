# Đối chiếu Đề tài 4

Soát từng dòng yêu cầu trong đề bài với bằng chứng đo được trong kho mã.

- **Nguồn yêu cầu**: `2026, De tai mon TTNT 2 - He tu xa.pdf`, mục 4 (trích nguyên văn)
- **Lớp**: CS106.F31.CN2 · **Nhóm 7** · GVHD: PGS.TS. Nguyễn Đình Hiển
- **Hạn báo cáo**: Buổi 10

> **Kết luận**: 7/7 mục yêu cầu chuyên môn đã đạt. Sản phẩm nộp cũng đã đủ:
> báo cáo hoàn chỉnh biên dịch từ LaTeX (`docs/BaoCao_Nhom7_CS106.pdf`, nguồn `docs/bao-cao-latex/`), slide trình chiếu
> (`docs/Slide_Nhom7_CS106.pptx`) và demo chạy được bằng Docker.

---

## a) Yêu cầu

### “Chọn 1 trong các lĩnh vực và 01 văn bản pháp luật tương ứng để thực hiện.”

**Đạt — nhưng cần giải trình.** Lĩnh vực *Luật giao thông*, song dùng **4 văn bản** chứ không phải 01:

| Văn bản | Vai trò |
|---|---|
| Luật 36/2024/QH15 | văn bản chính |
| Nghị định 168/2024/NĐ-CP | văn bản chế tài |
| Luật 118/2025/QH15 | sửa đổi Luật 36/2024 (hiệu lực 01/7/2026) |
| Nghị định 238/2026/NĐ-CP | sửa đổi NĐ 168/2024 (hiệu lực 15/8/2026) |

Lý do phải nêu trong báo cáo: **luật quy định hành vi, nghị định mới quy định mức phạt**.
Chỉ dùng luật gốc thì không trả lời được câu hỏi phổ biến nhất là *“phạt bao nhiêu tiền”*.
Đây là điểm mạnh, nhưng lệch chữ nghĩa của đề nên phải giải trình kẻo bị đọc là làm sai đề.

### “Xây dựng keyphrase trong lĩnh vực.”

**Đạt.** **1.674** keyphrase trong `data/kb/keyphrases.json`, mỗi cụm có bản không dấu và số từ,
trỏ tới khái niệm / quy tắc / hành vi.

- Khớp cụm dài nhất, chịu được truy vấn không dấu — `tests/test_keyphrases.py`
- Đã kiểm: không có keyphrase treo (trỏ tới định danh không tồn tại)

### “Đặc tả: các thành phần về khái niệm, dạng luật trong các quy định.”

**Đạt.** Mô hình `K = (C, R, Rules, F, Keyphrase)`, đặc tả bằng kiểu Pydantic v2 chứ không phải dict tự do.

| Thành phần | Số lượng | Tệp |
|---|---:|---|
| Khái niệm (C) | 73 | `data/kb/concepts.json` |
| Quan hệ (R) | 482 | `data/kb/relations.json` |
| Quy tắc (Rules) | 109 | `data/kb/rules.json` |
| Hành vi vi phạm (F) | 345 | `data/kb/violations.json` |
| Keyphrase | 1.674 | `data/kb/keyphrases.json` |

- `src/traffic_law/domain/models.py` — ràng buộc kiểu, cấm trường lạ
- `src/traffic_law/kb/validator.py` — kiểm toàn vẹn liên tệp: định danh trùng, quan hệ treo, thiếu căn cứ
- 100% mục tri thức có căn cứ pháp lý truy nguyên được

### “Thu thập các câu hỏi, truy vấn trong lĩnh vực + câu trả lời.”

**Đạt.** **120/120** câu hỏi có đáp án chuẩn dạng văn bản *và* căn cứ pháp lý — `eval/qa_dataset.json`.

- Trường: `cau_hoi`, `dap_an_chuan`, `nguon`, `id_tri_thuc_dung`, `lop_bai_toan_dung`, `do_kho`
- Phủ cả 7 lớp bài toán: P1 20 · P2 20 · P3 40 · P4 12 · P5 15 · P6 8 · P7 5
- Ba mức độ khó: dễ 28 · trung bình 68 · khó 24
- Thêm **40** truy vấn *ngoài* lĩnh vực, phủ 11 chủ đề — `eval/truy_van_ngoai_mien.json`

### “Thiết kế giải pháp để trả lời.”

**Có trong mã, thiếu tài liệu → đã bổ sung.** Xem [`thiet_ke_giai_phap.md`](thiet_ke_giai_phap.md).

---

## b) Bài toán

### “Tra cứu các quy định”

**Đạt.** Tra được theo nội dung (P2) và theo căn cứ điều – khoản – điểm (P6).

```
Hỏi: "Điều 6 khoản 9 điểm a Nghị định 168/2024/NĐ-CP nói về lỗi gì?"
→ P6_TRA_CUU_CAN_CU · đúng hành vi · điểm 1.0
```

P6 phân lớp đúng 100%, Top-1 87,5%. P2 phân lớp đúng 95%, Top-5 85%.

### “Tra cứu theo ngữ nghĩa đơn giản của câu truy vấn”

**Đạt.** TF-IDF char *n*-gram kết hợp word *n*-gram, chịu được khẩu ngữ và lỗi chính tả.

```
Hỏi: "nhậu xong lái xe máy bị phạt nhiêu tiền"
→ P3_TRA_CUU_CHE_TAI · đúng khung nồng độ cồn · điểm 0,79
```

Chữ *“nhậu”* không hề xuất hiện trong bất kỳ văn bản luật nào — đây chính là phần “ngữ nghĩa”.
Truy vấn không dấu cho cùng lớp bài toán với truy vấn có dấu.

---

## Số đo

Từ `eval/ket_qua_danh_gia.json` · 120 câu hỏi · k = 5.

| Chỉ số | Giá trị | Ghi chú |
|---|---:|---|
| Độ chính xác phân lớp | 95,83% | 115/120 câu vào đúng lớp bài toán |
| Top-1 | 76,67% | cổng chỉ số CI chặn mọi PR làm tụt dưới mức này |
| Top-3 · Top-5 | 90,83% · 95,00% | 9/120 câu sai hoàn toàn |
| MRR | 0,8384 | đáp án đúng thường ở vị trí 1–2 |
| Precision · Recall · F1 | 0,3373 · 0,9306 · 0,4399 | trả 5 kết quả cho đáp án 1 mẩu → trần precision 0,20 mỗi câu |
| Thời gian trung bình | 6,2 ms | đo trên máy cá nhân; phụ thuộc phần cứng |
| Độ phủ kiểm thử | 90% | ngưỡng CI là 80% |
| Kiểm thử tự động | 256 đạt · 5 xfail · 4 bỏ qua | 4 test bỏ qua cần gói tuỳ chọn `dense` |

Theo từng lớp bài toán:

| Lớp | n | Phân lớp | Top-1 | Top-5 |
|---|---:|---:|---:|---:|
| P1 · Tra cứu khái niệm | 20 | 95,0% | 85,0% | 95,0% |
| P2 · Tra cứu quy định | 20 | 95,0% | 55,0% | 85,0% |
| P3 · Tra cứu chế tài | 40 | 97,5% | 85,0% | 97,5% |
| P4 · Tra cứu ngược | 12 | 100% | 66,7% | 100% |
| P5 · Suy diễn tình huống | 15 | 86,7% | 86,7% | 93,3% |
| P6 · Tra cứu căn cứ | 8 | 100% | 87,5% | 100% |
| P7 · Tra cứu liên quan | 5 | 100% | 40,0% | 100% |

---

## Sản phẩm nộp

| Hạng mục | Trạng thái | Tệp |
|---|---|---|
| Báo cáo (LaTeX) | **xong** — 46 trang, 6 mục, 2 phụ lục, 19 bảng, 9 hình, đúng 4 thiết lập định dạng | `docs/BaoCao_Nhom7_CS106.pdf` |
| Slide trình chiếu | **xong** — 21 trang, bám hệ thiết kế Organic của giao diện | `docs/Slide_Nhom7_CS106.pptx` |
| Hai sơ đồ | **xong** — kiến trúc và luồng B1–B6 | `docs/so_do/` |
| Giao diện demo | **xong** — 6 màn hình, chạy bằng Docker một lệnh | `src/traffic_law/api/` |
| Tài liệu thiết kế | **xong** | `docs/thiet_ke_giai_phap.md` |
| Giải trình “01 văn bản” | **xong** — mục 3.1 của báo cáo | xem mục a) ở trên |
| Hạn chế đã đo | **xong** — mục 6.2 của báo cáo | `eval/*.json` |

Mọi tệp đều dựng lại được bằng lệnh — `scripts/ve_so_do.py`, `scripts/thong_ke_du_lieu.py`
(hình), `latexmk -xelatex main.tex` trong `docs/bao-cao-latex/` (báo cáo, mục lục tự
cập nhật) và `scripts/lam_slide.js` (slide).

---

## Hạn chế đã đo

`xfail(strict=True)` — nếu ngày nào chúng bất ngờ đạt, CI báo lỗi và buộc cập nhật tài liệu.
Năm test xfail ở cấu hình mặc định; cài thêm gói tuỳ chọn `dense` thì có test thứ sáu.

| Số | Tệp | Nội dung |
|---:|---|---|
| 3 | `tests/test_confidence_threshold.py` | Cấu hình mặc định không từ chối được truy vấn ngoài lĩnh vực: trên độ tương đồng thô, 56/120 câu hợp lệ chấm điểm thấp hơn hoặc bằng truy vấn rác. |
| 1 | `tests/test_confidence_threshold.py` | 12/120 câu hợp lệ không rút được keyphrase nào. |
| 1 | `tests/test_kb_validator.py` | 46 chú thích sửa đổi của Luật 118/2025 chưa mô hình hoá — mô hình `SuaDoi` đóng khung theo NĐ 168. |
| 1* | `tests/test_domain_detection.py` | *(cần gói `dense`)* Dense embedding nâng AUC 0,8746 → 0,9958; riêng điểm dense loại được **77,5%** truy vấn rác khi ép buộc 0 câu hợp lệ bị oan, bộ lọc kết hợp keyphrase + dense loại được **92,5%**. Nhưng trần điểm của rác (0,516) vẫn trên sàn câu hợp lệ không keyphrase (0,464). |

---

## Kiểm chứng lại

Mọi con số trong tài liệu này sinh ra từ các lệnh sau, chạy tại gốc kho:

```bash
pytest -q --cov                              # 256 passed · 5 xfailed · 4 skipped · phủ 90%
python eval/evaluate.py --gate-top1 0.7667   # cổng chỉ số Top-1
python eval/ablation.py                      # thí nghiệm loại bỏ thành phần
python eval/kich_ban.py --chi-tiet           # 12/12 ca nghiệm thu
python eval/phat_hien_mien.py --dense --ghi  # bảng AUC tách miền
python scripts/suy_dien_hieu_luc.py --kiem-tra
ruff check . && mypy
```
