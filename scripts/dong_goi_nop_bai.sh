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
mkdir -p "$DICH"/ma_nguon "$DICH"/docker "$DICH"/bao_cao/hinh "$DICH"/so_lieu "$DICH"/slide

echo "==> [1/8] Ma nguon (ban sach theo git — khong kem .venv hay cache)"
git -C "$GOC" archive --format=tar HEAD | tar -x -C "$DICH/ma_nguon"
# `git archive` chi lay tep DA COMMIT. Bo sung nhung tep sinh ra ma bo nop van
# can de dung lai duoc bao cao/slide, ke ca khi chua kip commit.
for T in scripts/ve_so_do.py scripts/tao_bao_cao_day_du.py scripts/lam_slide.js \
         eval/ket_qua_kiem_thu.json eval/kich_ban_nghiem_thu.md; do
  [ -f "$GOC/$T" ] && { mkdir -p "$DICH/ma_nguon/$(dirname "$T")"; cp "$GOC/$T" "$DICH/ma_nguon/$T"; }
done
mkdir -p "$DICH/ma_nguon/docs/so_do" && cp "$GOC"/docs/so_do/*.png "$DICH/ma_nguon/docs/so_do/" 2>/dev/null || true
echo "    $(find "$DICH/ma_nguon" -type f | wc -l | tr -d ' ') tep"

echo "==> [2/8] Anh Docker — buoc nay lau nhat"
# Khong co docker CLI (vi du dang chay trong mot shell han che) thi van dong goi
# duoc: dung lai anh da xuat o lan truoc neu tim thay. Dat ANH_CU= de tro thang
# toi mot tep .tar.gz cu the.
TEP_ANH="$DICH/docker/traffic-law-image.tar.gz"
if command -v docker >/dev/null 2>&1; then
  if ! docker image inspect "$ANH" >/dev/null 2>&1; then
    echo "    Chua co anh $ANH, dang build..."
    docker build -t "$ANH" "$GOC"
  fi
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

echo "==> [3/8] So lieu danh gia"
cp "$GOC"/eval/ket_qua_danh_gia.json \
   "$GOC"/eval/ket_qua_ablation.json \
   "$GOC"/eval/ket_qua_phat_hien_mien.json \
   "$GOC"/eval/ket_qua_kiem_thu.json \
   "$GOC"/eval/qa_dataset.json \
   "$GOC"/eval/truy_van_ngoai_mien.json "$DICH/so_lieu/"
# Bang 12 ca nghiem thu: sinh lai neu chay duoc, khong thi dung ban da luu trong eval/.
if ( cd "$GOC" && "$PY" eval/kich_ban.py --markdown ) > "$DICH/so_lieu/kich_ban_nghiem_thu.md" 2>/dev/null; then
  cp "$DICH/so_lieu/kich_ban_nghiem_thu.md" "$GOC/eval/kich_ban_nghiem_thu.md"
else
  cp "$GOC/eval/kich_ban_nghiem_thu.md" "$DICH/so_lieu/"
  echo "    (dung ban kich_ban_nghiem_thu.md da luu — khong chay lai duoc)" >&2
fi
echo "    6 tep JSON + bang 12 ca nghiem thu (Markdown)"

echo "==> [4/8] Hai so do cho bao cao va slide"
if ( cd "$GOC" && "$PY" scripts/ve_so_do.py ) >/dev/null 2>&1; then
  echo "    da ve lai tu ma"
else
  echo "    BO QUA ve lai (thieu matplotlib) — dung ban da luu trong docs/so_do/" >&2
fi
cp "$GOC"/docs/so_do/*.png "$DICH/bao_cao/hinh/"
echo "    $(ls "$DICH/bao_cao/hinh" | wc -l | tr -d ' ') so do"

echo "==> [5/8] Khung bao cao Word"
if ( cd "$GOC" && PYTHONPATH=src "$PY" -m traffic_law.report.builder ) >/dev/null 2>&1; then
  cp "$GOC/docs/bao_cao_de_tai_4_khung.docx" "$DICH/bao_cao/"
  echo "    bao_cao_de_tai_4_khung.docx"
else
  echo "    BO QUA: thieu goi 'bao-cao' (pip install -e '.[bao-cao]')" >&2
fi
cp "$GOC"/docs/doi_chieu_de_tai_4.md "$GOC"/docs/thiet_ke_giai_phap.md \
   "$GOC"/docs/kien_truc.md "$GOC"/docs/bao_cao_du_lieu.md "$DICH/bao_cao/"
# ADR di kem: nguoi cham co the muon biet vi sao chon nhu vay
mkdir -p "$DICH/bao_cao/adr" && cp "$GOC"/docs/adr/*.md "$DICH/bao_cao/adr/"
cp "$GOC"/docs/slide/index.html "$DICH/slide/"

echo "==> [6/8] Bao cao hoan chinh + slide trinh chieu"
# Sinh lai neu moi truong cho phep; khong thi dung ban da luu trong docs/.
( cd "$GOC" && "$PY" scripts/tao_bao_cao_day_du.py ) >/dev/null 2>&1 \
  || echo "    BO QUA sinh lai .docx (thieu python-docx) — dung ban da luu" >&2
( cd "$GOC" && node scripts/lam_slide.js ) >/dev/null 2>&1 \
  || echo "    BO QUA sinh lai .pptx (thieu node/pptxgenjs) — dung ban da luu" >&2
cp "$GOC/docs/BaoCao_Nhom7_CS106.docx" "$DICH/bao_cao/"
cp "$GOC/docs/Slide_Nhom7_CS106.pptx" "$DICH/slide/"
echo "    BaoCao_Nhom7_CS106.docx + Slide_Nhom7_CS106.pptx"

echo "==> [7/8] Script khoi dong demo"
cp "$GOC"/scripts/nop_bai/chay_demo.sh "$GOC"/scripts/nop_bai/chay_demo.bat "$DICH/docker/"
chmod +x "$DICH/docker/chay_demo.sh"

echo "==> [8/8] Tai lieu huong dan"
cp "$GOC"/scripts/nop_bai/README_NOP_BAI.md "$DICH/README.md"
cp "$GOC"/scripts/nop_bai/HUONG_DAN_BAO_CAO.md "$DICH/"
cp "$GOC"/scripts/nop_bai/KICH_BAN_DEMO.md "$DICH/"

echo
echo "XONG. Tong dung luong: $(du -sh "$DICH" | cut -f1)"
echo "Mo: $DICH"
