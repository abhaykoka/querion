import chromadb
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection
from fastapi import Depends
from dotenv import load_dotenv
import os
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

load_dotenv()

class NVIDIAEmbeddingFunction(EmbeddingFunction[Documents]):
    def __init__(self, model_name: str = "nvidia/nv-embedqa-e5-v5", input_type: str = "passage"):
        try:
            from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
        except ImportError:
            raise ImportError(
                "Could not import langchain_nvidia_ai_endpoints. "
                "Please install it with `pip install langchain-nvidia-ai-endpoints`."
            )
        self.client = NVIDIAEmbeddings(model=model_name, input_type=input_type)

    def __call__(self, input: Documents) -> Embeddings:
        # The input is a list of documents (strings).
        # The NVIDIAEmbeddings client expects a list of strings for embedding.
        embeddings = self.client.embed_documents(input)
        return embeddings

_client: ClientAPI | None = None
_collection: Collection | None = None

def get_chroma_client() -> ClientAPI:
	global _client
	if _client is None:
		_client = chromadb.CloudClient(
            api_key=os.getenv("CHROMA_API_KEY"),
            tenant=os.getenv("CHROMA_TENANT"),
            database=os.getenv("CHROMA_DATABASE")
        )
	return _client

def get_chroma_collection(client: ClientAPI = Depends(get_chroma_client)) -> Collection:
	global _collection
	if _collection is None:

		embedding_function = NVIDIAEmbeddingFunction()
		_collection = client.get_or_create_collection(
		    name="user_files",
		    embedding_function=embedding_function
		)
	return _collection