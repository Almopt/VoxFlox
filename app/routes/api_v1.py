from fastapi import APIRouter, HTTPException, File, UploadFile, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from twilio.twiml.voice_response import VoiceResponse
import os
import jwt
import redis
from ..handlers.twilio_handler import TwilioHandler
from ..handlers.langchain_handler import LangChainHandler
from ..handlers.supabase_handler import SupabaseHandler
from starlette.requests import Request
from urllib.parse import parse_qs
from pydantic import BaseModel

router = APIRouter()

# Redis DB Object
redis_db = redis.Redis(host=os.environ['REDIS_HOST'], port=os.environ['REDIS_PORT'],
                       password=os.environ['REDIS_PASSWORD'])
# Twilio Handler Object
twilio = TwilioHandler(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])

# LangChain Handler Object
langchain = LangChainHandler(os.environ['OPENAI_API_KEY'], os.environ['PINECODE_API_KEY'],
                             os.environ['PINECODE_API_ENV'], os.environ['PINECODE_API_INDEX'])

# Supase DB Object
db = SupabaseHandler(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])
JWT_SECRET = os.environ['JWT_SECRET']


# Pydantic model for the request body
class SignInRequest(BaseModel):
    email: str
    password: str


# Function to validate JWT tokens
def validate_jwt(token: str):
    try:
        #payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'], audience='authenticated')
        return jwt.decode(token, JWT_SECRET, algorithms=['HS256'], audience='authenticated')
        # Optionally, you can add additional validation logic here, such as checking the token's expiration (exp) or custom claims
    except jwt.ExpiredSignatureError as error:
        raise HTTPException(status_code=401, detail=f'{error}')
    except jwt.InvalidTokenError as error:
        raise HTTPException(status_code=401, detail=f'Invalid Token - {error}')


def validate_file_type(file: UploadFile):
    allowed_extensions = [".txt", ".pdf"]  # Allowed file extensions
    file_extension = os.path.splitext(file.filename)[1].lower()  # Extract file extension from filename

    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Invalid file type")


@router.post("/answer_call", response_class=HTMLResponse)
async def answer_call(request: Request):

    url = 'https://voxflowapi.onrender.com/v1/answer_call'
    twilio_signature = request.headers.get('X-Twilio-Signature')
    request_form = await request.form()

    if not twilio.request_validator(url, request_form, twilio_signature):
        raise HTTPException(status_code=403, detail="Twilio Validation Error")

    # Create Conversation ID
    resp = VoiceResponse()

    return twilio.greet_and_gather(resp, 'testeCVID')


@router.post("/handle-dialog", response_class=HTMLResponse)
async def handle_dialog(request: Request):
    body = await request.body()
    request_form = await request.form()

    query = request.query_params
    print(query)
    print(query.get('cv_id'))

    print(request.headers)

    print(request.items())

    print(request.values())
    print(request.query_params)
    #print(dict(request.query_params))
    print(body.decode())
    data_dict = parse_qs(body.decode())
    print(data_dict.get('SpeechResult', ['']))
    print(request_form)
    #print(data_dict.get('Confidence', ['']))

    resp = VoiceResponse()
    return twilio.handle_dialog(resp)


@router.post("/signintest")
def handle_dialog(request_data: SignInRequest):
    # Create a dictionary with email and password
    user_credentials = {"email": request_data.email, "password": request_data.password}
    #signin_data = supabase_client.auth.sign_in_with_password(user_credentials)
    signin_data = db.sign_in_with_password(user_credentials)
    #print(f'SignIn User Data - {signin_data.user}')
    #print(f'SignIn Session Data - {signin_data.session}')
    access_token = signin_data.session.access_token
    print(f'Access Token {access_token}')

    return JSONResponse(content={"message": "Sign In Sucessful"})


@router.post("/uploadFile")
async def upload_file(file: UploadFile, current_user: dict = Depends(validate_jwt)):

    # Check if the user is authenticated (JWT validation was successful)
    if current_user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Validate the file type
    validate_file_type(file)

    # Get user info by ID
    user_info = await db.get_user_by_id(current_user.get('sub'))

    # Load file into Vector DB
    await langchain.load_doc(file, user_info.data[0].get('RestaurantName'))
    #langchain.get_response(current_user.get('sub'))

    # Return a success message
    return JSONResponse(content={"message": "File uploaded with success"})



