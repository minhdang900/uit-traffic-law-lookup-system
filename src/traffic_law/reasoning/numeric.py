"""
numeric_reasoner.py -- Mô-đun suy diễn số học trên tri thức pháp luật.

Nhiều quy định xử phạt được phân mức theo một dải giá trị (nồng độ cồn,
mức vượt tốc độ...). Nếu chỉ so khớp từ khoá thì hệ thống không thể chọn
đúng khung xử phạt. Mô-đun này thực hiện:

  1. Rút trích CÁC NGƯỠNG số từ chính nguyên văn của hành vi vi phạm
     (không viết cứng trong mã nguồn -> tri thức vẫn nằm trong cơ sở tri thức).
  2. Rút trích GIÁ TRỊ số trong câu truy vấn của người dùng.
  3. Suy diễn khung xử phạt đúng bằng phép so sánh khoảng.

Nhờ vậy hệ thống trả lời đúng "0,3 mg/l khí thở" thuộc khung nào, thay vì
chỉ trả về mọi hành vi có chứa cụm từ "nồng độ cồn".
"""
import re
import unicodedata

# --------------------------------------------------------------------------
# Cac loai dai luong duoc suy dien
# --------------------------------------------------------------------------
BREATH_ALCOHOL = "con_khi_tho"        # miligam / 1 lit khi tho
BLOOD_ALCOHOL = "con_mau"                # miligam / 100 mililit mau
OVER_SPEED = "vuot_toc_do"        # km/h vuot qua toc do quy dinh

QUANTITY_NAMES = {
    BREATH_ALCOHOL: "nồng độ cồn trong khí thở (mg/1 lít khí thở)",
    BLOOD_ALCOHOL: "nồng độ cồn trong máu (mg/100 ml máu)",
    OVER_SPEED: "mức vượt quá tốc độ quy định (km/h)",
}


