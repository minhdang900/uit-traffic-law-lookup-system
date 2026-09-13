"""
kb_engine.py -- Động cơ suy diễn và tra cứu trên cơ sở tri thức pháp luật
giao thông đường bộ.

Mô hình tri thức:  K = (C, R, Rules, F, Keyphrase)

Thuật giải xử lý truy vấn (QP):
    B1. Chuẩn hoá truy vấn
    B2. Rút trích keyphrase (so khớp cụm dài nhất, có bản không dấu)
    B3. Phân loại lớp bài toán bằng hàm điểm có trọng số
    B4. Xây dựng biểu diễn truy vấn hình thức Q
    B5. Suy diễn / truy hồi trên cơ sở tri thức
    B6. Sinh câu trả lời kèm căn cứ pháp lý và tri thức liên quan
"""
# GHI CHU KIEN TRUC — duong bien kieu du lieu
# Tri thuc di suot tang nay duoi dang MO HINH CO KIEU (Pydantic): kb.violations
# la tuple[ViPham], kb.concepts la tuple[KhaiNiem]... Truy cap bang thuoc tinh
# (v.hanh_vi), khong con v["hanh_vi"].
#
# Chi co DUNG MOT cho chuyen nguoc ve dict: ham _ra_dict(), goi khi TRA KET QUA
# ra ngoai. Ly do la hinh dang dict cua ket qua {"id":..., "diem":...} la hop
# dong cong khai ma giao dien, bo danh gia va bo kiem thu dang doc; doi no la
# mot thay doi pha vo tuong thich, khac han voi viec don dep noi bo.
#
# Cac dict KHAC trong tep nay khong phai tri thuc nen giu nguyen: Q (bieu dien
# truy van), kq (ket qua dang dung), cc/rb (rang buoc rut tu cau hoi), va ban
# ghi keyphrase sau khi da qua _ra_dict().
#
# Buoc chuyen doi nay duoc canh boi ba lop: cong chi so trong CI, anh chup vang
# tests/test_hop_dong_dau_ra.py (13 truy van, khoa ca bo truong cua dict tra
# ve), va 106 test. Ket qua eval sau refactor giong TUNG BYTE ban truoc.
import json
import os
import re
from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from traffic_law.domain.models import Relation
from traffic_law.kb.text import normalise, parse_money, strip_accents
from traffic_law.reasoning.numeric import NumericReasoner

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
KB_DIR = os.path.join(ROOT, "data", "kb")

# --------------------------------------------------------------------------
# Cac lop bai toan he thong giai quyet
# --------------------------------------------------------------------------
P1_KHAI_NIEM = "P1_TRA_CUU_KHAI_NIEM"
P2_QUY_DINH = "P2_TRA_CUU_QUY_DINH"
P3_CHE_TAI = "P3_TRA_CUU_CHE_TAI"
P4_TRA_CUU_NGUOC = "P4_TRA_CUU_NGUOC"
P5_TINH_HUONG = "P5_SUY_DIEN_TINH_HUONG"
P6_CAN_CU = "P6_TRA_CUU_CAN_CU"
P7_LIEN_QUAN = "P7_TRA_CUU_LIEN_QUAN"

# Nguong tin cay toi thieu de mot mau tri thuc duoc BO SUNG vao ket qua khi
# bo giai cua lop bai toan khong tim duoc gi.
#
# Chon bang thuc nghiem tren bo 120 cau hoi chuan va 10 truy van ngoai linh vuc:
#     truy van hop le      : trung vi 0.8625 | phan vi 5% 0.45 | nho nhat 0.30
#     truy van ngoai linh vuc: lon nhat 0.3225
# Nguong 0.40 nam giua hai phan bo: chan 10/10 truy van rac ma van duoi phan vi
# 5% cua truy van hop le. Nguong CHI ap dung cho tri thuc bo sung, khong bao gio
# chan ket qua chinh cua bo giai.
SUPPLEMENT_THRESHOLD = 0.40

PROBLEM_CLASS_NAMES = {
    P1_KHAI_NIEM: "Tra cứu khái niệm / định nghĩa",
    P2_QUY_DINH: "Tra cứu quy định, quy tắc giao thông",
    P3_CHE_TAI: "Tra cứu chế tài (mức phạt) của hành vi vi phạm",
    P4_TRA_CUU_NGUOC: "Tra cứu ngược theo mức phạt / số điểm bị trừ",
    P5_TINH_HUONG: "Suy diễn tình huống nhiều hành vi vi phạm",
    P6_CAN_CU: "Tra cứu theo căn cứ pháp lý (điều - khoản - điểm)",
    P7_LIEN_QUAN: "Tra cứu kiến thức liên quan",
}


# ==========================================================================
# 1. TIEN XU LY NGON NGU
# ==========================================================================






def _to_dict(mau):
    """Chuyển một mô hình tri thức thành ``dict`` để TRẢ RA ngoài.

    Hình dạng dict là hợp đồng công khai: giao diện, bộ đánh giá và bộ kiểm thử
    đều đọc ``x["id"]``, ``x["diem"]``... Bên trong tầng suy diễn thì luôn dùng
    mô hình có kiểu; phép chuyển chỉ xảy ra ở đúng đường biên này.

    Dùng ``mode="json"`` để ngày tháng ra chuỗi, giữ y hệt dạng dữ liệu mà bộ
    đánh giá đã đo được đường cơ sở Top-1 76,67%.
    """
    return mau.model_dump(mode="json")


