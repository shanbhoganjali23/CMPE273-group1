"""Process health only. No trace queries, diagnosis or provider calls."""

import json
import logging
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Literal

from agentmesh_analysis.config import Settings


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Fixed operational messages only; no request bodies, env or exception dumps.
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": "analysis-service",
            "message": record.getMessage(),
        })


class Health(BaseModel):
    status: Literal["UP", "DOWN"]


def create_app() -> FastAPI:
    app = FastAPI(title="AgentMesh Analysis", version="0.1.0", docs_url=None,
                  redoc_url=None, openapi_url=None)

    @app.get("/health/live", response_model=Health)
    def live() -> Health:
        return Health(status="UP")

    @app.get("/health/ready", response_model=Health)
    def ready() -> Health:
        # This skeleton has no required dependencies. Model access is optional.
        return Health(status="UP")

    return app


app = create_app()


def main() -> None:
    settings = Settings()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
    uvicorn.run(app, host=settings.bind_host, port=settings.port,
                log_config=None, access_log=False)


if __name__ == "__main__":
    main()
