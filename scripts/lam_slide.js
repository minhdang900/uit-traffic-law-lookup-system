// Slide báo cáo CS106 Nhóm 7 — bám hệ thiết kế Organic của giao diện tra cứu.
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// Chạy được ở HAI nơi, tự nhận ra mình đang ở đâu:
//   • trong repo mã nguồn   → đọc eval/ + docs/ + data/kb/, ghi ra docs/
//   • trong thư mục nộp bài → đọc so_lieu/ + ma_nguon/…, ghi ra slide/
const REPO = path.resolve(__dirname, "..");
const TRONG_REPO = fs.existsSync(path.join(REPO, "eval")) &&
                   fs.existsSync(path.join(REPO, "data", "kb"));
const GOC = process.argv[2] || (TRONG_REPO ? REPO : path.resolve(__dirname, "..", ".."));
const HINH = process.argv[3] ||
  path.join(GOC, ...(TRONG_REPO ? ["docs", "so_do"] : ["bao_cao", "hinh"]));
const RA = process.argv[4] ||
  path.join(GOC, TRONG_REPO ? "docs" : "slide", "Slide_Nhom7_CS106.pptx");
fs.mkdirSync(path.dirname(RA), { recursive: true });

/** Trả về đường dẫn đầu tiên tồn tại — cho phép cả hai bố cục thư mục. */
function tim(...ungVien) {
  for (const c of ungVien) {
    const p = path.join(GOC, c);
    if (fs.existsSync(p)) return p;
  }
  throw new Error("Khong tim thay " + ungVien[0] + " duoi " + GOC);
}
const j = (...ungVien) => JSON.parse(fs.readFileSync(tim(...ungVien), "utf8"));

const dg = j("so_lieu/ket_qua_danh_gia.json", "eval/ket_qua_danh_gia.json").summary;
const ab = j("so_lieu/ket_qua_ablation.json", "eval/ket_qua_ablation.json");
const mien = j("so_lieu/ket_qua_phat_hien_mien.json", "eval/ket_qua_phat_hien_mien.json");
const kt = j("so_lieu/ket_qua_kiem_thu.json", "eval/ket_qua_kiem_thu.json");
const kd = j("so_lieu/ket_qua_kiem_dinh.json", "eval/ket_qua_kiem_dinh.json");
const pl = j("so_lieu/ket_qua_phan_tich_loi.json", "eval/ket_qua_phan_tich_loi.json");
const tk = j("so_lieu/thong_ke_du_lieu.json", "eval/thong_ke_du_lieu.json");
const tv = j("ma_nguon/docs/thanh_vien.json", "docs/thanh_vien.json");
const dem = (f) => j(`ma_nguon/data/kb/${f}.json`, `data/kb/${f}.json`).length;

// ── bảng màu Organic (tokens.css của giao diện) ──────────────────────────────
const BG = "F5EAD8", SURFACE = "EBDDC5", TEXT = "201E1D";
const ACCENT = "C67139", ACCENT2 = "7A8A5E";
const N100 = "F9F4ED", N300 = "DCD3C4", N600 = "82796A", N700 = "645C50";
const A100 = "FFF2EB", A200 = "FFE1D0", A700 = "8C491A";
const G100 = "F0FAE1", G200 = "E1EECC", G700 = "56633F";
const TOI = "2E2B25";
const FONT = "Arial";

const pc = (x, n = 1) => (x * 100).toFixed(n).replace(".", ",") + "%";
const so = (x, n = 4) => x.toFixed(n).replace(".", ",");
const nghin = (x) => String(x).replace(/\B(?=(\d{3})+(?!\d))/g, ".");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";          // 13,333 × 7,5 inch
pres.author = "Nhóm 7 — CS106.F31.CN2";
pres.title = "Đề tài 4 — Hệ thống tra cứu kiến thức pháp luật giao thông";
const W = 13.333, H = 7.5;
const L = 0.75, RW = W - 1.5;         // lề trái và bề rộng nội dung

// ── các khối dựng lại đúng ngôn ngữ của giao diện ────────────────────────────
let STT = 0;
/** Tạo slide mới và tự tăng số thứ tự — thêm/bớt slide không phải đánh số lại. */
function slide(toi = false) {
  const s = pres.addSlide();
  s.background = { color: toi ? TOI : BG };
  STT += 1;
  return s;
}
function nen(s, mau = BG) { s.background = { color: mau }; }

function pill(s, x, y, chu, { nen: n = ACCENT, chu_mau = BG, co = 11, w = null } = {}) {
  const rong = w || Math.max(0.72, chu.length * 0.088 + 0.34);
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w: rong, h: 0.30, fill: { color: n }, line: { type: "none" },
    rectRadius: 0.15,
  });
  s.addText(chu, {
    x, y, w: rong, h: 0.30, align: "center", valign: "middle", isTextBox: true,
    margin: 0, fontFace: FONT, fontSize: co, bold: true, color: chu_mau,
  });
  return rong;
}

function the(s, x, y, w, h, { nen: n = N100, vien = N300, r = 0.14 } = {}) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, fill: { color: n },
    line: vien ? { color: vien, width: 1 } : { type: "none" },
    rectRadius: r,
  });
}

function tieu_de(s, nhan, chinh, { toi = false } = {}) {
  s.addText(nhan.toUpperCase(), {
    x: L, y: 0.42, w: RW, h: 0.26, isTextBox: true, margin: 0, fontFace: FONT,
    fontSize: 12, bold: true, charSpacing: 2, color: toi ? "F6A06B" : A700,
  });
  s.addText(chinh, {
    x: L, y: 0.72, w: RW, h: 0.62, isTextBox: true, margin: 0, fontFace: FONT,
    fontSize: 30, bold: true, color: toi ? N100 : TEXT,
  });
}

function chan(s, ghi, { toi = false } = {}) {
  s.addText(ghi, {
    x: L, y: H - 0.62, w: RW - 0.9, h: 0.3, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 10, color: toi ? N600 : N600, italic: true,
  });
  s.addText(String(STT), {
    x: W - L - 0.7, y: H - 0.62, w: 0.7, h: 0.3, isTextBox: true, margin: 0,
    align: "right", fontFace: FONT, fontSize: 10, color: N600,
  });
}

function stat(s, x, y, w, tri, nhan, { mau = ACCENT, nenThe = N100, co = 34 } = {}) {
  the(s, x, y, w, 1.38, { nen: nenThe });
  s.addText(tri, {
    x, y: y + 0.16, w, h: 0.66, isTextBox: true, margin: 0, align: "center",
    fontFace: FONT, fontSize: co, bold: true, color: mau,
  });
  s.addText(nhan, {
    x: x + 0.1, y: y + 0.84, w: w - 0.2, h: 0.44, isTextBox: true, margin: 0,
    align: "center", valign: "top", fontFace: FONT, fontSize: 11, color: N700,
  });
}

// ═══════════════════════════════════ 1. Bìa ═════════════════════════════════
{
  const s = slide(true);
  s.addShape(pres.ShapeType.ellipse, {
    x: W - 2.4, y: -1.9, w: 5.0, h: 5.0, fill: { color: "402310" },
    line: { type: "none" },
  });
  s.addShape(pres.ShapeType.ellipse, {
    x: -1.5, y: H - 1.5, w: 3.2, h: 3.2, fill: { color: "3D472B" },
    line: { type: "none" },
  });
  pill(s, L, 0.95, "CS106 · TRÍ TUỆ NHÂN TẠO", { nen: ACCENT, co: 12 });
  s.addText("ĐỀ TÀI 4", {
    x: L, y: 1.55, w: RW, h: 0.5, isTextBox: true, margin: 0, fontFace: FONT,
    fontSize: 20, bold: true, color: "F6A06B", charSpacing: 3,
  });
  s.addText("Xây dựng hệ thống\ntra cứu kiến thức pháp luật", {
    x: L, y: 2.05, w: 9.6, h: 1.9, isTextBox: true, margin: 0, fontFace: FONT,
    fontSize: 40, bold: true, color: N100, lineSpacing: 46,
  });
  s.addText("Lĩnh vực: Giao thông đường bộ  ·  Luật 36/2024/QH15 và Nghị định 168/2024/NĐ-CP", {
    x: L, y: 4.0, w: 10.2, h: 0.36, isTextBox: true, margin: 0, fontFace: FONT,
    fontSize: 15, color: "C0B6A5", italic: true,
  });
  the(s, L, 4.66, 5.7, 1.7, { nen: "3A352D", vien: "56503F" });
  s.addText([
    { text: "Giảng viên hướng dẫn\n", options: { fontSize: 11, color: "A19786" } },
    { text: "PGS.TS. Nguyễn Đình Hiển\n\n", options: { fontSize: 15, bold: true, color: N100 } },
    { text: "Lớp CS106.F31.CN2   ·   Nhóm 7   ·   7 thành viên", options: { fontSize: 12, color: "C0B6A5" } },
  ], { x: L + 0.32, y: 4.86, w: 5.1, h: 1.15, isTextBox: true, margin: 0, fontFace: FONT });

  const ten = tv.thanh_vien.map((n) => n.ho_ten);
  s.addText(
    ten.map((t, i) => ({ text: t, options: { breakLine: i !== ten.length - 1 } })),
    { x: 6.85, y: 4.66, w: 3.2, h: 1.9, isTextBox: true, margin: 0, fontFace: FONT,
      fontSize: 11.5, color: "C0B6A5", lineSpacing: 16 });
  s.addText(
    tv.thanh_vien.map((n, i) => ({ text: n.mssv, options: { breakLine: i !== 6 } })),
    { x: 10.1, y: 4.66, w: 1.5, h: 1.9, isTextBox: true, margin: 0, fontFace: FONT,
      fontSize: 11.5, color: "A19786", lineSpacing: 16 });
  s.addText("Thành phố Hồ Chí Minh, tháng 9 năm 2026", {
    x: L, y: H - 0.62, w: 6, h: 0.3, isTextBox: true, margin: 0, fontFace: FONT,
    fontSize: 10, color: N600, italic: true,
  });
  s.addNotes("Chào hội đồng. Nhóm 7 lớp CS106.F31.CN2 báo cáo Đề tài 4 — hệ thống tra cứu kiến thức pháp luật giao thông đường bộ.");
}

