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
mkdir -p "$DICH"/ma_nguon "$DICH"/docker "$DICH"/bao_cao "$DICH"/so_lieu

echo "==> [1/6] Ma nguon (ban sach theo git — khong kem .venv hay cache)"
git -C "$GOC" archive --format=tar HEAD | tar -x -C "$DICH/ma_nguon"
echo "    $(find "$DICH/ma_nguon" -type f | wc -l | tr -d ' ') tep"

echo "==> [2/6] Anh Docker — buoc nay lau nhat"
if ! docker image inspect "$ANH" >/dev/null 2>&1; then
  echo "    Chua co anh $ANH, dang build..."
  docker build -t "$ANH" "$GOC"
fi
docker save "$ANH" | gzip -1 > "$DICH/docker/traffic-law-image.tar.gz"
echo "    $(du -h "$DICH/docker/traffic-law-image.tar.gz" | cut -f1)"

echo "==> [3/6] So lieu danh gia"
cp "$GOC"/eval/ket_qua_danh_gia.json \
   "$GOC"/eval/ket_qua_ablation.json \
   "$GOC"/eval/ket_qua_phat_hien_mien.json \
   "$GOC"/eval/qa_dataset.json \
   "$GOC"/eval/truy_van_ngoai_mien.json "$DICH/so_lieu/"
( cd "$GOC" && "$PY" eval/kich_ban.py --markdown ) > "$DICH/so_lieu/kich_ban_nghiem_thu.md"
echo "    5 tep JSON + bang 12 ca nghiem thu (Markdown)"

echo "==> [4/6] Khung bao cao Word"
if ( cd "$GOC" && PYTHONPATH=src "$PY" -m traffic_law.report.builder ) >/dev/null 2>&1; then
  cp "$GOC/docs/bao_cao_de_tai_4_khung.docx" "$DICH/bao_cao/"
  echo "    bao_cao_de_tai_4_khung.docx"
else
  echo "    BO QUA: thieu goi 'bao-cao' (pip install -e '.[bao-cao]')" >&2
fi
cp "$GOC"/docs/doi_chieu_de_tai_4.md "$GOC"/docs/thiet_ke_giai_phap.md "$DICH/bao_cao/"

echo "==> [5/6] Script khoi dong demo"
cp "$GOC"/scripts/nop_bai/chay_demo.sh "$GOC"/scripts/nop_bai/chay_demo.bat "$DICH/docker/"
chmod +x "$DICH/docker/chay_demo.sh"

echo "==> [6/6] Tai lieu huong dan"
cp "$GOC"/scripts/nop_bai/README_NOP_BAI.md "$DICH/README.md"
cp "$GOC"/scripts/nop_bai/HUONG_DAN_BAO_CAO.md "$DICH/"
cp "$GOC"/scripts/nop_bai/KICH_BAN_DEMO.md "$DICH/"

echo
echo "XONG. Tong dung luong: $(du -sh "$DICH" | cut -f1)"
echo "Mo: $DICH"
