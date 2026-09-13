"""Kiểm thử việc xây dựng và rút trích keyphrase.

Đề bài yêu cầu tường minh: "Xây dựng keyphrase trong lĩnh vực."
Đây là thành phần Keyphrase trong mô hình K = (C, R, Rules, F, Keyphrase).
"""
import pytest

pytestmark = pytest.mark.cham


class TestKeyphraseDictionary:
    """Cấu trúc của từ điển keyphrase."""

    def test_every_keyphrase_has_unaccented_form(self, indexed_kb):
        """Bản không dấu cho phép người dùng gõ 'vuot den do' vẫn tra được."""
        missing = [k.phrase for k in indexed_kb.keyphrases if not k.unaccented]
        assert missing == [], f"{len(missing)} keyphrase thiếu bản không dấu: {missing[:5]}"

    def test_unaccented_form_really_has_no_accents(self, indexed_kb):
        from traffic_law.reasoning.engine import strip_accents
        wrong = [k.phrase for k in indexed_kb.keyphrases[:200]
               if k.unaccented != strip_accents(k.phrase)]
        assert wrong == [], f"Bản không dấu không khớp bo_dau(): {wrong[:5]}"

    def test_word_count_matches_phrase(self, indexed_kb):
        """Trường so_tu quyết định thứ tự ưu tiên khi so khớp cụm dài nhất."""
        wrong = [k.phrase for k in indexed_kb.keyphrases
               if k.word_count != len(k.phrase.split())]
        assert wrong == [], f"so_tu không khớp số từ thực tế: {wrong[:5]}"


class TestKeyphraseExtraction:
    """Rút trích keyphrase từ truy vấn người dùng."""

    def test_prefers_longest_phrase(self, system):
        """'nồng độ cồn' phải thắng 'cồn' — nếu không, truy vấn sẽ khớp sai hành vi."""
        Q = system.engine.analyzer.analyze("nồng độ cồn bao nhiêu thì bị phạt")
        cum = [k["phrase"] for k in Q["keyphrase"]]
        assert "nồng độ cồn" in cum, f"Không bắt được cụm dài: {cum}"
        assert "cồn" not in cum, (
            f"Bắt cả cụm ngắn lồng trong cụm dài — so khớp cụm dài nhất bị hỏng: {cum}")

    def test_longest_phrase_spans_correct_position(self, system):
        """vi_tri = [đầu, cuối) theo chỉ số từ. 'nồng độ cồn' phải chiếm trọn 3 từ đầu."""
        Q = system.engine.analyzer.analyze("nồng độ cồn bao nhiêu thì bị phạt")
        kp = next(k for k in Q["keyphrase"] if k["phrase"] == "nồng độ cồn")
        assert tuple(kp["span"]) == (0, 3), f"Vị trí sai: {kp['span']}"

    def test_keyphrase_leads_to_concepts_and_candidate_violations(self, system):
        """Rút trích keyphrase phải kéo theo được tri thức liên quan, nếu không thì
        bước suy diễn phía sau không có gì để làm việc."""
        Q = system.engine.analyzer.analyze("nồng độ cồn bao nhiêu thì bị phạt")
        assert Q["concepts"], "Không suy ra được khái niệm nào từ keyphrase"
        assert Q["candidate_violations"], "Không suy ra được hành vi ứng viên nào"

    def test_unaccented_query_gives_equivalent_result(self, system):
        """Người dùng Việt Nam thường gõ không dấu. Hai cách gõ phải ra cùng lớp bài toán."""
        co_dau = system.ask("vượt đèn đỏ xe máy phạt bao nhiêu")
        unaccented = system.ask("vuot den do xe may phat bao nhieu")
        assert co_dau["problem_class"] == unaccented["problem_class"]
        assert unaccented["violations"], "Truy vấn không dấu không trả về hành vi nào"

    def test_empty_query_does_not_crash(self, system):
        kq = system.ask("")
        assert isinstance(kq, dict) and "problem_class" in kq
