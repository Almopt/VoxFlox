from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from twilio.twiml.voice_response import VoiceResponse
import os
from ..handlers.twilio_handler import TwilioHandler, TwilioValidationException
from ..handlers.langchain_handler import LangChainHandler
from starlette.requests import Request
from urllib.parse import parse_qs

router = APIRouter()
twilio = TwilioHandler(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
langchain = LangChainHandler(os.environ['OPENAI_API_KEY'])


@router.post("/answer_call", response_class=HTMLResponse)
async def answer_call(request: Request):
    #try:
    url = 'https://voxflowapi.onrender.com/v1/answer_call'
    #body = await request.body()
    twilio_signature = request.headers.get('X-Twilio-Signature')
    request_form = await request.form()

    if not twilio.request_validator(url, request_form, twilio_signature):
        raise HTTPException(status_code=403, detail="Twilio Validation Error")
    resp = VoiceResponse()
    return twilio.greet_and_gather(resp)

    # except TwilioValidationException as e:
    #     raise HTTPException(status_code=403, detail=str(e))
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))


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

