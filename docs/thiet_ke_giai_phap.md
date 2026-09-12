# Thiết kế giải pháp

Đáp ứng yêu cầu *“Thiết kế giải pháp để trả lời”* của Đề tài 4.

---

## 1. Mô hình tri thức

```
K = (C, R, Rules, F, Keyphrase)
```

| Ký hiệu | Thành phần | Số lượng | Vai trò |
|---|---|---:|---|
| C | Khái niệm | 73 | định nghĩa pháp lý — “xe cơ giới là gì” |
| R | Quan hệ | 482 | đồ thị hai chiều nối các mảng tri thức |
| Rules | Quy tắc | 109 | quy định phải/không được làm |
| F | Hành vi vi phạm | 345 | hành vi + chế tài (tiền, trừ điểm, hình phạt bổ sung) |
| Keyphrase | Cụm từ khoá | 1.674 | cầu nối giữa ngôn ngữ người dùng và định danh tri thức |

Mọi mục đều mang **căn cứ pháp lý** (điều – khoản – điểm – văn bản) và **khoảng hiệu lực**
`(từ, đến)`, nên hệ thống trả lời được cả câu hỏi *“tại thời điểm nào”*.

Tri thức đi suốt tầng suy diễn dưới dạng **mô hình Pydantic có kiểu**; chỉ khi trả kết quả
ra ngoài mới chuyển thành `dict` (hàm `_ra_dict`), vì hình dạng dict là hợp đồng công khai
mà giao diện và bộ đánh giá đang đọc.

---

## 2. Kiến trúc

```
   Câu hỏi (ngôn ngữ tự nhiên)
              │
              ▼
   ┌──────────────────────┐
   │  QueryAnalyzer       │  B1 → B4
   │  chuẩn hoá, keyphrase│
   │  phân lớp bài toán   │
   └──────────┬───────────┘
              │ Q (biểu diễn hình thức)
              ▼
   ┌──────────────────────┐      ┌────────────────────┐
   │  InferenceEngine     │◄─────┤  KnowledgeBase     │
   │  điều phối P1..P7    │      │  chỉ mục + TF-IDF  │
   └──────────┬───────────┘      │  NumericReasoner   │
              │                   └────────────────────┘
              ▼
   ┌──────────────────────┐
   │  sinh_van_ban        │  B6
   │  câu trả lời + căn cứ│
   └──────────────────────┘
```

Tầng `retrieval/dense.py` là **tuỳ chọn**, chỉ dùng khi cần phát hiện truy vấn ngoài lĩnh vực;
đường đi mặc định không gọi tới nó.

---

## 3. Thuật giải xử lý truy vấn (B1 – B6)

| Bước | Việc | Hiện thực |
|---|---|---|
| **B1** | Chuẩn hoá truy vấn | `chuan_hoa`, `bo_dau` — hạ chữ thường, chuẩn Unicode, sinh bản không dấu |
| **B2** | Rút trích keyphrase | so khớp **cụm dài nhất** trên bản không dấu, không chồng lấn |
| **B3** | Phân loại lớp bài toán | hàm điểm có trọng số trên 6 nhóm mẫu biểu thức chính quy |
| **B4** | Dựng biểu diễn hình thức `Q` | keyphrase, nhóm, phương tiện, chủ thể, căn cứ, ràng buộc số |
| **B5** | Suy diễn / truy hồi | bộ giải riêng cho từng lớp P1–P7 |
| **B6** | Sinh câu trả lời | kèm căn cứ pháp lý và tri thức liên quan |

Vì sao **B2 khớp cụm dài nhất**: “nồng độ cồn” phải thắng “nồng độ” + “cồn” rời rạc,
nếu không sẽ trỏ sai mảng tri thức.

---

## 4. Bảy lớp bài toán

