"""Kiểm thử việc xây dựng và rút trích keyphrase.

Đề bài yêu cầu tường minh: "Xây dựng keyphrase trong lĩnh vực."
Đây là thành phần Keyphrase trong mô hình K = (C, R, Rules, F, Keyphrase).
"""
import pytest

pytestmark = pytest.mark.cham


class TestTuDienKeyphrase:
    """Cấu trúc của từ điển keyphrase."""

    def test_moi_keyphrase_co_ban_khong_dau(self, kb_da_lap_chi_muc):
        """Bản không dấu cho phép người dùng gõ 'vuot den do' vẫn tra được."""
        thieu = [k.cum_tu for k in kb_da_lap_chi_muc.keyphrases if not k.khong_dau]
        assert thieu == [], f"{len(thieu)} keyphrase thiếu bản không dấu: {thieu[:5]}"

    def test_ban_khong_dau_that_su_khong_con_dau(self, kb_da_lap_chi_muc):
        from tra_cuu_gtdb.reasoning.engine import bo_dau
        sai = [k.cum_tu for k in kb_da_lap_chi_muc.keyphrases[:200]
               if k.khong_dau != bo_dau(k.cum_tu)]
        assert sai == [], f"Bản không dấu không khớp bo_dau(): {sai[:5]}"

    def test_so_tu_khop_voi_cum_tu(self, kb_da_lap_chi_muc):
        """Trường so_tu quyết định thứ tự ưu tiên khi so khớp cụm dài nhất."""
        sai = [k.cum_tu for k in kb_da_lap_chi_muc.keyphrases
               if k.so_tu != len(k.cum_tu.split())]
        assert sai == [], f"so_tu không khớp số từ thực tế: {sai[:5]}"


class TestRutTrichKeyphrase:
    """Rút trích keyphrase từ truy vấn người dùng."""

    def test_uu_tien_cum_dai_nhat(self, he_thong):
        """'nồng độ cồn' phải thắng 'cồn' — nếu không, truy vấn sẽ khớp sai hành vi."""
        Q = he_thong.engine.analyzer.analyze("nồng độ cồn bao nhiêu thì bị phạt")
        cum = [k["cum_tu"] for k in Q["keyphrase"]]
        assert "nồng độ cồn" in cum, f"Không bắt được cụm dài: {cum}"
        assert "cồn" not in cum, (
            f"Bắt cả cụm ngắn lồng trong cụm dài — so khớp cụm dài nhất bị hỏng: {cum}")

    def test_cum_dai_nhat_phu_dung_vi_tri_trong_truy_van(self, he_thong):
        """vi_tri = [đầu, cuối) theo chỉ số từ. 'nồng độ cồn' phải chiếm trọn 3 từ đầu."""
        Q = he_thong.engine.analyzer.analyze("nồng độ cồn bao nhiêu thì bị phạt")
        kp = next(k for k in Q["keyphrase"] if k["cum_tu"] == "nồng độ cồn")
        assert tuple(kp["vi_tri"]) == (0, 3), f"Vị trí sai: {kp['vi_tri']}"

    def test_keyphrase_dan_toi_khai_niem_va_hanh_vi_ung_vien(self, he_thong):
        """Rút trích keyphrase phải kéo theo được tri thức liên quan, nếu không thì
        bước suy diễn phía sau không có gì để làm việc."""
        Q = he_thong.engine.analyzer.analyze("nồng độ cồn bao nhiêu thì bị phạt")
        assert Q["khai_niem"], "Không suy ra được khái niệm nào từ keyphrase"
        assert Q["hanh_vi_ung_vien"], "Không suy ra được hành vi ứng viên nào"

    def test_truy_van_khong_dau_cho_ket_qua_tuong_duong(self, he_thong):
        """Người dùng Việt Nam thường gõ không dấu. Hai cách gõ phải ra cùng lớp bài toán."""
        co_dau = he_thong.hoi("vượt đèn đỏ xe máy phạt bao nhiêu")
        khong_dau = he_thong.hoi("vuot den do xe may phat bao nhieu")
        assert co_dau["lop_bai_toan"] == khong_dau["lop_bai_toan"]
        assert khong_dau["hanh_vi"], "Truy vấn không dấu không trả về hành vi nào"

    def test_truy_van_rong_khong_lam_sap_he_thong(self, he_thong):
        kq = he_thong.hoi("")
        assert isinstance(kq, dict) and "lop_bai_toan" in kq
