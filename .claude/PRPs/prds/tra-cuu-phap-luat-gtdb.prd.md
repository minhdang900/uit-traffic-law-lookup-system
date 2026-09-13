# Hệ thống tra cứu kiến thức pháp luật giao thông đường bộ

> **PRD hồi cố.** Hệ thống đã xây xong và đo được. Tài liệu này ghi lại vấn đề,
> giả thuyết và bằng chứng *sau khi* đã kiểm chứng — không phải bản đặc tả viết
> trước. Mọi con số đều tái lập được bằng lệnh nêu ở cuối.

## Problem Statement

Người dân Việt Nam tra cứu mức phạt giao thông bằng cách gõ câu hỏi đời thường
("vượt đèn đỏ phạt bao nhiêu") vào công cụ tìm kiếm, rồi nhận về các bài viết
tổng hợp **không dẫn căn cứ**, thường đã lỗi thời sau khi Nghị định 168/2024 thay
Nghị định 100/2019. Không kiểm chứng được câu trả lời là rủi ro thật: mức phạt
nồng độ cồn chênh nhau từ 100.000 đ tới 40.000.000 đ tuỳ khung và tuỳ phương tiện.

Trong phạm vi môn học, đây là Đề tài 4 của CS106 — yêu cầu xây hệ tra cứu tri
thức pháp luật với keyphrase, đặc tả khái niệm/dạng luật, và tra cứu theo ngữ
nghĩa đơn giản.

## Evidence

- **Đo được, không phỏng đoán**: so khớp từ khoá đơn thuần chỉ đạt Top-1 35,8%
  (`eval/ablation.py`, cấu hình B). Người dùng gõ khẩu ngữ thì từ khoá không khớp.
- **Chữ "nhậu" không xuất hiện trong bất kỳ văn bản luật nào** — nhưng là cách
  người thật hỏi. Ca TC10 trong bộ nghiệm thu.
- **Văn bản đổi liên tục**: Luật 36/2024 đã bị Luật 118/2025 sửa (hiệu lực
  01/7/2026); NĐ 168/2024 bị NĐ 238/2026 sửa (15/8/2026). Bản hợp nhất
  55/VBHN-VPQH ra ngày 23/3/2026. Trả lời sai mốc thời gian là trả lời sai.
- **Giả định chưa kiểm chứng**: chưa có nghiên cứu người dùng thật nào. Toàn bộ
  phần "người dân gặp khó" là suy luận từ bối cảnh, *cần kiểm chứng* nếu đưa ra
  ngoài phạm vi môn học.

## Proposed Solution

Mô hình tri thức tường minh `K = (C, R, Rules, F, Keyphrase)` thay cho tìm kiếm
toàn văn: 73 khái niệm, 482 quan hệ, 109 quy tắc, 345 hành vi vi phạm, 1.674 cụm
từ khoá — mỗi mẩu mang **căn cứ pháp lý** và **khoảng hiệu lực**. Truy vấn được
phân vào 7 lớp bài toán rồi xếp hạng bằng hàm điểm lai
`0,55·keyphrase + 0,30·ngữ nghĩa + 0,15·ngữ cảnh`, cộng một bước suy diễn số học
chọn đúng khung phạt theo giá trị đo được.

Chọn cách này thay vì (a) tìm kiếm toàn văn — không dẫn được căn cứ, và (b) mô
hình sinh ngôn ngữ — một hệ tra cứu pháp luật **không được diễn giải lại lời của
luật**.

## Key Hypothesis

Chúng tôi tin rằng **mô hình tri thức có căn cứ + hàm điểm lai** sẽ giúp **người
hỏi bằng tiếng Việt tự nhiên** nhận được **đúng điều khoản kèm căn cứ kiểm chứng
được**. Chúng tôi biết mình đúng khi **Top-1 ≥ 70% trên 120 câu hỏi chuẩn có đáp
án và căn cứ**.

**Kết quả: Top-1 76,67% — giả thuyết được chấp nhận.**

## What We're NOT Building

