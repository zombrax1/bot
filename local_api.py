import os
import json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI(title="Local Gift Code API")

DATA_FILE = "local_api_data.json"
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
else:
    db = {"codes": {}, "players": {}}


def save_db():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


class GiftCode(BaseModel):
    code: str
    date: str | None = None


@app.get("/giftcode_api.php")
async def get_codes(action: str | None = None, giftcode: str | None = None):
    if action == "check" and giftcode is not None:
        return {"exists": giftcode in db["codes"]}
    return {"codes": [f"{c} {d}" for c, d in db["codes"].items()]}


@app.post("/giftcode_api.php")
async def add_code(gift: GiftCode):
    if gift.code in db["codes"]:
        raise HTTPException(status_code=409, detail="Code already exists")
    db["codes"][gift.code] = gift.date or ""
    save_db()
    return {"success": True}


@app.delete("/giftcode_api.php")
async def delete_code(gift: GiftCode):
    if gift.code in db["codes"]:
        db["codes"].pop(gift.code)
        save_db()
    return {"success": True}


@app.post("/api/player")
async def player_info(request: Request):
    form = await request.form()
    fid = form.get("fid")
    if not fid:
        raise HTTPException(status_code=400, detail="fid required")
    player = db["players"].get(fid)
    if not player:
        return {"data": None}
    return {"data": player}
