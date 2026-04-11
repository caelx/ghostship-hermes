"""Health check endpoint."""

from fastapi import APIRouter

from ..collectors.health import collect_health
from .serialize import to_dict

router = APIRouter()


@router.get("/health")
async def get_health():
    return to_dict(collect_health())
