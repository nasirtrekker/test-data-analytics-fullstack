FROM python:3.12-slim
RUN useradd -m -u 1000 appuser
WORKDIR /app
COPY pyproject.toml /app/
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -e "."
COPY app /app/app
RUN python -c "import fastapi, pandas, sklearn; print('OK')"
EXPOSE 8000
ENV APP_DATA_PATH=/app/sample_videos.csv
USER appuser
CMD ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