// ═════════════════════════ 2. Nội dung báo cáo ══════════════════════════════
{
  const s = slide();
  tieu_de(s, "Nội dung", "Sáu phần");
  const phan = [
    ["1", "Tổng quan", "Bối cảnh · phát biểu bài toán Input → Output · đóng góp", ACCENT],
    ["2", "Các công trình liên quan", "Bốn hướng tiếp cận · bộ dữ liệu đã có · khoảng trống", ACCENT],
    ["3", "Xây dựng dữ liệu", "Nguồn và cách lấy · thống kê phân bố độ dài, nhãn, chủ đề", ACCENT],
    ["4", "Phương pháp và thực nghiệm", "Kiến trúc · thuật giải B1–B6 · hàm điểm · siêu tham số", ACCENT2],
    ["5", "Kết quả và phân tích", "Chỉ số + kiểm định thống kê · ablation · phân tích lỗi sâu", ACCENT2],
    ["6", "Ứng dụng, kết luận, hướng phát triển", "Demo · hạn chế đã đo · việc còn lại", ACCENT2],
  ];
  phan.forEach(([n, t, m, c], i) => {
    const x = L + (i % 2) * (RW / 2 + 0.14);
    const y = 1.74 + Math.floor(i / 2) * 1.62;
    the(s, x, y, RW / 2 - 0.14, 1.4, { nen: i < 3 ? A100 : G100, vien: i < 3 ? "FFC6A5" : "CCDBB2" });
    s.addShape(pres.ShapeType.ellipse, {
      x: x + 0.3, y: y + 0.28, w: 0.52, h: 0.52, fill: { color: c }, line: { type: "none" },
    });
    s.addText(n, {
      x: x + 0.3, y: y + 0.28, w: 0.52, h: 0.52, isTextBox: true, margin: 0,
      align: "center", valign: "middle", fontFace: FONT, fontSize: 16, bold: true, color: BG,
    });
    s.addText(t, {
      x: x + 1.0, y: y + 0.26, w: RW / 2 - 1.3, h: 0.34, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 15.5, bold: true, color: TEXT,
    });
    s.addText(m, {
      x: x + 1.0, y: y + 0.63, w: RW / 2 - 1.3, h: 0.6, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 11.5, color: N700, lineSpacing: 15,
    });
  });
  chan(s, "Đề tài 4 · Hệ thống tra cứu kiến thức pháp luật giao thông đường bộ");
  s.addNotes("Nói nhanh bố cục, dừng lâu nhất ở phần 3 và phần 5 vì đó là phần có số đo.");
}

// ═══════════════════════════ 2. Vấn đề thực tế ══════════════════════════════
{
  const s = slide();
  tieu_de(s, "1 · Tổng quan", "Luật thì có, câu trả lời thì không");
  const y = 1.72;
  const o = [
    ["Hành vi nằm ở Luật", "Luật 36/2024/QH15 quy định hành vi nào bị nghiêm cấm — nhưng không hề nói phạt bao nhiêu.", ACCENT],
    ["Mức phạt nằm ở Nghị định", "Toàn bộ chế tài — tiền phạt, trừ điểm GPLX — nằm ở Nghị định 168/2024/NĐ-CP.", ACCENT],
    ["Và cả hai đều đã bị sửa", "Luật 118/2025 (01/7/2026) và NĐ 238/2026 (15/8/2026) sửa đổi cả hai văn bản trên.", ACCENT2],
  ];
  o.forEach(([t, m, c], i) => {
    const x = L + i * 4.02;
    the(s, x, y, 3.79, 2.2, { nen: i === 2 ? G100 : N100 });
    s.addShape(pres.ShapeType.ellipse, {
      x: x + 0.32, y: y + 0.32, w: 0.46, h: 0.46, fill: { color: c }, line: { type: "none" },
    });
    s.addText(String(i + 1), {
      x: x + 0.32, y: y + 0.32, w: 0.46, h: 0.46, isTextBox: true, margin: 0,
      align: "center", valign: "middle", fontFace: FONT, fontSize: 14, bold: true, color: BG,
    });
    s.addText(t, {
      x: x + 0.32, y: y + 0.92, w: 3.15, h: 0.34, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 15, bold: true, color: i === 2 ? G700 : TEXT,
    });
    s.addText(m, {
      x: x + 0.32, y: y + 1.28, w: 3.15, h: 0.8, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 11.5, color: N700, lineSpacing: 15,
    });
  });
  the(s, L, 4.32, RW, 1.5, { nen: A100, vien: "FFC6A5" });
  s.addText("“Vượt đèn đỏ xe máy phạt bao nhiêu?”", {
    x: L + 0.42, y: 4.54, w: RW - 0.84, h: 0.44, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 21, bold: true, color: A700,
  });
  s.addText("Câu hỏi phổ biến nhất của người dân — và không một văn bản đơn lẻ nào trả lời được. Phải đọc Luật để biết hành vi bị cấm, đọc Nghị định để biết mức phạt, rồi đối chiếu bản hợp nhất để chắc chắn đang đọc bản còn hiệu lực.", {
    x: L + 0.42, y: 5.02, w: RW - 0.84, h: 0.7, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 12.5, color: N700, lineSpacing: 17,
  });
  s.addText("→  Mục tiêu: trả lời câu hỏi tiếng Việt tự nhiên, luôn kèm căn cứ điều – khoản – điểm truy nguyên được.", {
    x: L, y: 6.08, w: RW, h: 0.4, isTextBox: true, margin: 0, fontFace: FONT,
    fontSize: 14, bold: true, color: ACCENT2,
  });
  chan(s, "Đề tài 4 · Nhóm 7");
  s.addNotes("Vấn đề không phải thiếu thông tin mà là thông tin bị tách rời giữa luật và nghị định, lại còn đang bị sửa đổi.");
}

// ══════════════════════ 3. Phát biểu bài toán ═══════════════════════════════
{
  const s = slide();
  tieu_de(s, "1 · Tổng quan", "Phát biểu bài toán: Input → Output");

  the(s, L, 1.7, 5.9, 2.42, { nen: A100, vien: "FFC6A5" });
  pill(s, L + 0.32, 1.92, "INPUT", { nen: ACCENT, co: 10 });
  s.addText("q  —  câu hỏi tiếng Việt tự nhiên", {
    x: L + 0.32, y: 2.36, w: 5.3, h: 0.3, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 12.5, bold: true, color: TEXT });
  s.addText("có dấu hoặc không dấu  ·  kèm tuỳ chọn mốc thời gian t (mặc định: hôm nay) và bộ lọc phương tiện", {
    x: L + 0.32, y: 2.68, w: 5.3, h: 0.6, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 11.5, color: "5A4032", lineSpacing: 15 });
  s.addText("Cơ sở tri thức  K = (C, R, Rules, F, Keyphrase)\nmỗi x mang căn cứ cc(x) và khoảng hiệu lực hl(x)", {
    x: L + 0.32, y: 3.3, w: 5.3, h: 0.64, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 11.5, italic: true, color: N700, lineSpacing: 15 });

  s.addText("→", { x: 6.78, y: 2.6, w: 0.6, h: 0.6, isTextBox: true, margin: 0,
    align: "center", valign: "middle", fontFace: FONT, fontSize: 30, bold: true, color: ACCENT });

  the(s, 7.45, 1.7, RW - 6.7, 2.42, { nen: G100, vien: "CCDBB2" });
  pill(s, 7.77, 1.92, "OUTPUT", { nen: ACCENT2, co: 10 });
  s.addText("A(q, t)  =  ( p,  T,  E )", {
    x: 7.77, y: 2.36, w: 4.5, h: 0.3, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 12.5, bold: true, color: TEXT });
  s.addText([
    { text: "p  ", options: { bold: true, color: G700 } },
    { text: "lớp bài toán ∈ {P1 … P7}\n", options: { color: "3F4A2E", breakLine: true } },
    { text: "T  ", options: { bold: true, color: G700 } },
    { text: `tối đa k = ${dg.top_k} mẩu tri thức đã xếp hạng, mọi x ∈ T đều còn hiệu lực tại t\n`, options: { color: "3F4A2E", breakLine: true } },
    { text: "E  ", options: { bold: true, color: G700 } },
    { text: "nguyên văn điều khoản + căn cứ cc(x) của từng x", options: { color: "3F4A2E" } },
  ], { x: 7.77, y: 2.7, w: 4.5, h: 1.3, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 11.5, lineSpacing: 15 });

  the(s, L, 4.3, RW, 0.82, { nen: SURFACE, vien: null });
  s.addText([
    { text: "Ràng buộc:  ", options: { bold: true, color: A700 } },
    { text: "hệ KHÔNG sinh ngôn ngữ tự nhiên — mọi câu chữ trong E là trích nguyên văn. Không có x nào thoả thì trả tập rỗng kèm lý do, không suy đoán.", options: { color: N700 } },
  ], { x: L + 0.34, y: 4.5, w: RW - 0.68, h: 0.46, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 12.5, lineSpacing: 16 });

  pill(s, L, 5.36, "ĐÓNG GÓP CỦA NHÓM", { nen: ACCENT, co: 10 });
  const dg4 = [
    ["Cơ sở tri thức mở", `${nghin(dem("concepts"))} khái niệm · ${nghin(dem("rules"))} quy tắc · ${nghin(dem("violations"))} hành vi, 100% có căn cứ`],
    ["Hiệu lực theo thời gian", `${nghin(dem("amendments"))} bản ghi sửa đổi lưu như DỮ LIỆU, truy vấn được theo mốc t`],
    ["Suy diễn số học", "Tính đúng khung phạt theo ngưỡng — không chỉ so khớp văn bản"],
    ["Bộ dữ liệu + số đo", `${dg.so_cau_hoi} câu hỏi gán tới ĐỊNH DANH tri thức, tái lập bằng một lệnh`],
  ];
  dg4.forEach(([t, m], i) => {
    const x = L + i * (RW / 4 + 0.02);
    the(s, x, 5.76, RW / 4 - 0.16, 0.94, { nen: N100 });
    s.addText(t, { x: x + 0.2, y: 5.9, w: RW / 4 - 0.5, h: 0.28, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 12.5, bold: true, color: A700 });
    s.addText(m, { x: x + 0.2, y: 6.16, w: RW / 4 - 0.5, h: 0.5, isTextBox: true,
      margin: 0, valign: "top", fontFace: FONT, fontSize: 10, color: N700, lineSpacing: 13 });
  });
  chan(s, "Tách bạch hai việc thường bị gộp: TÌM ĐÚNG mẩu tri thức (T) và GIẢI TRÌNH được vì sao (E)");
  s.addNotes("Nhấn ràng buộc không sinh ngôn ngữ — đây là điểm phân biệt với hướng RAG/LLM ở phần 2.");
}

