# syntax=docker/dockerfile:1
# Anh Docker cho he thong tra cuu phap luat giao thong duong bo.
#
# Dung hai tang: tang 'xay' cai phu thuoc vao mot virtualenv roi CHEP nguyen
# virtualenv sang tang chay. Nho vay anh cuoi khong mang theo trinh bien dich
# va bo nho dem cua pip.
#
# CO Y KHONG cai goi 'dense': mo hinh ~470 MB, khong can cho duong di mac dinh.
# Muon do tach mien thi chay ngoai container, hoac them vao dong pip ben duoi.

FROM python:3.12-slim AS xay
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Chep truoc phan khai bao phu thuoc de tan dung bo nho dem tang khi chi doi ma nguon
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e ".[ui]"

FROM python:3.12-slim AS chay
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
WORKDIR /app
COPY --from=xay /opt/venv /opt/venv

# Chay bang nguoi dung thuong, khong phai root
RUN useradd --create-home --uid 10001 tracuu
COPY --chown=tracuu:tracuu src/ ./src/
COPY --chown=tracuu:tracuu data/ ./data/
COPY --chown=tracuu:tracuu eval/ ./eval/
COPY --chown=tracuu:tracuu scripts/ ./scripts/
COPY --chown=tracuu:tracuu pyproject.toml README.md ./
USER tracuu

EXPOSE 8501
HEALTHCHECK --interval=15s --timeout=5s --start-period=90s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health',timeout=4).status==200 else 1)"

CMD ["streamlit", "run", "src/tra_cuu_gtdb/api/app.py", \
     "--server.port=8501", "--server.address=0.0.0.0"]