# ==========================================================================
# 2. CO SO TRI THUC
# ==========================================================================
class IndexedKnowledgeBase:
    """Nạp và lập chỉ mục cho cơ sở tri thức K = (C, R, Rules, F, Keyphrase)."""

    def __init__(self, kb_dir=KB_DIR, co_so=None):
        """Lập chỉ mục cho cơ sở tri thức.

        ĐƯỜNG BIÊN KIỂU DỮ LIỆU
        Tri thức đi suốt tầng này dưới dạng MÔ HÌNH CÓ KIỂU (Pydantic), không
        còn ``dict``. Chỉ khi TRẢ RA cho người gọi mới chuyển thành ``dict``
        (xem ``_ra_dict``), vì hình dạng dict là hợp đồng công khai mà giao
        diện và bộ đánh giá đang đọc.

        ``co_so``  : đối tượng CoSoTriThuc đã kiểm kiểu (đường đi chuẩn)
        ``kb_dir`` : chỉ dùng khi không truyền ``co_so`` — tự nạp từ thư mục.
        """
        if co_so is None:
            from pathlib import Path

            from traffic_law.kb.loader import load_knowledge_base
            co_so = load_knowledge_base(Path(kb_dir))
        self.dir = kb_dir
        self.co_so = co_so

        self.concepts = list(co_so.concepts)      # C
        self.relations = list(co_so.relations)       # R
        self.rules = list(co_so.rules)           # Rules
        self.violations = list(co_so.violations)      # F
        self.keyphrases = list(co_so.keyphrases)  # Keyphrase
        self.documents = list(co_so.documents)
        self.amendments = list(co_so.amendments)
        pl = co_so.taxonomy
        self.field = pl.field
        self.group_name = pl.group_name
        self.vehicle_names = pl.vehicle_names
        self.subject_names = pl.subject_names
        self.synonyms = pl.synonyms
        self._build_index()
        self.numeric = NumericReasoner(self.violations)

    def _load(self, name):
        """Đọc một tệp JSON trong thư mục cơ sở tri thức."""
        with open(os.path.join(self.dir, name), encoding="utf-8") as f:
            return json.load(f)

    # ---------------------------------------------------------------- index
    def _build_index(self):
        """Lập chỉ mục cho cơ sở tri thức: chỉ mục theo định danh, theo nhóm, theo lĩnh vực,
        theo phương tiện và theo điều luật; dựng từ điển keyphrase tra cứu bằng bảng băm;
        dựng đồ thị quan hệ hai chiều; và dựng các không gian véc-tơ TF-IDF phục vụ
        so khớp ngữ nghĩa ở ba mức: hành vi, khái niệm, quy tắc và nhóm tri thức.
        """
        self.by_id = {v.id: v for v in self.violations}
        self.concept_by_id = {c.id: c for c in self.concepts}
        self.rule_by_id = {r.id: r for r in self.rules}

        self.by_nhom = defaultdict(list)
        self.by_linh_vuc = defaultdict(list)
        self.by_phuong_tien = defaultdict(list)
        self.by_dieu = defaultdict(list)
        for v in self.violations:
            self.by_nhom[v.group].append(v)
            self.by_linh_vuc[v.field].append(v)
            for p in v.vehicles:
                self.by_phuong_tien[p].append(v)
            self.by_dieu[(v.citation.documents, v.citation.article)].append(v)

        # tu dien keyphrase: tra cuu theo ban khong dau, uu tien cum dai
        self.kp_index = {}
        for k in self.keyphrases:
            self.kp_index.setdefault(k.unaccented, k)
        self.kp_max_words = max((k.word_count for k in self.keyphrases), default=1)

        # do thi quan he (dung cho goi y tri thuc lien quan)
        self.rel_out = defaultdict(list)
        for r in self.relations:
            self.rel_out[r.source].append(r)
            self.rel_out[r.target].append(
                Relation(name=r.name, relation_kind=r.relation_kind, source=r.target,
                       target=r.source, description=r.description))

        # --- khong gian vector cho so khop ngu nghia (TF-IDF char n-gram) ---
        self.v_corpus = [strip_accents(v.text_search) for v in self.violations]
        self.c_corpus = [strip_accents(c.text_search) for c in self.concepts]
        self.r_corpus = [strip_accents(r.text_search) for r in self.rules]

        self.vec_char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                        min_df=1, sublinear_tf=True)
        self.vec_word = TfidfVectorizer(analyzer="word", ngram_range=(1, 3),
                                        min_df=1, sublinear_tf=True)
        all_corpus = self.v_corpus + self.c_corpus + self.r_corpus
        self.vec_char.fit(all_corpus)
        self.vec_word.fit(all_corpus)

        self.M_v_char = self.vec_char.transform(self.v_corpus)
        self.M_v_word = self.vec_word.transform(self.v_corpus)
        self.M_c_char = self.vec_char.transform(self.c_corpus)
        self.M_c_word = self.vec_word.transform(self.c_corpus)
        self.M_r_char = self.vec_char.transform(self.r_corpus)
        self.M_r_word = self.vec_word.transform(self.r_corpus)

        # --- khong gian vector muc NHOM tri thuc (nhan dien nhom theo ngu nghia) ---
        self.danh_sach_nhom = sorted(self.by_nhom)
        gom = []
        for n in self.danh_sach_nhom:
            txt = [self.group_name.get(n, n)]
            for v in self.by_nhom[n]:
                txt.append(v.behavior)
                txt.extend(v.keyphrases or [])
            gom.append(strip_accents(normalise(" ".join(txt))))
        self.M_nhom_char = self.vec_char.transform(gom)
        self.M_nhom_word = self.vec_word.transform(gom)

        # --- khong gian vector chi tren TEN cua khai niem / quy tac ---
        self.M_c_ten = self.vec_char.transform(
            [strip_accents(normalise(c.name)) for c in self.concepts])
        self.M_r_ten = self.vec_char.transform(
            [strip_accents(normalise(r.name)) for r in self.rules])

    # ------------------------------------------------------------ semantic
    def sim(self, query, kind="violation"):
        """Đo tương đồng ngữ nghĩa giữa truy vấn và từng phần tử tri thức.
        Kết hợp TF-IDF char n-gram (chịu được lỗi chính tả, cách tách từ) với
        word n-gram, và ưu tiên phần khớp với TÊN của khái niệm hoặc quy tắc."""
        q = strip_accents(normalise(query))
        Mc, Mw = {"violation": (self.M_v_char, self.M_v_word),
                  "concept": (self.M_c_char, self.M_c_word),
                  "rule": (self.M_r_char, self.M_r_word)}[kind]
        qv_c = self.vec_char.transform([q])
        sc = cosine_similarity(qv_c, Mc)[0]
        sw = cosine_similarity(self.vec_word.transform([q]), Mw)[0]
        s = 0.5 * sc + 0.5 * sw
        Mt = {"concept": self.M_c_ten, "rule": self.M_r_ten}.get(kind)
        if Mt is not None:                      # uu tien khop voi TEN
            s = 0.6 * s + 0.4 * cosine_similarity(qv_c, Mt)[0]
        return s

    def semantic_groups(self, query, threshold=0.24, toi_da=2):
        """Nhận diện nhóm tri thức theo ngữ nghĩa khi keyphrase không bắt được."""
        q = strip_accents(normalise(query))
        s = (0.5 * cosine_similarity(self.vec_char.transform([q]), self.M_nhom_char)[0]
             + 0.5 * cosine_similarity(self.vec_word.transform([q]), self.M_nhom_word)[0])
        idx = np.argsort(-s)[:toi_da]
        return [(self.danh_sach_nhom[i], float(s[i])) for i in idx if s[i] >= threshold]


