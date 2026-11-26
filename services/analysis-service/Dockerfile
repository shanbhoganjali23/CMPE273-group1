# Build from repository root: docker build -f services/analysis-service/Dockerfile .
FROM python:3.11.16-slim-bookworm@sha256:a36c24f9cbdf4fd0f52d67f0823eeac19c2028c637cecc392d97f980d4fec56b
WORKDIR /app
COPY services/analysis-service/requirements.lock ./requirements.lock
RUN python -m pip install --no-cache-dir -r requirements.lock
COPY services/analysis-service/src ./src
ENV PYTHONPATH=/app/src PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 ANALYSIS_BIND_HOST=0.0.0.0
USER 10001:10001
EXPOSE 8001
ENTRYPOINT ["python", "-m", "agentmesh_analysis.main"]
