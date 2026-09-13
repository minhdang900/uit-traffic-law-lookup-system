# Báo cáo về bộ dữ liệu

Số liệu đo trực tiếp từ `data/kb/`, `eval/qa_dataset.json` và
`eval/truy_van_ngoai_mien.json`. Mọi con số tái lập được.

---

## 1. Cơ sở tri thức

| Thành phần | Ký hiệu | Số lượng |
|---|---|---:|
| Khái niệm | C | 73 |
| Quan hệ | R | 482 |
| Quy tắc | Rules | 109 |
| Hành vi vi phạm | F | 345 |
| Cụm từ khoá | Keyphrase | 1.674 |
| Văn bản pháp luật | — | 4 |
| Khoản sửa đổi | — | 63 |

**Tổng mục tri thức truy hồi được**: 527 (73 + 109 + 345).

### Nguồn

Luật 36/2024/QH15 · Nghị định 168/2024/NĐ-CP · Luật 118/2025/QH15 ·
Nghị định 238/2026/NĐ-CP. Toàn bộ đối chiếu **Văn bản hợp nhất 55/VBHN-VPQH
ngày 23/3/2026** — dữ liệu là bản **sau** sửa đổi.

---

## 2. Phân bố hành vi vi phạm

### Theo lĩnh vực

| Lĩnh vực | Số hành vi | Tỷ lệ |
|---|---:|---:|
| Quy tắc giao thông đường bộ | 129 | 37,4% |
| An toàn người tham gia giao thông | 65 | 18,8% |
| Điều kiện của người điều khiển | 61 | 17,7% |
| Điều kiện của phương tiện | 57 | 16,5% |
| Vận tải đường bộ và hàng hoá | 22 | 6,4% |
| Nội dung khác | 11 | 3,2% |

### Theo phương tiện

Một hành vi có thể áp dụng cho nhiều phương tiện, nên tổng lớn hơn 345.

| Phương tiện | Số hành vi |
|---|---:|
| Ô tô | 178 |
| Mô tô | 116 |
| Xe gắn máy | 107 |
| Xe máy chuyên dùng | 56 |
| Xe đạp | 32 |
| Xe thô sơ | 30 |
| Không áp dụng phương tiện cụ thể | 27 |

### Chế tài

| Loại | Số hành vi | Tỷ lệ |
|---|---:|---:|
| Có phạt tiền | 341 / 345 | 98,8% |
| Có trừ điểm GPLX | 116 / 345 | 33,6% |
| Có hình phạt bổ sung | 82 / 345 | 23,8% |

Mức phạt trải từ **0 đồng** (cảnh cáo) tới **75.000.000 đồng**. Trung vị của mức
phạt tối đa là **3.000.000 đồng**; phân vị 90% là **20.000.000 đồng** — nghĩa là
phân bố **lệch mạnh về phía thấp**, các mức phạt rất cao là thiểu số.

---

## 3. Cụm từ khoá

- **1.674** cụm, trung bình **5,91 từ**, dài nhất **24 từ**
- Trỏ tới hành vi vi phạm: 1.042 · khái niệm: 280 · quy tắc: 176
- Mỗi cụm có bản **không dấu** để so khớp truy vấn người dùng gõ thiếu dấu

Cụm dài (trung bình gần 6 từ) là lý do thuật giải phải khớp **cụm dài nhất** —
"nồng độ cồn trong máu hoặc hơi thở" phải thắng "nồng độ cồn" rời rạc.

---

## 4. Bộ câu hỏi đánh giá

**120 câu**, mỗi câu có đáp án chuẩn dạng văn bản **và** căn cứ pháp lý —
120/120 đủ cả hai trường.

| Lớp bài toán | Số câu | Tỷ lệ |
|---|---:|---:|
| P3 · Tra cứu chế tài | 40 | 33,3% |
| P1 · Tra cứu khái niệm | 20 | 16,7% |
| P2 · Tra cứu quy định | 20 | 16,7% |
| P5 · Suy diễn tình huống | 15 | 12,5% |
| P4 · Tra cứu ngược | 12 | 10,0% |
| P6 · Tra cứu căn cứ | 8 | 6,7% |
| P7 · Tra cứu liên quan | 5 | 4,2% |

| Chiều | Phân bố |
|---|---|
| Độ khó | dễ 28 · trung bình 68 · khó 24 |
| Loại tri thức | vi phạm 73 · quy tắc 25 · khái niệm 22 |
| Độ dài câu hỏi | ngắn nhất 11 · trung bình 61 · dài nhất 155 ký tự |

