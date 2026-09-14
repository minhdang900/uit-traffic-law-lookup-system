#!/usr/bin/env bash
# Đóng gói bộ nộp bài CS106 Đề tài 4 — Nhóm 7.
#
# VÌ SAO LÀ SCRIPT CHỨ KHÔNG PHẢI THƯ MỤC CHÉP TAY
# Bộ nộp phải khớp với mã nguồn tại thời điểm nộp. Chép tay thì mỗi lần sửa mã
# lại phải nhớ cập nhật; chạy script thì luôn đồng bộ, và người chấm dựng lại
# được y hệt.
#
#   ./scripts/dong_goi_nop_bai.sh [thu_muc_dich]
#
# Mặc định ghi ra ../nop_bai_CS106_Nhom7 (ngoài repo, để không lẫn vào git).
#
# AN TOÀN: script KHÔNG tự xoá thư mục đích. Nếu đã tồn tại, nó dừng và bảo
# bạn tự đổi tên — vì thư mục đó rất có thể đang chứa bản báo cáo đã gõ dở.
set -euo pipefail

GOC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DICH="${1:-$(dirname "$GOC")/nop_bai_CS106_Nhom7}"
ANH="traffic-law:latest"
PY="${GOC}/.venv/bin/python"
[ -x "$PY" ] || PY=python3

if [ -e "$DICH" ]; then
  echo "DUNG: '$DICH' da ton tai." >&2
  echo "Thu muc do co the dang chua ban bao cao ban da go do — script khong tu" >&2
  echo "xoa. Hay doi ten no roi chay lai, vi du:" >&2
  echo "    mv '$DICH' '${DICH}_cu'" >&2
  exit 1
fi

echo "==> Thu muc dich: $DICH"
mkdir -p "$DICH"/ma_nguon "$DICH"/docker "$DICH"/bao_cao "$DICH"/so_lieu "$DICH"/slide

echo "==> [1/9] Ma nguon (ban sach theo git — khong kem .venv hay cache)"
git -C "$GOC" archive --format=tar HEAD | tar -x -C "$DICH/ma_nguon"
# `git archive` chi lay tep DA COMMIT. Bo sung nhung tep sinh ra ma bo nop van
# can de dung lai duoc bao cao/slide, ke ca khi chua kip commit.
for T in scripts/ve_so_do.py scripts/lam_slide.js \
         scripts/thong_ke_du_lieu.py eval/phan_tich_loi.py \
         eval/ket_qua_kiem_thu.json eval/kich_ban_nghiem_thu.md; do
  [ -f "$GOC/$T" ] && { mkdir -p "$DICH/ma_nguon/$(dirname "$T")"; cp "$GOC/$T" "$DICH/ma_nguon/$T"; }
done
mkdir -p "$DICH/ma_nguon/docs/so_do" && cp "$GOC"/docs/so_do/*.png "$DICH/ma_nguon/docs/so_do/" 2>/dev/null || true
echo "    $(find "$DICH/ma_nguon" -type f | wc -l | tr -d ' ') tep"

echo "==> [2/9] Anh Docker — buoc nay lau nhat"
# Khong co docker CLI (vi du dang chay trong mot shell han che) thi van dong goi
# duoc: dung lai anh da xuat o lan truoc neu tim thay. Dat ANH_CU= de tro thang
# toi mot tep .tar.gz cu the.
TEP_ANH="$DICH/docker/traffic-law-image.tar.gz"
if command -v docker >/dev/null 2>&1; then
  # LUON build lai: truoc day chi build khi chua co anh, nen mot anh cu tren may
  # bi xuat lai lang le va demo khong khop ma nguon. Cache cua Docker giu cho lan
  # build khong doi van nhanh.
  echo "    dang build $ANH tu ma nguon hien tai..."
  docker build -q -t "$ANH" "$GOC" >/dev/null
  echo "    anh tao luc $(docker image inspect "$ANH" --format '{{.Created}}')"
  docker save "$ANH" | gzip -1 > "$TEP_ANH"
  echo "    $(du -h "$TEP_ANH" | cut -f1)"
else
  CU="${ANH_CU:-}"
  if [ -z "$CU" ]; then
    CU="$(ls -t "$(dirname "$DICH")"/nop_bai_CS106_Nhom7*/docker/traffic-law-image.tar.gz \
          2>/dev/null | head -1 || true)"
  fi
  if [ -n "$CU" ] && [ -f "$CU" ]; then
    cp "$CU" "$TEP_ANH"
    echo "    khong co docker CLI — dung lai anh da xuat: $CU ($(du -h "$TEP_ANH" | cut -f1))"
  else
    echo "    CANH BAO: khong co docker CLI va khong tim thay anh cu." >&2
    echo "    Bo nop se THIEU docker/traffic-law-image.tar.gz — chay lai tren may co" >&2
    echo "    Docker truoc khi nop." >&2
  fi
