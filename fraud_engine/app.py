"""
SpaceLoop Fraud & Trust Engine FastAPI Application
Provides high-performance, asynchronous REST endpoints for event ingestion, scoring, and alerts.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from fraud_engine.schemas import (
    FraudEventInput,
    ScoreRequest,
    FraudScoreResponse,
    EventIngestResponse,
    AlertResponse,
    HealthResponse
)
from fraud_engine.service import FraudService
from fraud_engine.db import get_db, ensure_fraud_tables

app = FastAPI(
    title="SpaceLoop Fraud & Trust Engine",
    description="Hybrid fraud detection, anomaly scoring, and trust infrastructure for SpaceLoop P2P marketplace.",
    version="1.0.0",
    docs_url="/fraud/docs",
    openapi_url="/fraud/openapi.json"
)

# Enable CORS for frontend and service-to-service communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    ensure_fraud_tables()


@app.get("/fraud/health", response_model=HealthResponse, tags=["Health"])
def get_fraud_health():
    """
    Health check endpoint returning service status, engine versions, and timestamp.
    """
    return HealthResponse(
        status="healthy",
        service="SpaceLoop Fraud & Trust Engine",
        version="1.0.0",
        framework="FastAPI + Pandas + NumPy",
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/fraud/events", response_model=EventIngestResponse, status_code=status.HTTP_201_CREATED, tags=["Events"])
def ingest_fraud_event(event: FraudEventInput, db: Session = Depends(get_db)):
    """
    Ingest a SpaceLoop event into the fraud engine pipeline:
    SPACELOOP EVENT → FRAUD SERVICE → FEATURE EXTRACTION → RULE ENGINE → RISK ENGINE
    """
    try:
        return FraudService.ingest_event(event, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process fraud event: {str(e)}")


@app.post("/fraud/score", response_model=FraudScoreResponse, tags=["Scoring"])
def score_prospective_event(request: ScoreRequest, db: Session = Depends(get_db)):
    """
    Calculate on-demand risk score and policy decision without storing an uncommitted event record.
    """
    try:
        return FraudService.score_event(request, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to score event: {str(e)}")


@app.get("/fraud/alerts", response_model=List[AlertResponse], tags=["Alerts"])
def list_fraud_alerts(
    status: Optional[str] = Query(default=None, description="Filter by status (open, investigating, resolved, dismissed)"),
    severity: Optional[str] = Query(default=None, description="Filter by severity (low, medium, high, critical)"),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Retrieve list of actionable fraud alerts for moderation and triage.
    """
    return FraudService.get_alerts(db, status=status, severity=severity, limit=limit)


@app.get("/fraud/alerts/{id}", response_model=AlertResponse, tags=["Alerts"])
def get_fraud_alert_detail(id: str, db: Session = Depends(get_db)):
    """
    Retrieve detailed evidence, triggered rules, and feature snapshot for a specific fraud alert.
    """
    alert = FraudService.get_alert_by_id(db, id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Fraud alert '{id}' not found.")
    return alert
