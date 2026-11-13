FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv

COPY api/requirements.txt api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt psycopg2-binary

# Kök dizinden derlenir (main branch'inde api/ ve chatbot/ birlikte bulunur):
#   docker build -f api/Dockerfile -t fatura-api .
COPY api/ api/
COPY chatbot/ chatbot/

WORKDIR /srv/api
# Gizli bilgiler imaja girmez; çalışırken ortam değişkeni olarak verilir (JWT_SECRET, DATABASE_URL, ...)
RUN useradd --create-home appuser && mkdir -p /srv/api/storage && chown -R appuser /srv/api
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

