from fastapi import APIRouter

from app.api.v1.cases import router as cases_router
from app.api.v1.contradictions import router as contradictions_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.events import router as events_router
from app.api.v1.graph import router as graph_router
from app.api.v1.health import router as health_router
from app.api.v1.hypotheses import router as hypotheses_router
from app.api.v1.timeline import router as timeline_router
from app.api.v1.assistant import router as assistant_router
from app.api.v1.movement import router as movement_router


api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(cases_router)
api_router.include_router(evidence_router)
api_router.include_router(events_router)
api_router.include_router(timeline_router)
api_router.include_router(contradictions_router)
api_router.include_router(graph_router)
api_router.include_router(hypotheses_router)
api_router.include_router(assistant_router)
api_router.include_router(movement_router)