// ═══════════════════ 4. Khảo sát công trình liên quan ═══════════════════════
{
  const s = slide();
  tieu_de(s, "2 · Công trình liên quan", "Bốn hướng — khác nhau ở chỗ tri thức nằm ở đâu");
  const h = [
    ["Truy hồi ngữ nghĩa\nbằng mạng nơ-ron", "Tri thức nằm trong THAM SỐ mô hình", "PhoBERT · multi-stage IR · LEGAL-BERT · COLIEE", "Trả về đoạn văn bản, không giải trình được", N600],
    ["Ontology &\nđồ thị tri thức", "Tri thức được mô hình hoá TƯỜNG MINH", "Legal-Onto · Rela-model · COKB · KG luật lao động", "Chưa có suy diễn số học, chưa phủ GTĐB 2024–2026", ACCENT2],
    ["RAG &\nmô hình ngôn ngữ lớn", "Tri thức lấy từ truy hồi, câu chữ do MÔ HÌNH SINH", "KG+RAG luật VN · agent ReAct pháp lý", "Công cụ thương mại vẫn ảo giác 17–33%", ACCENT],
    ["Hiệu lực theo\nthời gian", "Tri thức có CHIỀU THỜI GIAN", "Logic khả bác · LegalRuleML · SAT-Graph RAG", "Phía VN mới dừng ở đối sánh hai phiên bản luật", ACCENT2],
  ];
  const w = 3.0, gx = 0.19;
  h.forEach(([t, m, vd, gap, c], i) => {
    const x = L + i * (w + gx);
    the(s, x, 1.7, w, 3.3, { nen: N100 });
    s.addShape(pres.ShapeType.rect, { x, y: 1.7, w, h: 0.07, fill: { color: c }, line: { type: "none" } });
    s.addText(t, { x: x + 0.24, y: 1.92, w: w - 0.48, h: 0.66, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 14, bold: true, color: TEXT, lineSpacing: 17 });
    s.addText(m, { x: x + 0.24, y: 2.62, w: w - 0.48, h: 0.5, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 11, color: N700, lineSpacing: 14 });
    s.addText(vd, { x: x + 0.24, y: 3.14, w: w - 0.48, h: 0.72, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 10.5, italic: true, color: N600, lineSpacing: 14 });
    s.addShape(pres.ShapeType.rect, { x: x + 0.24, y: 3.92, w: w - 0.48, h: 0.012,
      fill: { color: N300 }, line: { type: "none" } });
    s.addText(gap, { x: x + 0.24, y: 4.02, w: w - 0.48, h: 0.8, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 10.5, color: A700, lineSpacing: 14 });
  });

  pill(s, L, 5.22, "CÁC BỘ DỮ LIỆU ĐÃ CÓ", { nen: ACCENT, co: 10 });
  const bo = [
    ["VLQA / DRILL", "3.129 câu hỏi · 59.636 điều luật · 27 lĩnh vực", "gán nhãn ở mức ĐIỀU"],
    ["MLQA-TSR (VLSP 2025)", "776 câu hỏi · 402 điều · 498 ảnh biển báo", "đa phương thức ảnh – văn bản"],
    ["COLIEE (Task 3–4)", "768 điều Bộ luật Dân sự Nhật", "khác hệ thống pháp luật"],
    ["Bộ dữ liệu của nhóm", `${dg.so_cau_hoi} câu hỏi · GTĐB 2024–2026`, "gán tới ĐỊNH DANH tri thức"],
  ];
  bo.forEach(([a, b_, c], i) => {
    const y = 5.6 + i * 0.32;
    const dam = i === 3;
    s.addText(a, { x: L, y, w: 3.0, h: 0.3, isTextBox: true, margin: 0, fontFace: FONT,
      fontSize: 11.5, bold: true, color: dam ? A700 : TEXT });
    s.addText(b_, { x: L + 3.05, y, w: 4.6, h: 0.3, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 11.5, color: N700 });
    s.addText(c, { x: L + 7.75, y, w: 4.1, h: 0.3, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 11.5, italic: true, color: dam ? ACCENT2 : N600 });
  });
  chan(s, "Chỉ ghi con số kiểm chứng được từ nguồn chính thức — ALQAC và Zalo 2021 để trống thay vì điền số ước đoán");
  s.addNotes("Nếu hội đồng hỏi về ALQAC hay Zalo: nhóm chưa kiểm chứng được quy mô từ nguồn gốc nên không điền số.");
}

// ═══════════════════════════ 5. Khoảng trống ════════════════════════════════
{
  const s = slide();
  tieu_de(s, "2 · Công trình liên quan", "Khoảng trống — và chỗ nhóm đứng vào");
  const gap = [
    ["Miền", "Chưa có hệ tra cứu tri thức cho GTĐB Việt Nam theo khung 2024–2026",
     "Công trình KG cùng miền gần nhất dựa trên Luật 23/2008 đã hết hiệu lực"],
    ["Đầu ra", "Các hệ hiện có trả về ĐOẠN VĂN BẢN, không phải tri thức có cấu trúc",
     "Chấm ở mức “xếp hạng điều luật đúng” — không đo được khả năng giải trình"],
    ["Suy diễn", "Chưa có công trình tiếng Việt ghép mô hình tri thức với suy diễn SỐ HỌC",
     "GTĐB đòi hỏi tính mức phạt, thời hạn tước GPLX, điểm trừ theo điều kiện"],
    ["Thời gian", "Chưa mô hình hoá hiệu lực theo thời gian cho pháp luật Việt Nam",
     "Lý thuyết đã có ở quốc tế; phía VN mới dừng ở phát hiện thay đổi giữa hai bản"],
    ["Tin cậy", "RAG/LLM chưa đảm bảo trung thực căn cứ ở mức chấp nhận được",
     "Nhóm loại bỏ hoàn toàn khâu sinh — đổi độ “mượt” lấy truy vết 100% căn cứ"],
  ];
  gap.forEach(([nhan, t, m], i) => {
    const y = 1.68 + i * 0.86;
    the(s, L, y, RW, 0.76, { nen: i === 4 ? G100 : N100, vien: i === 4 ? "CCDBB2" : N300 });
    pill(s, L + 0.24, y + 0.23, nhan.toUpperCase(), { nen: i === 4 ? ACCENT2 : ACCENT, co: 9, w: 1.3 });
    s.addText(t, { x: L + 1.72, y: y + 0.1, w: 6.3, h: 0.3, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 12.5, bold: true, color: TEXT });
    s.addText(m, { x: L + 1.72, y: y + 0.4, w: 6.3, h: 0.3, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 11, color: N700 });
    s.addText("→  " + ["Nhóm xây trên Luật 36/2024 + NĐ 168/2024 + hai văn bản sửa đổi",
                       "Nhóm trả về khái niệm, quy tắc, hành vi + căn cứ điều–khoản–điểm",
                       "Nhóm có NumericReasoner rút ngưỡng từ chính nguyên văn điều khoản",
                       "Nhóm gắn khoảng hiệu lực hl(x) cho từng mẩu tri thức",
                       "Nhóm chỉ ghép nguyên văn điều khoản, không diễn giải lại"][i], {
      x: L + 8.2, y: y + 0.17, w: RW - 8.44, h: 0.46, isTextBox: true, margin: 0,
      valign: "middle", fontFace: FONT, fontSize: 11, color: i === 4 ? G700 : A700, lineSpacing: 14 });
  });
  chan(s, "Năm khoảng trống — ba cái đầu là đóng góp về tài nguyên, hai cái sau là đóng góp về phương pháp");
  s.addNotes("Đây là slide trả lời câu hỏi “đề tài này mới ở chỗ nào”. Nhấn cột phải.");
}

// ═════════════════════════ 3. Cơ sở tri thức ════════════════════════════════
{
  const s = slide();
  tieu_de(s, "3 · Xây dựng dữ liệu", "K = (C, R, Rules, F, Keyphrase)");
  const o = [
    [nghin(dem("concepts")), "Khái niệm  C\nđịnh nghĩa pháp lý", ACCENT],
    [nghin(dem("relations")), "Quan hệ  R\nđồ thị nối tri thức", ACCENT],
    [nghin(dem("rules")), "Quy tắc  Rules\nphải / không được làm", ACCENT],
    [nghin(dem("violations")), "Hành vi vi phạm  F\nkèm chế tài có kiểu", ACCENT2],
    [nghin(dem("keyphrases")), "Cụm từ khoá\ncầu nối ngôn ngữ người dùng", ACCENT2],
  ];
  const w = 2.17, gap = 0.245;
  o.forEach(([v, n, c], i) => {
    const x = L + i * (w + gap);
    the(s, x, 1.78, w, 1.72, { nen: i > 2 ? G100 : A100, vien: i > 2 ? "CCDBB2" : "FFC6A5" });
    s.addText(v, {
      x, y: 1.94, w, h: 0.68, isTextBox: true, margin: 0, align: "center",
      fontFace: FONT, fontSize: 34, bold: true, color: c,
    });
    s.addText(n, {
      x: x + 0.08, y: 2.62, w: w - 0.16, h: 0.8, isTextBox: true, margin: 0,
      align: "center", fontFace: FONT, fontSize: 11, color: N700, lineSpacing: 14,
    });
  });
  s.addText("Mọi mục tri thức đều mang căn cứ pháp lý (điều – khoản – điểm – văn bản) và khoảng hiệu lực (từ, đến).", {
    x: L, y: 3.68, w: RW, h: 0.34, isTextBox: true, margin: 0, fontFace: FONT,
    fontSize: 13, color: N700, italic: true,
  });

  the(s, L, 4.2, 7.5, 2.3, { nen: N100 });
  pill(s, L + 0.34, 4.42, "BỐN VĂN BẢN NGUỒN", { nen: ACCENT, co: 10 });
  const vb = [
    ["Luật 36/2024/QH15", "văn bản chính — hành vi bị cấm", "01/01/2025"],
    ["Nghị định 168/2024/NĐ-CP", "văn bản chế tài — mức phạt", "01/01/2025"],
    ["Luật 118/2025/QH15", "sửa đổi Luật 36/2024", "01/7/2026"],
    ["Nghị định 238/2026/NĐ-CP", "sửa đổi NĐ 168/2024", "15/8/2026"],
  ];
  vb.forEach(([a, b, c], i) => {
    const y = 4.88 + i * 0.37;
    s.addText(a, { x: L + 0.34, y, w: 2.6, h: 0.3, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 11.5, bold: true, color: TEXT });
    s.addText(b, { x: L + 3.0, y, w: 3.1, h: 0.3, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 11.5, color: N700 });
    s.addText(c, { x: L + 6.05, y, w: 1.1, h: 0.3, isTextBox: true, margin: 0,
      align: "right", fontFace: FONT, fontSize: 11.5, color: N600 });
  });

  the(s, 8.55, 4.2, RW - 7.8, 2.3, { nen: A200, vien: ACCENT });
  s.addText("Vì sao 4 văn bản chứ không phải 1?", {
    x: 8.87, y: 4.42, w: 3.35, h: 0.34, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 14, bold: true, color: A700,
  });
  s.addText("Luật quy định hành vi, nghị định mới quy định mức phạt. Chỉ dùng luật gốc thì không trả lời được câu hỏi “phạt bao nhiêu tiền”. Hai văn bản sửa đổi để hệ thống trả lời đúng theo mốc thời gian.", {
    x: 8.87, y: 4.8, w: 3.35, h: 1.5, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 11.5, color: "5A4032", lineSpacing: 15,
  });
  chan(s, "Đối chiếu Văn bản hợp nhất 55/VBHN-VPQH ngày 23/3/2026 — tức bản sau sửa đổi");
  s.addNotes("Nhấn mạnh phần giải trình: đề ghi 01 văn bản, nhóm dùng 4 và đây là quyết định thiết kế, không phải làm lệch đề.");
}

