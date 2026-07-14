FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src:/app/apps/web

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src
COPY apps/web /app/apps/web

EXPOSE 8000

CMD ["uvicorn", "geococo_web.main:app", "--host", "0.0.0.0", "--port", "8000"]