- **Sinh ngôn ngữ tự nhiên** — câu trả lời ghép từ nguyên văn điều khoản. Có chủ
  đích: hệ tra cứu pháp luật diễn giải lại lời luật là tạo rủi ro pháp lý.
- **Suy luận đa bước** — P5 cộng dồn nhiều hành vi độc lập, không suy diễn dây chuyền.
- **Lĩnh vực khác** (đất đai, BHXH, BHYT) — đề bài cho chọn 1.
- **Tư vấn pháp lý** — mọi màn hình có kết quả đều mang miễn trừ trách nhiệm.

## Success Metrics

| Metric | Target | Thực đo | How Measured |
|---|---|---|---|
| Top-1 | ≥ 70% | **76,67%** | `eval/evaluate.py`, 120 câu, k=5 |
| Độ chính xác phân lớp | ≥ 90% | **95,83%** | như trên |
| Top-5 | ≥ 90% | **95,00%** | như trên |
| Thời gian trả lời | < 100 ms | **6,2 ms** | như trên |
| Ca nghiệm thu | 12/12 | **12/12** | `eval/kich_ban.py` |
| Không hồi quy | CI chặn | cổng `--gate-top1 0.7667` | GitHub Actions |

**Precision macro 0,3375 không phải chỉ số thất bại**: trả k=5 kết quả cho đáp án
1 mẩu → trần precision toán học là 0,20/câu.

## Open Questions

- [ ] Chưa có người dùng thật nào thử. Toàn bộ giả định về hành vi tra cứu **chưa
      kiểm chứng**.
- [ ] Hỏi nồng độ cồn không nêu phương tiện → trả về khung **xe đạp**. Đúng về tri
      thức (không bịa phương tiện) nhưng sai kỳ vọng người dùng. Chưa quyết cách xử lý.
- [ ] Chưa mô hình hoá 46 khoản sửa đổi của Luật 118/2025 ở mức từng khoản —
      mô hình `Amendment` đang đóng khung theo Nghị định 168.
- [ ] `reasoning/engine.py` đã 1.018 dòng — nợ kỹ thuật đến hạn, xem
      [`docs/kien_truc.md`](../../../docs/kien_truc.md) mục 4.

---

## Users & Context

**Primary User** — *giả định, chưa kiểm chứng*
- **Who**: người điều khiển xe máy/ô tô vừa bị lập biên bản hoặc sắp đi đăng kiểm
- **Current behavior**: gõ câu hỏi vào Google, đọc bài tổng hợp không dẫn căn cứ
- **Trigger**: vừa bị phạt, hoặc nghe tin đồn về mức phạt mới
- **Success state**: biết đúng khung tiền, số điểm bị trừ, và **điều khoản nào**
  quy định điều đó — để tự kiểm chứng

**Job to Be Done**
Khi *vừa bị CSGT lập biên bản và không biết mức phạt thế nào*, tôi muốn *tra
nhanh bằng câu hỏi đời thường*, để *biết mình phải nộp bao nhiêu và căn cứ ở đâu*.

**Non-Users**
- Luật sư / cán bộ pháp chế — họ cần toàn văn và bản án, không phải tra nhanh.
- Người hỏi lĩnh vực khác — cơ sở tri thức chỉ phủ giao thông đường bộ; truy vấn
  ngoài lĩnh vực cho kết quả rỗng là **có chủ đích**.

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|---|---|---|
| Must | Tra cứu theo ngữ nghĩa tiếng Việt tự nhiên | Yêu cầu b) của đề bài |
| Must | Mọi câu trả lời kèm căn cứ điều–khoản–điểm | Không kiểm chứng được thì vô dụng |
| Must | Suy diễn số học chọn đúng khung phạt | Không có thì sai 22/120 câu |
| Must | Hiệu lực theo thời gian | Trả lời sai mốc = trả lời sai |
| Should | Giao diện web nhiều màn hình | Cần cho buổi báo cáo |
| Should | Cổng chỉ số trong CI | Chặn hồi quy khi 7 người cùng sửa |
| Could | Từ chối truy vấn ngoài lĩnh vực | Đã thử dense; còn chồng lấn |
| Won't | Sinh ngôn ngữ tự nhiên | Rủi ro pháp lý |