def _unaccent(s):
    """Đưa chuỗi tiếng Việt về dạng không dấu, viết thường
    (dùng cho so khớp biểu thức chính quy)."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def _number(x):
    """'0,25' -> 0.25 ; '05' -> 5.0"""
    try:
        return float(str(x).replace(".", "").replace(",", "."))
    except ValueError:
        return None


# ==========================================================================
# 1. RUT TRICH NGUONG TU NGUYEN VAN HANH VI VI PHAM
# ==========================================================================
def extract_thresholds(behavior):
    """Đọc nguyên văn một hành vi vi phạm, trả về danh sách ngưỡng dạng
    {dai_luong, can_duoi, can_tren, mo_ta}.
    can_duoi / can_tren tạo thành khoảng nửa mở: (can_duoi, can_tren].
    Giá trị None nghĩa là vô cực."""
    t = _unaccent(behavior)
    out = []

    # ---------------- nong do con ----------------
    if "nong do con" in t:
        # 'chua vuot qua 50 miligam/100 mililit mau hoac chua vuot qua 0,25 miligam/1 lit khi tho'
        m = re.search(r"chua vuot qua\s+([\d.,]+)\s*miligam\s*/\s*100", t)
        if m:
            out.append({"quantity": BLOOD_ALCOHOL, "lower": 0.0,
                        "upper": _number(m.group(1)),
                        "description": "chưa vượt quá %s" % m.group(1)})
        m = re.search(r"chua vuot qua\s+([\d.,]+)\s*miligam\s*/\s*1\s*lit", t)
        if m:
            out.append({"quantity": BREATH_ALCOHOL, "lower": 0.0,
                        "upper": _number(m.group(1)),
                        "description": "chưa vượt quá %s" % m.group(1)})
        # 'vuot qua 50 miligam den 80 miligam/100 mililit mau'
        m = re.search(r"vuot qua\s+([\d.,]+)\s*miligam\s*den\s*([\d.,]+)\s*miligam\s*/\s*100", t)
        if m:
            out.append({"quantity": BLOOD_ALCOHOL, "lower": _number(m.group(1)),
                        "upper": _number(m.group(2)),
                        "description": "vượt quá %s đến %s" % (m.group(1), m.group(2))})
        m = re.search(
            r"vuot qua\s+([\d.,]+)\s*miligam\s*den\s*([\d.,]+)\s*miligam\s*/\s*1\s*lit", t)
        if m:
            out.append({"quantity": BREATH_ALCOHOL, "lower": _number(m.group(1)),
                        "upper": _number(m.group(2)),
                        "description": "vượt quá %s đến %s" % (m.group(1), m.group(2))})
        # 'vuot qua 80 miligam/100 mililit mau' (khong co 'den') -> khung cao nhat
        if not any(o["quantity"] == BLOOD_ALCOHOL for o in out):
            m = re.search(r"vuot qua\s+([\d.,]+)\s*miligam\s*/\s*100", t)
            if m:
                out.append({"quantity": BLOOD_ALCOHOL, "lower": _number(m.group(1)),
                            "upper": None, "description": "vượt quá %s" % m.group(1)})
        if not any(o["quantity"] == BREATH_ALCOHOL for o in out):
            m = re.search(r"vuot qua\s+([\d.,]+)\s*miligam\s*/\s*1\s*lit", t)
            if m:
                out.append({"quantity": BREATH_ALCOHOL, "lower": _number(m.group(1)),
                            "upper": None, "description": "vượt quá %s" % m.group(1)})

    # ---------------- vuot toc do ----------------
    if "qua toc do" in t and "duoi toc do" not in t:
        # 'tu 05 km/h den duoi 10 km/h'
        m = re.search(r"tu\s+([\d.,]+)\s*km/h\s*den\s*duoi\s*([\d.,]+)\s*km/h", t)
        if m:
            out.append({"quantity": OVER_SPEED, "lower": _number(m.group(1)) - 1e-9,
                        "upper": _number(m.group(2)) - 1e-9,
                        "description": "từ %s km/h đến dưới %s km/h" % (m.group(1), m.group(2))})
        else:
            # 'tu 10 km/h den 20 km/h'
            m = re.search(r"tu\s+([\d.,]+)\s*km/h\s*den\s*([\d.,]+)\s*km/h", t)
            if m:
                out.append({"quantity": OVER_SPEED, "lower": _number(m.group(1)) - 1e-9,
                            "upper": _number(m.group(2)),
                            "description": "từ %s km/h đến %s km/h" % (m.group(1), m.group(2))})
            else:
                # 'tren 20 km/h den 35 km/h'
                m = re.search(r"tren\s+([\d.,]+)\s*km/h\s*den\s*([\d.,]+)\s*km/h", t)
                if m:
                    out.append({"quantity": OVER_SPEED, "lower": _number(m.group(1)),
                                "upper": _number(m.group(2)),
                                "description": "trên %s km/h đến %s km/h" % (m.group(1),
                                            m.group(2))})
                else:
                    # 'tren 35 km/h'
                    m = re.search(r"tren\s+([\d.,]+)\s*km/h", t)
                    if m:
                        out.append({"quantity": OVER_SPEED, "lower": _number(m.group(1)),
                                    "upper": None, "description": "trên %s km/h" % m.group(1)})
    return out


# ==========================================================================
# 2. RUT TRICH GIA TRI SO TRONG TRUY VAN
# ==========================================================================
def extract_values(query):
    """Trả về dict {đại_lượng: giá_trị} tìm thấy trong câu hỏi."""
    t = _unaccent(query)
    gt = {}

    # --- nong do con trong khi tho: '0,3 mg/l', '0.3 miligam/1 lit khi tho' ---
    for pat in [r"([\d.,]+)\s*(?:mg|miligam)\s*/\s*(?:1\s*)?(?:l\b|lit)",
                r"([\d.,]+)\s*(?:mg|miligam)\s*tren\s*(?:1\s*)?lit",
                r"([\d.,]+)\s*mg/l"]:
        m = re.search(pat, t)
        if m:
            v = _number(m.group(1))
            if v is not None and v < 10:          # khi tho luon < 10 mg/l
                gt[BREATH_ALCOHOL] = v
            break

    # --- nong do con trong mau: '60 mg/100ml mau' ---
    for pat in [r"([\d.,]+)\s*(?:mg|miligam)\s*/\s*100\s*(?:ml|mililit)",
                r"([\d.,]+)\s*(?:mg|miligam).{0,12}mau"]:
        m = re.search(pat, t)
        if m:
            v = _number(m.group(1))
            if v is not None:
                gt[BLOOD_ALCOHOL] = v
            break

    # --- muc vuot toc do: 'qua toc do 25 km/h', 'vuot 25km/h' ---
    if re.search(r"(qua toc do|vuot toc do|chay qua|vuot qua toc do)", t):
        m = re.search(r"([\d.,]+)\s*km/?h", t)
        if m:
            v = _number(m.group(1))
            if v is not None and v <= 100:
                gt[OVER_SPEED] = v
    return gt


# ==========================================================================
# 3. SUY DIEN: gia tri co thoa nguong khong?
# ==========================================================================
def within_range(value, threshold):
    """Kiểm tra giá trị có rơi vào khoảng (can_duoi, can_tren] của ngưỡng hay không."""
    lo, hi = threshold["lower"], threshold["upper"]
    if lo is not None and value <= lo:
        return False
    if hi is not None and value > hi:
        return False
    return True


class NumericReasoner:
    """Lập chỉ mục ngưỡng cho toàn bộ cơ sở tri thức và suy diễn khung xử phạt."""

    def __init__(self, violations):
        """Lập chỉ mục ngưỡng cho toàn bộ tập sự kiện F: với mỗi hành vi vi phạm,
        rút trích các khoảng giá trị từ chính nguyên văn quy định."""
        self.threshold = {}          # id hanh vi -> danh sach nguong
        self.theo_dai_luong = {}  # dai_luong -> [(id, nguong)]
        for v in violations:
            ng = extract_thresholds(v.behavior)
            if ng:
                self.threshold[v.id] = ng
                for n in ng:
                    self.theo_dai_luong.setdefault(n["quantity"], []).append((v.id, n))

    def infer(self, query, vehicles=None, violations_by_id=None):
        """Trả về (giá_trị_tìm_thấy, tập_id_hành_vi_thoả_mãn, giải_thích)."""
        gt = extract_values(query)
        if not gt:
            return {}, None, []
        thoa, giai_thich = set(), []
        for dl, val in gt.items():
            ids = set()
            for vid, ng in self.theo_dai_luong.get(dl, []):
                if not within_range(val, ng):
                    continue
                if vehicles and violations_by_id:
                    v = violations_by_id.get(vid)
                    if v and not (set(vehicles) & set(v.vehicles)):
                        continue
                ids.add(vid)
            if ids:
                thoa |= ids
                giai_thich.append(
                    "Giá trị %s = %s thuộc khung %s"
                    % (QUANTITY_NAMES[dl], ("%g" % val).replace(".", ","),
                       "; ".join(sorted({n["description"] for vid, n in self.theo_dai_luong[dl]
                                         if vid in ids and n["quantity"] == dl}))))
        return gt, (thoa or None), giai_thich