# ==========================================================================
# 3. PHAN TICH TRUY VAN
# ==========================================================================
MAU_KHAI_NIEM = [r"\bla gi\b", r"\bnghia la\b", r"\bdinh nghia\b", r"\bkhai niem\b",
                 r"\bhieu the nao\b", r"\bthe nao la\b", r"\bgom nhung gi\b",
                 r"\bbao gom\b", r"\bduoc hieu\b", r"\bkhac nhau (cho nao|the nao|nhu the nao)\b",
                 r"\bphan biet\b", r"\bco phai la\b", r"\bgom nhung loai\b",
                 r"\bco may loai\b", r"\bnghia cua\b", r"\bde lam gi\b",
                 r"\bla sao\b", r"\bnghia la sao\b", r"\b(chay|lai) duoc xe gi\b",
                 r"\bduoc lai xe gi\b", r"\bthoi han bao lau\b", r"\bco thoi han\b",
                 r"\bmay tuoi\b", r"\bbao nhieu tuoi\b", r"\bbao nhieu diem\b",
                 r"\bgoi la gi\b", r"\bduoc goi la\b", r"\bgom nhung xe nao\b"]
MAU_CHE_TAI = [r"\bphat\b", r"\bmuc phat\b", r"\bbao nhieu tien\b", r"\bbi gi\b",
               r"\bxu phat\b", r"\btru.{0,6}diem\b", r"\btuoc\b", r"\btich thu\b",
               r"\bbao nhieu(?!\s+(diem|tuoi|nguoi|lan|thang|nam))\b",
               r"\bgiam xe\b", r"\bnop phat\b", r"\bloi\b",
               r"\bxu ly (sao|the nao|nhu the nao)\b", r"\bthi sao\b", r"\bbi lam sao\b",
               r"\bcanh cao\b", r"\bbi xu\b"]
MAU_QUY_DINH = [r"\bquy dinh\b", r"\bco duoc\b", r"\bduoc phep\b", r"\bcam\b",
                r"\bphai lam gi\b", r"\bco bat buoc\b", r"\bnguyen tac\b", r"\bquy tac\b",
                r"\bthu tuc\b", r"\bdieu kien\b", r"\bkhi nao\b", r"\bnhung cho nao\b",
                r"\bnhung truong hop nao\b", r"\bcho toi da may\b", r"\bngoi o dau\b",
                r"\bco duoc.{0,15}khong\b", r"\bcan phai\b", r"\bthe nao cho dung\b",
                r"\bphai lam sao\b", r"\bmay gio\b", r"\bduoc may nguoi\b",
                r"\bcho duoc may\b", r"\bbao lau\b", r"\bco phai\b.{0,25}\bkhong\b",
                r"\bphai mang\b", r"\bnhuong xe nao\b", r"\bphai bat\b",
                r"\bbat buoc\b", r"\bthi phai\b", r"\bcan mang\b", r"\bgiay to gi\b",
                r"\bphuc hoi\b", r"\bduoc chay\b", r"\bco duoc di\b"]
MAU_TRA_CUU_NGUOC = [r"\b(loi|hanh vi|vi pham)\s+(nao|gi)\b", r"\bnhung loi\b",
                     r"\bcac loi\b", r"\bdanh sach\b", r"\bliet ke\b", r"\btren \d",
                     r"\bcao nhat\b", r"\bnang nhat\b", r"\bbi tru \d+ diem\b",
                     r"\bnao bi\b", r"\bnao thi bi\b", r"\bco loi nao\b",
                     r"\bnhung hanh vi\b", r"\bnao chi bi\b"]
MAU_CAN_CU = [r"\bđiều\s+\d+", r"\bkhoản\s+\d+", r"\bđiểm\s+[a-zđ]\b\s*khoản"]
MAU_TINH_HUONG = [r"\btoi\b", r"\bem\b", r"\bminh\b", r"\bcsgt\b", r"\bcanh sat\b",
                  r"\bvua\b.{0,25}\bvua\b", r"\bdong thoi\b", r"\bbi bat\b",
                  r"\bhom qua\b", r"\btoi qua\b", r"\bva lai\b", r"\blai con\b",
                  r"\btong cong\b", r"\btong muc phat\b", r"\btong so tien\b",
                  r"\banh toi\b", r"\bban toi\b", r"\bluc do\b", r"\bcung luc\b",
                  r"\bthem nua\b", r"\bnua\b"]


