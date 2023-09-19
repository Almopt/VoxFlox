from fastapi import APIRouter, HTTPException, UploadFile, Depends, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from twilio.twiml.voice_response import VoiceResponse, Connect
import os
import jwt
import redis
from ..handlers.twilio_handler import TwilioHandler
from ..handlers.langchain_handler import LangChainHandler
from ..handlers.supabase_handler import SupabaseHandler
from starlette.requests import Request
from pydantic import BaseModel

router = APIRouter()

# Redis DB Object
redis_db = redis.Redis(host=os.environ['REDIS_HOST'], port=os.environ['REDIS_PORT'],
                       password=os.environ['REDIS_PASSWORD'])

# LangChain Handler Object
langchain = LangChainHandler(os.environ['OPENAI_API_KEY'], os.environ['PINECODE_API_KEY'],
                             os.environ['PINECODE_API_ENV'], os.environ['PINECODE_API_INDEX'])

# Twilio Handler Object
twilio = TwilioHandler(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'], redis_db, langchain)

# Supase DB Object
db = SupabaseHandler(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY'])

# SB JWT Secret
JWT_SECRET = os.environ['JWT_SECRET']

# Twilio Endpoints
ENDPOINT_ANSWER_CALL = os.environ['TWILIO_ENDPOINT_ANSWER_CALL']
ENDPOINT_DIALOG = os.environ['TWILIO_ENDPOINT_DIALOG']

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


@router.websocket_route("/audio_stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await twilio.handle_response_stream(websocket)



@router.post("/answer_call", response_class=HTMLResponse)
async def answer_call(request: Request):

    # Validate Twilio Request
    twilio_signature = request.headers.get('X-Twilio-Signature')
    request_form = await request.form()

    if not twilio.request_validator(ENDPOINT_ANSWER_CALL, request_form, twilio_signature):
        raise HTTPException(status_code=403, detail="Twilio Validation Error")

    resp = VoiceResponse()
    connect = Connect()

    return twilio.greet_and_gather(resp, connect)


@router.post("/handle-dialog", response_class=HTMLResponse)
async def handle_dialog(request: Request):

    # Validate Twilio Request
    twilio_signature = request.headers.get('X-Twilio-Signature')
    request_form = await request.form()
    data_dict = dict(request_form)

    #body = await request.body()
    conversation_id = request.query_params.get('cv_id')

    full_url = f'{ENDPOINT_DIALOG}?cv_id={conversation_id}'

    if not twilio.request_validator(full_url, request_form, twilio_signature):
        raise HTTPException(status_code=403, detail="Twilio Validation Error")

    #print(body.decode())
    #customer_response = parse_qs(body.decode()).get('SpeechResult', [''])[0]
    customer_response = data_dict.get('SpeechResult', '')
    #print(data_dict.get('Confidence', ['']))

    resp = VoiceResponse()
    return twilio.handle_dialog(resp, customer_response, conversation_id)


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



