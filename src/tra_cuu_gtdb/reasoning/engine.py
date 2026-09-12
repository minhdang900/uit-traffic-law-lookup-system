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
# Tang kb/ nap va kiem kieu bang Pydantic. Tang nay nhan lai dang dict qua
# model_dump() de giu NGUYEN VAN thuat giai da do duoc Top-1 76,67%. Viec
# chuyen loi suy dien sang truy cap thuoc tinh la mot buoc refactor RIENG,
# chi nen lam khi da co cong chi so canh giu trong CI.
import json
import os
import re
from collections import defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from tra_cuu_gtdb.kb.text import bo_dau, chuan_hoa, tach_so_tien
from tra_cuu_gtdb.reasoning.numeric import NumericReasoner

GOC = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
KB_DIR = os.path.join(GOC, "data", "kb")

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
NGUONG_BO_SUNG = 0.40

TEN_LOP_BAI_TOAN = {
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






# ==========================================================================
# 2. CO SO TRI THUC
# ==========================================================================
class KnowledgeBase:
    """Nạp và lập chỉ mục cho cơ sở tri thức K = (C, R, Rules, F, Keyphrase)."""

    def __init__(self, kb_dir=KB_DIR, co_so=None):
        """Lập chỉ mục cho cơ sở tri thức.

        ĐƯỜNG BIÊN KIỂU DỮ LIỆU (có chủ đích, xem ghi chú đầu module):
        tầng ``kb`` nạp và kiểm kiểu bằng Pydantic; tầng suy diễn này nhận lại
        dạng ``dict`` qua ``model_dump()``. Nhờ đó toàn bộ thuật giải xếp hạng
        và suy diễn được giữ NGUYÊN VĂN so với bản đã đo Top-1 76,67%.

        ``co_so``  : đối tượng CoSoTriThuc đã kiểm kiểu (đường đi chuẩn)
        ``kb_dir`` : chỉ dùng khi không truyền ``co_so`` — tự nạp từ thư mục.
        """
        if co_so is None:
            from pathlib import Path

            from tra_cuu_gtdb.kb.loader import nap_co_so_tri_thuc
            co_so = nap_co_so_tri_thuc(Path(kb_dir))
        self.dir = kb_dir
        self.co_so = co_so

        def _bo(tap):
            return [x.model_dump(mode="json") for x in tap]

        self.concepts = _bo(co_so.khai_niem)      # C
        self.relations = _bo(co_so.quan_he)       # R
        self.rules = _bo(co_so.quy_tac)           # Rules
        self.violations = _bo(co_so.vi_pham)      # F
        self.keyphrases = _bo(co_so.cum_tu_khoa)  # Keyphrase
        self.documents = _bo(co_so.van_ban)
        self.amendments = _bo(co_so.sua_doi)
        pl = co_so.phan_loai
        self.linh_vuc = pl.linh_vuc
        self.ten_nhom = pl.ten_nhom
        self.ten_phuong_tien = pl.ten_phuong_tien
        self.ten_chu_the = pl.ten_chu_the
        self.dong_nghia = pl.dong_nghia
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
        self.by_id = {v["id"]: v for v in self.violations}
        self.concept_by_id = {c["id"]: c for c in self.concepts}
        self.rule_by_id = {r["id"]: r for r in self.rules}

        self.by_nhom = defaultdict(list)
        self.by_linh_vuc = defaultdict(list)
        self.by_phuong_tien = defaultdict(list)
        self.by_dieu = defaultdict(list)
        for v in self.violations:
            self.by_nhom[v["nhom"]].append(v)
            self.by_linh_vuc[v["linh_vuc"]].append(v)
            for p in v["phuong_tien"]:
                self.by_phuong_tien[p].append(v)
            self.by_dieu[(v["can_cu"].get("van_ban"), v["can_cu"].get("dieu"))].append(v)

        # tu dien keyphrase: tra cuu theo ban khong dau, uu tien cum dai
        self.kp_index = {}
        for k in self.keyphrases:
            self.kp_index.setdefault(k["khong_dau"], k)
        self.kp_max_words = max((k["so_tu"] for k in self.keyphrases), default=1)

        # do thi quan he (dung cho goi y tri thuc lien quan)
        self.rel_out = defaultdict(list)
        for r in self.relations:
            self.rel_out[r["nguon"]].append(r)
            self.rel_out[r["dich"]].append(
                {"ten": r["ten"], "kieu": r["kieu"], "nguon": r["dich"],
                 "dich": r["nguon"], "mo_ta": r["mo_ta"]})

        # --- khong gian vector cho so khop ngu nghia (TF-IDF char n-gram) ---
        self.v_corpus = [bo_dau(v["text_search"]) for v in self.violations]
        self.c_corpus = [bo_dau(c["text_search"]) for c in self.concepts]
        self.r_corpus = [bo_dau(r["text_search"]) for r in self.rules]

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
            txt = [self.ten_nhom.get(n, n)]
            for v in self.by_nhom[n]:
                txt.append(v["hanh_vi"])
                txt.extend(v.get("keyphrases") or [])
            gom.append(bo_dau(chuan_hoa(" ".join(txt))))
        self.M_nhom_char = self.vec_char.transform(gom)
        self.M_nhom_word = self.vec_word.transform(gom)

        # --- khong gian vector chi tren TEN cua khai niem / quy tac ---
        self.M_c_ten = self.vec_char.transform(
            [bo_dau(chuan_hoa(c["ten"])) for c in self.concepts])
        self.M_r_ten = self.vec_char.transform(
            [bo_dau(chuan_hoa(r["ten"])) for r in self.rules])

    # ------------------------------------------------------------ semantic
    def sim(self, query, kind="violation"):
        """Đo tương đồng ngữ nghĩa giữa truy vấn và từng phần tử tri thức.
        Kết hợp TF-IDF char n-gram (chịu được lỗi chính tả, cách tách từ) với
        word n-gram, và ưu tiên phần khớp với TÊN của khái niệm hoặc quy tắc."""
        q = bo_dau(chuan_hoa(query))
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

    def nhom_ngu_nghia(self, query, nguong=0.24, toi_da=2):
        """Nhận diện nhóm tri thức theo ngữ nghĩa khi keyphrase không bắt được."""
        q = bo_dau(chuan_hoa(query))
        s = (0.5 * cosine_similarity(self.vec_char.transform([q]), self.M_nhom_char)[0]
             + 0.5 * cosine_similarity(self.vec_word.transform([q]), self.M_nhom_word)[0])
        idx = np.argsort(-s)[:toi_da]
        return [(self.danh_sach_nhom[i], float(s[i])) for i in idx if s[i] >= nguong]


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
               r"\bbao nhieu(?!\s+(diem|tuoi|nguoi|lan|thang|nam))\b", r"\bgiam xe\b", r"\bnop phat\b", r"\bloi\b",
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

    def __init__(self, kb: KnowledgeBase):
        """Khởi tạo bộ phân tích truy vấn trên một cơ sở tri thức đã nạp."""
        self.kb = kb

    # ---------------------------------------------------------- keyphrase
    def rut_trich_keyphrase(self, text):
        """So khớp cụm dài nhất trên từ điển keyphrase (bản không dấu).
        Trả về danh sách bản ghi keyphrase, không chồng lấn."""
        toks = bo_dau(chuan_hoa(text)).split()
        n = len(toks)
        i, found = 0, []
        max_w = min(self.kb.kp_max_words, 8)
        while i < n:
            matched = False
            for w in range(min(max_w, n - i), 0, -1):
                cand = " ".join(toks[i:i + w])
                kp = self.kb.kp_index.get(cand)
                if kp is not None and (w > 1 or len(cand) >= 4):
                    found.append({"cum_tu": kp["cum_tu"], "vi_tri": (i, i + w), **kp})
                    i += w
                    matched = True
                    break
            if not matched:
                i += 1
        return found

    # --------------------------------------------------------- phuong tien
    def nhan_dien_phuong_tien(self, text):
        """Nhận diện loại phương tiện được nhắc tới trong câu hỏi dựa trên bảng từ khoá
        (bao gồm cả cách gọi đời thường như xe hơi, bốn bánh, kẹp ba).
        """
        t = bo_dau(chuan_hoa(text))
        pt = set()
        bang = {
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
        for k, kws in bang.items():
            if any(kw in t for kw in kws):
                pt.add(k)
        if "mo_to" in pt and "xe_gan_may" not in pt:
            pt.add("xe_gan_may")
        return sorted(pt)

    # ---------------------------------------------------------- chu the
    def nhan_dien_chu_the(self, text):
        """Nhận diện chủ thể của hành vi: người điều khiển, chủ phương tiện, người đi bộ hay hành khách."""
        t = bo_dau(chuan_hoa(text))
        if any(k in t for k in ["nguoi di bo", "di bo", "khach bo hanh"]):
            return "nguoi_di_bo"
        if any(k in t for k in ["chu xe", "chu phuong tien", "chu so huu"]):
            return "chu_phuong_tien"
        if any(k in t for k in ["hanh khach", "nguoi ngoi tren xe", "nguoi duoc cho"]):
            return "hanh_khach"
        return None

    # ------------------------------------------------------- can cu phap ly
    def nhan_dien_can_cu(self, text):
        """Nhận diện căn cứ pháp lý (điều - khoản - điểm và số hiệu văn bản) nếu người dùng
        hỏi trực tiếp theo căn cứ.
        """
        t = chuan_hoa(text)
        cc = {}
        m = re.search(r"điều\s+(\d+)", t)
        if m:
            cc["dieu"] = int(m.group(1))
        m = re.search(r"khoản\s+(\d+[a-zđ]?)", t)
        if m:
            cc["khoan"] = m.group(1)
        m = re.search(r"điểm\s+([a-zđ])\b", t)
        if m:
            cc["diem"] = m.group(1)
        if "168" in t:
            cc["van_ban"] = "Nghị định 168/2024/NĐ-CP"
        elif "36/2024" in t or "luật" in t:
            cc["van_ban"] = "Luật 36/2024/QH15"
        return cc if "dieu" in cc else None

    # ------------------------------------------------------- rang buoc so
    def nhan_dien_rang_buoc(self, text):
        """Nhận diện các ràng buộc định lượng trong câu hỏi: số điểm bị trừ, khoảng tiền phạt,
        hình phạt bổ sung (tịch thu, tước giấy phép lái xe), trường hợp chỉ bị cảnh cáo,
        và yêu cầu sắp xếp (cao nhất, thấp nhất).
        """
        t = chuan_hoa(text)
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
            a = tach_so_tien("%s %s" % (m.group(1), dv))
            b = tach_so_tien("%s %s" % (m.group(3), m.group(4) or dv))
            if a and b:
                rb["tien_khoang"] = (a[0], b[0])
        else:
            tien = tach_so_tien(t)
            if tien:
                if re.search(r"\b(trên|hơn|lớn hơn|từ)\b", t):
                    rb["tien_min"] = max(tien)
                if re.search(r"\b(dưới|nhỏ hơn|không quá|đến)\b", t):
                    rb["tien_max"] = max(tien)
        if re.search(r"tịch thu", t):
            rb["hinh_phat_bo_sung"] = "tịch thu"
        m = re.search(r"tước.{0,20}?(\d+)\s*(?:tháng)?\s*(?:đến|tới|-)\s*(\d+)\s*tháng", t)
        if m:
            rb["hinh_phat_bo_sung"] = "%s tháng đến %s tháng" % (m.group(1), m.group(2))
        elif re.search(r"\btước\b", t):
            rb["hinh_phat_bo_sung"] = "tước"
        if re.search(r"cảnh cáo", t):
            rb["chi_canh_cao"] = True
        if re.search(r"\b(cao nhất|nặng nhất|lớn nhất|kịch khung)\b", t):
            rb["sap_xep"] = "giam_dan"
        if re.search(r"\b(thấp nhất|nhẹ nhất|nhỏ nhất)\b", t):
            rb["sap_xep"] = "tang_dan"
        return rb

    # --------------------------------------------------- lop bai toan
    def phan_loai_bai_toan(self, text, kps, rang_buoc, can_cu, nhom_tap=frozenset()):
        """Phân loại câu hỏi vào một trong bảy lớp bài toán bằng hàm điểm có trọng số trên hai
        nhóm đặc trưng: đặc trưng ngôn ngữ (số mẫu nghi vấn khớp được) và đặc trưng tri thức
        (số khái niệm, quy tắc, nhóm nhận diện được và sự tồn tại của ràng buộc định lượng).
        Mỗi nhóm đặc trưng được chặn trần để một lớp không áp đảo chỉ vì câu hỏi dài.
        """
        t = bo_dau(chuan_hoa(text))

        def hit(pats):
            return sum(1 for p in pats if re.search(p, t))

        if can_cu:
            return P6_CAN_CU
        s_nguoc = hit(MAU_TRA_CUU_NGUOC) + (2 if rang_buoc else 0)
        s_che_tai = hit(MAU_CHE_TAI)
        s_khai_niem = hit(MAU_KHAI_NIEM)
        s_quy_dinh = hit(MAU_QUY_DINH)
        s_tinh_huong = hit(MAU_TINH_HUONG)

        n_nhom = len({n for n in nhom_tap if n != "khac"})
        n_kn = len({c for k in kps for c in k["khai_niem"]})
        n_qt = len({r for k in kps for r in k["quy_tac"]})
        co_tong = bool(re.search(r"\b(tong cong|tong muc|tong so|tong hop|tong)\b", t))

        # chan tran dong gop cua tung nhom dac trung de mot lop khong ap dao
        c_kn = min(s_khai_niem, 2)
        c_ct = min(s_che_tai, 2)
        c_qd = min(s_quy_dinh, 2)
        c_ng = min(s_nguoc, 2)
        c_th = min(s_tinh_huong, 3)

        # P5 la lop co DIEU KIEN CAN: >= 2 nhom tri thuc khac nhau (bo qua 'khac')
        du_dieu_kien_p5 = n_nhom >= 2 and (c_ct >= 1 or co_tong)

        diem = {
            P1_KHAI_NIEM: 2.0 * c_kn + 0.7 * min(n_kn, 2) - 1.5 * c_ct - 1.2 * c_ng,
            P2_QUY_DINH: 1.7 * c_qd + 0.6 * min(n_qt, 2) - 1.3 * c_ct - 0.9 * c_kn,
            P3_CHE_TAI: 1.8 * c_ct + 0.4 * min(n_nhom, 2) - 0.9 * c_kn,
            P4_TRA_CUU_NGUOC: 1.9 * c_ng + 1.8 * bool(rang_buoc) + 0.6 * c_ct
                              - 1.5 * c_th,
            P5_TINH_HUONG: (4.3 + 0.7 * c_th + 1.2 * co_tong + 0.8 * (n_nhom >= 3)
                            if du_dieu_kien_p5 else 0.0),
            P7_LIEN_QUAN: 0.9,
        }
        return max(diem, key=lambda k: diem[k])

    # -------------------------------------------------------------- main
    def analyze(self, text):
        """Thực hiện các bước B1 đến B4 của thuật giải xử lý truy vấn và trả về biểu diễn
        hình thức Q của câu hỏi.
        """
        kps = self.rut_trich_keyphrase(text)
        can_cu = self.nhan_dien_can_cu(text)
        rang_buoc = self.nhan_dien_rang_buoc(text)

        nhom_kp = ({n for k in kps for n in k["nhom"]}
                   | {self.kb.by_id[h]["nhom"] for k in kps for h in k["hanh_vi"]
                      if h in self.kb.by_id})
        nhom_nn = self.kb.nhom_ngu_nghia(text)
        nhom_tap = nhom_kp | ({n for n, _ in nhom_nn} if nhom_kp else
                              {n for n, _ in nhom_nn[:1]})
        loai = self.phan_loai_bai_toan(text, kps, rang_buoc, can_cu, nhom_tap)
        pt = self.nhan_dien_phuong_tien(text)
        gia_tri, id_thoa, giai_thich = self.kb.numeric.suy_dien(text, pt, self.kb.by_id)
        return {
            "truy_van_goc": text,
            "truy_van_chuan_hoa": chuan_hoa(text),
            "lop_bai_toan": loai,
            "ten_lop_bai_toan": TEN_LOP_BAI_TOAN[loai],
            "keyphrase": kps,
            "khai_niem": sorted({c for k in kps for c in k["khai_niem"]}),
            "nhom": sorted(nhom_kp),
            "nhom_ngu_nghia": [{"nhom": n, "diem": round(d, 4)} for n, d in nhom_nn],
            "nhom_suy_dien": sorted(nhom_tap),
            "quy_tac": sorted({r for k in kps for r in k["quy_tac"]}),
            "hanh_vi_ung_vien": sorted({h for k in kps for h in k["hanh_vi"]}),
            "phuong_tien": pt,
            "chu_the": self.nhan_dien_chu_the(text),
            "gia_tri_so": gia_tri,
            "hanh_vi_thoa_nguong": sorted(id_thoa) if id_thoa else [],
            "giai_thich_suy_dien": giai_thich,
            "can_cu": can_cu,
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

    def __init__(self, kb: KnowledgeBase):
        """Khởi tạo động cơ suy diễn cùng bộ phân tích truy vấn tương ứng."""
        self.kb = kb
        self.analyzer = QueryAnalyzer(kb)

    # ------------------------------------------------------------- ranking
    def _xep_hang_hanh_vi(self, Q, ung_vien=None, top_k=10):
        """Xếp hạng các hành vi vi phạm theo độ đo lai
        score = ALPHA*keyphrase + BETA*ngữ nghĩa + GAMMA*ngữ cảnh,
        có tích hợp kết quả suy diễn số học (chọn đúng khung xử phạt) và các heuristic
        loại trừ hành vi 'không chấp hành yêu cầu kiểm tra' khi câu hỏi không nhắc tới.
        """
        kb = self.kb
        sem = kb.sim(Q["truy_van_goc"], "violation")
        sem = sem / (sem.max() + 1e-9)

        nhom_q = set(Q["nhom"])
        pt_q = set(Q["phuong_tien"])
        hv_q = set(Q["hanh_vi_ung_vien"])
        chu_the_q = Q["chu_the"]
        so_thoa = set(Q.get("hanh_vi_thoa_nguong") or [])
        co_nguong = set(kb.numeric.nguong)
        # nguoi hoi co nhac den viec tu choi / khong chap hanh kiem tra hay khong?
        t_kd = bo_dau(Q["truy_van_chuan_hoa"])
        hoi_ve_tu_choi = any(k in t_kd for k in
                             ["khong chap hanh", "tu choi", "khong thoi", "khong hop tac",
                              "chong doi", "khong cho kiem tra"])

        ket_qua = []
        for i, v in enumerate(kb.violations):
            if ung_vien is not None and v["id"] not in ung_vien:
                continue

            # --- diem keyphrase (tri thuc) ---
            s_kp = 0.0
            if v["id"] in hv_q:
                s_kp += 1.0
            if v["nhom"] in nhom_q:
                s_kp += 0.75
            elif nhom_q:
                s_kp -= 0.30          # lech nhom tri thuc -> ha diem
            s_kp = min(s_kp, 1.0)

            # --- suy dien so hoc: chon dung khung xu phat ---
            if so_thoa:
                if v["id"] in so_thoa:
                    s_kp = 1.0
                elif v["id"] in co_nguong and v["nhom"] in nhom_q:
                    s_kp -= 1.0       # cung dai luong nhung sai khung -> loai

            # --- khong neu gia tri cu the -> uu tien khung thap nhat ---
            if not so_thoa and v["id"] in co_nguong and v["nhom"] in nhom_q:
                if all((n.get("can_duoi") or 0) <= 0 for n in kb.numeric.nguong[v["id"]]):
                    s_kp += 0.25
                else:
                    s_kp -= 0.10

            # --- heuristic: hanh vi 'khong chap hanh yeu cau kiem tra' ---
            if ("khong chap hanh yeu cau kiem tra" in bo_dau(v["hanh_vi"])
                    and not hoi_ve_tu_choi):
                s_kp -= 0.55

            # --- diem khai niem / phuong tien / chu the ---
            s_cx = 0.0
            if pt_q:
                if pt_q & set(v["phuong_tien"]):
                    s_cx += 1.0
                else:
                    s_cx -= 1.2          # phat nang neu sai phuong tien
            if chu_the_q:
                s_cx += 0.6 if v["chu_the"] == chu_the_q else -0.6
            elif v["chu_the"] == "nguoi_dieu_khien":
                s_cx += 0.15
            s_cx = max(min(s_cx, 1.0), -1.5)

            score = self.ALPHA * s_kp + self.BETA * sem[i] + self.GAMMA * s_cx
            if v["tinh_trang"] == "da_sua_doi":
                score += 0.02        # uu tien quy dinh moi nhat
            if score > 0.05:
                ket_qua.append((score, v, {"keyphrase": s_kp, "ngu_nghia": float(sem[i]),
                                           "ngu_canh": s_cx}))
        ket_qua.sort(key=lambda x: -x[0])
        return ket_qua[:top_k]

    def _xep_hang(self, Q, kind, items, top_k=5):
        """Xếp hạng khái niệm hoặc quy tắc: cộng điểm ưu tiên nếu phần tử được keyphrase trỏ
        trực tiếp, cộng điểm tương đồng ngữ nghĩa cho phần còn lại.
        """
        sem = self.kb.sim(Q["truy_van_goc"], kind)
        sem = sem / (sem.max() + 1e-9)
        uu_tien = set(Q["khai_niem"]) if kind == "concept" else set(Q["quy_tac"])
        out = []
        for i, it in enumerate(items):
            s = self.BETA * sem[i] + (self.ALPHA if it["id"] in uu_tien else 0.0)
            if s > 0.03:
                out.append((s, it))
        out.sort(key=lambda x: -x[0])
        return out[:top_k]

    # ------------------------------------------------------- tri thuc lien quan
    def tri_thuc_lien_quan(self, Q, ket_qua_hanh_vi, gioi_han=6):
        """Duyệt đồ thị quan hệ R từ các nhóm tri thức liên quan tới kết quả để gợi ý
        các mảng kiến thức lân cận cho người dùng.
        """
        kb, goi_y = self.kb, []
        seen = set()
        nhom_lq = set()
        for _, v, _ in ket_qua_hanh_vi[:3]:
            nhom_lq.add("NHOM_%s" % v["nhom"].upper())
        for c_id in Q["khai_niem"]:
            nhom_lq.update(r["dich"] for r in kb.rel_out.get(c_id, [])
                           if r["dich"].startswith("NHOM_"))
        for node in nhom_lq:
            for r in kb.rel_out.get(node, []):
                if not r["dich"].startswith("NHOM_"):
                    continue
                nhom = r["dich"][5:].lower()
                if nhom in seen or nhom not in kb.by_nhom:
                    continue
                seen.add(nhom)
                goi_y.append({"loai": "nhom", "ma": nhom,
                              "ten": kb.ten_nhom.get(nhom, nhom),
                              "so_quy_dinh": len(kb.by_nhom[nhom]),
                              "quan_he": r["ten"]})
                if len(goi_y) >= gioi_han:
                    return goi_y
        return goi_y

    # ============================================================ tra loi
    def answer(self, cau_hoi, top_k=5):
        """Điểm vào chính của động cơ suy diễn: phân tích câu hỏi, điều phối sang bộ giải của
        lớp bài toán tương ứng, bổ sung đủ ba loại tri thức (khái niệm, quy tắc, chế tài)
        để kết quả không phụ thuộc hoàn toàn vào bước phân loại, rồi tổng hợp căn cứ pháp lý
        và tri thức liên quan.
        """
        Q = self.analyzer.analyze(cau_hoi)
        loai = Q["lop_bai_toan"]
        kq = {"phan_tich": Q, "lop_bai_toan": loai,
              "ten_lop_bai_toan": TEN_LOP_BAI_TOAN[loai],
              "khai_niem": [], "quy_tac": [], "hanh_vi": [],
              "tong_hop": None, "lien_quan": [], "can_cu": [],
              "khong_tim_thay": False}

        if loai == P6_CAN_CU:
            self._giai_P6(Q, kq)
        elif loai == P1_KHAI_NIEM:
            self._giai_P1(Q, kq, top_k)
        elif loai == P2_QUY_DINH:
            self._giai_P2(Q, kq, top_k)
        elif loai == P3_CHE_TAI:
            self._giai_P3(Q, kq, top_k)
        elif loai == P4_TRA_CUU_NGUOC:
            self._giai_P4(Q, kq, top_k)
        elif loai == P5_TINH_HUONG:
            self._giai_P5(Q, kq)
        else:
            self._giai_P7(Q, kq, top_k)

        # --- bo sung: luon co san ca 3 loai tri thuc (khai niem / quy tac / che tai)
        #     de ket qua khong phu thuoc hoan toan vao buoc phan loai lop bai toan ---
        if not kq["hanh_vi"]:
            bs = [(sc, v, d) for sc, v, d in self._xep_hang_hanh_vi(Q, top_k=3)
                  if sc >= NGUONG_BO_SUNG]
            kq["_raw_hv"] = bs
            kq["hanh_vi"] = [{**v, "diem": round(sc, 4), "chi_tiet_diem": d,
                              "bo_sung": True} for sc, v, d in bs]
        if not kq["khai_niem"]:
            kq["khai_niem"] = [{**c, "diem": round(sc, 4), "bo_sung": True}
                               for sc, c in self._xep_hang(Q, "concept",
                                                           self.kb.concepts, 2)
                               if sc >= NGUONG_BO_SUNG]
        if not kq["quy_tac"]:
            kq["quy_tac"] = [{**r, "diem": round(sc, 4), "bo_sung": True}
                             for sc, r in self._xep_hang(Q, "rule",
                                                         self.kb.rules, 2)
                             if sc >= NGUONG_BO_SUNG]

        # Khong con tri thuc nao vuot nguong -> he thong thua nhan khong tra duoc,
        # thay vi tra ve mot danh sach hanh vi vi pham khong lien quan.
        kq["khong_tim_thay"] = not (kq["khai_niem"] or kq["quy_tac"] or kq["hanh_vi"])

        kq["lien_quan"] = self.tri_thuc_lien_quan(Q, kq.get("_raw_hv", []))
        kq.pop("_raw_hv", None)
        kq["can_cu"] = sorted({v["can_cu_text"] for v in kq["hanh_vi"]}
                              | {c["can_cu_text"] for c in kq["khai_niem"]}
                              | {r["can_cu_text"] for r in kq["quy_tac"]})
        return kq

    # ---------------------------------------------------------------- P1
    def _giai_P1(self, Q, kq, top_k):
        """Giải lớp P1 - tra cứu khái niệm: xếp hạng và trả về các khái niệm phù hợp."""
        for s, c in self._xep_hang(Q, "concept", self.kb.concepts, top_k):
            kq["khai_niem"].append({**c, "diem": round(s, 4)})
        if not kq["khai_niem"]:
            self._giai_P7(Q, kq, top_k)

    # ---------------------------------------------------------------- P2
    def _giai_P2(self, Q, kq, top_k):
        """Giải lớp P2 - tra cứu quy định: trả về quy tắc giao thông kèm nguyên văn, bổ sung
        khái niệm và một vài chế tài liên quan.
        """
        for s, r in self._xep_hang(Q, "rule", self.kb.rules, top_k):
            kq["quy_tac"].append({**r, "diem": round(s, 4)})
        for s, c in self._xep_hang(Q, "concept", self.kb.concepts, 2):
            kq["khai_niem"].append({**c, "diem": round(s, 4)})
        hv = self._xep_hang_hanh_vi(Q, top_k=3)
        kq["_raw_hv"] = hv
        kq["hanh_vi"] = [{**v, "diem": round(s, 4), "chi_tiet_diem": d} for s, v, d in hv]

    # ---------------------------------------------------------------- P3
    def _giai_P3(self, Q, kq, top_k):
        """Giải lớp P3 - tra cứu chế tài: trả về các hành vi vi phạm kèm mức phạt và căn cứ."""
        hv = self._xep_hang_hanh_vi(Q, top_k=top_k)
        kq["_raw_hv"] = hv
        kq["hanh_vi"] = [{**v, "diem": round(s, 4), "chi_tiet_diem": d} for s, v, d in hv]
        for s, c in self._xep_hang(Q, "concept", self.kb.concepts, 2):
            kq["khai_niem"].append({**c, "diem": round(s, 4)})

    # ---------------------------------------------------------------- P4
    def _giai_P4(self, Q, kq, top_k):
        """Giải lớp P4 - tra cứu ngược: lọc toàn bộ tập sự kiện F theo các ràng buộc định lượng
        (số điểm trừ, khoảng tiền, hình phạt bổ sung, chỉ cảnh cáo) rồi sắp xếp kết quả.
        Khi đã có ràng buộc định lượng, nhóm tri thức chỉ dùng để ưu tiên chứ không lọc cứng.
        """
        rb = Q["rang_buoc"]
        pt_q = set(Q["phuong_tien"])
        nhom_q = set(Q["nhom"])
        # khi truy van da co rang buoc dinh luong (so tien / diem tru / hinh phat bo sung)
        # thi KHONG loc cung theo nhom -- nhom chi dung de sap xep uu tien
        loc_nhom = bool(nhom_q) and not rb
        ds = []
        for v in self.kb.violations:
            if pt_q and not (pt_q & set(v["phuong_tien"])):
                continue
            if loc_nhom and v["nhom"] not in nhom_q:
                continue
            if "tru_diem" in rb and (v["tru_diem_gplx"] or 0) != rb["tru_diem"]:
                continue
            mn, mx = v["phat_tien"].get("min"), v["phat_tien"].get("max")
            if "tien_khoang" in rb:
                a, b = rb["tien_khoang"]
                if mn != a or mx != b:
                    continue
            if "tien_min" in rb and (mx is None or mx < rb["tien_min"]):
                continue
            if "tien_max" in rb and (mn is None or mn > rb["tien_max"]):
                continue
            if "hinh_phat_bo_sung" in rb:
                bs = bo_dau(" ".join(v["hinh_phat_bo_sung"]))
                if bo_dau(rb["hinh_phat_bo_sung"]) not in bs:
                    continue
            if rb.get("chi_canh_cao") and not (mn in (0, None) and mx in (0, None)):
                continue
            if Q["chu_the"] and v["chu_the"] != Q["chu_the"]:
                continue
            ds.append(v)
        rev = rb.get("sap_xep", "giam_dan") != "tang_dan"
        ds.sort(key=lambda v: (v["phat_tien"].get("max") or 0,
                               v["tru_diem_gplx"] or 0), reverse=rev)
        if nhom_q:   # uu tien cac hanh vi dung nhom tri thuc nguoi dung hoi
            ds.sort(key=lambda v: v["nhom"] not in nhom_q)
        gh = 20 if (rb or nhom_q or pt_q) else top_k
        kq["hanh_vi"] = [{**v, "diem": 1.0} for v in ds[:gh]]
        kq["tong_hop"] = {"kieu": "danh_sach", "tong_so": len(ds), "hien_thi": len(kq["hanh_vi"])}
        kq["_raw_hv"] = [(1.0, v, {}) for v in ds[:3]]

    # ---------------------------------------------------------------- P5
    def _giai_P5(self, Q, kq):
        """Giải lớp P5 - suy diễn tình huống: mỗi nhóm tri thức nhận diện được ứng với
        một hành vi vi phạm, sau đó tổng hợp mức phạt và số điểm bị trừ."""
        chon = []
        uu_tien = Q["nhom"] or Q["nhom_suy_dien"]
        for nhom in (uu_tien + [n for n in Q["nhom_suy_dien"] if n not in uu_tien]):
            Qn = dict(Q)
            Qn["nhom"] = [nhom]
            ung_vien = {v["id"] for v in self.kb.by_nhom.get(nhom, [])}
            if not ung_vien:
                continue
            best = self._xep_hang_hanh_vi(Qn, ung_vien=ung_vien, top_k=1)
            if best:
                chon.append(best[0])
        if not chon:
            chon = self._xep_hang_hanh_vi(Q, top_k=3)
        kq["_raw_hv"] = chon
        kq["hanh_vi"] = [{**v, "diem": round(s, 4), "chi_tiet_diem": d} for s, v, d in chon]

        tien_min = sum((v["phat_tien"].get("min") or 0) for _, v, _ in chon)
        tien_max = sum((v["phat_tien"].get("max") or 0) for _, v, _ in chon)
        diem = sum((v["tru_diem_gplx"] or 0) for _, v, _ in chon)
        bo_sung = [b for _, v, _ in chon for b in v["hinh_phat_bo_sung"]]
        canh_bao = []
        for _, v, _ in chon:
            if v["id"] in self.kb.numeric.nguong and not Q.get("gia_tri_so"):
                canh_bao.append(
                    "Hành vi \"%s\" được phân mức theo giá trị đo được; "
                    "hệ thống đang lấy khung thấp nhất. Nêu rõ giá trị cụ thể "
                    "để có kết quả chính xác." % v["hanh_vi"][:70])
        kq["tong_hop"] = {
            "kieu": "tinh_huong", "so_hanh_vi": len(chon), "canh_bao": canh_bao,
            "tong_phat_tien": {"min": tien_min, "max": tien_max},
            "tong_tru_diem": diem,
            "canh_bao_het_diem": diem >= 12,
            "hinh_phat_bo_sung": bo_sung,
        }

    # ---------------------------------------------------------------- P6
    def _giai_P6(self, Q, kq):
        """Giải lớp P6 - tra cứu theo căn cứ pháp lý: trả về mọi quy định tại điều - khoản - điểm
        mà người dùng chỉ định.
        """
        cc = Q["can_cu"]
        ds = []
        for v in self.kb.violations:
            c = v["can_cu"]
            if c.get("dieu") != cc.get("dieu"):
                continue
            if cc.get("van_ban") and cc["van_ban"] != c.get("van_ban"):
                continue
            if "khoan" in cc and str(c.get("khoan")) != str(cc["khoan"]):
                continue
            if "diem" in cc and str(c.get("diem")) != str(cc["diem"]):
                continue
            ds.append(v)
        kq["hanh_vi"] = [{**v, "diem": 1.0} for v in ds[:30]]
        for r in self.kb.rules:
            c = r.get("can_cu") or {}
            if c.get("dieu") == cc.get("dieu") and "Luật" in str(c.get("van_ban", "")):
                if "khoan" in cc and str(c.get("khoan")) != str(cc["khoan"]):
                    continue
                kq["quy_tac"].append({**r, "diem": 1.0})
        kq["tong_hop"] = {"kieu": "can_cu", "tong_so": len(ds)}
        kq["_raw_hv"] = [(1.0, v, {}) for v in ds[:3]]

    # ---------------------------------------------------------------- P7
    def _giai_P7(self, Q, kq, top_k):
        """Giải lớp P7 - tra cứu kiến thức liên quan: trả về đồng thời chế tài, khái niệm và quy tắc
        có liên quan tới câu hỏi.
        """
        hv = self._xep_hang_hanh_vi(Q, top_k=top_k)
        kq["_raw_hv"] = hv
        kq["hanh_vi"] = [{**v, "diem": round(s, 4), "chi_tiet_diem": d} for s, v, d in hv]
        for s, c in self._xep_hang(Q, "concept", self.kb.concepts, 3):
            kq["khai_niem"].append({**c, "diem": round(s, 4)})
        for s, r in self._xep_hang(Q, "rule", self.kb.rules, 3):
            kq["quy_tac"].append({**r, "diem": round(s, 4)})


# ==========================================================================
# 5. SINH CAU TRA LOI DANG VAN BAN
# ==========================================================================
def dinh_dang_tien(n):
    """Định dạng một số tiền sang chuỗi tiếng Việt, ví dụ 6000000 thành '6.000.000 đồng'."""
    if n is None:
        return "—"
    if n == 0:
        return "0 đồng"
    return f"{n:,.0f}".replace(",", ".") + " đồng"


def mo_ta_muc_phat(v):
    """Mô tả mức phạt tiền của một hành vi thành chuỗi đọc được, xử lý cả trường hợp
        không quy định phạt tiền hoặc chỉ phạt cảnh cáo.
    """
    mn, mx = v["phat_tien"].get("min"), v["phat_tien"].get("max")
    if mn is None and mx is None:
        return "Không quy định phạt tiền"
    if mn == mx == 0:
        return "Không phạt tiền (cảnh cáo hoặc hình thức khác)"
    if mn == mx:
        return dinh_dang_tien(mn)
    return "từ %s đến %s" % (dinh_dang_tien(mn), dinh_dang_tien(mx))


def sinh_van_ban(kq, kb: KnowledgeBase):
    """Sinh câu trả lời dạng văn bản thuần từ kết quả suy diễn."""
    L = []
    Q = kq["phan_tich"]
    L.append("● Lớp bài toán: %s" % kq["ten_lop_bai_toan"])
    if Q["keyphrase"]:
        L.append("● Keyphrase nhận diện: " + ", ".join(
            sorted({k["cum_tu"] for k in Q["keyphrase"]})))
    if Q["phuong_tien"]:
        L.append("● Phương tiện: " + ", ".join(
            kb.ten_phuong_tien.get(p, p) for p in Q["phuong_tien"]))
    for g in Q.get("giai_thich_suy_dien") or []:
        L.append("● Suy diễn số học: %s" % g)
    L.append("")

    for c in kq["khai_niem"]:
        L.append("▸ KHÁI NIỆM: %s" % c["ten"])
        if c.get("dinh_nghia"):
            L.append("  %s" % c["dinh_nghia"])
        elif c.get("thuoc_tinh"):
            for k, val in list(c["thuoc_tinh"].items())[:6]:
                L.append("  - %s: %s" % (k, val))
        L.append("  (Căn cứ: %s)" % c["can_cu_text"])
        L.append("")

    for r in kq["quy_tac"]:
        L.append("▸ QUY ĐỊNH: %s" % r["ten"])
        if r.get("nguyen_van"):
            L.append("  %s" % r["nguyen_van"][:900])
        else:
            for k in r.get("ket_luan", [])[:3]:
                L.append("  - %s" % k)
        L.append("  (Căn cứ: %s)" % r["can_cu_text"])
        L.append("")

    if kq["hanh_vi"]:
        L.append("▸ CHẾ TÀI XỬ PHẠT")
        for i, v in enumerate(kq["hanh_vi"], 1):
            L.append("  %d. %s" % (i, v["hanh_vi"]))
            L.append("     • Phương tiện: %s | Chủ thể: %s"
                     % (", ".join(kb.ten_phuong_tien.get(p, p) for p in v["phuong_tien"]),
                        kb.ten_chu_the.get(v["chu_the"], v["chu_the"])))
            L.append("     • Phạt tiền: %s" % mo_ta_muc_phat(v))
            if v["phat_tien"].get("ghi_chu"):
                L.append("       (%s)" % v["phat_tien"]["ghi_chu"])
            if v.get("tru_diem_gplx"):
                L.append("     • Trừ %d điểm giấy phép lái xe" % v["tru_diem_gplx"])
            for b in v.get("hinh_phat_bo_sung", []):
                L.append("     • Hình phạt bổ sung: %s" % b)
            for b in v.get("bien_phap_khac_phuc", []):
                L.append("     • Biện pháp khắc phục: %s" % b)
            L.append("     • Căn cứ: %s" % v["can_cu_text"])
            if v.get("tinh_trang") == "da_sua_doi":
                L.append("     • ⚠ Đã được sửa đổi bởi %s" % v.get("sua_doi_boi"))
            L.append("")

    th = kq.get("tong_hop")
    if th and th.get("kieu") == "tinh_huong":
        L.append("▸ TỔNG HỢP TÌNH HUỐNG (suy diễn %d hành vi vi phạm)" % th["so_hanh_vi"])
        L.append("  • Tổng mức phạt tiền dự kiến: từ %s đến %s"
                 % (dinh_dang_tien(th["tong_phat_tien"]["min"]),
                    dinh_dang_tien(th["tong_phat_tien"]["max"])))
        if th["tong_tru_diem"]:
            L.append("  • Tổng số điểm giấy phép lái xe bị trừ: %d điểm" % th["tong_tru_diem"])
        if th["canh_bao_het_diem"]:
            L.append("  • ⚠ Bị trừ hết 12 điểm — phải kiểm tra kiến thức pháp luật "
                     "về trật tự, an toàn giao thông đường bộ để được phục hồi điểm.")
        for b in th["hinh_phat_bo_sung"]:
            L.append("  • Hình phạt bổ sung: %s" % b)
        for c in th.get("canh_bao", []):
            L.append("  • ⓘ %s" % c)
        L.append("")
    elif th and th.get("kieu") == "danh_sach":
        L.append("▸ Tìm thấy %d quy định thoả điều kiện (hiển thị %d)."
                 % (th["tong_so"], th["hien_thi"]))
        L.append("")

    if kq["lien_quan"]:
        L.append("▸ KIẾN THỨC LIÊN QUAN: " + ", ".join(
            "%s (%d quy định)" % (g["ten"], g["so_quy_dinh"]) for g in kq["lien_quan"]))

    if not (kq["khai_niem"] or kq["quy_tac"] or kq["hanh_vi"]):
        L.append("Không tìm thấy quy định phù hợp trong cơ sở tri thức. "
                 "Bạn thử diễn đạt lại câu hỏi hoặc nêu rõ loại phương tiện.")
    return "\n".join(L)


# ==========================================================================
class TraCuuPhapLuat:
    """Lớp mặt tiền (facade) cho toàn hệ thống: nạp tri thức và trả lời câu hỏi."""

    def __init__(self, kb_dir=KB_DIR):
        """Nạp cơ sở tri thức và khởi tạo động cơ suy diễn."""
        self.kb = KnowledgeBase(kb_dir)
        self.engine = InferenceEngine(self.kb)

    def hoi(self, cau_hoi, top_k=5):
        """Trả lời một câu hỏi và trả về kết quả dạng cấu trúc (dùng cho giao diện và đánh giá)."""
        return self.engine.answer(cau_hoi, top_k=top_k)

    def tra_loi_van_ban(self, cau_hoi, top_k=5):
        """Trả lời một câu hỏi và trả về câu trả lời dạng văn bản thuần."""
        return sinh_van_ban(self.hoi(cau_hoi, top_k), self.kb)

    def thong_ke(self):
        """Trả về thống kê quy mô của cơ sở tri thức."""
        return {"khai_niem": len(self.kb.concepts), "quan_he": len(self.kb.relations),
                "quy_tac": len(self.kb.rules), "hanh_vi": len(self.kb.violations),
                "keyphrase": len(self.kb.keyphrases), "van_ban": len(self.kb.documents)}


if __name__ == "__main__":
    import sys
    sys_ = TraCuuPhapLuat()
    print("Cơ sở tri thức:", sys_.thong_ke())
    q = " ".join(sys.argv[1:]) or "Vượt đèn đỏ xe máy phạt bao nhiêu tiền?"
    print("\nCÂU HỎI:", q, "\n" + "-" * 70)
    print(sys_.tra_loi_van_ban(q))
