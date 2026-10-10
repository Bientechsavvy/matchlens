FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY frontend ./frontend
RUN pip install --no-cache-dir ".[azure,agents]"
ENV FRONTEND_DIR=/app/frontend
EXPOSE 8000
CMD ["uvicorn", "matchlens.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