// ═════════════════ Thống kê dữ liệu — phân bố độ dài ════════════════════════
{
  const s = slide();
  tieu_de(s, "3 · Xây dựng dữ liệu", "Thống kê: phân bố độ dài");
  s.addImage({ path: path.join(HINH, "hinh3_phan_bo_do_dai.png"), x: 0.62, y: 1.46, w: 8.5, h: 3.63 });

  const ch = tk.do_dai.cau_hoi, qt = tk.do_dai.quy_tac, hv = tk.do_dai.hanh_vi;
  the(s, 9.35, 1.5, RW - 8.6, 3.55, { nen: A100, vien: "FFC6A5" });
  s.addText([
    { text: "Câu hỏi ngắn, văn bản luật dài.\n\n", options: { fontSize: 14, bold: true, color: A700, breakLine: true } },
    { text: `Câu hỏi trung bình ${so(ch.trung_binh, 2)} từ (trung vị ${ch.trung_vi}, khoảng ${ch.min}–${ch.max}).\n\n`, options: { color: "5A4032", breakLine: true } },
    { text: `Quy tắc trung bình ${so(qt.trung_binh, 1)} từ, hành vi vi phạm ${so(hv.trung_binh, 1)} từ — dài gấp khoảng ${so(qt.trung_binh / ch.trung_binh, 1)} lần câu hỏi.\n\n`, options: { color: "5A4032", breakLine: true } },
    { text: "Đây là gốc rễ của bài toán: câu ngắn và đời thường phải khớp với văn bản dài và trang trọng.", options: { color: "5A4032" } },
  ], { x: 9.62, y: 1.76, w: 3.1, h: 3.1, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 11.5, lineSpacing: 15 });

  the(s, L, 5.3, RW, 1.34, { nen: SURFACE, vien: null });
  s.addText([
    { text: "Đuôi lệch phải là chỗ đáng chú ý.  ", options: { bold: true, color: TEXT } },
    { text: `75% câu dưới ${ch.p75} từ, nhưng đuôi kéo tới ${ch.max} từ — đó là các câu khẩu ngữ kể cả tình huống (“Nhóm em 4 đứa đi chung một xe máy, không ai đội mũ bảo hiểm, lại còn…”). Phần 5 sẽ cho thấy phần lớn ca lỗi NẶNG tập trung đúng ở đuôi này: câu càng dài, keyphrase càng bị loãng giữa các từ không mang thông tin pháp lý.`, options: { color: N700 } },
  ], { x: L + 0.34, y: 5.5, w: RW - 0.68, h: 0.98, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 12.5, lineSpacing: 17 });
  chan(s, "python scripts/thong_ke_du_lieu.py — số liệu sinh lại được, không chép tay");
  s.addNotes("Chỉ vào đuôi phải của histogram khi nói câu dài là chỗ hệ thống yếu nhất.");
}

// ═══════════ Thống kê dữ liệu — phân bố nhãn và chủ đề ══════════════════════
{
  const s = slide();
  tieu_de(s, "3 · Xây dựng dữ liệu", "Thống kê: phân bố nhãn và phân bố chủ đề");

  const TEN_LOP = { P1_TRA_CUU_KHAI_NIEM: "P1", P2_TRA_CUU_QUY_DINH: "P2",
    P3_TRA_CUU_CHE_TAI: "P3", P4_TRA_CUU_NGUOC: "P4", P5_SUY_DIEN_TINH_HUONG: "P5",
    P6_TRA_CUU_CAN_CU: "P6", P7_TRA_CUU_LIEN_QUAN: "P7" };
  const khoaLop = Object.keys(TEN_LOP);
  const nhanLop = khoaLop.map((k) => TEN_LOP[k]);
  const lxk = tk.nhan.lop_x_do_kho;
  s.addChart(
    pres.ChartType.bar,
    [
      { name: "Dễ", labels: nhanLop, values: khoaLop.map((k) => (lxk[k] || {}).de || 0) },
      { name: "Trung bình", labels: nhanLop, values: khoaLop.map((k) => (lxk[k] || {}).trung_binh || 0) },
      { name: "Khó", labels: nhanLop, values: khoaLop.map((k) => (lxk[k] || {}).kho || 0) },
    ],
    {
      x: L, y: 1.56, w: 6.3, h: 2.86,
      barDir: "col", barGrouping: "stacked", barGapWidthPct: 55,
      chartColors: [G200, ACCENT2, ACCENT],
      showTitle: true, title: "Số câu hỏi theo lớp bài toán × mức độ khó",
      titleFontFace: FONT, titleFontSize: 12.5, titleColor: TEXT,
      showValue: false,
      catAxisLabelColor: N700, catAxisLabelFontFace: FONT, catAxisLabelFontSize: 11,
      valAxisLabelColor: N600, valAxisLabelFontFace: FONT, valAxisLabelFontSize: 9,
      valAxisMinVal: 0, valAxisMajorUnit: 10,
      valGridLine: { color: N300, size: 0.5 }, catGridLine: { style: "none" },
      showLegend: true, legendPos: "t", legendFontFace: FONT, legendFontSize: 10,
      legendColor: N700, plotArea: { fill: { color: BG } }, chartArea: { fill: { color: BG } },
    },
  );

  const TEN_LV = { LV_QUY_TAC: "Quy tắc GT", LV_AN_TOAN: "An toàn người", 
    LV_NGUOI_LAI: "ĐK người lái", LV_PHUONG_TIEN: "ĐK phương tiện",
    LV_VAN_TAI: "Vận tải", LV_KHAC: "Khác" };
  const khoaLV = Object.keys(TEN_LV).slice().reverse();
  const tKB = khoaLV.reduce((a, k) => a + (tk.chu_de.linh_vuc_kb[k] || 0), 0) || 1;
  const tQA = khoaLV.reduce((a, k) => a + (tk.chu_de.linh_vuc_qa[k] || 0), 0) || 1;
  s.addChart(
    pres.ChartType.bar,
    [
      { name: "Cơ sở tri thức", labels: khoaLV.map((k) => TEN_LV[k]),
        values: khoaLV.map((k) => +(100 * (tk.chu_de.linh_vuc_kb[k] || 0) / tKB).toFixed(1)) },
      { name: "Bộ câu hỏi", labels: khoaLV.map((k) => TEN_LV[k]),
        values: khoaLV.map((k) => +(100 * (tk.chu_de.linh_vuc_qa[k] || 0) / tQA).toFixed(1)) },
    ],
    {
      x: 6.95, y: 1.56, w: RW - 6.2, h: 2.86,
      barDir: "bar", barGrouping: "clustered", barGapWidthPct: 45,
      chartColors: [ACCENT, ACCENT2],
      showTitle: true, title: "Tỉ trọng theo 6 lĩnh vực (%)",
      titleFontFace: FONT, titleFontSize: 12.5, titleColor: TEXT,
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 8.5,
      dataLabelColor: N700, dataLabelFontFace: FONT, dataLabelFormatCode: "0",
      catAxisLabelColor: N700, catAxisLabelFontFace: FONT, catAxisLabelFontSize: 10,
      valAxisLabelColor: N600, valAxisLabelFontFace: FONT, valAxisLabelFontSize: 9,
      valAxisMinVal: 0, valAxisMaxVal: 50, valAxisMajorUnit: 25,
      valGridLine: { color: N300, size: 0.5 }, catGridLine: { style: "none" },
      showLegend: true, legendPos: "t", legendFontFace: FONT, legendFontSize: 10,
      legendColor: N700, plotArea: { fill: { color: BG } }, chartArea: { fill: { color: BG } },
    },
  );

  const o = [
    ["Không chia đều là CHỦ Ý", `Tra cứu chế tài P3 chiếm ${tk.nhan.lop_bai_toan.P3_TRA_CUU_CHE_TAI}/${dg.so_cau_hoi} câu vì đó là câu người dân hỏi nhiều nhất.`, A100, "FFC6A5", A700],
    ["Câu nhiều đáp án", `${tk.nhan.so_cau_nhieu_dap_an}/${dg.so_cau_hoi} câu có nhiều hơn một mẩu tri thức đúng — chi tiết này giải thích con số precision ở phần 5.`, N100, N300, TEXT],
    ["Hạn chế nhóm tự nêu", "Bộ câu hỏi phản ánh NHU CẦU TRA CỨU, nên chưa phủ đều cơ sở tri thức — lĩnh vực điều kiện phương tiện bị đánh giá nhẹ hơn tỉ trọng thật.", G100, "CCDBB2", G700],
  ];
  o.forEach(([t, m, bg, vien, mau], i) => {
    const x = L + i * (RW / 3 + 0.06);
    the(s, x, 4.66, RW / 3 - 0.12, 1.7, { nen: bg, vien });
    s.addText(t, { x: x + 0.26, y: 4.86, w: RW / 3 - 0.64, h: 0.3, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 13, bold: true, color: mau });
    s.addText(m, { x: x + 0.26, y: 5.2, w: RW / 3 - 0.64, h: 1.0, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 11, color: N700, lineSpacing: 15 });
  });
  chan(s, `Cơ sở tri thức chia thành 6 lĩnh vực và ${tk.chu_de.so_nhom_trong_taxonomy} nhóm hành vi`);
  s.addNotes("Chủ động nêu hạn chế phủ chưa đều trước khi hội đồng hỏi — đó là điểm cộng, không phải điểm trừ.");
}

// ═════════════════════════════ 4. Kiến trúc ═════════════════════════════════
{
  const s = slide();
  tieu_de(s, "4 · Phương pháp", "Ba tầng nối tiếp, tri thức có kiểu suốt đường đi");
  s.addImage({ path: path.join(HINH, "hinh1_kien_truc.png"), x: 1.32, y: 1.5, w: 7.34, h: 5.1 });
  const y0 = 1.75;
  [["QueryAnalyzer", "biến câu hỏi tiếng Việt thành biểu diễn hình thức Q"],
   ["InferenceEngine", "chọn bộ giải P1–P7, truy hồi từ cơ sở tri thức"],
   ["sinh_van_ban", "ghép câu trả lời kèm căn cứ pháp lý"]].forEach(([t, m], i) => {
    const y = y0 + i * 1.16;
    s.addText(t, { x: 9.9, y, w: 2.68, h: 0.3, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 14, bold: true, color: A700 });
    s.addText(m, { x: 9.9, y: y + 0.32, w: 2.68, h: 0.78, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 11.5, color: N700, lineSpacing: 15 });
  });
  the(s, 9.9, 5.34, 2.68, 1.32, { nen: G100, vien: "CCDBB2" });
  s.addText("Tầng dense embedding là tuỳ chọn và mặc định KHÔNG được gọi — lý do ở phần hạn chế.", {
    x: 10.12, y: 5.54, w: 2.24, h: 1.0, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 11, color: G700, lineSpacing: 14,
  });
  chan(s, "Tầng suy diễn và cơ sở tri thức tách rời — đổi cơ sở tri thức không phải sửa bộ giải");
  s.addNotes("Ba tầng: phân tích truy vấn, suy diễn, sinh câu trả lời. Cơ sở tri thức đứng bên cạnh chứ không nằm trong tầng suy diễn.");
}

// ═════════════════════════════ 5. Luồng B1–B6 ═══════════════════════════════
{
  const s = slide();
  tieu_de(s, "4 · Phương pháp", "Sáu bước, bám theo một truy vấn thật");
  s.addImage({ path: path.join(HINH, "hinh2_luong_b1_b6.png"), x: 1.57, y: 1.45, w: 10.2, h: 5.317 });
  chan(s, "Vì sao B2 khớp cụm dài nhất: “nồng độ cồn” phải thắng hai cụm rời “nồng độ” và “cồn” — khớp cụm ngắn trước thì mọi bước sau đều sai theo");
  s.addNotes("Chỉ vào ô ví dụ: chữ nhậu không có trong luật, B2 không khớp cụm nào, nhưng B5 vẫn ra đúng khung nhờ TF-IDF.");
}

