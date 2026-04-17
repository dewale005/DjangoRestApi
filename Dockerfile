FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
RUN chmod +x /app/scripts/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["gunicorn", "webapp.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
