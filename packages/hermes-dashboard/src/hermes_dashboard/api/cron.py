"""Cron jobs endpoint."""

from fastapi import APIRouter

from ..collectors.cron import collect_cron
from .serialize import to_dict

router = APIRouter()


@router.get("/cron")
async def get_cron():
    return to_dict(collect_cron())
