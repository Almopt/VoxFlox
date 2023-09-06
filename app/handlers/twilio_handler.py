from twilio.rest import Client
from twilio.request_validator import RequestValidator


# Custom exception class for validation failure
class TwilioValidationException(Exception):
    def __init__(self, detail):
        self.detail = detail

class TwilioHandler:
    def __init__(self, account_sid, auth_token):
        self.__account_sid = account_sid
        self.__auth_token = auth_token
        self.client = Client(account_sid, auth_token)
        self.__validator = RequestValidator(auth_token)

    def request_validator(self, request_url, request_body, twilio_signature):
        print('entrou no metodo do validator')
        # print(request_url)
        # print(request_body)
        # print(twilio_signature)
        # print(self.__validator.validate(request_url, request_body, twilio_signature))
        try:
            if self.__validator.validate(request_url, request_body, twilio_signature):
                print('correu bem')
                return True
            else:
                print('correu mal')
                raise TwilioValidationException("Twilio request validation failed")
        except Exception as e:
            raise TwilioValidationException(f"Twilio validation error: {str(e)}")


    def greet_and_gather(self, response):
        #response.record(action='/v1/handle-record')
        with response.gather(input='speech', action='/v1/handle-dialog', speechTimeout='1.5',
                             speech_model='experimental_conversations', language='pt-PT') as gather:
            gather.say(message='Olá! Bem-vindo á Pizzaria Imaginária, em que posso ajudá-lo?', language='pt-PT')

        return str(response)

    def handle_dialog(self, response):
        with response.gather(input='speech', action='/v1/handle-dialog', speechTimeout='1.5',
                             speech_model='experimental_conversations', method='POST', language='pt-PT') as gather:
            gather.say(message='Recebemos a sua mensagem com sucesso, para terminar a chamada diga adeus',
                       language='pt-PT')

        return str(response)


