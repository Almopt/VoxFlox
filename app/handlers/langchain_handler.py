from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryMemory
from langchain.document_loaders import UnstructuredPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
import pinecone
import tempfile
import os


class LangChainHandler:
    def __init__(self, openai_api_key, pinecode_api_key, pinecode_api_env):
        self.__open_api_key = openai_api_key

        # Initialize PineCode
        pinecone.init(api_key=pinecode_api_key, environment=pinecode_api_env)

        #Create Embeddings of your documents to get ready for semantic search
        self.__embeddings = OpenAIEmbeddings(openai_api_key=self.__open_api_key)

        #Pinecode Index
        self.__index = pinecone.Index("voxflowv1")

        self.__llm = ChatOpenAI(temperature='0.2', openai_api_key=openai_api_key)
        self.__memory = ConversationSummaryMemory(llm=self.__llm)
        self.__template = """
            You are a nice and professional assistance for restaurants. I will share the restaurant menu and all
            his information and you will give me the best answer that will help the costumer make a order or a 
            reservation. You will follow all rules bellow:
            
            1/Understand the purpose of the call, whether it's to place a takeaway order, 
            delivery or to make a reservation.
            
            2/ If it's a take-away order, help with any questions the customer may have about the menu. 
            Ask what the order is under and thank them for their preference.
            
            3/If it's a home delivery order, help with any questions the customer may have about the menu. 
            Ask for the delivery address and thank them for their preference.
            
            4/If it's a reservation, ask how many people the reservation is for and what name the reservation is in.
            
            Bellow is the menu of the restaurant:
            {rest_menu}
            
            Please answer nicely.
        """

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
            print(data)

            # Chunk data up into smaller documents
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            texts = text_splitter.split_documents(data)
            print(texts)

            # Metadata
            #meta = [{'company': company_name}]

            #Pinecone.from_texts([t.page_content for t in texts], self.__embeddings, metadatas=meta * len(texts)
            #                    , index_name='voxflowv01')
        finally:
            # Clean up the temporary file
            os.remove(temp_file_path)

    def get_response(self, company_name):

        print(company_name)

        metadata_filter = {
            "company": {"$eq": company_name},
        }

        # index = pinecone.Index("voxflowv01")
        # print(index.describe_index_stats())

        vectorstore = Pinecone(self.__index, self.__embeddings.embed_query, 'text')

        query = 'Quais as pizzas que têm fiambre?'
        docs = vectorstore.similarity_search(
            query,  # our search query
            k=3,  # return 3 most relevant docs
            filter=metadata_filter,
        )

        print(docs)

    def delete_items(self):

        self.__index.delete()






# if __name__ == "__main__":
#     lang = LangChainHandler('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',
#                             '88f45129-5d59-47c7-98b7-aaa43fa128de',
#                             'gcp-starter')
#     #lang.get_response('Pizzaria Amanti')
#     lang.delete_items()


