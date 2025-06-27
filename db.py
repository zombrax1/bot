import aiosqlite
from typing import Dict

_connections: Dict[str, aiosqlite.Connection] = {}

async def get_connection(path: str) -> aiosqlite.Connection:
    """Return a shared aiosqlite connection for the given database path."""
    conn = _connections.get(path)
    if conn is None:
        conn = await aiosqlite.connect(path)
        _connections[path] = conn
    return conn

async def close_all() -> None:
    """Close all tracked database connections."""
    for conn in _connections.values():
        await conn.close()
    _connections.clear()
