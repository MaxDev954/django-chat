FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /app/src

ENV PYTHONPATH=/app/src

CMD ["sh", "-c", "python manage.py migrate && \
                  python manage.py collectstatic --noinput && \
                  uvicorn core.asgi:application --host 0.0.0.0 --port 8000 --reload"]