| Lớp | Tên | Câu hỏi tiêu biểu |
|---|---|---|
| P1 | Tra cứu khái niệm / định nghĩa | *Xe cơ giới là gì?* |
| P2 | Tra cứu quy định, quy tắc | *Quy tắc nhường đường tại nơi giao nhau?* |
| P3 | Tra cứu chế tài | *Vượt đèn đỏ xe máy phạt bao nhiêu?* |
| P4 | Tra cứu ngược theo mức phạt / điểm trừ | *Lỗi nào bị trừ 10 điểm giấy phép lái xe?* |
| P5 | Suy diễn tình huống nhiều hành vi | *Vừa vượt đèn đỏ vừa không có bằng thì tổng bao nhiêu?* |
| P6 | Tra cứu theo căn cứ pháp lý | *Điều 6 khoản 9 điểm a NĐ 168/2024 nói về lỗi gì?* |
| P7 | Tra cứu kiến thức liên quan | *Cho tôi thông tin về điểm giấy phép lái xe.* |

Phân lớp **không** chặn kết quả: sau khi bộ giải chạy, hệ thống luôn **bổ sung** đủ ba loại
tri thức (khái niệm / quy tắc / chế tài) nếu còn thiếu, miễn là vượt `NGUONG_BO_SUNG = 0.40`.
Nhờ vậy một câu bị phân lớp sai vẫn có cơ hội trả đúng — đây là lý do Top-5 (95,00%)
cao hơn hẳn Top-1 (76,67%).

---

## 5. Hàm điểm lai

```
score = ALPHA·s_keyphrase + BETA·s_ngữ_nghĩa + GAMMA·s_ngữ_cảnh
        ALPHA = 0,55       BETA = 0,30        GAMMA = 0,15
```

| Thành phần | Ý nghĩa | Vì sao trọng số đó |
|---|---|---|
| `s_keyphrase` | keyphrase trỏ thẳng tới định danh tri thức | **Cao nhất (0,55)** vì đây là tín hiệu *chắc chắn*: khớp cụm từ pháp lý gần như không sai. |
| `s_ngữ_nghĩa` | cosine TF-IDF char 3–5 gram + word 1–3 gram | 0,30 — cứu các câu khẩu ngữ không có keyphrase, nhưng nhiễu hơn nên không cho vượt keyphrase. |
| `s_ngữ_cảnh` | khớp phương tiện / chủ thể / nhóm | 0,15 — chỉ dùng để *phân biệt* các hành vi na ná nhau, không đủ sức tự chọn. |

Char *n*-gram chịu được lỗi chính tả và cách tách từ tiếng Việt; word *n*-gram giữ được
cụm nhiều từ. Với khái niệm và quy tắc, điểm còn được trộn thêm 0,4 phần khớp riêng với **tên**.

### Kiểm chứng bằng thí nghiệm loại bỏ thành phần

`python eval/ablation.py` — đo đúng đóng góp của từng thành phần trên cả 120 câu:

| Cấu hình | Top-1 | Top-5 | MRR |
|---|---:|---:|---:|
| A. Chỉ so khớp ngữ nghĩa (TF-IDF) | 58,3% | 89,2% | 0,7054 |
| B. Chỉ so khớp keyphrase | 35,8% | 59,2% | 0,4381 |
| C. Lai keyphrase + ngữ nghĩa + ngữ cảnh | 66,7% | 94,2% | 0,7759 |
| **D. Hệ thống đầy đủ (C + suy diễn số học)** | **76,7%** | **95,0%** | **0,8384** |

Ba điều rút ra:

1. **Không thành phần nào tự đứng được.** Keyphrase một mình chỉ đạt 35,8%, TF-IDF một
   mình 58,3% — nhưng lai lại thì lên 66,7%. Hai tín hiệu bắt được những câu khác nhau.
2. **Keyphrase yếu hơn TF-IDF khi đứng riêng, nhưng vẫn xứng trọng số cao nhất.** Vì khi
   nó khớp thì gần như luôn đúng; nó chỉ thua ở *độ phủ*, không phải ở *độ chính xác*.
   Lai lại, TF-IDF lo phần phủ còn keyphrase lo phần chuẩn.