// ═════════════════════ 6. Bảy lớp bài toán + hàm điểm ═══════════════════════
{
  const s = slide();
  tieu_de(s, "4 · Phương pháp", "Bảy lớp bài toán và hàm điểm lai");
  const lop = [
    ["P1", "Tra cứu khái niệm", "Xe cơ giới là gì?"],
    ["P2", "Tra cứu quy định", "Quy tắc nhường đường tại nơi giao nhau?"],
    ["P3", "Tra cứu chế tài", "Vượt đèn đỏ xe máy phạt bao nhiêu?"],
    ["P4", "Tra cứu ngược", "Lỗi nào bị trừ 10 điểm giấy phép lái xe?"],
    ["P5", "Suy diễn tình huống", "Vừa vượt đèn đỏ vừa không có bằng?"],
    ["P6", "Tra cứu căn cứ", "Điều 6 khoản 9 điểm a NĐ 168 nói lỗi gì?"],
    ["P7", "Tra cứu liên quan", "Cho tôi thông tin về điểm giấy phép lái xe."],
  ];
  const w = 3.79, h = 1.0, gx = 0.23, gy = 0.18;
  lop.forEach(([ma, ten, vd], i) => {
    const x = L + (i % 3) * (w + gx), y = 1.72 + Math.floor(i / 3) * (h + gy);
    the(s, x, y, w, h, { nen: N100 });
    pill(s, x + 0.24, y + 0.2, ma, { nen: i === 6 ? ACCENT2 : ACCENT, co: 10, w: 0.56 });
    s.addText(ten, { x: x + 0.94, y: y + 0.18, w: w - 1.15, h: 0.3, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 13, bold: true, color: TEXT });
    s.addText(vd, { x: x + 0.24, y: y + 0.56, w: w - 0.48, h: 0.4, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 10.5, color: N600, italic: true });
  });
  const xN = L + (w + gx), yN = 1.72 + 2 * (h + gy);
  the(s, xN, yN, w * 2 + gx, h, { nen: G100, vien: "CCDBB2" });
  s.addText("Phân lớp KHÔNG chặn kết quả: sau khi bộ giải chạy, hệ luôn bổ sung đủ ba loại tri thức còn thiếu nếu điểm ≥ 0,40 — nhờ vậy một câu bị phân lớp sai vẫn có cơ hội trả đúng.", {
    x: xN + 0.26, y: yN + 0.16, w: w * 2 + gx - 0.52, h: 0.7,
    isTextBox: true, margin: 0, fontFace: FONT, fontSize: 12, color: G700, lineSpacing: 16,
  });

  the(s, L, 5.26, 8.0, 1.4, { nen: SURFACE, vien: null });
  s.addText("Hàm điểm lai", { x: L + 0.34, y: 5.4, w: 2.4, h: 0.28, isTextBox: true,
    margin: 0, fontFace: FONT, fontSize: 13, bold: true, color: A700 });
  s.addText("score = 0,55·s_keyphrase + 0,30·s_ngữ_nghĩa + 0,15·s_ngữ_cảnh", {
    x: L + 0.34, y: 5.7, w: 7.4, h: 0.3, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 12.5, bold: true, color: TEXT,
  });
  s.addText("Keyphrase nhận trọng số cao nhất vì là tín hiệu chắc chắn; TF-IDF char n-gram lo phần phủ cho câu khẩu ngữ; ngữ cảnh chỉ để phân biệt các hành vi na ná nhau.", {
    x: L + 0.34, y: 6.02, w: 7.32, h: 0.56, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 11, color: N700, lineSpacing: 14,
  });
  the(s, 9.05, 5.26, 1.66, 1.4, { nen: N100 });
  s.addText(pc(ab.toan_bo["A. Chỉ so khớp ngữ nghĩa (TF-IDF)"].top1 / 100, 1), {
    x: 9.05, y: 5.44, w: 1.66, h: 0.5, isTextBox: true, margin: 0, align: "center",
    fontFace: FONT, fontSize: 22, bold: true, color: N600 });
  s.addText("chỉ TF-IDF", { x: 9.05, y: 5.96, w: 1.66, h: 0.28, isTextBox: true,
    margin: 0, align: "center", fontFace: FONT, fontSize: 11, color: N700 });
  the(s, 10.92, 5.26, 1.66, 1.4, { nen: A100, vien: "FFC6A5" });
  s.addText(pc(ab.toan_bo["D. Hệ thống đầy đủ (C + suy diễn số học)"].top1 / 100, 1), {
    x: 10.92, y: 5.44, w: 1.66, h: 0.5, isTextBox: true, margin: 0, align: "center",
    fontFace: FONT, fontSize: 22, bold: true, color: ACCENT });
  s.addText("hệ đầy đủ", { x: 10.92, y: 5.96, w: 1.66, h: 0.28, isTextBox: true,
    margin: 0, align: "center", fontFace: FONT, fontSize: 11, color: N700 });
  chan(s, "Top-1 trên 120 câu hỏi");
  s.addNotes("Bảy lớp bài toán phủ đủ hai yêu cầu của đề: tra cứu quy định và tra cứu theo ngữ nghĩa.");
}


// ═══════════════════════ Cấu hình siêu tham số ══════════════════════════════
{
  const s = slide();
  tieu_de(s, "4 · Phương pháp", "Cấu hình siêu tham số");

  the(s, L, 1.68, 7.55, 2.5, { nen: A100, vien: "FFC6A5" });
  s.addText("score(x, q)  =  0,55 · s_keyphrase  +  0,30 · s_ngữ_nghĩa  +  0,15 · s_ngữ_cảnh", {
    x: L + 0.34, y: 1.9, w: 6.9, h: 0.34, isTextBox: true, margin: 0,
    fontFace: "Courier New", fontSize: 12.5, bold: true, color: TEXT });
  const ts = [
    ["ALPHA = 0,55", "làn keyphrase — tín hiệu chắc chắn nhất"],
    ["BETA = 0,30", "làn ngữ nghĩa TF-IDF — lo phần phủ"],
    ["GAMMA = 0,15", "làn ngữ cảnh — phân biệt hành vi na ná nhau"],
    ["ngưỡng bổ sung = 0,40", "bổ sung loại tri thức còn thiếu sau khi bộ giải chạy"],
    ["ngưỡng nhóm ngữ nghĩa = 0,24", "tối đa 2 nhóm — chặn suy đoán khi tín hiệu yếu"],
  ];
  ts.forEach(([a, b_], i) => {
    const y = 2.38 + i * 0.34;
    s.addText(a, { x: L + 0.34, y, w: 2.9, h: 0.3, isTextBox: true, margin: 0,
      fontFace: "Courier New", fontSize: 11, bold: true, color: A700 });
    s.addText(b_, { x: L + 3.3, y, w: 4.1, h: 0.3, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 11, color: "5A4032" });
  });

  the(s, 8.55, 1.68, RW - 7.8, 2.5, { nen: N100 });
  pill(s, 8.87, 1.9, "ĐẶC TRƯNG", { nen: ACCENT2, co: 9 });
  s.addText([
    { text: "TF-IDF ký tự\n", options: { bold: true, color: TEXT, breakLine: true } },
    { text: "char_wb · n-gram 3–5 · sublinear_tf\nchịu lỗi chính tả và cách tách từ tiếng Việt\n\n", options: { color: N700, breakLine: true } },
    { text: "TF-IDF từ\n", options: { bold: true, color: TEXT, breakLine: true } },
    { text: "word · n-gram 1–3 · sublinear_tf\ngiữ được cụm nhiều từ\n\n", options: { color: N700, breakLine: true } },
    { text: `k = ${dg.top_k} kết quả mỗi truy vấn`, options: { bold: true, color: TEXT } },
  ], { x: 8.87, y: 2.3, w: 3.4, h: 1.76, isTextBox: true, margin: 0, valign: "top",
       fontFace: FONT, fontSize: 10.5, lineSpacing: 13 });

  the(s, L, 4.38, RW, 1.5, { nen: G100, vien: "CCDBB2" });
  s.addText("Hệ thống KHÔNG huấn luyện mô hình nào", {
    x: L + 0.36, y: 4.58, w: 6.0, h: 0.32, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 15, bold: true, color: G700 });
  s.addText([
    { text: "Không có bước học tham số, không có tập huấn luyện — nên cũng không có rủi ro rò rỉ dữ liệu giữa tập huấn luyện và tập đánh giá. ", options: { color: "3F4A2E" } },
    { text: `Ba trọng số là lựa chọn thiết kế và được BIỆN MINH BẰNG SỐ ĐO ở thí nghiệm ablation, không phải tinh chỉnh trên chính ${dg.so_cau_hoi} câu hỏi đánh giá.`, options: { bold: true, color: G700 } },
  ], { x: L + 0.36, y: 4.94, w: RW - 0.72, h: 0.84, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 12.5, lineSpacing: 17 });

  s.addText("Tầng dense embedding (tuỳ chọn, mặc định TẮT):  paraphrase-multilingual-MiniLM-L12-v2  ·  ngưỡng miền an toàn 0,45  ·  ngưỡng nghiêm ngặt 0,52  ·  mô hình ~470 MB", {
    x: L, y: 6.06, w: RW, h: 0.42, isTextBox: true, margin: 0, fontFace: FONT,
    fontSize: 11, color: N700, lineSpacing: 14 });
  chan(s, "Mọi giá trị đều nằm trong mã nguồn và có test khoá lại — không có tham số nào chỉnh ngầm lúc chạy");
  s.addNotes("Câu hỏi hay gặp: ba trọng số này chọn kiểu gì? Trả lời: thiết kế, rồi chứng minh bằng ablation ở slide sau.");
}

