from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate, SystemMessagePromptTemplate
from langchain.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
import pinecone
import tempfile
import os


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

        self.__llm = ChatOpenAI(temperature='0.2', openai_api_key=openai_api_key)

        self.__prompt_template = """
            You are a nice and professional assistance for restaurants. I will share the restaurant menu and all
            the information required and you will give me the best answer that will help the costumer make a order or a 
            reservation. You only have to identify the price and ingredients of the dishes when the customer asks you to.
            You will follow all rules bellow:
            
            1/Understand the purpose of the call, whether it's to place a takeaway order, 
            delivery or to make a reservation.
            
            2/ If it's a take-away order, help with any questions the customer may have about the menu. 
            Ask what the order is under and thank them for their preference.
            
            3/If it's a home delivery order, help with any questions the customer may have about the menu. 
            Ask for the delivery address and thank them for their preference.
            
            4/If it's a reservation, ask how many people the reservation is for and what name the reservation is in.
            
            
            Bellow is the required information you need to answer:
            {company_info}
            
            Please answer nicely.
        """

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


    def get_response(self, company_name, query, conversation):

        # Defining Metadata Filter
        metadata_filter = {
            "company": {"$eq": company_name},
        }

        #print(self.__index.describe_index_stats())

        # Get vector from Pinecode Index
        vectorstore = Pinecone(self.__index, self.__embeddings.embed_query, 'text')

        # Query
        docs = vectorstore.similarity_search(
            query,  # our search query
            k=3,  # return 3 most relevant docs
            filter=metadata_filter  # query filter
        )

        # Prepare the prompt
        prompt = self.__system_message_prompt.format(company_info=self.__format_docs(docs))

        # Combine prompt with new messages and chat history
        messages = [prompt] + self.__create_messages(conversation=conversation['conversation'])

        result = self.__llm(messages)
        return result

    def __format_docs(self, docs):
        formatted_docs = []
        for doc in docs:
            formatted_doc = "Source: " + doc.page_content
            formatted_docs.append(formatted_doc)
        return '\n'.join(formatted_docs)


if __name__ == "__main__":
    langchain = LangChainHandler('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',
                                 '88f45129-5d59-47c7-98b7-aaa43fa128de',
                                 'gcp-starter', 'voxflowdev')
    query = 'Olá é possivel fazer um reserva de lugar para jantar hoje a noite?'
    conversation = {"conversation": [{"role": "system", "content": "You are a helpful assistant."},
                                     {'role': 'user', 'content': query}]}
    langchain.get_response('Pizzaria Amanti', query, conversation)