3. **Suy diễn số học đóng góp 10 điểm phần trăm** (66,7% → 76,7%) dù chỉ ảnh hưởng 22/120 câu.

---

## 6. Suy diễn số học

Nhiều quy định phân mức theo dải giá trị (nồng độ cồn, mức vượt tốc độ). So khớp từ khoá
đơn thuần sẽ trả về *mọi* khung phạt có chữ “nồng độ cồn”. `reasoning/numeric.py` xử lý:

1. Rút **ngưỡng** từ chính nguyên văn hành vi (không viết cứng trong mã → tri thức vẫn nằm trong KB)
2. Rút **giá trị** trong câu hỏi người dùng
3. So sánh khoảng nửa mở `(cận dưới, cận trên]` để chọn đúng khung

```
"nồng độ cồn 0,3 mg/l phạt thế nào"
→ 0,3 thuộc khoảng (0,25 – 0,4]  → đúng một khung, không phải cả bốn
```

Không nêu giá trị cụ thể thì hệ thống lấy **khung thấp nhất** và kèm cảnh báo.

Riêng 22 câu hỏi có giá trị số, đóng góp của bước này rất rõ:

| Cấu hình | Top-1 | Top-5 | MRR |
|---|---:|---:|---:|
| C. Không suy diễn số học | 40,9% | 95,5% | 0,6364 |
| **D. Có suy diễn số học** | **95,5%** | **100%** | **0,9773** |

Top-5 gần như không đổi (95,5% → 100%) còn Top-1 nhảy từ 40,9% lên 95,5%: đúng như kỳ vọng —
so khớp từ khoá vẫn *tìm ra* đủ các khung phạt, nó chỉ không biết **chọn khung nào**.

---

## 7. Hiệu lực theo thời gian

Mỗi quy tắc và hành vi mang khoảng hiệu lực suy ra từ ngày hiệu lực của văn bản và các
văn bản sửa đổi (`scripts/suy_dien_hieu_luc.py`, có kiểm tra bất biến trong CI).

Ví dụ: R15 (chở trẻ em dưới 10 tuổi) mang nguyên văn **sau** sửa đổi của Luật 118/2025,
nên hiệu lực từ **01/7/2026**, không phải 01/01/2025.

---

## 8. Đánh giá và cổng chất lượng

| Lớp bảo vệ | Cơ chế |
|---|---|
| Toàn vẹn dữ liệu | `kb/validator.py` — định danh trùng, quan hệ treo, thiếu căn cứ, văn bản sửa đổi thiếu |
| Hành vi đầu ra | ảnh chụp vàng `tests/test_hop_dong_dau_ra.py` — 13 truy vấn, khoá cả bộ trường dict trả về |
| Chất lượng truy hồi | `eval/evaluate.py --gate-top1 0.7667` — CI đỏ nếu Top-1 tụt |
| Độ phủ | `pytest --cov-fail-under=80` (hiện đạt 88%) |
| Kiểu và định dạng | `mypy` (strict trên `domain`, `kb`, `retrieval`) và `ruff` |

---

## 9. Giới hạn của thiết kế

Ghi lại để không ai tưởng hệ thống làm được nhiều hơn thực tế:

- **Không tách được truy vấn ngoài lĩnh vực ở cấu hình mặc định.** Đã đo: đặc trưng TF-IDF
  quá yếu, 56/120 câu hợp lệ chấm điểm thấp hơn hoặc bằng truy vấn rác. Dense embedding
  nâng AUC lên 0,9958 và loại 92,5% rác, nhưng hai phân bố vẫn chồng lấn.
- **Không sinh ngôn ngữ tự nhiên.** Câu trả lời ghép từ nguyên văn điều khoản, cố ý như vậy:
  một hệ tra cứu pháp luật không được diễn giải lại lời của luật.
- **Không suy luận đa bước.** P5 cộng dồn nhiều hành vi độc lập, không suy diễn dây chuyền.