// ═══════════════════════════ 7. Kết quả chính ═══════════════════════════════
{
  const s = slide();
  tieu_de(s, "5 · Kết quả", `Kết quả trên ${dg.so_cau_hoi} câu hỏi có đáp án chuẩn`);
  const o = [
    [pc(dg.do_chinh_xac_phan_lop, 2), "Độ chính xác phân lớp", ACCENT, A100, "FFC6A5"],
    [pc(dg.top1, 2), "Top-1 — cổng chỉ số của CI", ACCENT, A100, "FFC6A5"],
    [pc(dg.top5, 2), `Top-5 — ${dg.so_cau_sai}/${dg.so_cau_hoi} câu sai hoàn toàn`, ACCENT2, G100, "CCDBB2"],
    [so(dg.mrr), "MRR — đáp án đúng ở vị trí 1–2", ACCENT2, G100, "CCDBB2"],
  ];
  const w = 2.78, gx = 0.23;
  o.forEach((r, i) => {
    const x = L + i * (w + gx);
    the(s, x, 1.72, w, 1.5, { nen: r[3], vien: r[4] });
    s.addText(r[0], { x, y: 1.88, w, h: 0.62, isTextBox: true, margin: 0, align: "center",
      fontFace: FONT, fontSize: 30, bold: true, color: r[2] });
    s.addText(r[1], { x: x + 0.14, y: 2.52, w: w - 0.28, h: 0.6, isTextBox: true, margin: 0,
      align: "center", fontFace: FONT, fontSize: 11.5, color: N700, lineSpacing: 15 });
  });

  const lop = Object.entries(dg.theo_lop_bai_toan);
  const nhan = lop.map(([k]) => k.split("_")[0]);
  s.addChart(
    pres.ChartType.bar,
    [
      { name: "Top-1", labels: nhan, values: lop.map(([, v]) => +(v.top1 * 100).toFixed(1)) },
      { name: "Top-5", labels: nhan, values: lop.map(([, v]) => +(v.top5 * 100).toFixed(1)) },
    ],
    {
      x: L, y: 3.42, w: 7.3, h: 3.28,
      barDir: "col", barGrouping: "clustered", barGapWidthPct: 60,
      chartColors: [ACCENT, ACCENT2],
      showTitle: true, title: "Top-1 và Top-5 theo từng lớp bài toán (%)",
      titleFontFace: FONT, titleFontSize: 13, titleColor: TEXT,
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 8.5,
      dataLabelColor: N700, dataLabelFontFace: FONT, dataLabelFormatCode: "0",
      catAxisLabelColor: N700, catAxisLabelFontFace: FONT, catAxisLabelFontSize: 11,
      valAxisLabelColor: N600, valAxisLabelFontFace: FONT, valAxisLabelFontSize: 9,
      valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 25,
      valGridLine: { color: N300, size: 0.5 }, catGridLine: { style: "none" },
      showLegend: true, legendPos: "t", legendFontFace: FONT, legendFontSize: 10,
      legendColor: N700, plotArea: { fill: { color: BG } }, chartArea: { fill: { color: BG } },
    },
  );

  the(s, 8.4, 3.42, RW - 7.65, 3.28, { nen: N100 });
  pill(s, 8.72, 3.64, "NHẬN XÉT", { nen: ACCENT, co: 10 });
  s.addText([
    { text: "P2 và P7 có Top-1 thấp nhưng Top-5 rất cao.\n", options: { bold: true, color: TEXT, breakLine: true } },
    { text: "Đáp án đúng CÓ trong danh sách trả về, chỉ chưa xếp đầu. P2 vì nhiều quy tắc gần nghĩa; P7 vì “kiến thức liên quan” vốn không có một đáp án duy nhất.\n\n", options: { color: N700, breakLine: true } },
    { text: `Precision ${so(dg.precision_macro)} không phải khiếm khuyết.\n`, options: { bold: true, color: TEXT, breakLine: true } },
    { text: `Trả k = ${dg.top_k} kết quả cho đáp án một mẩu → trần toán học 0,20 mỗi câu. Recall ${so(dg.recall_macro)} mới là chỉ số phản ánh đúng mục tiêu của một hệ tra cứu.`, options: { color: N700 } },
  ], { x: 8.72, y: 4.08, w: 3.55, h: 2.4, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 11.5, lineSpacing: 15 });
  chan(s, `Thời gian trả lời trung bình ${so(dg.thoi_gian_tb_ms, 1)} ms · chạy hoàn toàn cục bộ`);
  s.addNotes("Chủ động nêu P2 và P7 trước khi hội đồng hỏi. Precision thấp là do thiết kế trả 5 kết quả, không phải lỗi.");
}

// ═══════════════════ Kiểm định ý nghĩa thống kê ═════════════════════════════
{
  const s = slide();
  tieu_de(s, "5 · Kết quả", "Kiểm định: con số có đứng vững không?");
  const mc = kd.mcnemar_suy_dien_so_hoc, tp = kd.tran_precision, bd = kd.bo_dau;

  const o = [
    ["a", "Suy diễn số học có thật sự cải thiện?",
     `McNemar: ${mc.sai_thanh_dung} câu sai → đúng, ${mc.dung_thanh_sai} câu đúng → sai,  p = ${so(mc.p, 6)}`,
     "p < 0,001 nên KHÔNG phải ngẫu nhiên. Đáng chú ý hơn trị số p là hình dạng bảng chéo: không câu nào bị suy diễn số học làm hỏng — thành phần này chỉ thêm chứ không phá.",
     A100, "FFC6A5", A700],
    ["b", `Precision ${so(tp.precision)} là kém hay đã kịch trần?`,
     `Trần toán học trên chính bộ câu hỏi này = ${so(tp.tran)}  →  đạt ${pc(tp.dat_duoc_so_voi_tran, 1)} của trần`,
     `Trả k = ${dg.top_k} kết quả cho câu chỉ có một đáp án thì precision tối đa là 0,20. Precision thấp là HỆ QUẢ CỦA THIẾT KẾ top-k, không phải khiếm khuyết mô hình — recall ${so(dg.recall_macro)} mới phản ánh đúng mục tiêu.`,
     N100, N300, TEXT],
    ["c", "Có chịu được truy vấn gõ không dấu?",
     `Bỏ dấu toàn bộ: Top-1 ${pc(bd.top1.ty_le, 2)} · Top-5 ${pc(bd.top5.ty_le, 2)} · phân lớp ${pc(bd.phan_lop.ty_le, 2)}`,
     "TRÙNG KHỚP tuyệt đối với bản có dấu ở cả bảy lớp. Vì mọi keyphrase đều lưu kèm bản không dấu và B1 chuẩn hoá về bản đó — dấu không tham gia vào so khớp.",
     G100, "CCDBB2", G700],
    ["d", "Mọi câu hỏi có thật sự chấm được?",
     `${kd.cham_duoc.so_cau}/${dg.so_cau_hoi} câu có đáp án chuẩn giải được về tri thức CÓ THẬT — 0 định danh treo`,
     "Có test kiểm chứng riêng. Nếu bước này không được kiểm thì mọi chỉ số ở trên đều vô nghĩa, vì có thể hệ đang bị chấm trên những câu không thể đúng.",
     N100, N300, TEXT],
  ];
  o.forEach(([n, hoi, so_do, y_nghia, bg, vien, mau], i) => {
    const x = L + (i % 2) * (RW / 2 + 0.14);
    const y = 1.6 + Math.floor(i / 2) * 2.42;
    the(s, x, y, RW / 2 - 0.14, 2.22, { nen: bg, vien });
    pill(s, x + 0.28, y + 0.22, n.toUpperCase(), { nen: mau === TEXT ? ACCENT : mau, co: 9, w: 0.4 });
    s.addText(hoi, { x: x + 0.82, y: y + 0.2, w: RW / 2 - 1.2, h: 0.34, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 13.5, bold: true, color: mau });
    s.addText(so_do, { x: x + 0.28, y: y + 0.66, w: RW / 2 - 0.7, h: 0.5, isTextBox: true,
      margin: 0, fontFace: "Courier New", fontSize: 10.5, bold: true, color: TEXT, lineSpacing: 14 });
    s.addText(y_nghia, { x: x + 0.28, y: y + 1.2, w: RW / 2 - 0.7, h: 0.92, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 11, color: N700, lineSpacing: 14 });
  });

  const kt1 = kd.khoang_tin_cay.top1;
  s.addText([
    { text: "Và một lưu ý về cỡ mẫu:  ", options: { bold: true, color: TEXT } },
    { text: `với ${dg.so_cau_hoi} câu, Top-1 ${pc(dg.top1, 2)} thực chất nằm trong khoảng tin cậy 95% [${pc(kt1.ktc95[0], 1)} – ${pc(kt1.ktc95[1], 1)}]. Một thay đổi làm Top-1 nhích 1–2 điểm phần trăm thì KHÔNG kết luận được là cải tiến.`, options: { color: N700 } },
  ], { x: L, y: 6.3, w: RW, h: 0.46, isTextBox: true, margin: 0, valign: "top",
       fontFace: FONT, fontSize: 11, lineSpacing: 14 });
  chan(s, "python eval/kiem_dinh.py — khoảng tin cậy Wilson, McNemar, trần precision");
  s.addNotes("Slide này trả lời trước câu hỏi kinh điển của hội đồng: số đẹp vậy có chắc không, hay chỉ là may.");
}

// ═══════════════════ 8. Ablation — từng thành phần đóng góp ═════════════════
{
  const s = slide();
  tieu_de(s, "5 · Kết quả", "Ablation — từng thành phần đóng góp bao nhiêu?");
  const key = Object.keys(ab.toan_bo);
  s.addChart(
    pres.ChartType.bar,
    [{ name: "Top-1 (%)", labels: ["A. Chỉ TF-IDF", "B. Chỉ keyphrase", "C. Lai ba thành phần", "D. C + suy diễn số học"],
       values: key.map((k) => +ab.toan_bo[k].top1.toFixed(1)) }],
    {
      x: L, y: 1.68, w: 7.3, h: 2.6, barDir: "bar", barGapWidthPct: 45,
      chartColors: [N600, N600, ACCENT2, ACCENT],
      varyColors: true,
      showTitle: true, title: "Top-1 theo cấu hình — toàn bộ 120 câu hỏi",
      titleFontFace: FONT, titleFontSize: 13, titleColor: TEXT,
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10,
      dataLabelColor: N700, dataLabelFontFace: FONT, dataLabelFormatCode: "0.0",
      catAxisLabelColor: N700, catAxisLabelFontFace: FONT, catAxisLabelFontSize: 11,
      valAxisLabelColor: N600, valAxisLabelFontFace: FONT, valAxisLabelFontSize: 9,
      valAxisMinVal: 0, valAxisMaxVal: 100, valAxisMajorUnit: 25,
      valGridLine: { color: N300, size: 0.5 }, catGridLine: { style: "none" },
      showLegend: false, plotArea: { fill: { color: BG } }, chartArea: { fill: { color: BG } },
    },
  );
  the(s, 8.4, 1.68, RW - 7.65, 2.6, { nen: A100, vien: "FFC6A5" });
  s.addText([
    { text: "Keyphrase đứng riêng YẾU HƠN TF-IDF\n", options: { bold: true, color: A700, breakLine: true } },
    { text: `${pc(ab.toan_bo[key[1]].top1 / 100, 1)} so với ${pc(ab.toan_bo[key[0]].top1 / 100, 1)} — nhưng vẫn xứng trọng số cao nhất 0,55. Nó thua về ĐỘ PHỦ, không thua về ĐỘ CHÍNH XÁC. Lai lại: TF-IDF lo phần phủ, keyphrase lo phần chuẩn.`, options: { color: "5A4032" } },
  ], { x: 8.72, y: 1.94, w: 3.55, h: 2.1, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 12, lineSpacing: 16 });

  the(s, L, 4.5, RW, 2.16, { nen: SURFACE, vien: null });
  pill(s, L + 0.36, 4.72, "22 CÂU HỎI CÓ GIÁ TRỊ SỐ", { nen: ACCENT2, co: 10 });
  const cC = ab.cau_hoi_co_gia_tri_so[Object.keys(ab.cau_hoi_co_gia_tri_so)[0]];
  const cD = ab.cau_hoi_co_gia_tri_so[Object.keys(ab.cau_hoi_co_gia_tri_so)[1]];
  s.addText(pc(cC.top1 / 100, 1), { x: L + 0.36, y: 5.2, w: 2.0, h: 0.72, isTextBox: true,
    margin: 0, align: "center", fontFace: FONT, fontSize: 36, bold: true, color: N600 });
  s.addText("chưa suy diễn số học", { x: L + 0.36, y: 5.92, w: 2.0, h: 0.3, isTextBox: true,
    margin: 0, align: "center", fontFace: FONT, fontSize: 11, color: N700 });
  s.addText("→", { x: L + 2.46, y: 5.2, w: 0.8, h: 0.72, isTextBox: true, margin: 0,
    align: "center", valign: "middle", fontFace: FONT, fontSize: 30, bold: true, color: ACCENT });
  s.addText(pc(cD.top1 / 100, 1), { x: L + 3.3, y: 5.2, w: 2.0, h: 0.72, isTextBox: true,
    margin: 0, align: "center", fontFace: FONT, fontSize: 36, bold: true, color: ACCENT });
  s.addText("có suy diễn số học", { x: L + 3.3, y: 5.92, w: 2.0, h: 0.3, isTextBox: true,
    margin: 0, align: "center", fontFace: FONT, fontSize: 11, color: N700 });
  s.addText([
    { text: `Trong khi đó Top-5 gần như không đổi: ${pc(cC.topk / 100, 1)} → ${pc(cD.topk / 100, 1)}.\n`, options: { bold: true, color: TEXT, breakLine: true } },
    { text: "Con số này nói đúng một điều: so khớp từ khoá VẪN TÌM RA đủ các khung phạt, nó chỉ không biết CHỌN KHUNG NÀO. NumericReasoner rút ngưỡng từ chính nguyên văn điều khoản rồi so sánh khoảng — giải quyết đúng khâu đó.", options: { color: N700 } },
  ], { x: L + 5.7, y: 5.16, w: 5.8, h: 1.3, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 12.5, lineSpacing: 17 });
  chan(s, "python eval/ablation.py");
  s.addNotes("Đây là slide đáng tiền nhất của phần thực nghiệm: chứng minh trọng số không phải chọn cảm tính.");
}

