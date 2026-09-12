# Hệ thống tra cứu kiến thức pháp luật giao thông đường bộ

Đồ án môn **CS106 — Trí tuệ nhân tạo**, Trường Đại học Công nghệ Thông tin, ĐHQG-HCM
Lớp **CS106.F31.CN2** · **Nhóm 7** · GVHD: **PGS.TS. Nguyễn Đình Hiển**
Đề tài 4: *Xây dựng hệ thống tra cứu kiến thức pháp luật* — lĩnh vực **giao thông đường bộ**

---

## Mô hình tri thức

Hệ thống biểu diễn tri thức pháp luật theo mô hình năm thành phần:

$$K = (C,\ R,\ Rules,\ F,\ Keyphrase)$$

| Thành phần | Ý nghĩa | Quy mô |
|---|---|---|
| `C` | Tập khái niệm | 73 |
| `R` | Tập quan hệ hai ngôi | 482 |
| `Rules` | Quy tắc giao thông và luật dẫn | 109 |
| `F` | Sự kiện: hành vi vi phạm + chế tài | 345 |
| `Keyphrase` | Từ điển cụm từ khoá (kèm bản không dấu) | 1.674 |

## Văn bản pháp luật

| Văn bản | Hiệu lực | Vai trò |
|---|---|---|
| Luật Trật tự, an toàn GTĐB **36/2024/QH15** | 01/01/2025 | Văn bản chính |
| Nghị định **168/2024/NĐ-CP** | 01/01/2025 | Văn bản chế tài |
| Nghị định **238/2026/NĐ-CP** | 15/08/2026 | Văn bản sửa đổi |

Hệ thống mô hình hoá **hiệu lực theo thời gian**: mỗi điều khoản mang khoảng hiệu lực,
sửa đổi được lưu như **dữ liệu** chứ không hợp nhất lúc dựng cơ sở tri thức. Nhờ đó có
thể truy vấn *"mức phạt tại thời điểm nào"* thay vì chỉ biết bản hiện hành.

## Bảy lớp bài toán

| Mã | Lớp bài toán | Ví dụ |
|---|---|---|
| P1 | Tra cứu khái niệm | *Nồng độ cồn là gì?* |
| P2 | Tra cứu quy định | *Gặp đèn đỏ có được đi tiếp không?* |
| P3 | Tra cứu chế tài | *Vượt đèn đỏ xe máy phạt bao nhiêu?* |
| P4 | Tra cứu ngược | *Lỗi nào bị trừ 10 điểm giấy phép lái xe?* |
| P5 | Suy diễn tình huống | *Vừa vượt đèn đỏ vừa có nồng độ cồn thì sao?* |
| P6 | Tra cứu theo căn cứ | *Điều 6 khoản 9 Nghị định 168 quy định gì?* |
| P7 | Tra cứu liên quan | *Cho tôi thông tin về mũ bảo hiểm* |

## Kết quả thực nghiệm

Trên bộ 120 câu hỏi tự xây dựng có đáp án chuẩn, **toàn bộ 120/120 câu đều chấm được**
(mọi đáp án chuẩn giải được về tri thức có thật trong cơ sở tri thức — có test kiểm chứng).

| Chỉ số | Giá trị |
|---|---|
| Độ chính xác phân lớp bài toán | 95,83% |
| Truy hồi đúng Top-1 | 76,67% |
| Truy hồi đúng Top-3 | 90,83% |
| Truy hồi đúng Top-5 | 95,00% |
| MRR | 0,8384 |
| Thời gian trả lời trung bình | ~25 ms |

> Precision (macro) 0,3375 phản ánh đặc tính của truy hồi **top-k** (trả về 5 kết quả
> trong khi đáp án chuẩn thường chỉ có 1 mẩu tri thức, nên precision tối đa là 0,20/câu),
> **không** phải khiếm khuyết thiết kế.

## Cài đặt

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,ui]"
```

## Sử dụng

```bash
pytest                       # chạy toàn bộ kiểm thử
python eval/evaluate.py      # đo lại các chỉ số
streamlit run ui/app.py      # giao diện web
```

## Cấu trúc

```
src/tra_cuu_gtdb/
  domain/      Mô hình dữ liệu thuần (Pydantic), không I/O
  kb/          Nạp, kiểm tra toàn vẹn, lập chỉ mục cơ sở tri thức
  retrieval/   Các làn truy hồi (từ khoá + TF-IDF, tuỳ chọn dense)
  reasoning/   Phân tích truy vấn, suy diễn số học, bộ giải P1–P7
  api/         Lớp mặt tiền
data/kb/       Cơ sở tri thức (JSON — nguồn sự thật, diff được trên git)
data/raw/      Dữ liệu bóc tách từ văn bản gốc
eval/          Bộ đánh giá và thí nghiệm loại bỏ thành phần
tests/         Kiểm thử
ui/            Giao diện Streamlit
```

Cơ sở tri thức để dạng **JSON** có chủ đích: khi một nghị định thay đổi, diff trên
pull request cho thấy chính xác điều khoản nào đã đổi — điều mà cơ sở dữ liệu che mất.

## Giấy phép

MIT — xem [LICENSE](LICENSE).

> ⚠️ Kết quả tra cứu mang tính tham khảo, **không thay thế** ý kiến của cơ quan có thẩm quyền.
