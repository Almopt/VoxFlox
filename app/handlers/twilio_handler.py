from twilio.rest import Client


class TwilioHandler:
    def __init__(self, account_sid, auth_token):
        self.client = Client(account_sid, auth_token)

    def greet_and_gather(self, response):
        with response.gather(input='speech', action='/handle-speech', speech_model='experimental_conversations',
                             language='pt-PT') as gather:
            gather.say(message='Olá! Bem-vindo á Pizzaria Imaginária, em que posso ajudá-lo?', language='pt-PT')

        return str(response)

    def handle_speech(self, response):
        with response.gather(input='speech', action='/handle-speech', speechTimeout='2',
                             speech_model='experimental_conversations', method='POST', language='pt-PT') as gather:
            gather.say(message='Recebemos a sua mensagem com sucesso, para terminar a chamada diga adeus',
                       language='pt-PT')

        # response.say('Se desejar, você pode finalizar a chamada a qualquer momento. Caso contrário, continue a falar.')
        # response.record(timeout=5, action='/handle-record', method='POST')

        return str(response)