// ═══════════════════════ Phân tích lỗi sâu ══════════════════════════════════
{
  const s = slide();
  tieu_de(s, "5 · Kết quả", "Phân tích lỗi sâu — mỗi ca quy về một nguyên nhân gốc");
  s.addImage({ path: path.join(HINH, "hinh6_phan_tich_loi.png"), x: 0.55, y: 1.44, w: 8.3, h: 3.19 });

  const nTop1 = pl.so_ca_chua_toi_uu - pl.so_ca_ngoai_top_k - pl.so_ca_trong_top_k_nhung_khong_hang_1;
  the(s, 9.05, 1.5, RW - 8.3, 3.1, { nen: A100, vien: "FFC6A5" });
  s.addText([
    { text: "Phần lớn là lỗi XẾP HẠNG,\nkhông phải lỗi tìm kiếm.\n\n", options: { fontSize: 14, bold: true, color: A700, breakLine: true } },
    { text: `${pl.so_ca_chua_toi_uu}/${dg.so_cau_hoi} ca chưa tối ưu:\n`, options: { bold: true, color: "5A4032", breakLine: true } },
    { text: `• ${pl.so_ca_ngoai_top_k} ca đáp án rơi hẳn ngoài Top-${dg.top_k}\n`, options: { color: "5A4032", breakLine: true } },
    { text: `• ${pl.so_ca_trong_top_k_nhung_khong_hang_1} ca đáp án CÓ trong danh sách nhưng không đứng đầu\n`, options: { color: "5A4032", breakLine: true } },
    { text: `• ${nTop1} ca đáp án đã ở hạng 1 nhưng câu bị gán sai lớp`, options: { color: "5A4032" } },
  ], { x: 9.32, y: 1.74, w: 3.4, h: 2.7, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 11.5, lineSpacing: 15 });

  const nn = pl.theo_nguyen_nhan;
  const o = [
    ["L5", `Khoảng trống từ vựng — ${nn.L5 || 0} ca`,
     "“nón bảo hiểm” thay vì “mũ bảo hiểm”, “bằng lái” thay vì “giấy phép lái xe”. Làn keyphrase im lặng, chỉ còn TF-IDF gánh.",
     "Sửa bằng DỮ LIỆU, không cần đổi thuật giải", ACCENT2, G100, "CCDBB2", G700],
    ["L1", `Định tuyến sai lớp — ${nn.L1 || 0} ca`,
     "“Đèn giao thông có mấy màu?” bị đẩy sang P7 vì câu quá ngắn; con số 12 trong câu hỏi kích hoạt nhầm mẫu tra cứu ngược.",
     "Bộ giải sai kiểu chạy — lỗi nặng nhất", ACCENT, A100, "FFC6A5", A700],
    ["L2", `Trượt hẳn ngoài Top-${dg.top_k} — ${nn.L2 || 0} ca`,
     "Câu khẩu ngữ dài kể tình huống, hoặc câu dạng có/không: người hỏi chờ một câu khẳng định, hệ trả điều khoản gần nghĩa nhất.",
     "Lỗi người dùng thật sự cảm nhận được", "8C491A", N100, N300, TEXT],
    ["L3", `Thứ tự trong tập trả về — ${nn.L3 || 0} ca`,
     "Toàn bộ thuộc P4/P6/P7, nơi hệ trả NGUYÊN MỘT TẬP thoả ràng buộc. Đáp án có trong tập, chỉ không đứng đầu.",
     "Recall đủ — vấn đề trình bày, không phải truy hồi", N600, N100, N300, TEXT],
  ];
  const w = 3.0, gx = 0.19;
  o.forEach(([ma, t, m, kl, c, bg, vien, mau], i) => {
    const x = L + i * (w + gx);
    the(s, x, 4.82, w, 1.82, { nen: bg, vien });
    pill(s, x + 0.24, 5.0, ma, { nen: c, co: 9, w: 0.5 });
    s.addText(t.split(" — ")[0], { x: x + 0.84, y: 4.98, w: w - 1.05, h: 0.3, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 11.5, bold: true, color: mau });
    s.addText(t.split(" — ")[1], { x: x + 0.24, y: 5.34, w: w - 0.48, h: 0.24, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 11, bold: true, color: c === N600 ? N700 : c });
    s.addText(m, { x: x + 0.24, y: 5.56, w: w - 0.48, h: 0.66, isTextBox: true, margin: 0,
      valign: "top", fontFace: FONT, fontSize: 9.6, color: N700, lineSpacing: 12.5 });
    s.addText("→ " + kl, { x: x + 0.24, y: 6.22, w: w - 0.48, h: 0.36, isTextBox: true,
      margin: 0, valign: "top", fontFace: FONT, fontSize: 9.3, italic: true, color: mau });
  });
  chan(s, "python eval/phan_tich_loi.py — mỗi ca quy về đúng một nguyên nhân, theo thứ tự ưu tiên");
  s.addNotes("Đây là slide chứng minh nhóm hiểu hệ của mình hỏng ở đâu chứ không chỉ biết con số tổng.");
}

// ═══════════════════ Giải thích: vì sao số lại như vậy ══════════════════════
{
  const s = slide();
  tieu_de(s, "5 · Kết quả", "Giải thích: vì sao các con số lại như vậy");
  const cC = ab.cau_hoi_co_gia_tri_so[Object.keys(ab.cau_hoi_co_gia_tri_so)[0]];
  const cD = ab.cau_hoi_co_gia_tri_so[Object.keys(ab.cau_hoi_co_gia_tri_so)[1]];
  const o = [
    [`Vì sao Top-5 (${pc(dg.top5, 1)}) bỏ xa Top-1 (${pc(dg.top1, 1)})?`,
     "Vì phân lớp KHÔNG chặn kết quả: kể cả khi B3 chọn sai lớp, hệ vẫn nạp thêm tri thức của các loại còn thiếu nếu điểm ≥ 0,40.",
     `Hệ quả: đáp án đúng hiếm khi biến mất khỏi danh sách — ${pl.so_ca_trong_top_k_nhung_khong_hang_1} ca nằm trong danh sách mà không ở hạng 1.`, ACCENT],
    ["Vì sao khoảng cách đó lớn nhất ở P2?",
     "Vì quy tắc giao thông là loại tri thức có nhiều điều khoản gần nghĩa nhất — nhường đường, chuyển hướng, quay đầu chia sẻ rất nhiều từ vựng.",
     "Cả ba làn điểm cho các ứng viên này số gần nhau; hệ chưa có tín hiệu nào tách chúng ngoài độ tương đồng văn bản.", ACCENT],
    [`Vì sao suy diễn số học tạo khác biệt lớn (${pc(cC.top1 / 100, 1)} → ${pc(cD.top1 / 100, 1)}) mà Top-5 gần như không đổi?`,
     "Vì bài toán ở nhóm câu này không phải TÌM mà là CHỌN. Các khung phạt của cùng một hành vi có văn bản gần như giống hệt, chỉ khác con số ngưỡng.",
     "So khớp văn bản đưa cả bốn khung vào top-5 nhưng không có cơ sở xếp hạng giữa chúng. Chỉ khi so sánh KHOẢNG SỐ mới chọn đúng.", ACCENT2],
    [`Vì sao hệ chưa từ chối được truy vấn nào trong ${mien.so_cau_ngoai_mien} truy vấn ngoài lĩnh vực?`,
     `Vì đặc trưng TF-IDF không tách được hai phân bố: 56/${dg.so_cau_hoi} câu HỢP LỆ chấm điểm thấp hơn hoặc bằng truy vấn rác.`,
     "Không tồn tại ngưỡng nào vừa loại hết rác vừa không từ chối oan. Số đo đầy đủ ở slide hạn chế.", ACCENT2],
  ];
  o.forEach(([hoi, vi, hq, c], i) => {
    const x = L + (i % 2) * (RW / 2 + 0.14);
    const y = 1.68 + Math.floor(i / 2) * 2.5;
    the(s, x, y, RW / 2 - 0.14, 2.28, { nen: N100 });
    s.addShape(pres.ShapeType.rect, { x, y, w: RW / 2 - 0.14, h: 0.07,
      fill: { color: c }, line: { type: "none" } });
    s.addText(hoi, { x: x + 0.3, y: y + 0.26, w: RW / 2 - 0.74, h: 0.62, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 13, bold: true, color: TEXT, lineSpacing: 16 });
    s.addText(vi, { x: x + 0.3, y: y + 0.94, w: RW / 2 - 0.74, h: 0.72, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 11.5, color: N700, lineSpacing: 15 });
    s.addShape(pres.ShapeType.rect, { x: x + 0.3, y: y + 1.68, w: RW / 2 - 0.74, h: 0.012,
      fill: { color: N300 }, line: { type: "none" } });
    s.addText(hq, { x: x + 0.3, y: y + 1.78, w: RW / 2 - 0.74, h: 0.44, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 11, color: c === ACCENT ? A700 : G700, lineSpacing: 14 });
  });
  chan(s, "Bốn cơ chế này giải thích gần như toàn bộ hình dạng của kết quả");
  s.addNotes("Nếu chỉ được giữ một slide của phần kết quả thì giữ slide này — nó cho thấy nhóm hiểu VÌ SAO chứ không chỉ đo được.");
}

