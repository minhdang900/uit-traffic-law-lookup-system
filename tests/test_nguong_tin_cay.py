"""Kiểm thử ngưỡng tin cậy và khả năng nói "không tìm thấy".

KẾT QUẢ THỰC NGHIỆM CỦA PHA 2 — GIẢ THUYẾT BAN ĐẦU ĐÃ BỊ BÁC BỎ
================================================================

Giả thuyết ban đầu:
    "precision_macro 0.3375 thấp là do khối bổ sung luôn điền kết quả.
     Thêm ngưỡng tin cậy sẽ nâng precision lên >= 0.55 và F1 lên >= 0.65."

Đo đạc cho thấy giả thuyết SAI ở hai điểm:

1. precision_macro 0.3375 KHÔNG phải dấu hiệu của lỗi.
   Bộ đánh giá trả về k=5 kết quả trong khi đáp án chuẩn thường chỉ có 1 mẩu
   tri thức. Precision tối đa về mặt toán học khi đó là 1/5 = 0.20 mỗi câu.
   Con số 0.3375 đã CAO HƠN mức đó — nó phản ánh đặc tính của truy hồi top-k,
   không phải khiếm khuyết của khối bổ sung.

2. Áp ngưỡng 0.40 vào lớp P7 làm chỉ số XẤU ĐI, không tốt lên:
       Top-1   76.67% → 75.00%
       F1      0.4401 → 0.4234     (giảm, trái hướng kỳ vọng)
       P7 Top-1  40%  → 0%          (bị xoá sổ)
   Thay đổi này vi phạm chính tiêu chí chấp nhận của kế hoạch nên ĐÃ ĐƯỢC
   HOÀN NGUYÊN. Cơ sở tri thức và chỉ số hiện giữ nguyên đường cơ sở.

VÌ SAO KHÔNG TÁCH ĐƯỢC TRUY VẤN RÁC
------------------------------------
Đo điểm cao nhất trả về:
    Q118 "Xe ưu tiên."        → khái niệm 0.300 · quy tắc 0.300 · hành vi 0.323
    "cách nấu phở bò"         → khái niệm 0.300 · quy tắc 0.300 · hành vi 0.323
Hai truy vấn — một hợp lệ, một hoàn toàn ngoài lĩnh vực — cho điểm GIỐNG HỆT
nhau. Giá trị 0.300/0.3225 là SÀN của hàm tính điểm, không phải độ tương đồng
thật. Không ngưỡng nào tách được hai phân bố này.

Thử tín hiệu thay thế (số keyphrase rút trích được):
    8/8 truy vấn rác          → 0 keyphrase  ✅ tách được
    nhưng 12/120 câu hợp lệ   → 0 keyphrase  ❌ sẽ bị từ chối oan (10%)

KẾT LUẬN: với tập đặc trưng hiện tại, KHÔNG thể phát hiện truy vấn ngoài lĩnh
vực mà không hy sinh khoảng 10% câu hỏi hợp lệ. Đây là hạn chế đã đo được, ghi
nhận bằng các test xfail bên dưới thay vì giấu đi.

HƯỚNG XỬ LÝ ĐỀ XUẤT (ngoài phạm vi pha này)
    - Sửa hàm tính điểm để bỏ sàn 0.300, cho điểm phản ánh độ tương đồng thật
    - Hoặc thêm một bộ phân lớp miền (trong/ngoài lĩnh vực giao thông) riêng

CẬP NHẬT — ĐỀ XUẤT THỨ HAI ĐÃ ĐƯỢC KIỂM CHỨNG
----------------------------------------------
``src/tra_cuu_gtdb/retrieval/dense.py`` hiện thực bộ lọc miền bằng dense
embedding. Đo trên chính 120 câu này cộng 40 truy vấn ngoài miền:

    tín hiệu            AUC     loại rác khi 0 câu oan
    TF-IDF thô        0.8746     7,5%
    số keyphrase      0.9500     0,0%
    dense             0.9958    77,5%
    dense + keyphrase    --     92,5%

Tức là tách miền LÀ KHẢ THI, chỉ không khả thi với đặc trưng thưa. Tầng dense
là tuỳ chọn (mô hình ~470 MB) nên cấu hình mặc định — thứ mà tệp này đo — vẫn
giữ nguyên hành vi cũ, và các xfail dưới đây vẫn đúng.
"""
import pytest

from tra_cuu_gtdb.reasoning.engine import NGUONG_BO_SUNG

pytestmark = pytest.mark.cham

NGOAI_LINH_VUC = ["cách nấu phở bò", "giá vàng hôm nay", "lập trình Python cơ bản"]

TRONG_LINH_VUC = [
    "vượt đèn đỏ xe máy phạt bao nhiêu",
    "nồng độ cồn 0,3 mg/l phạt thế nào",
    "không đội mũ bảo hiểm phạt bao nhiêu",
    "xe cơ giới là gì",
    "lỗi nào bị trừ 10 điểm giấy phép lái xe",
]