class QueryAnalyzer:
    """Phân tích truy vấn ngôn ngữ tự nhiên thành biểu diễn hình thức."""

    def __init__(self, kb: IndexedKnowledgeBase):
        """Khởi tạo bộ phân tích truy vấn trên một cơ sở tri thức đã nạp."""
        self.kb = kb

    # ---------------------------------------------------------- keyphrase
    def extract_keyphrases(self, text):
        """So khớp cụm dài nhất trên từ điển keyphrase (bản không dấu).
        Trả về danh sách bản ghi keyphrase, không chồng lấn."""
        toks = strip_accents(normalise(text)).split()
        n = len(toks)
        i, found = 0, []
        max_w = min(self.kb.kp_max_words, 8)
        while i < n:
            matched = False
            for w in range(min(max_w, n - i), 0, -1):
                cand = " ".join(toks[i:i + w])
                kp = self.kb.kp_index.get(cand)
                if kp is not None and (w > 1 or len(cand) >= 4):
                    found.append({**_to_dict(kp), "span": (i, i + w)})
                    i += w
                    matched = True
                    break
            if not matched:
                i += 1
        return found

    # --------------------------------------------------------- phuong tien
    def detect_vehicles(self, text):
        """Nhận diện loại phương tiện được nhắc tới trong câu hỏi dựa trên bảng từ khoá
        (bao gồm cả cách gọi đời thường như xe hơi, bốn bánh, kẹp ba).
        """
        t = strip_accents(normalise(text))
        pt = set()
        table = {
            "o_to": ["o to", "oto", "xe hoi", "xe con", "xe tai", "xe khach", "xe ban tai",
                     "bon banh", "4 banh", "xe 4 cho", "xe 7 cho", "container", "xe buyt"],
            "mo_to": ["mo to", "xe may", "xe gan may", "xe 2 banh", "hai banh", "honda",
                      "wave", "sh ", "vision", "exciter", "xe con tay"],
            "xe_gan_may": ["xe gan may", "xe 50cc", "xe may 50"],
            "xe_dap": ["xe dap", "xe dap dien", "xe dap may", "xe dien"],
            "xe_tho_so": ["xe tho so", "xich lo", "xe ba gac", "xe suc vat keo"],
            "xe_may_chuyen_dung": ["xe may chuyen dung", "may keo", "xe cong trinh",
                                   "xe lu", "may xuc"],
        }
        for k, kws in table.items():
            if any(kw in t for kw in kws):
                pt.add(k)
        if "mo_to" in pt and "xe_gan_may" not in pt:
            pt.add("xe_gan_may")
        return sorted(pt)

    # ---------------------------------------------------------- chu the
    def detect_subject(self, text):
        """Nhận diện chủ thể của hành vi: người điều khiển, chủ phương tiện,
        người đi bộ hay hành khách."""
        t = strip_accents(normalise(text))
        if any(k in t for k in ["nguoi di bo", "di bo", "khach bo hanh"]):
            return "nguoi_di_bo"
        if any(k in t for k in ["chu xe", "chu phuong tien", "chu so huu"]):
            return "chu_phuong_tien"
        if any(k in t for k in ["hanh khach", "nguoi ngoi tren xe", "nguoi duoc cho"]):
            return "hanh_khach"
        return None

    # ------------------------------------------------------- can cu phap ly
    def detect_citation(self, text):
        """Nhận diện căn cứ pháp lý (điều - khoản - điểm và số hiệu văn bản) nếu người dùng
        hỏi trực tiếp theo căn cứ.
        """
        t = normalise(text)
        cc = {}
        m = re.search(r"điều\s+(\d+)", t)
        if m:
            cc["article"] = int(m.group(1))
        m = re.search(r"khoản\s+(\d+[a-zđ]?)", t)
        if m:
            cc["clause"] = m.group(1)
        m = re.search(r"điểm\s+([a-zđ])\b", t)
        if m:
            cc["point"] = m.group(1)
        if "168" in t:
            cc["documents"] = "Nghị định 168/2024/NĐ-CP"
        elif "36/2024" in t or "luật" in t:
            cc["documents"] = "Luật 36/2024/QH15"
        return cc if "article" in cc else None

    # ------------------------------------------------------- rang buoc so
    def detect_constraints(self, text):
        """Nhận diện các ràng buộc định lượng trong câu hỏi: số điểm bị trừ, khoảng tiền phạt,
        hình phạt bổ sung (tịch thu, tước giấy phép lái xe), trường hợp chỉ bị cảnh cáo,
        và yêu cầu sắp xếp (cao nhất, thấp nhất).
        """
        t = normalise(text)
        rb = {}
        m = re.search(r"trừ\s*(?:tới|đến|tận|hết)?\s*(\d+)\s*điểm", t)
        if m:
            rb["tru_diem"] = int(m.group(1))
        # khoang tien "tu X den Y"
        m = re.search(r"từ\s*([\d.,]+)\s*(triệu|nghìn|ngàn|đồng)?\s*(?:đồng)?\s*"
                      r"(?:đến|tới|-)\s*([\d.,]+)\s*(triệu|nghìn|ngàn|đồng)"
                      r"(?!\s*tháng)", t)
        if m:
            dv = m.group(2) or m.group(4) or "đồng"
            a = parse_money("%s %s" % (m.group(1), dv))
            b = parse_money("%s %s" % (m.group(3), m.group(4) or dv))
            if a and b:
                rb["tien_khoang"] = (a[0], b[0])
        else:
            tien = parse_money(t)
            if tien:
                if re.search(r"\b(trên|hơn|lớn hơn|từ)\b", t):
                    rb["tien_min"] = max(tien)
                if re.search(r"\b(dưới|nhỏ hơn|không quá|đến)\b", t):
                    rb["tien_max"] = max(tien)
        if re.search(r"tịch thu", t):
            rb["extra_penalties"] = "tịch thu"
        m = re.search(r"tước.{0,20}?(\d+)\s*(?:tháng)?\s*(?:đến|tới|-)\s*(\d+)\s*tháng", t)
        if m:
            rb["extra_penalties"] = "%s tháng đến %s tháng" % (m.group(1), m.group(2))
        elif re.search(r"\btước\b", t):
            rb["extra_penalties"] = "tước"
        if re.search(r"cảnh cáo", t):
            rb["chi_canh_cao"] = True
        if re.search(r"\b(cao nhất|nặng nhất|lớn nhất|kịch khung)\b", t):
            rb["sap_xep"] = "giam_dan"
        if re.search(r"\b(thấp nhất|nhẹ nhất|nhỏ nhất)\b", t):
            rb["sap_xep"] = "tang_dan"
        return rb

    # --------------------------------------------------- lop bai toan
    def classify_problem(self, text, kps, rang_buoc, citation, nhom_tap=frozenset()):
        """Phân loại câu hỏi vào một trong bảy lớp bài toán bằng hàm điểm có trọng số trên hai
        nhóm đặc trưng: đặc trưng ngôn ngữ (số mẫu nghi vấn khớp được) và đặc trưng tri thức
        (số khái niệm, quy tắc, nhóm nhận diện được và sự tồn tại của ràng buộc định lượng).
        Mỗi nhóm đặc trưng được chặn trần để một lớp không áp đảo chỉ vì câu hỏi dài.
        """
        t = strip_accents(normalise(text))

        def hit(pats):
            return sum(1 for p in pats if re.search(p, t))

        if citation:
            return P6_CAN_CU
        s_nguoc = hit(MAU_TRA_CUU_NGUOC) + (2 if rang_buoc else 0)
        s_che_tai = hit(MAU_CHE_TAI)
        s_khai_niem = hit(MAU_KHAI_NIEM)
        s_quy_dinh = hit(MAU_QUY_DINH)
        s_tinh_huong = hit(MAU_TINH_HUONG)

        n_nhom = len({n for n in nhom_tap if n != "khac"})
        n_kn = len({c for k in kps for c in k["concept_ids"]})
        n_qt = len({r for k in kps for r in k["rule_ids"]})
        co_tong = bool(re.search(r"\b(tong cong|tong muc|tong so|tong hop|tong)\b", t))

        # chan tran dong gop cua tung nhom dac trung de mot lop khong ap dao
        c_kn = min(s_khai_niem, 2)
        c_ct = min(s_che_tai, 2)
        c_qd = min(s_quy_dinh, 2)
        c_ng = min(s_nguoc, 2)
        c_th = min(s_tinh_huong, 3)

        # P5 la lop co DIEU KIEN CAN: >= 2 nhom tri thuc khac nhau (bo qua 'khac')
        du_dieu_kien_p5 = n_nhom >= 2 and (c_ct >= 1 or co_tong)

        point = {
            P1_KHAI_NIEM: 2.0 * c_kn + 0.7 * min(n_kn, 2) - 1.5 * c_ct - 1.2 * c_ng,
            P2_QUY_DINH: 1.7 * c_qd + 0.6 * min(n_qt, 2) - 1.3 * c_ct - 0.9 * c_kn,
            P3_CHE_TAI: 1.8 * c_ct + 0.4 * min(n_nhom, 2) - 0.9 * c_kn,
            P4_TRA_CUU_NGUOC: 1.9 * c_ng + 1.8 * bool(rang_buoc) + 0.6 * c_ct
                              - 1.5 * c_th,
            P5_TINH_HUONG: (4.3 + 0.7 * c_th + 1.2 * co_tong + 0.8 * (n_nhom >= 3)
                            if du_dieu_kien_p5 else 0.0),
            P7_LIEN_QUAN: 0.9,
        }
        return max(point, key=lambda k: point[k])

    # -------------------------------------------------------------- main
    def analyze(self, text):
        """Thực hiện các bước B1 đến B4 của thuật giải xử lý truy vấn và trả về biểu diễn
        hình thức Q của câu hỏi.
        """
        kps = self.extract_keyphrases(text)
        citation = self.detect_citation(text)
        rang_buoc = self.detect_constraints(text)

        nhom_kp = ({n for k in kps for n in k["group"]}
                   | {self.kb.by_id[h].group for k in kps for h in k["violation_ids"]
                      if h in self.kb.by_id})
        nhom_nn = self.kb.semantic_groups(text)
        nhom_tap = nhom_kp | ({n for n, _ in nhom_nn} if nhom_kp else
                              {n for n, _ in nhom_nn[:1]})
        kind = self.classify_problem(text, kps, rang_buoc, citation, nhom_tap)
        pt = self.detect_vehicles(text)
        value, id_thoa, giai_thich = self.kb.numeric.infer(text, pt, self.kb.by_id)
        return {
            "raw_query": text,
            "normalised_query": normalise(text),
            "problem_class": kind,
            "problem_class_name": PROBLEM_CLASS_NAMES[kind],
            "keyphrase": kps,
            "concepts": sorted({c for k in kps for c in k["concept_ids"]}),
            "group": sorted(nhom_kp),
            "semantic_groups": [{"group": n, "score": round(d, 4)} for n, d in nhom_nn],
            "inferred_groups": sorted(nhom_tap),
            "rules": sorted({r for k in kps for r in k["rule_ids"]}),
            "candidate_violations": sorted({h for k in kps for h in k["violation_ids"]}),
            "vehicles": pt,
            "subject": self.detect_subject(text),
            "numeric_values": value,
            "violations_in_range": sorted(id_thoa) if id_thoa else [],
            "numeric_explanation": giai_thich,
            "citation": citation,
            "rang_buoc": rang_buoc,
        }