// ═══════════════════════════════ 9. Demo ════════════════════════════════════
{
  const s = slide(true);
  tieu_de(s, "6 · Ứng dụng", "Demo trực tiếp — năm điều muốn chứng minh", { toi: true });
  const b = [
    ["01", "Vượt đèn đỏ xe máy phạt bao nhiêu?", "4.000.000 – 6.000.000 đ · trừ 4 điểm", "Căn cứ Điều 7 khoản 7 điểm c NĐ 168/2024 hiện ngay dưới thẻ — mọi câu trả lời đều truy nguyên được"],
    ["02", "nhậu xong lái xe máy bị phạt nhiêu tiền", "đúng khung nồng độ cồn", "Chữ “nhậu” KHÔNG có trong bất kỳ văn bản luật nào — đây chính là phần “ngữ nghĩa” của đề bài"],
    ["03", "xe máy nồng độ cồn 0,2 → 0,3 → 0,5 mg/l", "ba khung phạt khác nhau", "So khớp từ khoá trả về cả bốn khung; hệ rút ngưỡng từ nguyên văn rồi so khoảng"],
    ["04", "Điều 6 khoản 9 điểm a NĐ 168/2024 nói về lỗi gì?", "đúng 1 kết quả", "Tra theo căn cứ mà trả về 5 kết quả là sai"],
    ["05", "Màn /hieu-luc — hiệu lực theo thời gian", "R15 có hiệu lực từ 01/7/2026", "Sửa đổi lưu như DỮ LIỆU, không hợp nhất cứng lúc dựng cơ sở tri thức"],
  ];
  b.forEach(([n, hoi, ra, y_nghia], i) => {
    const y = 1.62 + i * 1.02;
    s.addShape(pres.ShapeType.roundRect, {
      x: L, y, w: RW, h: 0.9, fill: { color: i === 4 ? "3D472B" : "3A352D" },
      line: { type: "none" }, rectRadius: 0.12,
    });
    s.addText(n, { x: L + 0.26, y: y + 0.1, w: 0.6, h: 0.7, isTextBox: true, margin: 0,
      align: "center", valign: "middle", fontFace: FONT, fontSize: 20, bold: true,
      color: i === 4 ? "AEBF92" : "F6A06B" });
    s.addText(hoi, { x: L + 0.95, y: y + 0.13, w: 4.6, h: 0.32, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 13, bold: true, color: N100 });
    s.addText("→  " + ra, { x: L + 0.95, y: y + 0.47, w: 4.6, h: 0.3, isTextBox: true,
      margin: 0, fontFace: FONT, fontSize: 11.5, color: i === 4 ? "AEBF92" : "F6A06B" });
    s.addText(y_nghia, { x: L + 5.85, y: y + 0.16, w: RW - 6.2, h: 0.62, isTextBox: true,
      margin: 0, valign: "middle", fontFace: FONT, fontSize: 11.5, color: "CFC6B6",
      lineSpacing: 15 });
  });
  chan(s, "docker/chay_demo.sh  ·  http://localhost:8000  ·  chạy hoàn toàn offline", { toi: true });
  s.addNotes("Mở Docker và chạy script trước giờ trình bày ít nhất 5 phút. Dự phòng: bảng 12 ca nghiệm thu trong so_lieu/.");
}

// ══════════════════════ 10. Hạn chế đã đo ═══════════════════════════════════
{
  const s = slide();
  tieu_de(s, "6 · Hạn chế", "Đã đo, đã ghi lại — kể cả những hướng đã bác bỏ");
  const r = Object.fromEntries(mien.results.map((x) => [x.tin_hieu, x]));
  s.addChart(
    pres.ChartType.bar,
    [{ name: "AUC", labels: mien.results.map((x) => x.tin_hieu),
       values: mien.results.map((x) => +x.auc.toFixed(4)) }],
    {
      x: L, y: 1.7, w: 6.5, h: 2.5, barDir: "bar", barGapWidthPct: 45,
      chartColors: [N600, ACCENT2, "C0B6A5", ACCENT], varyColors: true,
      showTitle: true, title: "Khả năng tách truy vấn ngoài lĩnh vực (AUC)",
      titleFontFace: FONT, titleFontSize: 13, titleColor: TEXT,
      showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 10,
      dataLabelColor: N700, dataLabelFontFace: FONT, dataLabelFormatCode: "0.000",
      catAxisLabelColor: N700, catAxisLabelFontFace: FONT, catAxisLabelFontSize: 11,
      valAxisLabelColor: N600, valAxisLabelFontFace: FONT, valAxisLabelFontSize: 9,
      valAxisMinVal: 0, valAxisMaxVal: 1.15, valAxisMajorUnit: 0.25,
      valGridLine: { color: N300, size: 0.5 }, catGridLine: { style: "none" },
      showLegend: false, plotArea: { fill: { color: BG } }, chartArea: { fill: { color: BG } },
    },
  );
  the(s, 7.5, 1.7, RW - 6.75, 2.5, { nen: A100, vien: "FFC6A5" });
  s.addText([
    { text: "Truy vấn ngoài lĩnh vực vẫn trả về kết quả.\n", options: { bold: true, color: A700, breakLine: true } },
    { text: `Hỏi “cách nấu phở bò” thì hệ vẫn đưa ra một hành vi vi phạm. Đặc trưng TF-IDF quá yếu để tách miền: 56/${dg.so_cau_hoi} câu hợp lệ chấm điểm thấp hơn hoặc bằng truy vấn rác. Không ngưỡng nào tách được.`, options: { color: "5A4032" } },
  ], { x: 7.82, y: 1.96, w: 4.44, h: 2.06, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 11.5, lineSpacing: 15 });

  the(s, L, 4.42, 6.5, 1.62, { nen: G100, vien: "CCDBB2" });
  s.addText([
    { text: "Đã thử dense embedding — và đã từ chối đánh đổi.\n", options: { bold: true, color: G700, breakLine: true } },
    { text: `AUC ${so(r["TF-IDF thô"].auc)} → ${so(r["dense"].auc)}, loại được ${pc(r["dense"].loai_rac_khi_0_oan, 1)} truy vấn rác mà không từ chối oan câu nào. Nhưng hai phân bố VẪN chồng lấn: trần điểm của rác ${so(r["dense"].tran_ngoai_mien)} còn nằm trên sàn ${so(r["dense"].san_trong_mien)} của câu hợp lệ không có keyphrase. Loại 100% rác thì phải làm oan ${pc(r["dense"].oan_khi_loai_het_rac, 1)} câu hợp lệ.`, options: { color: "3F4A2E" } },
  ], { x: L + 0.28, y: 4.6, w: 5.94, h: 1.3, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 10.5, lineSpacing: 14 });

  the(s, 7.5, 4.42, RW - 6.75, 1.62, { nen: N100 });
  s.addText([
    { text: "Kết quả âm cũng là kết quả.\n", options: { bold: true, color: TEXT, breakLine: true } },
    { text: `Phủ từ vựng cơ sở tri thức là tín hiệu vô dụng cho việc tách miền — AUC ${so(r["phủ từ vựng KB"].auc)}, thấp hơn cả TF-IDF thô. Hướng này đã thử và đã bác bỏ.`, options: { color: N700 } },
  ], { x: 7.82, y: 4.6, w: 4.44, h: 1.3, isTextBox: true, margin: 0,
       fontFace: FONT, fontSize: 11.5, lineSpacing: 15 });

  s.addText(`Còn lại: 12/${dg.so_cau_hoi} câu hợp lệ không rút được keyphrase nào  ·  46 chú thích sửa đổi của Luật 118/2025 chưa mô hình hoá ở mức từng khoản  ·  hệ không sinh ngôn ngữ tự nhiên (lựa chọn có chủ đích)`, {
    x: L, y: 6.2, w: RW, h: 0.44, isTextBox: true, margin: 0, fontFace: FONT,
    fontSize: 11, color: N700, lineSpacing: 14,
  });
  chan(s, `${kt.so_xfail} test xfail strict — ngày nào chúng bất ngờ đạt, CI báo lỗi và buộc cập nhật tài liệu`);
  s.addNotes("Chủ động nêu hạn chế trước khi hội đồng hỏi. Nhấn: đây là hạn chế ĐÃ ĐO, không phải chưa biết.");
}

// ══════════════════════════ 11. Kết luận ════════════════════════════════════
{
  const s = slide(true);
  s.addShape(pres.ShapeType.ellipse, {
    x: W - 2.2, y: -1.7, w: 4.4, h: 4.4, fill: { color: "402310" }, line: { type: "none" },
  });
  tieu_de(s, "6 · Kết luận", "Điều nhóm giữ lại không phải con số Top-1", { toi: true });
  const o = [
    [`${nghin(dem("concepts"))} · ${nghin(dem("relations"))} · ${nghin(dem("rules"))} · ${nghin(dem("violations"))}`,
     "khái niệm · quan hệ · quy tắc · hành vi vi phạm, 100% có căn cứ pháp lý"],
    [`${nghin(dem("keyphrases"))} keyphrase`, `${dg.so_cau_hoi} câu hỏi có đáp án chuẩn · ${kt.ca_nghiem_thu_dat}/${kt.ca_nghiem_thu_tong} ca nghiệm thu đạt`],
    [`${kt.so_test_dat} test · phủ ${kt.do_phu_phan_tram}%`, `${kt.so_xfail} hạn chế đã đo và khoá bằng test xfail strict`],
  ];
  o.forEach(([a, b_], i) => {
    const y = 1.78 + i * 1.0;
    s.addText(a, { x: L, y, w: 5.6, h: 0.4, isTextBox: true, margin: 0, fontFace: FONT,
      fontSize: 19, bold: true, color: "F6A06B" });
    s.addText(b_, { x: L, y: y + 0.42, w: 5.6, h: 0.46, isTextBox: true, margin: 0,
      fontFace: FONT, fontSize: 12, color: "C0B6A5", lineSpacing: 15 });
  });
  the(s, 6.9, 1.78, RW - 6.15, 3.0, { nen: "3A352D", vien: "56503F" });
  s.addText([
    { text: "Kỷ luật đo đạc\n\n", options: { fontSize: 15, bold: true, color: N100, breakLine: true } },
    { text: "Mọi khẳng định trong báo cáo đều sinh ra từ một lệnh chạy lại được.\n\n", options: { color: "C0B6A5", breakLine: true } },
    { text: "Mọi hạn chế đều có số đo kèm theo.\n\n", options: { color: "C0B6A5", breakLine: true } },
    { text: "Những hướng đã thử rồi bác bỏ đều được ghi lại thay vì giấu đi.", options: { color: "C0B6A5" } },
  ], { x: 7.24, y: 2.02, w: 4.9, h: 2.6, isTextBox: true, margin: 0, fontFace: FONT,
       fontSize: 12, lineSpacing: 17 });

  the(s, L, 5.08, RW, 1.35, { nen: "3D472B", vien: null });
  s.addText("Hướng phát triển", { x: L + 0.36, y: 5.24, w: 3.0, h: 0.3, isTextBox: true,
    margin: 0, fontFace: FONT, fontSize: 13, bold: true, color: "AEBF92" });
  s.addText("Hỏi lại khi truy vấn thiếu phương tiện hoặc chủ thể  ·  tổng quát hoá mô hình sửa đổi để khép nốt 46 chú thích  ·  thêm tín hiệu phân biệt cho lớp P2 bằng đồ thị quan hệ  ·  đưa dense vào bản triển khai có tài nguyên với ngưỡng hai mức", {
    x: L + 0.36, y: 5.56, w: RW - 0.72, h: 0.74, isTextBox: true, margin: 0,
    fontFace: FONT, fontSize: 12, color: "C0B6A5", lineSpacing: 16,
  });
  s.addText("Cảm ơn thầy và các bạn đã lắng nghe.", {
    x: L, y: H - 0.66, w: 7, h: 0.34, isTextBox: true, margin: 0, fontFace: FONT,
    fontSize: 13, italic: true, color: N600,
  });
  s.addText(String(STT), { x: W - L - 0.7, y: H - 0.62, w: 0.7, h: 0.3, isTextBox: true,
    margin: 0, align: "right", fontFace: FONT, fontSize: 10, color: N600 });
  s.addNotes("Kết lại bằng kỷ luật đo đạc chứ không bằng con số. Sẵn sàng nhận câu hỏi.");
}

pres.writeFile({ fileName: RA }).then(() => console.log("Da ghi " + RA));
