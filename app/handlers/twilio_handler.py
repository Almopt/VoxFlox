from twilio.rest import Client
from twilio.request_validator import RequestValidator
import uuid


# Custom exception class for validation failure
class TwilioValidationException(Exception):
    def __init__(self, detail):
        self.detail = detail

class TwilioHandler:
    def __init__(self, account_sid, auth_token, endpoint):
        self.__account_sid = account_sid
        self.__auth_token = auth_token
        self.client = Client(account_sid, auth_token)
        self.__validator = RequestValidator(auth_token)
        self.__endpoint = endpoint


    def request_validator(self, request_form, twilio_signature):
        # Convert the form data into a dictionary
        parameters = {key: value for key, value in request_form.items()}

        return self.__validator.validate(self.__endpoint, request_form, twilio_signature)


    def greet_and_gather(self, response):

        with response.gather(input='speech', action='/v1/handle-dialog', speechTimeout=1,
                             speech_model='experimental_conversations', language='pt-PT') as gather:
            gather.say(message='Olá! Bem-vindo á Pizzaria Amanti, em que posso ajudá-lo?', language='pt-PT')

        return str(response)

    def handle_dialog(self, response, resp_customer):

        # Create Conversation ID
        unique_id = uuid.uuid4()

        # Create full endpoint with the Conversation ID
        action_url = f'/v1/handle-dialog?cv_id={unique_id}'


        with response.gather(input='speech', action=action_url, speechTimeout='1',
                             speech_model='experimental_conversations', method='POST', language='pt-PT') as gather:
            gather.say(message='Recebemos a sua mensagem com sucesso, para terminar a chamada diga adeus',
                       language='pt-PT')

        return str(response)


