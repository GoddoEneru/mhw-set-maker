import os
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores.faiss import FAISS


class Model:
    def __init__(
            self,
            api_key,
            chunk_size=3000,
            chunk_overlap=500,
            embedding_model="text-embedding-3-large",
            k=5,
            llm_model="gpt-4o-mini",
            temperature=0
            ):
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model
        self.k = k
        self.llm_model = llm_model
        self.temperature = temperature

    def prepare_csv(self):
        loader = DirectoryLoader(path=os.getcwd(), glob="src/data/*.csv", use_multithreading=True)
        data = loader.load()

        # Split data into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

        chunks = text_splitter.split_documents(data)

        embeddings = OpenAIEmbeddings(
            openai_api_key=self.api_key,
            model=self.embedding_model
        )

        db_faiss = FAISS.from_documents(chunks, embeddings)

        return db_faiss

    def rag(self, db_faiss, query):
        output_retrieval = db_faiss.similarity_search(query, k=self.k)

        output_retrieval_merged = "\n".join([doc.page_content for doc in output_retrieval])

        prompt = f"""
        based only on this context and not what you know: {output_retrieval_merged}
        answer the following question : {query}
        if you don't have information on the answer, say you don't know
        """

        model = ChatOpenAI(
            openai_api_key=self.api_key,
            model=self.llm_model,
            temperature=self.temperature
        )

        response_text = model.invoke(prompt)

        return response_text.content