# ==========================================================================
# 4. DONG CO SUY DIEN
# ==========================================================================
class InferenceEngine:
    """Suy diễn / truy hồi trên cơ sở tri thức theo từng lớp bài toán."""

    # trong so cua do do lai
    ALPHA = 0.55   # keyphrase (tri thuc)
    BETA = 0.30    # ngu nghia (TF-IDF)
    GAMMA = 0.15   # khai niem / nhom / phuong tien

    def __init__(self, kb: IndexedKnowledgeBase):
        """Khởi tạo động cơ suy diễn cùng bộ phân tích truy vấn tương ứng."""
        self.kb = kb
        self.analyzer = QueryAnalyzer(kb)

    # ------------------------------------------------------------- ranking
    def _rank_violations(self, Q, ung_vien=None, top_k=10):
        """Xếp hạng các hành vi vi phạm theo độ đo lai
        score = ALPHA*keyphrase + BETA*ngữ nghĩa + GAMMA*ngữ cảnh,
        có tích hợp kết quả suy diễn số học (chọn đúng khung xử phạt) và các heuristic
        loại trừ hành vi 'không chấp hành yêu cầu kiểm tra' khi câu hỏi không nhắc tới.
        """
        kb = self.kb
        sem = kb.sim(Q["raw_query"], "violation")
        sem = sem / (sem.max() + 1e-9)

        nhom_q = set(Q["group"])
        pt_q = set(Q["vehicles"])
        hv_q = set(Q["candidate_violations"])
        chu_the_q = Q["subject"]
        so_thoa = set(Q.get("violations_in_range") or [])
        co_nguong = set(kb.numeric.threshold)
        # nguoi hoi co nhac den viec tu choi / khong chap hanh kiem tra hay khong?
        t_plain = strip_accents(Q["normalised_query"])
        hoi_ve_tu_choi = any(k in t_plain for k in
                             ["khong chap hanh", "tu choi", "khong thoi", "khong hop tac",
                              "chong doi", "khong cho kiem tra"])

        results = []
        for i, v in enumerate(kb.violations):
            if ung_vien is not None and v.id not in ung_vien:
                continue

            # --- diem keyphrase (tri thuc) ---
            s_kp = 0.0
            if v.id in hv_q:
                s_kp += 1.0
            if v.group in nhom_q:
                s_kp += 0.75
            elif nhom_q:
                s_kp -= 0.30          # lech nhom tri thuc -> ha diem
            s_kp = min(s_kp, 1.0)

            # --- suy dien so hoc: chon dung khung xu phat ---
            if so_thoa:
                if v.id in so_thoa:
                    s_kp = 1.0
                elif v.id in co_nguong and v.group in nhom_q:
                    s_kp -= 1.0       # cung dai luong nhung sai khung -> loai

            # --- khong neu gia tri cu the -> uu tien khung thap nhat ---
            if not so_thoa and v.id in co_nguong and v.group in nhom_q:
                if all((n.get("lower") or 0) <= 0 for n in kb.numeric.threshold[v.id]):
                    s_kp += 0.25
                else:
                    s_kp -= 0.10

            # --- heuristic: hanh vi 'khong chap hanh yeu cau kiem tra' ---
            if ("khong chap hanh yeu cau kiem tra" in strip_accents(v.behavior)
                    and not hoi_ve_tu_choi):
                s_kp -= 0.55

            # --- diem khai niem / phuong tien / chu the ---
            s_cx = 0.0
            if pt_q:
                if pt_q & set(v.vehicles):
                    s_cx += 1.0
                else:
                    s_cx -= 1.2          # phat nang neu sai phuong tien
            if chu_the_q:
                s_cx += 0.6 if v.subject == chu_the_q else -0.6
            elif v.subject == "nguoi_dieu_khien":
                s_cx += 0.15
            s_cx = max(min(s_cx, 1.0), -1.5)

            score = self.ALPHA * s_kp + self.BETA * sem[i] + self.GAMMA * s_cx
            if v.status == "da_sua_doi":
                score += 0.02        # uu tien quy dinh moi nhat
            if score > 0.05:
                results.append((score, v, {"keyphrase": s_kp, "ngu_nghia": float(sem[i]),
                                           "ngu_canh": s_cx}))
        results.sort(key=lambda x: -x[0])
        return results[:top_k]

    def _rank(self, Q, kind, items, top_k=5):
        """Xếp hạng khái niệm hoặc quy tắc: cộng điểm ưu tiên nếu phần tử được keyphrase trỏ
        trực tiếp, cộng điểm tương đồng ngữ nghĩa cho phần còn lại.
        """
        sem = self.kb.sim(Q["raw_query"], kind)
        sem = sem / (sem.max() + 1e-9)
        uu_tien = set(Q["concepts"]) if kind == "concept" else set(Q["rules"])
        out = []
        for i, it in enumerate(items):
            s = self.BETA * sem[i] + (self.ALPHA if it.id in uu_tien else 0.0)
            if s > 0.03:
                out.append((s, it))
        out.sort(key=lambda x: -x[0])
        return out[:top_k]

    # ------------------------------------------------------- tri thuc lien quan
    def related_knowledge(self, Q, ket_qua_hanh_vi, gioi_han=6):
        """Duyệt đồ thị quan hệ R từ các nhóm tri thức liên quan tới kết quả để gợi ý
        các mảng kiến thức lân cận cho người dùng.
        """
        kb, goi_y = self.kb, []
        seen = set()
        nhom_lq = set()
        for _, v, _ in ket_qua_hanh_vi[:3]:
            nhom_lq.add("NHOM_%s" % v.group.upper())
        for c_id in Q["concepts"]:
            nhom_lq.update(r.target for r in kb.rel_out.get(c_id, [])
                           if r.target.startswith("NHOM_"))
        for node in nhom_lq:
            for r in kb.rel_out.get(node, []):
                if not r.target.startswith("NHOM_"):
                    continue
                group = r.target[5:].lower()
                if group in seen or group not in kb.by_nhom:
                    continue
                seen.add(group)
                goi_y.append({"kind": "group", "code": group,
                              "name": kb.group_name.get(group, group),
                              "so_quy_dinh": len(kb.by_nhom[group]),
                              "relations": r.name})
                if len(goi_y) >= gioi_han:
                    return goi_y
        return goi_y

    # ============================================================ tra loi
    def answer(self, question, top_k=5):
        """Điểm vào chính của động cơ suy diễn: phân tích câu hỏi, điều phối sang bộ giải của
        lớp bài toán tương ứng, bổ sung đủ ba loại tri thức (khái niệm, quy tắc, chế tài)
        để kết quả không phụ thuộc hoàn toàn vào bước phân loại, rồi tổng hợp căn cứ pháp lý
        và tri thức liên quan.
        """
        Q = self.analyzer.analyze(question)
        kind = Q["problem_class"]
        kq = {"analysis": Q, "problem_class": kind,
              "problem_class_name": PROBLEM_CLASS_NAMES[kind],
              "concepts": [], "rules": [], "violations": [],
              "summary": None, "related": [], "citation": [],
              "not_found": False}

        if kind == P6_CAN_CU:
            self._giai_P6(Q, kq)
        elif kind == P1_KHAI_NIEM:
            self._giai_P1(Q, kq, top_k)
        elif kind == P2_QUY_DINH:
            self._giai_P2(Q, kq, top_k)
        elif kind == P3_CHE_TAI:
            self._giai_P3(Q, kq, top_k)
        elif kind == P4_TRA_CUU_NGUOC:
            self._giai_P4(Q, kq, top_k)
        elif kind == P5_TINH_HUONG:
            self._giai_P5(Q, kq)
        else:
            self._giai_P7(Q, kq, top_k)

        # --- bo sung: luon co san ca 3 loai tri thuc (khai niem / quy tac / che tai)
        #     de ket qua khong phu thuoc hoan toan vao buoc phan loai lop bai toan ---
        if not kq["violations"]:
            bs = [(sc, v, d) for sc, v, d in self._rank_violations(Q, top_k=3)
                  if sc >= SUPPLEMENT_THRESHOLD]
            kq["_raw_hv"] = bs
            kq["violations"] = [{**_to_dict(v), "score": round(sc, 4), "score_detail": d,
                              "supplementary": True} for sc, v, d in bs]
        if not kq["concepts"]:
            kq["concepts"] = [{**_to_dict(c), "score": round(sc, 4), "supplementary": True}
                               for sc, c in self._rank(Q, "concept",
                                                           self.kb.concepts, 2)
                               if sc >= SUPPLEMENT_THRESHOLD]
        if not kq["rules"]:
            kq["rules"] = [{**_to_dict(r), "score": round(sc, 4), "supplementary": True}
                             for sc, r in self._rank(Q, "rule",
                                                         self.kb.rules, 2)
                             if sc >= SUPPLEMENT_THRESHOLD]

        # Khong con tri thuc nao vuot nguong -> he thong thua nhan khong tra duoc,
        # thay vi tra ve mot danh sach hanh vi vi pham khong lien quan.
        kq["not_found"] = not (kq["concepts"] or kq["rules"] or kq["violations"])

        kq["related"] = self.related_knowledge(Q, kq.get("_raw_hv", []))
        kq.pop("_raw_hv", None)
        kq["citation"] = sorted({v["citation_text"] for v in kq["violations"]}
                              | {c["citation_text"] for c in kq["concepts"]}
                              | {r["citation_text"] for r in kq["rules"]})
        return kq

    # ---------------------------------------------------------------- P1
    def _giai_P1(self, Q, kq, top_k):
        """Giải lớp P1 - tra cứu khái niệm: xếp hạng và trả về các khái niệm phù hợp."""
        for s, c in self._rank(Q, "concept", self.kb.concepts, top_k):
            kq["concepts"].append({**_to_dict(c), "score": round(s, 4)})
        if not kq["concepts"]:
            self._giai_P7(Q, kq, top_k)

    # ---------------------------------------------------------------- P2
    def _giai_P2(self, Q, kq, top_k):
        """Giải lớp P2 - tra cứu quy định: trả về quy tắc giao thông kèm nguyên văn, bổ sung
        khái niệm và một vài chế tài liên quan.
        """
        for s, r in self._rank(Q, "rule", self.kb.rules, top_k):
            kq["rules"].append({**_to_dict(r), "score": round(s, 4)})
        for s, c in self._rank(Q, "concept", self.kb.concepts, 2):
            kq["concepts"].append({**_to_dict(c), "score": round(s, 4)})
        hv = self._rank_violations(Q, top_k=3)
        kq["_raw_hv"] = hv
        kq["violations"] = [{**_to_dict(v), "score": round(s, 4), "score_detail": d}
                            for s, v, d in hv]

    # ---------------------------------------------------------------- P3
    def _giai_P3(self, Q, kq, top_k):
        """Giải lớp P3 - tra cứu chế tài: trả về các hành vi vi phạm kèm mức phạt và căn cứ."""
        hv = self._rank_violations(Q, top_k=top_k)
        kq["_raw_hv"] = hv
        kq["violations"] = [{**_to_dict(v), "score": round(s, 4), "score_detail": d}
                            for s, v, d in hv]
        for s, c in self._rank(Q, "concept", self.kb.concepts, 2):
            kq["concepts"].append({**_to_dict(c), "score": round(s, 4)})

    # ---------------------------------------------------------------- P4
    def _giai_P4(self, Q, kq, top_k):
        """Giải lớp P4 - tra cứu ngược: lọc toàn bộ tập sự kiện F theo các ràng buộc định lượng
        (số điểm trừ, khoảng tiền, hình phạt bổ sung, chỉ cảnh cáo) rồi sắp xếp kết quả.
        Khi đã có ràng buộc định lượng, nhóm tri thức chỉ dùng để ưu tiên chứ không lọc cứng.
        """
        rb = Q["rang_buoc"]
        pt_q = set(Q["vehicles"])
        nhom_q = set(Q["group"])
        # khi truy van da co rang buoc dinh luong (so tien / diem tru / hinh phat bo sung)
        # thi KHONG loc cung theo nhom -- nhom chi dung de sap xep uu tien
        loc_nhom = bool(nhom_q) and not rb
        ds = []
        for v in self.kb.violations:
            if pt_q and not (pt_q & set(v.vehicles)):
                continue
            if loc_nhom and v.group not in nhom_q:
                continue
            if "tru_diem" in rb and (v.licence_points or 0) != rb["tru_diem"]:
                continue
            mn, mx = v.fine.min, v.fine.max
            if "tien_khoang" in rb:
                a, b = rb["tien_khoang"]
                if mn != a or mx != b:
                    continue
            if "tien_min" in rb and (mx is None or mx < rb["tien_min"]):
                continue
            if "tien_max" in rb and (mn is None or mn > rb["tien_max"]):
                continue
            if "extra_penalties" in rb:
                bs = strip_accents(" ".join(v.extra_penalties))
                if strip_accents(rb["extra_penalties"]) not in bs:
                    continue
            if rb.get("chi_canh_cao") and not (mn in (0, None) and mx in (0, None)):
                continue
            if Q["subject"] and v.subject != Q["subject"]:
                continue
            ds.append(v)
        rev = rb.get("sap_xep", "giam_dan") != "tang_dan"
        ds.sort(key=lambda v: (v.fine.max or 0,
                               v.licence_points or 0), reverse=rev)
        if nhom_q:   # uu tien cac hanh vi dung nhom tri thuc nguoi dung hoi
            ds.sort(key=lambda v: v.group not in nhom_q)
        gh = 20 if (rb or nhom_q or pt_q) else top_k
        kq["violations"] = [{**_to_dict(v), "score": 1.0} for v in ds[:gh]]
        kq["summary"] = {"kind": "danh_sach", "tong_so": len(ds), "hien_thi": len(kq["violations"])}
        kq["_raw_hv"] = [(1.0, v, {}) for v in ds[:3]]

    # ---------------------------------------------------------------- P5
    def _giai_P5(self, Q, kq):
        """Giải lớp P5 - suy diễn tình huống: mỗi nhóm tri thức nhận diện được ứng với
        một hành vi vi phạm, sau đó tổng hợp mức phạt và số điểm bị trừ."""
        chon = []
        uu_tien = Q["group"] or Q["inferred_groups"]
        for group in (uu_tien + [n for n in Q["inferred_groups"] if n not in uu_tien]):
            Qn = dict(Q)
            Qn["group"] = [group]
            ung_vien = {v.id for v in self.kb.by_nhom.get(group, [])}
            if not ung_vien:
                continue
            best = self._rank_violations(Qn, ung_vien=ung_vien, top_k=1)
            if best:
                chon.append(best[0])
        if not chon:
            chon = self._rank_violations(Q, top_k=3)
        kq["_raw_hv"] = chon
        kq["violations"] = [{**_to_dict(v), "score": round(s, 4), "score_detail": d}
                         for s, v, d in chon]

        tien_min = sum((v.fine.min or 0) for _, v, _ in chon)
        tien_max = sum((v.fine.max or 0) for _, v, _ in chon)
        point = sum((v.licence_points or 0) for _, v, _ in chon)
        supplementary = [b for _, v, _ in chon for b in v.extra_penalties]
        warnings = []
        for _, v, _ in chon:
            if v.id in self.kb.numeric.threshold and not Q.get("numeric_values"):
                warnings.append(
                    "Hành vi \"%s\" được phân mức theo giá trị đo được; "
                    "hệ thống đang lấy khung thấp nhất. Nêu rõ giá trị cụ thể "
                    "để có kết quả chính xác." % v.behavior[:70])
        kq["summary"] = {
            "kind": "tinh_huong", "so_hanh_vi": len(chon), "warnings": warnings,
            "tong_phat_tien": {"min": tien_min, "max": tien_max},
            "tong_tru_diem": point,
            "canh_bao_het_diem": point >= 12,
            "extra_penalties": supplementary,
        }

    # ---------------------------------------------------------------- P6
    def _giai_P6(self, Q, kq):
        """Giải lớp P6 - tra cứu theo căn cứ pháp lý: trả về mọi quy định tại điều - khoản - điểm
        mà người dùng chỉ định.
        """
        cc = Q["citation"]
        ds = []
        for v in self.kb.violations:
            c = v.citation
            if c.article != cc.get("article"):
                continue
            if cc.get("documents") and cc["documents"] != c.documents:
                continue
            if "clause" in cc and str(c.clause) != str(cc["clause"]):
                continue
            if "point" in cc and str(c.point) != str(cc["point"]):
                continue
            ds.append(v)
        kq["violations"] = [{**_to_dict(v), "score": 1.0} for v in ds[:30]]
        for r in self.kb.rules:
            c = r.citation
            if c.article == cc.get("article") and "Luật" in str(c.documents):
                if "clause" in cc and str(c.clause) != str(cc["clause"]):
                    continue
                kq["rules"].append({**_to_dict(r), "score": 1.0})
        kq["summary"] = {"kind": "citation", "tong_so": len(ds)}
        kq["_raw_hv"] = [(1.0, v, {}) for v in ds[:3]]

    # ---------------------------------------------------------------- P7
    def _giai_P7(self, Q, kq, top_k):
        """Giải lớp P7 - tra cứu kiến thức liên quan: trả về đồng thời chế tài, khái niệm và quy tắc
        có liên quan tới câu hỏi.
        """
        hv = self._rank_violations(Q, top_k=top_k)
        kq["_raw_hv"] = hv
        kq["violations"] = [{**_to_dict(v), "score": round(s, 4), "score_detail": d}
                            for s, v, d in hv]
        for s, c in self._rank(Q, "concept", self.kb.concepts, 3):
            kq["concepts"].append({**_to_dict(c), "score": round(s, 4)})
        for s, r in self._rank(Q, "rule", self.kb.rules, 3):
            kq["rules"].append({**_to_dict(r), "score": round(s, 4)})


