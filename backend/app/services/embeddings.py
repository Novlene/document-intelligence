from langchain_core.embeddings import Embeddings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


class LocalOnnxEmbeddings(Embeddings):
    def __init__(self):
        self._ef = DefaultEmbeddingFunction()

    def embed_documents(self, texts):
        return [[float(x) for x in v] for v in self._ef(texts)]

    def embed_query(self, text):
        return self.embed_documents([text])[0]
