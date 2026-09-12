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
CON_KHI_THO = "con_khi_tho"        # miligam / 1 lit khi tho
CON_MAU = "con_mau"                # miligam / 100 mililit mau
VUOT_TOC_DO = "vuot_toc_do"        # km/h vuot qua toc do quy dinh

TEN_DAI_LUONG = {
    CON_KHI_THO: "nồng độ cồn trong khí thở (mg/1 lít khí thở)",
    CON_MAU: "nồng độ cồn trong máu (mg/100 ml máu)",
    VUOT_TOC_DO: "mức vượt quá tốc độ quy định (km/h)",
}


def _kd(s):
    """Đưa chuỗi tiếng Việt về dạng không dấu, viết thường
    (dùng cho so khớp biểu thức chính quy)."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace("đ", "d").replace("Đ", "D").lower()


def _so(x):
    """'0,25' -> 0.25 ; '05' -> 5.0"""
    try:
        return float(str(x).replace(".", "").replace(",", "."))
    except ValueError:
        return None


# ==========================================================================
# 1. RUT TRICH NGUONG TU NGUYEN VAN HANH VI VI PHAM
# ==========================================================================
def trich_nguong(hanh_vi):
    """Đọc nguyên văn một hành vi vi phạm, trả về danh sách ngưỡng dạng
    {dai_luong, can_duoi, can_tren, mo_ta}.
    can_duoi / can_tren tạo thành khoảng nửa mở: (can_duoi, can_tren].
    Giá trị None nghĩa là vô cực."""
    t = _kd(hanh_vi)
    out = []

    # ---------------- nong do con ----------------
    if "nong do con" in t:
        # 'chua vuot qua 50 miligam/100 mililit mau hoac chua vuot qua 0,25 miligam/1 lit khi tho'
        m = re.search(r"chua vuot qua\s+([\d.,]+)\s*miligam\s*/\s*100", t)
        if m:
            out.append({"dai_luong": CON_MAU, "can_duoi": 0.0,
                        "can_tren": _so(m.group(1)), "mo_ta": "chưa vượt quá %s" % m.group(1)})
        m = re.search(r"chua vuot qua\s+([\d.,]+)\s*miligam\s*/\s*1\s*lit", t)
        if m:
            out.append({"dai_luong": CON_KHI_THO, "can_duoi": 0.0,
                        "can_tren": _so(m.group(1)), "mo_ta": "chưa vượt quá %s" % m.group(1)})
        # 'vuot qua 50 miligam den 80 miligam/100 mililit mau'
        m = re.search(r"vuot qua\s+([\d.,]+)\s*miligam\s*den\s*([\d.,]+)\s*miligam\s*/\s*100", t)
        if m:
            out.append({"dai_luong": CON_MAU, "can_duoi": _so(m.group(1)),
                        "can_tren": _so(m.group(2)),
                        "mo_ta": "vượt quá %s đến %s" % (m.group(1), m.group(2))})
        m = re.search(
            r"vuot qua\s+([\d.,]+)\s*miligam\s*den\s*([\d.,]+)\s*miligam\s*/\s*1\s*lit", t)
        if m:
            out.append({"dai_luong": CON_KHI_THO, "can_duoi": _so(m.group(1)),
                        "can_tren": _so(m.group(2)),
                        "mo_ta": "vượt quá %s đến %s" % (m.group(1), m.group(2))})
        # 'vuot qua 80 miligam/100 mililit mau' (khong co 'den') -> khung cao nhat
        if not any(o["dai_luong"] == CON_MAU for o in out):
            m = re.search(r"vuot qua\s+([\d.,]+)\s*miligam\s*/\s*100", t)
            if m:
                out.append({"dai_luong": CON_MAU, "can_duoi": _so(m.group(1)),
                            "can_tren": None, "mo_ta": "vượt quá %s" % m.group(1)})
        if not any(o["dai_luong"] == CON_KHI_THO for o in out):
            m = re.search(r"vuot qua\s+([\d.,]+)\s*miligam\s*/\s*1\s*lit", t)
            if m:
                out.append({"dai_luong": CON_KHI_THO, "can_duoi": _so(m.group(1)),
                            "can_tren": None, "mo_ta": "vượt quá %s" % m.group(1)})

    # ---------------- vuot toc do ----------------
    if "qua toc do" in t and "duoi toc do" not in t:
        # 'tu 05 km/h den duoi 10 km/h'
        m = re.search(r"tu\s+([\d.,]+)\s*km/h\s*den\s*duoi\s*([\d.,]+)\s*km/h", t)
        if m:
            out.append({"dai_luong": VUOT_TOC_DO, "can_duoi": _so(m.group(1)) - 1e-9,
                        "can_tren": _so(m.group(2)) - 1e-9,
                        "mo_ta": "từ %s km/h đến dưới %s km/h" % (m.group(1), m.group(2))})
        else:
            # 'tu 10 km/h den 20 km/h'
            m = re.search(r"tu\s+([\d.,]+)\s*km/h\s*den\s*([\d.,]+)\s*km/h", t)
            if m:
                out.append({"dai_luong": VUOT_TOC_DO, "can_duoi": _so(m.group(1)) - 1e-9,
                            "can_tren": _so(m.group(2)),
                            "mo_ta": "từ %s km/h đến %s km/h" % (m.group(1), m.group(2))})
            else:
                # 'tren 20 km/h den 35 km/h'
                m = re.search(r"tren\s+([\d.,]+)\s*km/h\s*den\s*([\d.,]+)\s*km/h", t)
                if m:
                    out.append({"dai_luong": VUOT_TOC_DO, "can_duoi": _so(m.group(1)),
                                "can_tren": _so(m.group(2)),
                                "mo_ta": "trên %s km/h đến %s km/h" % (m.group(1), m.group(2))})
                else:
                    # 'tren 35 km/h'
                    m = re.search(r"tren\s+([\d.,]+)\s*km/h", t)
                    if m:
                        out.append({"dai_luong": VUOT_TOC_DO, "can_duoi": _so(m.group(1)),
                                    "can_tren": None, "mo_ta": "trên %s km/h" % m.group(1)})
    return out


# ==========================================================================
# 2. RUT TRICH GIA TRI SO TRONG TRUY VAN
# ==========================================================================
def trich_gia_tri(truy_van):
    """Trả về dict {đại_lượng: giá_trị} tìm thấy trong câu hỏi."""
    t = _kd(truy_van)
    gt = {}

    # --- nong do con trong khi tho: '0,3 mg/l', '0.3 miligam/1 lit khi tho' ---
    for pat in [r"([\d.,]+)\s*(?:mg|miligam)\s*/\s*(?:1\s*)?(?:l\b|lit)",
                r"([\d.,]+)\s*(?:mg|miligam)\s*tren\s*(?:1\s*)?lit",
                r"([\d.,]+)\s*mg/l"]:
        m = re.search(pat, t)
        if m:
            v = _so(m.group(1))
            if v is not None and v < 10:          # khi tho luon < 10 mg/l
                gt[CON_KHI_THO] = v
            break

    # --- nong do con trong mau: '60 mg/100ml mau' ---
    for pat in [r"([\d.,]+)\s*(?:mg|miligam)\s*/\s*100\s*(?:ml|mililit)",
                r"([\d.,]+)\s*(?:mg|miligam).{0,12}mau"]:
        m = re.search(pat, t)
        if m:
            v = _so(m.group(1))
            if v is not None:
                gt[CON_MAU] = v
            break

    # --- muc vuot toc do: 'qua toc do 25 km/h', 'vuot 25km/h' ---
    if re.search(r"(qua toc do|vuot toc do|chay qua|vuot qua toc do)", t):
        m = re.search(r"([\d.,]+)\s*km/?h", t)
        if m:
            v = _so(m.group(1))
            if v is not None and v <= 100:
                gt[VUOT_TOC_DO] = v
    return gt


# ==========================================================================
# 3. SUY DIEN: gia tri co thoa nguong khong?
# ==========================================================================
def thoa_nguong(gia_tri, nguong):
    """Kiểm tra giá trị có rơi vào khoảng (can_duoi, can_tren] của ngưỡng hay không."""
    lo, hi = nguong["can_duoi"], nguong["can_tren"]
    if lo is not None and gia_tri <= lo:
        return False
    if hi is not None and gia_tri > hi:
        return False
    return True


class NumericReasoner:
    """Lập chỉ mục ngưỡng cho toàn bộ cơ sở tri thức và suy diễn khung xử phạt."""

    def __init__(self, violations):
        """Lập chỉ mục ngưỡng cho toàn bộ tập sự kiện F: với mỗi hành vi vi phạm,
        rút trích các khoảng giá trị từ chính nguyên văn quy định."""
        self.nguong = {}          # id hanh vi -> danh sach nguong
        self.theo_dai_luong = {}  # dai_luong -> [(id, nguong)]
        for v in violations:
            ng = trich_nguong(v.hanh_vi)
            if ng:
                self.nguong[v.id] = ng
                for n in ng:
                    self.theo_dai_luong.setdefault(n["dai_luong"], []).append((v.id, n))

    def suy_dien(self, truy_van, phuong_tien=None, violations_by_id=None):
        """Trả về (giá_trị_tìm_thấy, tập_id_hành_vi_thoả_mãn, giải_thích)."""
        gt = trich_gia_tri(truy_van)
        if not gt:
            return {}, None, []
        thoa, giai_thich = set(), []
        for dl, val in gt.items():
            ids = set()
            for vid, ng in self.theo_dai_luong.get(dl, []):
                if not thoa_nguong(val, ng):
                    continue
                if phuong_tien and violations_by_id:
                    v = violations_by_id.get(vid)
                    if v and not (set(phuong_tien) & set(v.phuong_tien)):
                        continue
                ids.add(vid)
            if ids:
                thoa |= ids
                giai_thich.append(
                    "Giá trị %s = %s thuộc khung %s"
                    % (TEN_DAI_LUONG[dl], ("%g" % val).replace(".", ","),
                       "; ".join(sorted({n["mo_ta"] for vid, n in self.theo_dai_luong[dl]
                                         if vid in ids and n["dai_luong"] == dl}))))
        return gt, (thoa or None), giai_thich