# ==========================================================================
# 5. SINH CAU TRA LOI DANG VAN BAN
# ==========================================================================
def format_money(n):
    """Định dạng một số tiền sang chuỗi tiếng Việt, ví dụ 6000000 thành '6.000.000 đồng'."""
    if n is None:
        return "—"
    if n == 0:
        return "0 đồng"
    return f"{n:,.0f}".replace(",", ".") + " đồng"


def describe_fine(v):
    """Mô tả mức phạt tiền của một hành vi thành chuỗi đọc được, xử lý cả trường hợp
        không quy định phạt tiền hoặc chỉ phạt cảnh cáo.
    """
    mn, mx = v["fine"].get("min"), v["fine"].get("max")
    if mn is None and mx is None:
        return "Không quy định phạt tiền"
    if mn == mx == 0:
        return "Không phạt tiền (cảnh cáo hoặc hình thức khác)"
    if mn == mx:
        return format_money(mn)
    return "từ %s đến %s" % (format_money(mn), format_money(mx))


def render_answer(kq, kb: IndexedKnowledgeBase):
    """Sinh câu trả lời dạng văn bản thuần từ kết quả suy diễn."""
    L = []
    Q = kq["analysis"]
    L.append("● Lớp bài toán: %s" % kq["problem_class_name"])
    if Q["keyphrase"]:
        L.append("● Keyphrase nhận diện: " + ",".join(
            sorted({k["phrase"] for k in Q["keyphrase"]})))
    if Q["vehicles"]:
        L.append("● Phương tiện: " + ",".join(
            kb.vehicle_names.get(p, p) for p in Q["vehicles"]))
    for g in Q.get("numeric_explanation") or []:
        L.append("● Suy diễn số học: %s" % g)
    L.append("")

    for c in kq["concepts"]:
        L.append("▸ KHÁI NIỆM: %s" % c["name"])
        if c.get("definition"):
            L.append("  %s" % c["definition"])
        elif c.get("attributes"):
            for k, val in list(c["attributes"].items())[:6]:
                L.append("  - %s: %s" % (k, val))
        L.append("  (Căn cứ: %s)" % c["citation_text"])
        L.append("")

    for r in kq["rules"]:
        L.append("▸ QUY ĐỊNH: %s" % r["name"])
        if r.get("text"):
            L.append("  %s" % r["text"][:900])
        else:
            for k in r.get("conclusions", [])[:3]:
                L.append("  - %s" % k)
        L.append("  (Căn cứ: %s)" % r["citation_text"])
        L.append("")

    if kq["violations"]:
        L.append("▸ CHẾ TÀI XỬ PHẠT")
        for i, v in enumerate(kq["violations"], 1):
            L.append("  %d. %s" % (i, v["behavior"]))
            L.append("     • Phương tiện: %s | Chủ thể: %s"
                     % (",".join(kb.vehicle_names.get(p, p) for p in v["vehicles"]),
                        kb.subject_names.get(v["subject"], v["subject"])))
            L.append("     • Phạt tiền: %s" % describe_fine(v))
            if v["fine"].get("note"):
                L.append("       (%s)" % v["fine"]["note"])
            if v.get("licence_points"):
                L.append("     • Trừ %d điểm giấy phép lái xe" % v["licence_points"])
            for b in v.get("extra_penalties", []):
                L.append("     • Hình phạt bổ sung: %s" % b)
            for b in v.get("remedies", []):
                L.append("     • Biện pháp khắc phục: %s" % b)
            L.append("     • Căn cứ: %s" % v["citation_text"])
            if v.get("status") == "da_sua_doi":
                L.append("     • ⚠ Đã được sửa đổi bởi %s" % v.get("amended_by"))
            L.append("")

    th = kq.get("summary")
    if th and th.get("kind") == "tinh_huong":
        L.append("▸ TỔNG HỢP TÌNH HUỐNG (suy diễn %d hành vi vi phạm)" % th["so_hanh_vi"])
        L.append("  • Tổng mức phạt tiền dự kiến: từ %s đến %s"
                 % (format_money(th["tong_phat_tien"]["min"]),
                    format_money(th["tong_phat_tien"]["max"])))
        if th["tong_tru_diem"]:
            L.append("  • Tổng số điểm giấy phép lái xe bị trừ: %d điểm" % th["tong_tru_diem"])
        if th["canh_bao_het_diem"]:
            L.append("  • ⚠ Bị trừ hết 12 điểm — phải kiểm tra kiến thức pháp luật "
                     "về trật tự, an toàn giao thông đường bộ để được phục hồi điểm.")
        for b in th["extra_penalties"]:
            L.append("  • Hình phạt bổ sung: %s" % b)
        for c in th.get("warnings", []):
            L.append("  • ⓘ %s" % c)
        L.append("")
    elif th and th.get("kind") == "danh_sach":
        L.append("▸ Tìm thấy %d quy định thoả điều kiện (hiển thị %d)."
                 % (th["tong_so"], th["hien_thi"]))
        L.append("")

    if kq["related"]:
        L.append("▸ KIẾN THỨC LIÊN QUAN: " + ",".join(
            "%s (%d quy định)" % (g["name"], g["so_quy_dinh"]) for g in kq["related"]))

    if not (kq["concepts"] or kq["rules"] or kq["violations"]):
        L.append("Không tìm thấy quy định phù hợp trong cơ sở tri thức. "
                 "Bạn thử diễn đạt lại câu hỏi hoặc nêu rõ loại phương tiện.")
    return "\n".join(L)


