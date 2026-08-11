"""Safe configuration primitives for the optional player-sync HTTP provider.

Secrets are referenced by environment-variable name, never stored in SQLite.
The generic provider contract is an object containing a configured members list;
each member requires the configured identity field and may contain mapped fields.
"""
import json
import os
import base64

DEFAULT_MAPPING = {"members": "members", "id": "player_id", "name": "name", "power": "power", "furnace": "furnace_level", "state": "state"}


def should_run_daily(enabled, daily_time, last_daily_date, now):
    return bool(enabled) and last_daily_date != now.date().isoformat() and now.strftime("%H:%M") == daily_time


def read_path(value, path):
    for part in path.split('.'):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def normalize_mapping(raw):
    mapping = json.loads(raw) if isinstance(raw, str) else raw
    if not isinstance(mapping, dict) or not all(isinstance(v, str) and v for v in mapping.values()):
        raise ValueError("mapping must contain non-empty JSON field paths")
    if not {"members", "id"}.issubset(mapping):
        raise ValueError("mapping requires members and id paths")
    return mapping


def normalize_generic_roster(payload, mapping):
    members = read_path(payload, mapping["members"])
    if not isinstance(members, list) or not members:
        raise ValueError("response has no configured members list")
    roster = {}
    for item in members:
        fid = read_path(item, mapping["id"])
        if fid is None:
            raise ValueError("response member is missing configured identity")
        normalized = {"player_id": fid}
        for output, source in mapping.items():
            if output not in ("members", "id"):
                value = read_path(item, source)
                if value is not None:
                    normalized["furnace_level" if output == "furnace" else output] = value
        roster[str(fid)] = normalized
    return roster


def auth_headers(auth_type, secret_env, header_name=""):
    secret = os.getenv(secret_env, "") if secret_env else ""
    if auth_type == "none":
        return {}
    if not secret:
        raise ValueError("credential is not configured")
    if auth_type == "bearer":
        return {"Authorization": f"Bearer {secret}"}
    if auth_type == "api_key":
        return {header_name or "X-API-Key": secret}
    if auth_type == "header":
        if not header_name:
            raise ValueError("custom header name is required")
        return {header_name: secret}
    if auth_type == "basic":
        encoded = base64.b64encode(secret.encode("utf-8")).decode("ascii")
        return {"Authorization": f"Basic {encoded}"}
    raise ValueError("unsupported authentication type")
