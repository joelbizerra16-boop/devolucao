FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/uploads/sap /app/logs \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin devolucao \
    && chown -R devolucao:devolucao /app

USER devolucao

EXPOSE 8501

HEALTHCHECK --interval=15s --timeout=5s --start-period=40s --retries=10 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4)"

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
