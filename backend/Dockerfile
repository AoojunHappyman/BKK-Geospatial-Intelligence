FROM python:3.13-slim
WORKDIR /workspace
COPY backend/requirements.txt backend/requirements.txt
COPY data-pipeline/requirements.txt data-pipeline/requirements.txt
RUN pip install --no-cache-dir -r data-pipeline/requirements.txt
COPY backend backend
COPY data-pipeline data-pipeline
COPY database database
COPY scripts scripts
COPY data data
ENV PYTHONPATH=/workspace/backend
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
