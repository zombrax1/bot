"""Apply a validated staged database restore before the bot opens SQLite."""
import json
import os
import shutil
import sqlite3
from pathlib import Path


def apply_pending_restore(backup_dir="backups", db_dir="db") -> bool:
    pending = Path(backup_dir) / ".restore-pending.json"
    if not pending.is_file():
        return False
    payload = json.loads(pending.read_text(encoding="utf-8"))
    root = (Path(backup_dir) / ".restore-staging").resolve()
    staging = (root / payload["restore_id"]).resolve()
    names = payload.get("files", [])
    if (not str(staging).startswith(str(root) + os.sep) or not names
            or any(Path(name).name != name or not name.endswith(".sqlite") for name in names)):
        raise RuntimeError("Invalid pending restore manifest")
    target = Path(db_dir)
    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        source = staging / name
        if not source.is_file():
            raise RuntimeError(f"Staged restore file is missing: {name}")
        conn = sqlite3.connect(source)
        try:
            if conn.execute("PRAGMA integrity_check").fetchone()[0].lower() != "ok":
                raise RuntimeError(f"Staged restore database is invalid: {name}")
        finally:
            conn.close()
    for name in names:
        os.replace(staging / name, target / name)
    for old in target.glob("*.sqlite"):
        if old.name not in names:
            old.unlink()
    pending.unlink()
    shutil.rmtree(staging, ignore_errors=True)
    print(f"Applied staged database restore ({len(names)} SQLite file(s)).", flush=True)
    return True