### MVP Scope

Bộ máy suy diễn + 120 câu hỏi chuẩn + cổng chỉ số. Đủ để trả lời câu hỏi *"cách
tiếp cận này có hoạt động không"* mà chưa cần giao diện.

### User Flow

Gõ câu hỏi → phân lớp bài toán → xếp hạng → thẻ kết quả (mức phạt · điểm trừ ·
**căn cứ**) → xem chi tiết điều khoản → xem hiệu lực theo thời gian.

---

## Technical Approach

**Feasibility**: HIGH — đã xây xong và đo được.

**Architecture Notes**
- Tri thức đi suốt tầng suy diễn dưới dạng **mô hình Pydantic có kiểu**; chỉ đổi
  sang `dict` tại đúng một chỗ khi trả kết quả ra ngoài (`_to_dict`).
- Dữ liệu JSON giữ **khoá tiếng Việt** (dữ liệu pháp lý), mã nguồn dùng **định
  danh tiếng Anh**; bắc cầu bằng `alias_generator` của Pydantic.
- Sửa đổi lưu như **dữ liệu**, không hợp nhất lúc dựng KB → truy vấn được theo mốc.
- Tầng dense (`retrieval/dense.py`) là **tuỳ chọn**: mô hình ~470 MB, CI không cài.

**Technical Risks**

| Risk | Likelihood | Mitigation |
|---|---|---|
| Sửa mã làm tụt chỉ số | H | Cổng `--gate-top1` trong CI + ảnh chụp vàng 13 truy vấn |
| Dữ liệu pháp lý lỗi thời | M | Dẫn bản hợp nhất 55/VBHN-VPQH; validator bắt văn bản sửa đổi thiếu |
| Trả lời truy vấn ngoài lĩnh vực | M | Đã đo, ghi bằng xfail; dense loại 92,5% nhưng chưa bật mặc định |
| 7 người cùng sửa | M | CI đầy đủ: ruff, mypy strict, 259 test, độ phủ ≥ 80% |

---

## Implementation Phases

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|---|---|---|---|---|---|
| 1 | Nền tảng tri thức | Mô hình dữ liệu, bộ nạp, kiểm toàn vẹn | complete | - | - | - |
| 2 | Hiệu lực theo thời gian | Khoảng hiệu lực, truy vấn theo mốc | complete | - | 1 | - |
| 3 | Truy hồi & suy diễn | 7 lớp bài toán, điểm lai, số học, cổng CI | complete | - | 1 | - |
| 4 | Phát hiện miền | Đo 4 tín hiệu tách miền; dense tuỳ chọn | complete | with 5 | 3 | - |
| 5 | Chuyển sang mô hình có kiểu | Bỏ dict trong tầng suy diễn | complete | with 4 | 3 | - |
| 6 | Luật 118/2025 | Mô hình hoá văn bản sửa đổi | complete | - | 2 | - |
| 7 | Giao diện web 7 màn hình | FastAPI + Jinja thay Streamlit | complete | - | 3 | - |
| 8 | Đóng gói nộp bài | Script gói mã nguồn + ảnh Docker + demo | complete | - | 7 | - |
| 9 | Giao diện 12 màn hình | Responsive 402–2560 px, 6 route | complete | - | 7 | - |
| 10 | Hoàn thiện báo cáo Word | Điền 3 mục còn trống, chèn 3 sơ đồ | pending | with 12 | 8 | - |
| 11 | Mặc định phương tiện | Xử lý truy vấn thiếu phương tiện | pending | - | 9 | - |
| 13 | Tách `engine.py` | 1.018 dòng → 4 module theo B1–B6 | pending | - | 9 | - |
| 12 | 46 khoản sửa đổi Luật 118 | Tổng quát hoá mô hình `Amendment` | pending | - | 6 | - |

### Phase Details

