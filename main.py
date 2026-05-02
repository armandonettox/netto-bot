from fastapi import FastAPI, Request, Query
from src.bot.handlers import handle_message
import os

app = FastAPI()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")


@app.get("/webhook")
async def verify(hub_mode: str = Query(None, alias="hub.mode"),
                 hub_challenge: str = Query(None, alias="hub.challenge"),
                 hub_verify_token: str = Query(None, alias="hub.verify_token")):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "invalid token"}, 403


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    await handle_message(data)
    return {"status": "ok"}
