from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from ..handlers import twilio_handler, langchain_handler

router = APIRouter()


@router.post("/twilio_voice", response_class=HTMLResponse)
async def handle_twilio_voice():
    twilio_handler.TwilioHandler()
    return {"message": "Twilio is okay"}