fi

echo "==> [3/9] So lieu danh gia"
cp "$GOC"/eval/ket_qua_danh_gia.json \
   "$GOC"/eval/ket_qua_ablation.json \
   "$GOC"/eval/ket_qua_phat_hien_mien.json \
   "$GOC"/eval/ket_qua_kiem_thu.json \
   "$GOC"/eval/ket_qua_kiem_dinh.json \
   "$GOC"/eval/ket_qua_phan_tich_loi.json \
   "$GOC"/eval/thong_ke_du_lieu.json \
   "$GOC"/eval/qa_dataset.json \
   "$GOC"/eval/truy_van_ngoai_mien.json "$DICH/so_lieu/"
# Bang 12 ca nghiem thu: sinh lai neu chay duoc, khong thi dung ban da luu trong eval/.
if ( cd "$GOC" && "$PY" eval/kich_ban.py --markdown ) > "$DICH/so_lieu/kich_ban_nghiem_thu.md" 2>/dev/null; then
  cp "$DICH/so_lieu/kich_ban_nghiem_thu.md" "$GOC/eval/kich_ban_nghiem_thu.md"
else
  cp "$GOC/eval/kich_ban_nghiem_thu.md" "$DICH/so_lieu/"
  echo "    (dung ban kich_ban_nghiem_thu.md da luu — khong chay lai duoc)" >&2
fi
echo "    $(ls "$DICH"/so_lieu/*.json | wc -l | tr -d ' ') tep JSON + bang 12 ca nghiem thu (Markdown)"

echo "==> [4/9] So do va bieu do cho bao cao va slide"
# ve_so_do.py: so do kien truc + luong B1-B6.
# thong_ke_du_lieu.py: bieu do phan bo do dai / nhan / chu de + phan tich loi.
VE_LAI=0
for S in scripts/ve_so_do.py scripts/thong_ke_du_lieu.py; do
  if ( cd "$GOC" && "$PY" "$S" ) >/dev/null 2>&1; then
    VE_LAI=$((VE_LAI + 1))
  else
    echo "    BO QUA $S (thieu matplotlib) — dung ban da luu trong docs/so_do/" >&2
  fi
done
[ "$VE_LAI" -gt 0 ] && echo "    da ve lai tu ma ($VE_LAI/2 bo sinh)"

echo "==> [5/9] Tai lieu kem bao cao"
cp "$GOC"/docs/doi_chieu_de_tai_4.md "$GOC"/docs/thiet_ke_giai_phap.md \
   "$GOC"/docs/kien_truc.md "$GOC"/docs/bao_cao_du_lieu.md "$DICH/bao_cao/"
