FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -e ".[dev]"
COPY app /app/app
EXPOSE 8000
ENV APP_DATA_PATH=/app/sample_videos.csv
CMD ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
