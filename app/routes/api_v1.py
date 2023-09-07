from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from twilio.twiml.voice_response import VoiceResponse
import os
from ..handlers.twilio_handler import TwilioHandler, TwilioValidationException
from ..handlers.langchain_handler import LangChainHandler
from starlette.requests import Request
from urllib.parse import parse_qs
from collections import OrderedDict

router = APIRouter()
twilio = TwilioHandler(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
langchain = LangChainHandler(os.environ['OPENAI_API_KEY'])


@router.post("/answer_call", response_class=HTMLResponse)
async def answer_call(request: Request):
    try:

        #body = await request.body()
        print(f'Url - {request.url}')
        #print(parse_qs(body.decode()))
        signature = request.headers.get('X-Twilio-Signature')
        print(f'Signature - {signature}')
        request_form = await request.form()
        print(request_form)

        # The data in string format
        data_str = str(request_form)
        print(f'Form in string {data_str}')

        # Extract the content within parentheses and split it by commas
        items = data_str[data_str.find("(") + 1:data_str.rfind(")")].split(",")
        print(items)

        # Initialize an empty dictionary
        data_dict = {}

        # Loop through the items and split them into key-value pairs
        for item in items:
            key, value = item.strip(" '()").split(", ")
            data_dict[key] = value

        # Sort the dictionary by keys and create an ordered dictionary
        sorted_dict = OrderedDict(sorted(data_dict.items(), key=lambda x: x[0]))

        print(sorted_dict)


        #form_data = {key: value.strip('[]') for key, value in sorted(request_form)}
        # form_data = {key: value for key, value in sorted(request_form)}
        # print(form_data)
        # if not twilio.request_validator(request.url, parse_qs(body.decode()), request.headers.get('x-twilio-signature')):
        #     raise HTTPException(status_code=403, detail='Unauthorized')
        twilio.request_validator(request.url, sorted_dict, request.headers.get('X-Twilio-Signature'))
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

