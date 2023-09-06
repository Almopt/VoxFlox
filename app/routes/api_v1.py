from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from twilio.twiml.voice_response import VoiceResponse
import os
from ..handlers.twilio_handler import TwilioHandler
from ..handlers.langchain_handler import LangChainHandler
from starlette.requests import Request
from urllib.parse import parse_qs

router = APIRouter()
twilio = TwilioHandler(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
langchain = LangChainHandler(os.environ['OPENAI_API_KEY'])


@router.post("/answer_call", response_class=HTMLResponse)
async def answer_call(request: Request):
    try:
        resp = VoiceResponse()
        body = await request.body()
        twilio.request_validator(request.url, body, request.headers.get('x-twilio-signature'))
        form_test = await request.form()
        print(form_test)
        return twilio.greet_and_gather(resp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/handle-dialog", response_class=HTMLResponse)
async def handle_dialog(request: Request):
    body = await request.body()
    print(body.decode())
    data_dict = parse_qs(body.decode())
    print(data_dict.get('SpeechResult', ['']))
    #print(data_dict.get('Confidence', ['']))

    resp = VoiceResponse()
    return twilio.handle_dialog(resp)

@router.post("/handle_record", response_class=HTMLResponse)
def handle_record():
    resp = VoiceResponse()
    return twilio.greet_and_gather(resp)

