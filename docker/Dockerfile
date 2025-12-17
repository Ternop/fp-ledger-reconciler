FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml /app/
RUN pip install -U pip && pip install -e ".[dev]"

COPY . /app/

EXPOSE 8000
CMD ["bash","-lc","alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
