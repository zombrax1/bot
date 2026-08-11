import json
import sqlite3

from cogs.restore_pending import apply_pending_restore


def test_applies_only_staged_sqlite_set(tmp_path):
    backups, db = tmp_path / "backups", tmp_path / "db"
    staging = backups / ".restore-staging" / "safeid"
    staging.mkdir(parents=True)
    db.mkdir()
    conn = sqlite3.connect(db / "old.sqlite")
    try:
        conn.execute("create table old (x)")
        conn.commit()
    finally:
        conn.close()
    conn = sqlite3.connect(staging / "settings.sqlite")
    try:
        conn.execute("create table restored (x)")
        conn.commit()
    finally:
        conn.close()
    (backups / ".restore-pending.json").write_text(json.dumps({
        "restore_id": "safeid", "files": ["settings.sqlite"], "source": "manual_1.zip"
    }), encoding="utf-8")

    assert apply_pending_restore(backups, db) is True
    assert (db / "settings.sqlite").is_file()
    assert not (db / "old.sqlite").exists()
    assert not (backups / ".restore-pending.json").exists()
