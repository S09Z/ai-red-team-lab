FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Run as an unprivileged user (contrast to the vulnerable app running as root).
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 5000
# Production WSGI server (not the Flask dev server); app factory entry point.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
