from twilio.rest import Client


class TwilioHandler:
    def __init__(self, account_sid, auth_token):
        self.client = Client(account_sid, auth_token)

    def greet_and_gather(self, response):
        with response.gather(input='speech', action='/handle-speech', speech_model='experimental_conversations',
                             language='pt-PT') as gather:
            gather.say(message='Olá! Bem-vindo á Pizzaria Imaginária, em que posso ajudá-lo?', language='pt-PT')

        return str(response)


