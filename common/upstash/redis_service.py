import json
from upstash_redis import Redis


def get_redis_client(url: str, token: str) -> Redis:
    """ Return a Upstash redis client"""
    return Redis(url=url, token=token)


def save_to_redis(redis: Redis, sid: str, key: str, value, ex: int = 86400):
    """ Function to save to Upstash redis used in operational relevant branches (streamlit) """
    redis.set(f"{sid}:{key}", json.dumps(value), ex=ex)


def get_from_redis(redis: Redis, sid: str, key: str, default=None):
    """ Function to get value from Upstash redis used in operational relevant branches (streamlit) """
    val = redis.get(f"{sid}:{key}")
    return json.loads(val) if val is not None else default