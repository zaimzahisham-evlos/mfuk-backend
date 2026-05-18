from redis.asyncio import Redis
from ..core.config import settings
from datetime import datetime, UTC


def redis_client():
 return Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB, decode_responses=True)

def _seconds_until_expiration(expiration_timestamp: int) -> int:
    now = int(datetime.now(UTC).timestamp())
    return max(expiration_timestamp - now, 1) # ensure at least 1 second until expiration

async def revoke_token(jti: str, expiration_timestamp: int) -> None:
    ttl = _seconds_until_expiration(expiration_timestamp)
    redis = redis_client()
    await redis.set(name=jti, value="", ex=ttl)


async def is_token_revoked(jti: str) -> bool:
    redis = redis_client()
    return await redis.get(name=jti) is not None # if token exists here, it means it has been revoked