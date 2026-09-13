# Hệ thống tra cứu kiến thức pháp luật giao thông đường bộ

Đồ án môn **CS106 — Trí tuệ nhân tạo**, Trường Đại học Công nghệ Thông tin, ĐHQG-HCM
Lớp **CS106.F31.CN2** · **Nhóm 7** · GVHD: **PGS.TS. Nguyễn Đình Hiển**
Đề tài 4: *Xây dựng hệ thống tra cứu kiến thức pháp luật* — lĩnh vực **giao thông đường bộ**

---

## Thành viên nhóm

| # | Họ tên | MSSV | Email |
|---|---|---|---|
| 1 | Nguyễn Quang Lâm | 25210289 | 25210289@ms.uit.edu.vn |
| 2 | Trần Trọng Tấn | 25210334 | 25210334@ms.uit.edu.vn |
| 3 | Lê Quang Thi | 25210337 | 25210337@ms.uit.edu.vn |
| 4 | Vỏ Cẩm Thu | 25210342 | 25210342@ms.uit.edu.vn |
| 5 | Nguyễn Trí Toàn | 26410135 | 26410135@ms.uit.edu.vn |
| 6 | Nguyễn Văn Thái | 26410108 | 26410108@ms.uit.edu.vn |
| 7 | Đỗ Quốc Hoàng | 26410043 | 26410043@ms.uit.edu.vn |

Danh sách đầy đủ: [`docs/thanh_vien.json`](docs/thanh_vien.json) ·
[`docs/danh_sach_nhom.csv`](docs/danh_sach_nhom.csv) (mở được bằng Excel)

## Tài liệu

| Tài liệu | Nội dung |
|---|---|
| [`docs/doi_chieu_de_tai_4.md`](docs/doi_chieu_de_tai_4.md) | Đối chiếu từng dòng yêu cầu đề bài với bằng chứng đo được |
| [`docs/thiet_ke_giai_phap.md`](docs/thiet_ke_giai_phap.md) | Mô hình tri thức, kiến trúc, thuật giải B1–B6, hàm điểm lai |

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
python eval/ablation.py      # thí nghiệm loại bỏ thành phần
```

Giao diện tra cứu (cần gói tuỳ chọn `ui`):

```bash
pip install -e '.[ui]'
streamlit run src/traffic_law/api/app.py
```

Bộ kịch bản nghiệm thu — 12 ca, mỗi ca nêu kỳ vọng kiểm chứng được bằng văn bản luật:

```bash
python eval/kich_ban.py --chi-tiet     # bảng cho người đọc
python eval/kich_ban.py --markdown     # dán thẳng vào báo cáo
```

### Chạy bằng Docker

Không cần cài Python hay phụ thuộc nào:

```bash
docker compose up giao-dien              # http://localhost:8501
PORT=8502 docker compose up giao-dien    # đổi cổng nếu 8501 đã bận

docker compose run --rm kich-ban         # 12 ca nghiệm thu
docker compose run --rm danh-gia         # đo chỉ số + cổng Top-1
docker compose run --rm kiem-thu         # toàn bộ kiểm thử + độ phủ
```

Bốn dịch vụ dùng **chung một ảnh**, chỉ khác lệnh chạy — nên số liệu in ra chắc
chắn đến từ đúng mã nguồn đang phục vụ giao diện.

Sinh khung báo cáo Word đúng định dạng đề bài (cần gói tuỳ chọn `bao-cao`):

```bash
pip install -e '.[bao-cao]'
python -m traffic_law.report.builder   # -> docs/bao_cao_de_tai_4_khung.docx
```

## Cấu trúc

```
src/traffic_law/
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
