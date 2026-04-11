"""Console endpoint."""

from fastapi import APIRouter, HTTPException

from ..console import close_console_session, get_console_status, open_console_session

router = APIRouter()


@router.get('/console')
async def get_console():
    return await get_console_status()


@router.post('/console/open')
async def open_console():
    try:
        return await open_console_session()
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post('/console/sessions/{session_id}/close')
async def close_console(session_id: str):
    return await close_console_session(session_id)
