"""Validation service FastAPI application: bootstrap y montaje de componentes."""

import logging

from fastapi import FastAPI
from shared.web.cors import add_cors, parse_origins
from shared.web.logging import RequestIdMiddleware, TimingMiddleware, setup_logging

from routes import router
from settings import get_settings

settings = get_settings()

setup_logging(
    "validation-service",
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
)

app = FastAPI(title="PDF Validation Service", version="1.0.0")

# CORS explícito por entorno (sin comodín); RequestId se registra último para
# quedar como middleware más externo y sellar también las respuestas de preflight.
# Timing se registra antes para quedar por dentro: su log recién emite cuando
# RequestId aún no reseteó el ContextVar, así el request_id no llega como `-`.
add_cors(app, origins=parse_origins(settings.cors_origins))
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIdMiddleware)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "validation-service"}


app.include_router(router)
