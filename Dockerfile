FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data
COPY demo ./demo
RUN pip install --no-cache-dir -e ".[resume_extract]"

EXPOSE 10000
CMD ["sh", "-c", "gunicorn 'medical_career_agent.api:create_app()' --bind 0.0.0.0:${PORT:-10000} --workers 2 --threads 4 --timeout 120"]
