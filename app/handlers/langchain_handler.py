from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate, SystemMessagePromptTemplate
from langchain.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from typing import AsyncIterable
import pinecone
import tempfile
import os
import asyncio
import time


ROLE_CLASS_MAP = {
    "assistant": AIMessage,
    "user": HumanMessage,
    "system": SystemMessage
}

class LangChainHandler:
    def __init__(self, openai_api_key, pinecode_api_key, pinecode_api_env, pinecode_index):
        self.__open_api_key = openai_api_key

        # Initialize PineCode
        pinecone.init(api_key=pinecode_api_key, environment=pinecode_api_env)

        # Create Embeddings of your documents to get ready for semantic search
        self.__embeddings = OpenAIEmbeddings(openai_api_key=self.__open_api_key)

        # Pinecode Index Name
        self.__index_name = pinecode_index

        # Pinecode Index
        self.__index = pinecone.Index(pinecode_index)

        # Pinecode Vector
        self.__vectorstore = Pinecone(self.__index, self.__embeddings.embed_query, 'text')

        # self.__llm = ChatOpenAI(streaming=True, callbacks=[StreamingStdOutCallbackHandler()], temperature=0,
        #                         openai_api_key=openai_api_key)

        self.__llm = ChatOpenAI(streaming=True, callbacks=[AsyncIteratorCallbackHandler()], temperature=0,
                                openai_api_key=openai_api_key)

        # self.__prompt_template = """
        #     You are a nice and professional assistance for restaurants. I will share the restaurant menu and all
        #     the information required and you will give me the best answer that will help the costumer make a order or a
        #     reservation. You only have to identify the price and ingredients of the dishes when the customer asks you to.
        #     You will follow all rules bellow:
        #
        #     1/Understand the purpose of the call, whether it's to place a takeaway order,
        #     delivery or to make a reservation.
        #
        #     2/ If it's a take-away order, help with any questions the customer may have about the menu.
        #     Ask what the order is under and thank them for their preference.
        #
        #     3/If it's a home delivery order, help with any questions the customer may have about the menu.
        #     Ask for the delivery address and thank them for their preference.
        #
        #     4/If it's a reservation, ask how many people the reservation is for and what name the reservation is in.
        #
        #     Bellow is the required information you need to answer:
        #     {company_info}
        #
        #     Please answer nicely.
        # """

        self.__prompt_template = """
        You are a restaurant assistant responsible for managing incoming calls and assisting customers with various
        requests. Your main tasks include taking reservations, processing take-away orders, and arranging home delivery
        orders. Your goal is to provide excellent customer service and ensure a smooth and efficient ordering process.

        As a restaurant assistant, you should be polite, patient, and attentive to customer needs. You should have good
        communication skills and be able to handle multiple tasks simultaneously. You should also be familiar with the
        restaurant's menu, pricing, and policies to answer customer inquiries accurately.

        In this role, you will receive calls from customers looking to make reservations for dining in, place orders for
        take-away, or request home delivery. You will need to gather relevant information such as the number of guests,
        preferred date and time, specific dietary requirements, and delivery address. Based on this information, you
        will assist customers in finding suitable options and provide recommendations if needed.

        To make a reservation, you will need to check the availability of tables and confirm the reservation details
        with the customer. For take-away orders, you will need to accurately record the order, suggest any specials or
        add-ons, and provide an estimated pick-up time. When handling home delivery orders, you will need to ensure the
        customer's address is within the delivery range and coordinate with the delivery team to ensure timely and
        accurate delivery.

        Throughout your interactions with customers, it is important to maintain a professional and friendly manner,
        addressing any concerns or issues promptly and finding appropriate solutions.
        Your ultimate goal is to provide a positive customer experience and ensure that all orders are processed
        efficiently and accurately.

        Bellow is the required information you need to answer:
        {company_info}

        Remember, as a restaurant assistant, you play a crucial role in managing customer interactions and contributing
        to the overall success of the restaurant.

        Please note that the answers to the following questions should be short and concise.
        """

        # self.__prompt_template = """
        #     As a restaurant assistant, your tasks include reservations, take-away orders, and home deliveries.
        #     Provide excellent service, handle inquiries, and ensure a smooth process. Be polite, attentive, and
        #     knowledgeable about the menu. Gather customer details for reservations, order specifics for take-away, and
        #     delivery addresses. Check table availability, record orders, and coordinate home deliveries efficiently.
        #     Maintain professionalism, address concerns promptly, and prioritize a positive customer experience.
        #     Bellow is the required information you need to answer:
        #     {company_info}
        # """

        self.__prompt = PromptTemplate(
            template=self.__prompt_template, input_variables=["company_info"]
        )
        self.__system_message_prompt = SystemMessagePromptTemplate(prompt=self.__prompt)

    async def load_doc(self, file, company_name):

        file_content = await file.read()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        try:
            # Load the file data
            loader = UnstructuredPDFLoader(temp_file_path)
            data = loader.load()
            #print(data)

            # Chunk data up into smaller documents
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            texts = text_splitter.split_documents(data)
            #print(texts)

            # Metadata
            #meta = [{'company': company_name}]
            metadata = [{'company': company_name} for _ in texts]

            Pinecone.from_texts([t.page_content for t in texts], self.__embeddings, metadatas=metadata
                                , index_name=self.__index_name)
        finally:
            # Clean up the temporary file
            os.remove(temp_file_path)

    def load_doc_local(self):
        # Load the file data
        loader = UnstructuredPDFLoader('/Users/alexmorg/PycharmProjects/FirstAIProject/docs/menu_test.pdf')
        data = loader.load()
        print(data)

        # Chunk data up into smaller documents
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(data)
        print(texts)

        # Metadata
        metadata = [{'company': 'Pizzaria Amanti'} for _ in texts]
        print(metadata)

        Pinecone.from_texts([t.page_content for t in texts], self.__embeddings, metadatas=metadata
                            , index_name=self.__index_name)

    def __create_messages(self, conversation):
        return [ROLE_CLASS_MAP[message['role']](content=message['content']) for message in conversation]


    async def get_response(self, company_name, query, conversation):  #-> AsyncIterable[str]:

        # Defining Metadata Filter
        metadata_filter = {
            "company": {"$eq": company_name},
        }

        #print(self.__index.describe_index_stats())

        # Get vector from Pinecode Index
        #vectorstore = Pinecone(self.__index, self.__embeddings.embed_query, 'text')

        # Query
        docs = self.__vectorstore.similarity_search(
            query,  # our search query
            k=3,  # return 3 most relevant docs
            filter=metadata_filter  # query filter
        )

        # Prepare the prompt
        prompt = self.__system_message_prompt.format(company_info=self.__format_docs(docs))

        # Combine prompt with new messages and chat history
        messages = [prompt] + self.__create_messages(conversation=conversation['conversation'])

        # task = asyncio.create_task(
        #     self.__llm.agenerate(messages=[messages])
        # )
        #
        # try:
        #     async for token in AsyncIteratorCallbackHandler().aiter():
        #         yield token
        # except Exception as e:
        #     print(f"Caught exception: {e}")
        # finally:
        #     AsyncIteratorCallbackHandler().done.set()
        #
        # await task

        result = self.__llm(messages)
        # print(self.__llm(messages))
        # result = {}
        #
        # return result

    def __format_docs(self, docs):
        formatted_docs = []
        for doc in docs:
            formatted_doc = "Source: " + doc.page_content
            formatted_docs.append(formatted_doc)
        return '\n'.join(formatted_docs)






