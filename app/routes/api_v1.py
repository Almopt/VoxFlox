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
    try:

        body = await request.body()
        print(f'Url - {request.url}')
        #print(parse_qs(body.decode()))
        signature = request.headers.get('X-Twilio-Signature')
        print(f'Signature - {signature}')
        request_form = await request.form()
        #form_data = {key: value.strip('[]') for key, value in sorted(request_form)}
        form_data = {key: value for key, value in sorted(request_form)}
        print(form_data)
        # if not twilio.request_validator(request.url, parse_qs(body.decode()), request.headers.get('x-twilio-signature')):
        #     raise HTTPException(status_code=403, detail='Unauthorized')
        twilio.request_validator(request.url, form_data, request.headers.get('X-Twilio-Signature'))
        resp = VoiceResponse()
        return twilio.greet_and_gather(resp)

    except TwilioValidationException as e:
        raise HTTPException(status_code=403, detail=str(e))
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

