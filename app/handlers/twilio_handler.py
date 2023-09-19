from twilio.rest import Client
from twilio.request_validator import RequestValidator
import uuid
import json
import base64


# Custom exception class for validation failure
class TwilioValidationException(Exception):
    def __init__(self, detail):
        self.detail = detail


class TwilioHandler:
    def __init__(self, account_sid, auth_token, redis_bd, langchain):
        self.__account_sid = account_sid
        self.__auth_token = auth_token
        self.client = Client(account_sid, auth_token)
        self.__validator = RequestValidator(auth_token)
        self.__redis = redis_bd
        self.__langchain = langchain

    def request_validator(self, url, request_form, twilio_signature):
        # Convert the form data into a dictionary
        parameters = {key: value for key, value in request_form.items()}

        return self.__validator.validate(url, request_form, twilio_signature)

    def greet_and_gather(self, response, connect):

        # Create Conversation ID
        unique_id = uuid.uuid4()

        # Create full endpoint with the Conversation ID
        action_url = f'/v1/handle-dialog?cv_id={unique_id}'

        response.append(connect.stream(url='wss://voxflowapi.onrender.com/v1/audio_stream'))
        response.say(message='Olá! Bem-vindo á Pizzaria Amanti, em que posso ajudá-lo?', language='pt-PT')

        # with response.gather(input='speech', action=action_url, speechTimeout=1,
        #                      speech_model='experimental_conversations', language='pt-PT') as gather:
        #     gather.say(message='Olá! Bem-vindo á Pizzaria Amanti, em que posso ajudá-lo?', language='pt-PT')

        return str(response)

    def handle_dialog(self, response, resp_customer, conversation_id):

        # Check if the conversation ID already exists
        existing_conversation_json = self.__redis.get(conversation_id)
        if existing_conversation_json:
            existing_conversation = json.loads(existing_conversation_json)
        else:
            existing_conversation = {"conversation": [{"role": "system", "content": "You are a helpful assistant."}]}

        # Add Customer response
        dict_customer = {'role': 'user', 'content': resp_customer}
        #existing_conversation["conversation"].append(conversation.dict()["conversation"][-1])
        existing_conversation["conversation"].append(dict_customer)

        action_url = f'/v1/handle-dialog?cv_id={conversation_id}'

        print(f'Customer Response - {resp_customer}')

        bot_response = self.__langchain.get_response('Pizzaria Amanti', resp_customer, existing_conversation)

        with response.gather(input='speech', action=action_url, speechTimeout=1,
                             speech_model='experimental_conversations', method='POST', language='pt-PT') as gather:
            gather.say(message=bot_response.content,
                       language='pt-PT')

        # Append VoxFlowBot Response
        existing_conversation["conversation"].append({"role": "assistant", "content": bot_response.content})

        self.__redis.set(conversation_id, json.dumps(existing_conversation))

        return str(response)

    async def handle_response_stream(self, websocket):

        while True:
            # Wait for user input (DTMF) from Twilio
            dtmf_input = await websocket.receive_text()
            print(dtmf_input)

            has_seen_media = False
            message_count = 0

            while True:
                message = await websocket.receive_text()
                if message is None:
                    print("No message received...")
                    continue

                data = json.loads(message)

                if data['event'] == "connected":
                    print("Connected Message received: {}".format(message))
                if data['event'] == "start":
                    print("Start Message received: {}".format(message))
                if data['event'] == "media":
                    if not has_seen_media:
                        print("Media message: {}".format(message))
                        payload = data['media']['payload']
                        print("Payload is: {}".format(payload))
                        chunk = base64.b64decode(payload)
                        print("That's {} bytes".format(len(chunk)))
                        print("Additional media messages from WebSocket are being suppressed....")
                        has_seen_media = True
                if data['event'] == "closed":
                    print("Closed Message received: {}".format(message))
                    break
                message_count += 1

            # # Process user input and generate responses in chunks
            # for response_chunk in generate_responses_in_chunks(dtmf_input):
            #     websocket.send_text(response_chunk)


