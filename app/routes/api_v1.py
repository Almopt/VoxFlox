from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from twilio.twiml.voice_response import VoiceResponse
import os
import supabase
import jwt
from ..handlers.twilio_handler import TwilioHandler
from ..handlers.langchain_handler import LangChainHandler
from starlette.requests import Request
from urllib.parse import parse_qs
from pydantic import BaseModel

router = APIRouter()
twilio = TwilioHandler(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
langchain = LangChainHandler(os.environ['OPENAI_API_KEY'], os.environ['PINECODE_API_KEY'], os.environ['PINECODE_API_ENV'])
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
JWT_SECRET = os.environ['JWT_SECRET']
supabase_client = supabase.Client(SUPABASE_URL, SUPABASE_KEY)


# Pydantic model for the request body
class SignInRequest(BaseModel):
    email: str
    password: str


# Function to validate JWT tokens
def validate_jwt(token: str):
    try:
        print(f'Token to validate {token}')
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'], audience='authenticated')
        print(payload)
        # Optionally, you can add additional validation logic here, such as checking the token's expiration (exp) or custom claims
        return payload
    except jwt.ExpiredSignatureError as error:
        raise HTTPException(status_code=401, detail=f'{error}')
    except jwt.InvalidTokenError as error:
        raise HTTPException(status_code=401, detail=f'Invalid Token - {error}')


# Function to get the current user based on the JWT token
# async def get_current_user(token: str = Depends(validate_jwt)):
#     if token is None:
#         raise HTTPException(status_code=401, detail="Not authenticated")
#     return token  # You can return the token or extract user information from it


def validate_file_type(file: UploadFile):
    allowed_extensions = [".txt", ".pdf"]  # Allowed file extensions
    file_extension = os.path.splitext(file.filename)[1].lower()  # Extract file extension from filename

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")


@router.post("/answer_call", response_class=HTMLResponse)
async def answer_call(request: Request):
    url = 'https://voxflowapi.onrender.com/v1/answer_call' #Validar se posso passar o request.url
    twilio_signature = request.headers.get('X-Twilio-Signature')
    request_form = await request.form()

    if not twilio.request_validator(url, request_form, twilio_signature):
        raise HTTPException(status_code=403, detail="Twilio Validation Error")
    resp = VoiceResponse()
    return twilio.greet_and_gather(resp)

@router.post("/handle-dialog", response_class=HTMLResponse)
async def handle_dialog(request: Request):
    body = await request.body()
    print(body.decode())
    data_dict = parse_qs(body.decode())
    print(data_dict.get('SpeechResult', ['']))
    #print(data_dict.get('Confidence', ['']))

    resp = VoiceResponse()
    return twilio.handle_dialog(resp)


@router.post("/signintest")
def handle_dialog(request_data: SignInRequest):
    # Create a dictionary with email and password
    user_credentials = {"email": request_data.email, "password": request_data.password}
    signin_data = supabase_client.auth.sign_in_with_password(user_credentials)
    supabase_client.auth.get_user()
    #print(f'SignIn User Data - {signin_data.user}')
    #print(f'SignIn Session Data - {signin_data.session}')
    access_token = signin_data.session.access_token
    print(f'Access Token {access_token}')

    return JSONResponse(content={"message": "Sign In Sucessful"})


@router.post("/uploadFile")
async def upload_file(file: UploadFile, current_user: dict = Depends(validate_jwt)):
    print('Entrou no metodo do upload')

    # Check if the user is authenticated (JWT validation was successful)
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Validate the file type
    validate_file_type(file)

    print(current_user)

    # Return a success message
    return JSONResponse(content={"message": "File uploaded successfully"})

@router.post("/handle_record", response_class=HTMLResponse)
def handle_record():
    resp = VoiceResponse()
    return twilio.greet_and_gather(resp)

