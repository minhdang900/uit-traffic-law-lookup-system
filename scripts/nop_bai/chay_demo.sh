#!/usr/bin/env bash
# Chạy demo từ ảnh Docker đã đóng gói — macOS / Linux.
#
# Không cần cài Python, không cần mạng, không cần build gì cả.
#
#   ./chay_demo.sh            → mở tại http://localhost:8000
#   PORT=8080 ./chay_demo.sh  → đổi cổng nếu 8000 đang bận
#   ./chay_demo.sh dung       → dừng và dọn container
set -euo pipefail

CD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANH="traffic-law:latest"
TEN="traffic-law-demo"
CONG="${PORT:-8000}"

if [ "${1:-}" = "dung" ]; then
  docker rm -f "$TEN" >/dev/null 2>&1 || true
  echo "Da dung va don container '$TEN'."
  exit 0
fi

command -v docker >/dev/null 2>&1 || {
  echo "Chua cai Docker. Tai tai: https://www.docker.com/products/docker-desktop/" >&2
  exit 1; }
docker info >/dev/null 2>&1 || {
  echo "Docker chua chay. Hay mo Docker Desktop roi thu lai." >&2
  exit 1; }

# 1) Nap anh neu may chua co
if docker image inspect "$ANH" >/dev/null 2>&1; then
  echo "==> Da co anh $ANH, bo qua buoc nap."
else
  echo "==> Nap anh Docker (mat 30-60 giay)..."
  gunzip -c "$CD/traffic-law-image.tar.gz" | docker load
fi

# 2) Don container cu cua chinh demo nay neu con sot
docker rm -f "$TEN" >/dev/null 2>&1 || true

# 3) Chay
echo "==> Khoi dong tren cong $CONG..."
docker run -d --name "$TEN" -p "${CONG}:8000" "$ANH" >/dev/null

# 4) Cho den khi san sang
echo -n "==> Dang nap co so tri thuc "
for _ in $(seq 1 60); do
  if curl -fsS -o /dev/null "http://localhost:${CONG}/" 2>/dev/null; then
    echo
    echo
    echo "  SAN SANG:  http://localhost:${CONG}"
    echo
    echo "  Cac man hinh:"
    echo "    /            Tra cuu"
    echo "    /chi-so      Chi so danh gia"
    echo "    /chu-de      Duyet chu de"
    echo "    /hieu-luc    Hieu luc theo thoi gian"
    echo "    /api/docs    Tai lieu API"
    echo
    echo "  Dung lai:  ./chay_demo.sh dung"
    echo
    command -v open >/dev/null 2>&1 && open "http://localhost:${CONG}" || true
    exit 0
  fi
  echo -n "."
  sleep 2
done

echo
echo "Qua 2 phut van chua len. Xem nhat ky:" >&2
echo "    docker logs $TEN" >&2
exit 1