# ADR di kem: nguoi cham co the muon biet vi sao chon nhu vay
mkdir -p "$DICH/bao_cao/adr" && cp "$GOC"/docs/adr/*.md "$DICH/bao_cao/adr/"
cp "$GOC"/docs/slide/index.html "$DICH/slide/"

echo "==> [6/9] Bao cao LaTeX + slide trinh chieu"
# Bao cao chinh thuc duy nhat la ban LaTeX (docs/bao-cao-latex). Chep nguon, lay
# hinh moi nhat tu docs/so_do, bien dich thang trong thu muc dich; thieu TeX thi
# dung ban PDF da commit. Tep .pptx sinh thang vao thu muc dich, KHONG ghi de ban
# trong docs/ vi .pptx nhung dau thoi gian — ghi de se lam git ban moi lan dong goi.
mkdir -p "$DICH/bao_cao/bao-cao-latex"
cp "$GOC/docs/bao-cao-latex/main.tex" "$DICH/bao_cao/bao-cao-latex/"
cp -R "$GOC/docs/bao-cao-latex/chapters" "$GOC/docs/bao-cao-latex/figures" \
  "$DICH/bao_cao/bao-cao-latex/"
find "$DICH/bao_cao/bao-cao-latex" -name .omc -prune -exec rm -rf {} +
for H in "$GOC"/docs/so_do/hinh*.png; do
  cp "$H" "$DICH/bao_cao/bao-cao-latex/figures/"
done
if command -v latexmk >/dev/null 2>&1 && ( cd "$DICH/bao_cao/bao-cao-latex" \
     && latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex ) >/dev/null 2>&1; then
  mv "$DICH/bao_cao/bao-cao-latex/main.pdf" "$DICH/bao_cao/BaoCao_Nhom7_CS106.pdf"
  ( cd "$DICH/bao_cao/bao-cao-latex" && latexmk -c >/dev/null 2>&1 ) || true
  echo "    BaoCao_Nhom7_CS106.pdf — bien dich lai tu LaTeX"
else
  cp "$GOC/docs/BaoCao_Nhom7_CS106.pdf" "$DICH/bao_cao/"
  echo "    BaoCao_Nhom7_CS106.pdf — dung ban da commit (thieu latexmk/XeLaTeX)" >&2
fi
if ( cd "$GOC" && node scripts/lam_slide.js "$GOC" "$GOC/docs/so_do" \
     "$DICH/slide/Slide_Nhom7_CS106.pptx" ) >/dev/null 2>&1; then
  echo "    Slide_Nhom7_CS106.pptx — sinh lai tu ma"
else
  cp "$GOC/docs/Slide_Nhom7_CS106.pptx" "$DICH/slide/"
  echo "    Slide_Nhom7_CS106.pptx — dung ban da luu (thieu node/pptxgenjs)" >&2
fi

echo "==> [7/9] Xuat PDF cho slide"
# Nguoi cham thuong mo PDF truoc. Dung scripts/xuat_pdf.py chu khong phai
# `soffice --convert-to` vi lenh do KHONG cap nhat truong TOC — PDF se co trang
# muc luc trong. Thieu LibreOffice thi bo qua, bo nop van co .pptx.
if "$PY" "$GOC/scripts/xuat_pdf.py" "$DICH/slide/Slide_Nhom7_CS106.pptx"; then
  :
else
  echo "    Bo qua PDF — xem canh bao o tren" >&2
fi

echo "==> [8/9] Script khoi dong demo"
cp "$GOC"/scripts/nop_bai/chay_demo.sh "$GOC"/scripts/nop_bai/chay_demo.bat "$DICH/docker/"
chmod +x "$DICH/docker/chay_demo.sh"

echo "==> [9/9] Tai lieu huong dan"
cp "$GOC"/scripts/nop_bai/README_NOP_BAI.md "$DICH/README.md"
cp "$GOC"/scripts/nop_bai/HUONG_DAN_BAO_CAO.md "$DICH/"
cp "$GOC"/scripts/nop_bai/KICH_BAN_DEMO.md "$DICH/"

echo
echo "XONG. Tong dung luong: $(du -sh "$DICH" | cut -f1)"
echo "Mo: $DICH"
