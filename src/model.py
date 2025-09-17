import os
import pandas as pd
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.vectorstores.faiss import FAISS


class Model:
    def __init__(
            self,
            api_key,
            embedding_model="text-embedding-3-large",
            k=20,
            llm_model="gpt-4.1-mini",
            temperature=0.5
            ):
        self.api_key = api_key
        self.embedding_model = embedding_model
        self.k = k
        self.llm_model = llm_model
        self.temperature = temperature

    def prepare_csv(self):
        chunks = []

        for file in os.listdir('src/data'):
            df_temp = pd.read_csv(f'src/data/{file}')

            for col in df_temp.columns.tolist():
                df_temp[col] = df_temp[col].apply(lambda x: f"{col}: {x}")

            for index, row in df_temp.iterrows():
                content = ", ".join(row.tolist())
                metadata = {"source": file}

                chunk = Document(
                    page_content=content,
                    metadata=metadata,
                )
                chunks.append(chunk)

        return chunks

    def create_database(self, chunks):
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
        based on what you can find on "Monster Hunter Wilds" and this context: {output_retrieval_merged}
        answer the following question: {query}
        if you don't have information on the answer, say you don't know
        """

        model = ChatOpenAI(
            openai_api_key=self.api_key,
            model=self.llm_model,
            temperature=self.temperature
        )

        response_text = model.invoke(prompt)

        return response_text.content
