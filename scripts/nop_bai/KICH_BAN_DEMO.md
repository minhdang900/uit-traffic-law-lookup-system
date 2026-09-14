# Kịch bản demo — buổi 10

**Chuẩn bị:** mở Docker Desktop, chạy `docker/chay_demo.sh` (hoặc
`chay_demo.bat`) **trước giờ trình bày ít nhất 5 phút**. Lần nạp ảnh đầu tiên
mất 30–60 giây, đừng để hội đồng ngồi chờ.

Kiểm tra nhanh: mở `http://localhost:8000`, gõ thử một câu, thấy kết quả là xong.

---

## Năm bước, 5–7 phút

### 1. Câu chuẩn — hệ thống làm được gì
> *"Vượt đèn đỏ xe máy phạt bao nhiêu?"*

→ **4.000.000 – 6.000.000 đ**, trừ **4 điểm**, kèm căn cứ Điều 7 khoản 7 điểm c
NĐ 168/2024.

Chỉ vào **căn cứ pháp lý** dưới thẻ: mọi câu trả lời đều truy nguyên được, hệ
thống không diễn giải lại lời của luật.

### 2. Khẩu ngữ — đây là phần "ngữ nghĩa" của đề bài
> *"nhậu xong lái xe máy bị phạt nhiêu tiền"*

→ đúng khung nồng độ cồn.

**Nhấn mạnh:** chữ *"nhậu"* **không xuất hiện** trong bất kỳ văn bản luật nào.
Đây chính là yêu cầu *"tra cứu theo ngữ nghĩa đơn giản của câu truy vấn"*.

### 3. Suy diễn số học — hỏi liên tiếp ba lần
> *"xe máy nồng độ cồn 0,2 mg/l"* → rồi *0,3* → rồi *0,5*

→ **ba khung phạt khác nhau**. So khớp từ khoá đơn thuần sẽ trả về cả bốn khung;
hệ thống rút ngưỡng từ chính nguyên văn điều khoản rồi so sánh khoảng.

Con số thuyết phục: riêng 22 câu có giá trị số, bước này đưa Top-1 từ **40,9%
lên 95,5%**.

### 4. Tra theo căn cứ — độ chính xác tuyệt đối
> *"Điều 6 khoản 9 điểm a Nghị định 168/2024/NĐ-CP nói về lỗi gì?"*

→ **đúng 1 kết quả**. Tra theo căn cứ mà trả về 5 kết quả là sai.

### 5. Hiệu lực theo thời gian — điểm khác biệt
Mở màn `/hieu-luc`.

Sửa đổi được lưu như **dữ liệu**, không hợp nhất lúc dựng cơ sở tri thức. Ví dụ
R15 (chở trẻ em dưới 10 tuổi) mang nguyên văn **sau** sửa đổi nên hiệu lực từ
**01/7/2026** theo Luật 118/2025, không phải 01/01/2025.

Nếu còn thời gian: mở `/chi-so` cho xem bảng ablation.

---

## Hai điều nên chủ động nói trước khi hội đồng hỏi

Chủ động nêu hạn chế bao giờ cũng ăn điểm hơn để hội đồng tự phát hiện.

**1. Truy vấn ngoài lĩnh vực vẫn trả về kết quả.** Hỏi *"cách nấu phở bò"* thì
hệ thống vẫn đưa ra hành vi vi phạm.

> Đây là hạn chế **đã đo và ghi lại**, không phải chưa biết. Với đặc trưng
> TF-IDF, 56/120 câu hợp lệ chấm điểm thấp hơn hoặc bằng truy vấn rác — không
> ngưỡng nào tách được. Nhóm đã thử dense embedding: AUC tăng 0,8746 → 0,9958 và
> riêng điểm dense loại được **77,5%** truy vấn rác mà không từ chối oan câu nào,
> còn bộ lọc kết hợp keyphrase + dense loại được **92,5%**. Nhưng hai phân bố
> **vẫn chồng lấn** — trần điểm của rác 0,516 nằm trên sàn 0,464 của câu hợp lệ
> không có keyphrase. Muốn loại 100% rác phải chấp nhận làm oan 3/120 câu, nên
> nhóm từ chối đánh đổi đó và giữ tầng dense ở dạng tuỳ chọn.

**2. Hỏi nồng độ cồn mà không nêu phương tiện thì ra khung xe đạp.** Hệ thống
không bịa phương tiện người dùng chưa nói — về mặt tri thức là đúng, nhưng là
vấn đề trải nghiệm đang tồn tại. Nêu rõ *"xe máy"* thì ra đúng 6–8 triệu.

---

## Nếu sự cố

| Tình huống | Xử lý |
|---|---|
| Cổng 8000 bận | `PORT=8080 ./chay_demo.sh` |
| Container không lên | `docker logs traffic-law-demo` |
| Docker hỏng hoàn toàn | Chạy từ mã nguồn: `uvicorn traffic_law.api.web:app` |
| Mạng chập chờn | Không sao — hệ thống chạy hoàn toàn offline |

Phương án dự phòng cuối: mở sẵn `slide/Slide_Nhom7_CS106.pptx` (trang 9 tóm tắt
đúng năm bước này) hoặc `so_lieu/kich_ban_nghiem_thu.md` — bảng 12 ca
nghiệm thu với kết quả thật, trình bày được mà không cần chạy gì.