# ==========================================================================
class LawLookup:
    """Lớp mặt tiền (facade) cho toàn hệ thống: nạp tri thức và trả lời câu hỏi."""

    def __init__(self, kb_dir=KB_DIR):
        """Nạp cơ sở tri thức và khởi tạo động cơ suy diễn."""
        self.kb = IndexedKnowledgeBase(kb_dir)
        self.engine = InferenceEngine(self.kb)

    def ask(self, question, top_k=5):
        """Trả lời một câu hỏi và trả về kết quả dạng cấu trúc (dùng cho giao diện và đánh giá)."""
        return self.engine.answer(question, top_k=top_k)

    def ask_text(self, question, top_k=5):
        """Trả lời một câu hỏi và trả về câu trả lời dạng văn bản thuần."""
        return render_answer(self.ask(question, top_k), self.kb)

    def stats(self):
        """Trả về thống kê quy mô của cơ sở tri thức."""
        return {"concepts": len(self.kb.concepts), "relations": len(self.kb.relations),
                "rules": len(self.kb.rules), "violations": len(self.kb.violations),
                "keyphrase": len(self.kb.keyphrases), "documents": len(self.kb.documents)}


if __name__ == "__main__":
    import sys
    sys_ = LawLookup()
    print("Cơ sở tri thức:", sys_.stats())
    q = " ".join(sys.argv[1:]) or "Vượt đèn đỏ xe máy phạt bao nhiêu tiền?"
    print("\nCÂU HỎI:", q, "\n" + "-" * 70)
    print(sys_.ask_text(q))
