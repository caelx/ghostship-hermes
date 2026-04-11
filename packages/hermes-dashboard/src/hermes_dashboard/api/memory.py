"""Memory endpoints."""

from fastapi import APIRouter

from ..collectors.memory import collect_memory
from ..collectors.config import collect_config
from .serialize import to_dict

router = APIRouter()


@router.get("/memory")
async def get_memory():
    """Memory and user profile state."""
    config = collect_config()
    memory, user = collect_memory(
        memory_char_limit=config.memory_char_limit,
        user_char_limit=config.user_char_limit,
    )
    return {
        "memory": to_dict(memory),
        "user": to_dict(user),
    }