class TestHopDongKetQua:
    """Những gì ĐÃ hoạt động và cần được khoá lại."""

    def test_khoa_khong_tim_thay_luon_ton_tai(self, he_thong):
        """Giao diện và bộ đánh giá đọc khoá này; thiếu nó sẽ ném KeyError."""
        for truy_van in TRONG_LINH_VUC + NGOAI_LINH_VUC:
            kq = he_thong.hoi(truy_van)
            assert "khong_tim_thay" in kq, f"Thiếu khoá với truy vấn {truy_van!r}"
            assert isinstance(kq["khong_tim_thay"], bool)

    @pytest.mark.parametrize("truy_van", TRONG_LINH_VUC)
    def test_truy_van_hop_le_khong_bi_tu_choi(self, he_thong, truy_van):
        kq = he_thong.hoi(truy_van)
        assert kq["khong_tim_thay"] is False
        assert kq["khai_niem"] or kq["quy_tac"] or kq["hanh_vi"]

    def test_toan_bo_120_cau_chuan_khong_bi_tu_choi_oan(self, he_thong, bo_qa):
        """Ràng buộc an toàn: ngưỡng bổ sung không được loại oan câu hợp lệ nào."""
        bi_tu_choi = [m["id"] for m in bo_qa
                      if he_thong.hoi(m["cau_hoi"])["khong_tim_thay"]]
        assert bi_tu_choi == [], f"{len(bi_tu_choi)}/120 câu bị từ chối oan: {bi_tu_choi[:10]}"


class TestNguongBoSung:
    """Ngưỡng chỉ chi phối tri thức BỔ SUNG, không bao giờ chặn kết quả chính."""

    def test_nguong_nam_giua_hai_phan_bo_do_duoc(self):
        """Trần truy vấn rác 0.3225 < ngưỡng < phân vị 5% truy vấn hợp lệ 0.45."""
        assert 0.3225 < NGUONG_BO_SUNG < 0.45

    def test_tri_thuc_bo_sung_deu_dat_nguong(self, he_thong):
        for truy_van in TRONG_LINH_VUC:
            kq = he_thong.hoi(truy_van)
            for loai in ("khai_niem", "quy_tac", "hanh_vi"):
                duoi = [x for x in kq[loai]
                        if x.get("bo_sung") and x.get("diem", 0) < NGUONG_BO_SUNG]
                assert not duoi, f"{truy_van!r}: {len(duoi)} mẩu bổ sung dưới ngưỡng"

    def test_nguong_khong_lam_tut_chi_so(self, he_thong, bo_qa):
        """Chốt chặn hồi quy: Top-1 phải giữ mức đường cơ sở 76,67%."""
        dung = 0
        for m in bo_qa:
            kq = he_thong.hoi(m["cau_hoi"], top_k=5)
            loai = m["loai_tri_thuc"]
            khoa = {"concept": "khai_niem", "rule": "quy_tac"}.get(loai, "hanh_vi")
            tra_ve = [x["id"] for x in kq[khoa]]
            if tra_ve and tra_ve[0] in m["id_tri_thuc_dung"]:
                dung += 1
        top1 = dung / len(bo_qa)
        assert top1 >= 0.76, f"Top-1 tụt xuống {top1:.2%} (đường cơ sở 76,67%)"


class TestHanCheDaBietVaDoDuoc:
    """Ghi nhận hạn chế đã đo được, KHÔNG che giấu bằng cách xoá test.

    strict=True nghĩa là: nếu ngày nào đó các test này BẤT NGỜ PASS, pytest sẽ
    báo lỗi XPASS — buộc phải cập nhật lại tài liệu thay vì im lặng bỏ qua.
    """

    @pytest.mark.xfail(strict=True, reason=(
        "Sàn 0.300/0.3225 do phép chuẩn hoá sem/sem.max() sinh ra: kết quả tốt "
        "nhất LUÔN được kéo về 1.0 dù khớp tệ tới đâu. NHƯNG bỏ chuẩn hoá cũng "
        "KHÔNG cứu được: đo trên độ tương đồng thô, 56/120 câu hợp lệ vẫn chấm "
        "điểm thấp hơn hoặc bằng truy vấn rác (concept 57/120, rule 82/120). "
        "Tín hiệu TF-IDF quá yếu để tách miền — cần đặc trưng khác, không phải "
        "chỉnh ngưỡng. ĐÃ KIỂM CHỨNG ĐỀ XUẤT ĐÓ: dense embedding nâng AUC "
        "0.8746 -> 0.9958 và loại được 92,5% truy vấn rác mà không làm oan câu "
        "hợp lệ nào (xem tests/test_phat_hien_mien.py). Test này vẫn xfail vì "
        "nó đo CẤU HÌNH MẶC ĐỊNH, nơi tầng dense cố ý không được bật: mô hình "
        "nặng ~470 MB nên là gói tuỳ chọn."))
    @pytest.mark.parametrize("truy_van", NGOAI_LINH_VUC)
    def test_nen_tu_choi_truy_van_ngoai_linh_vuc(self, he_thong, truy_van):
        kq = he_thong.hoi(truy_van)
        assert kq["khong_tim_thay"] is True, (
            f"{truy_van!r} vẫn trả về {len(kq['hanh_vi'])} hành vi vi phạm")

    @pytest.mark.xfail(strict=True, reason=(
        "12/120 câu hợp lệ cũng rút được 0 keyphrase, nên không dùng riêng tín "
        "hiệu keyphrase để lọc truy vấn ngoài lĩnh vực."))
    def test_nen_rut_duoc_keyphrase_cho_moi_cau_hop_le(self, he_thong, bo_qa):
        khong_co = [m["id"] for m in bo_qa
                    if not he_thong.engine.analyzer.analyze(m["cau_hoi"])["keyphrase"]]
        assert khong_co == [], f"{len(khong_co)}/120 câu không rút được keyphrase nào"
