"""Sessions endpoints."""

from fastapi import APIRouter

from ..collectors.sessions import collect_sessions
from .serialize import to_dict

router = APIRouter()


@router.get("/sessions")
async def get_sessions():
    return to_dict(collect_sessions())
