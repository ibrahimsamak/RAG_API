# Dockerfile
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

EXPOSE 8000
# gunicorn manages uvicorn workers in production
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", \
    "--workers", "4", "--bind", "0.0.0.0:8000"]