**Phase 9 — Giao diện 12 màn hình** — *hoàn thành 13/9/2026*
- **Goal**: mở rộng từ 7 lên 12 màn hình theo bản bàn giao mới
- **Kết quả**: 6 route responsive từ 402 px tới 2560 px (bản mobile không còn là
  route riêng mà là cùng một trang co giãn). Bộ test tăng 179 → 259.

**Phase 10 — Hoàn thiện báo cáo**
- **Goal**: bản Word nộp được
- **Scope**: mục 1, 4 (nhận xét), 6; hai sơ đồ kiến trúc và B1–B6
- **Success signal**: không còn chuỗi `[Cần viết thêm]`; xuất PDF đúng lề

**Phase 11 — Mặc định phương tiện**
- **Goal**: câu hỏi thiếu phương tiện không trả về khung xe đạp gây hiểu nhầm
- **Scope**: hỏi lại, hoặc hiện song song các phương tiện cùng khung
- **Success signal**: test khoá hành vi mới; Top-1 không tụt

### Parallelism Notes

Pha 9 và 10 chạy song song được: một bên là mã, một bên là văn bản. Pha 11 phải
đợi 9 vì cùng chạm tầng trình bày. Pha 12 độc lập hoàn toàn (chỉ chạm mô hình dữ
liệu và dữ liệu thô).

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|---|---|---|---|
| Số văn bản pháp luật | 4 | 1 như đề ghi | Luật quy định *hành vi*, nghị định mới quy định *mức phạt* — tách ra thì không trả lời được "phạt bao nhiêu" |
| Trọng số keyphrase | 0,55 (cao nhất) | Cho TF-IDF cao hơn | Ablation: keyphrase riêng yếu hơn TF-IDF (35,8% vs 58,3%) nhưng thua về *độ phủ*, không thua *độ chính xác* |
| Tầng dense | Tuỳ chọn, mặc định tắt | Bật mặc định | Mô hình ~470 MB; loại 92,5% rác nhưng hai phân bố vẫn chồng lấn |
| Ngưỡng lọc miền | 0,45 | 0,52 (loại 100% rác) | 0,52 làm oan 3/120 câu hợp lệ — từ chối đánh đổi |
| Giao diện | FastAPI + Jinja | Giữ Streamlit | Streamlit không dựng được bố cục bản thiết kế |
| Ngôn ngữ định danh | Anh cho mã, Việt cho dữ liệu | Việt toàn bộ | Dịch làm lộ nhập nhằng: `hanh_vi` vừa là danh sách vi phạm vừa là trường văn bản |

---

## Research Summary

**Market Context**
thuvienphapluat.vn là nguồn tham chiếu đề bài nêu — tra cứu theo *văn bản*, không
theo *câu hỏi*. Các bài tổng hợp mức phạt trên báo mạng trả lời theo câu hỏi nhưng
không dẫn căn cứ và không theo mốc thời gian. Khoảng trống: tra theo câu hỏi **và**
dẫn được căn cứ **và** đúng thời điểm.

**Technical Context**
TF-IDF char *n*-gram chịu được lỗi chính tả và cách tách từ tiếng Việt — quan trọng
vì truy vấn thật đầy khẩu ngữ và thiếu dấu. Kết quả **âm** đáng ghi: phủ từ vựng KB
là tín hiệu tách miền vô dụng (AUC 0,72) — đã thử và đã bác bỏ, để người sau không
thử lại.

**Tái lập mọi con số**
```bash
pytest -q --cov                              # 259 passed, 6 xfailed, phủ 91%
python eval/evaluate.py --gate-top1 0.7667   # chỉ số chính
python eval/ablation.py                      # bảng loại bỏ thành phần
python eval/kich_ban.py --chi-tiet           # 12 ca nghiệm thu
python eval/phat_hien_mien.py --dense --ghi  # AUC tách miền
```

---

*Generated: 2026-09-13 · cập nhật sau khi pha 9 hoàn thành*
*Status: DRAFT hồi cố — phần "người dùng" là giả định, chưa kiểm chứng*
