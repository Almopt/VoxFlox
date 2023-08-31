from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from twilio.twiml.voice_response import VoiceResponse
import os
from ..handlers.twilio_handler import TwilioHandler

router = APIRouter()
twilio = TwilioHandler(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])


@router.post("/twilio_voice", response_class=HTMLResponse)
async def handle_twilio_voice():
    resp = VoiceResponse()
    return await twilio.greet_and_gather(resp)


@router.post("/handle-speech", response_class=HTMLResponse)
async def handle_speech():
    resp = VoiceResponse()
    return await twilio.handle_speech(resp)