### Bộ truy vấn ngoài lĩnh vực

**40 câu**, phủ **11 chủ đề** (ẩm thực, tài chính, công nghệ, sức khoẻ, làm đẹp,
nông nghiệp, thú cưng, thể thao, giáo dục, giải trí, đời sống) — dùng để đo khả
năng từ chối, không phải để đo độ chính xác.

---

## 5. Ba hạn chế của bộ dữ liệu

Đây là phần quan trọng nhất của báo cáo này — nêu ra để người đọc biết con số
Top-1 76,67% có ý nghĩa tới đâu.

### 5.1 Bộ câu hỏi chỉ phủ 21,8% cơ sở tri thức

| Loại | Được hỏi đến | Tổng | Độ phủ |
|---|---:|---:|---:|
| Khái niệm | 22 | 73 | 30,1% |
| Quy tắc | 21 | 109 | 19,3% |
| Hành vi vi phạm | 72 | 345 | 20,9% |
| **Tổng** | **115** | **527** | **21,8%** |

Nghĩa là **412 mục tri thức chưa từng được kiểm chứng** bằng một câu hỏi nào.
Chỉ số Top-1 nói về phần được hỏi, không nói gì về phần còn lại. Muốn khẳng định
chất lượng toàn cơ sở tri thức thì cần mở rộng bộ câu hỏi.

### 5.2 Năng lực "chịu truy vấn không dấu" chỉ được kiểm bằng 3 câu

Hệ thống nêu khả năng xử lý truy vấn thiếu dấu như một điểm mạnh, nhưng trong
120 câu chỉ có **3 câu (2,5%)** viết hoàn toàn không dấu. Bằng chứng cho năng
lực này **mỏng hơn** so với ấn tượng nó tạo ra.

Tương tự, suy diễn số học được kiểm bằng **22/120 câu** — đủ để kết luận (Top-1
của nhóm này nhảy 40,9% → 95,5%) nhưng vẫn là một lát cắt hẹp.

### 5.3 Phân bố câu hỏi không khớp phân bố tri thức

Hành vi vi phạm chiếm **65,5%** cơ sở tri thức (345/527) nhưng chỉ chiếm **60,8%**
số câu hỏi (73/120) — tạm cân đối. Nhưng P7 chỉ có **5 câu**: một câu sai làm
chỉ số của lớp đó đổi 20 điểm phần trăm. **Top-1 40% của P7 thực chất là 2/5 câu**
— cỡ mẫu quá nhỏ để kết luận gì chắc chắn.

---

## 6. Hai cảnh báo chất lượng dữ liệu

Validator phát hiện và **cố ý không chặn CI** — đây là cảnh báo, không phải lỗi:

| Mã | Số lượng | Nội dung |
|---|---:|---|
| `CHE_TAI_PHI_CAU_TRUC` | 8 | Điều khoản ghi chế tài (cảnh cáo, tịch thu) dưới dạng văn bản tự do trong `ghi_chu` thay vì trường có cấu trúc |
| `KHAI_NIEM_KHONG_DINH_NGHIA` | 9 | Khái niệm không có định nghĩa trong luật, chỉ có thuộc tính — lớp P1 phải trả lời bằng thuộc tính và căn cứ |

Cả hai đều phản ánh **đặc tính của văn bản gốc**, không phải lỗi trích xuất: luật
Việt Nam có những điều khoản chỉ ghi "cảnh cáo" mà không nêu số tiền, và có những
khái niệm chỉ được liệt kê thành phần chứ không định nghĩa.

---

## 7. Tính toàn vẹn

Các kiểm tra chặn CI, tất cả đều đạt:

- Không trùng định danh trong cả ba tập
- Mọi quan hệ trỏ tới thực thể có thật
- Mọi keyphrase trỏ tới định danh tồn tại
- 100% mục tri thức có căn cứ pháp lý truy nguyên được
- Mọi điều khoản có khoảng hiệu lực (suy diễn bất biến)
- Mọi văn bản khai bị sửa đổi đều được mô hình hoá

---

## Tái lập

```bash
python eval/evaluate.py --gate-top1 0.7667   # chỉ số trên 120 câu
python eval/kich_ban.py --chi-tiet           # 12 ca nghiệm thu
pytest tests/test_kb_validator.py -q         # toàn vẹn dữ liệu
```
