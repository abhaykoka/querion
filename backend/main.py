from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import inspect
from chroma_connection import get_chroma_collection
from ai_agent import choose_model
from chromadb.api.models.Collection import Collection
import base64
import uuid
from pypdf import PdfReader
import io
import tiktoken
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import os
# from model_router import DEFAULT_MODEL_ID, select_pro_model 


DATABASE_URL = "postgresql://postgres:User123$@localhost/chatapp"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Query(BaseModel):
    query: str
    user_id: int
    version: str
    model: Optional[str] = None
    agent_mode: Optional[bool] = False

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login/")
def login_for_access_token(user: UserLogin, db: Session = Depends(get_db)):
    print(f"Login attempt for user: {user.username}")
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.hashed_password):
        print("Login failed")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print("Login successful")
    return {"message": "Login successful", "user_id": db_user.id}

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile, user_id: int, chroma_collection: Collection = Depends(get_chroma_collection)):
    contents = await file.read()
    document = ""
    if file.content_type == "application/pdf":
        pdf_reader = PdfReader(io.BytesIO(contents))
        for page in pdf_reader.pages:
            document += page.extract_text()
    else:
        try:
            # Try to decode as UTF-8
            document = contents.decode('utf-8')
        except UnicodeDecodeError:
            # If it fails, encode as base64
            document = base64.b64encode(contents).decode('utf-8')

    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(document)
    
    chunk_size = 400
    chunks = [tokens[i:i + chunk_size] for i in range(0, len(tokens), chunk_size)]

    for i, chunk in enumerate(chunks):
        chunk_text = encoding.decode(chunk)
        chroma_collection.add(
            documents=[chunk_text],
            metadatas=[{"user_id": str(user_id), "filename": file.filename, "chunk_number": i, "content_type": file.content_type}],
            ids=[f"{file.filename}-{i}-{uuid.uuid4()}"]
        )

    return {"filename": file.filename}

@app.post("/query/")
async def query_documents(query: Query, chroma_collection: Collection = Depends(get_chroma_collection)):
    results = chroma_collection.query(
        query_texts=[query.query],
        n_results=5,
        where={"user_id": str(query.user_id)}
    )
    print(results)
    
    context = ""
    for result in results['metadatas'][0]:
        context += result['filename'] + "\n"

    for result in results['documents'][0]:
        context += result + "\n"


    # If agent_mode is enabled, let the agent pick the model automatically
    if query.agent_mode:
        model_name = choose_model(query.query)
    elif query.model:
        model_name = query.model
    else:
        if query.version == "Pro":
            model_name = "meta/llama-3.1-405b-instruct"
            # model_name = select_pro_model(query.query)
        else:
            model_name = "nvidia/llama3-chatqa-1.5-8b"
    
    # model_name = select_pro_model(query.query)
    
    print(f"Using model: {model_name}")
    print(f"Context for query: {context}")
    try:
        # Try to instantiate the NVIDIA chat client. Some clients require a base_url or
        # other environment configuration (API key, tenant, etc.). If those values are
        # missing or of the wrong type the pydantic model used by the client will raise
        # a ValidationError complaining about `base_url` or similar fields.
        llm = ChatNVIDIA(model=model_name)
    except Exception as e:
        # Provide a clearer error to the caller with troubleshooting hints.
        hint = (
            "Failed to initialize the NVIDIA chat client. This typically means the client "
            "is missing configuration such as a string `base_url`, API key, or tenant. "
            "Check your environment variables (for example `NVIDIA_API_KEY`, `NVIDIA_BASE_URL`, "
            "`CHROMA_API_KEY`, or whichever variables your NVIDIA client expects) and ensure "
            "they are set to string values. See the `langchain_nvidia_ai_endpoints` docs for exact names."
        )
        raise HTTPException(status_code=500, detail=f"NVIDIA client init error: {e}. {hint}")

    response = llm.invoke(f""" You are a helpful assistant. Use the following context to answer the user's question.
If the answer is not in the context, say you don't know. 
Context includes files with filenames the user has uploaded. usually .pdf, .docx etc. Answer about the files themseves too.
                          Context: {context}\n\nQuestion: {query.query} 
""")

    #return {"response": response.content, "context": context}
    return {"response": response.content}


@app.post("/query/stream/")
async def query_documents_stream(query: Query, chroma_collection: Collection = Depends(get_chroma_collection)):
    """
    Stream model output to the client via Server-Sent Events (SSE).

    This function attempts a best-effort true stream: if the underlying LLM client's
    `invoke` method supports a `stream=True` flag and returns an iterable of partial
    responses, we iterate and forward them. Otherwise we fall back to calling the
    synchronous `invoke` and chunking the final response into pieces and streaming
    them to the client.
    """
    results = chroma_collection.query(
        query_texts=[query.query],
        n_results=5,
        where={"user_id": str(query.user_id)}
    )

    context = ""
    for result in results.get('metadatas', [[]])[0]:
        # include filename metadata to help the LLM
        if isinstance(result, dict) and 'filename' in result:
            context += result['filename'] + "\n"

    for result in results.get('documents', [[]])[0]:
        context += result + "\n"

    if query.agent_mode:
        model_name = choose_model(query.query)
    elif query.model:
        model_name = query.model
    else:
        if query.version == "Pro":
            model_name = "meta/llama-3.1-405b-instruct"
        else:
            model_name = "nvidia/llama3-chatqa-1.5-8b"

    #prompt = f""" You are a helpful assistant. Use the following context to answer the user's question.\nIf the answer is not in the context, say you don't know.\nContext: {context}\n\nQuestion: {query.query} """
    try:
    # user query text
        user_query = query.query

    # replace 'context' with 'provided information' just for the LLM
        safe_query = user_query.replace("context", "provided information")

        prompt = f"""
        You are a helpful assistant. Use the following provided information to answer the user's question.
        If the answer is not in the provided information, say you don't know.

        Provided Information: {context}

        Question: {safe_query}
        """

        # send the prompt to the model
        response = model.invoke(prompt)

    except Exception as e:
        # handle errors gracefully
        print("Error while processing model prompt:", e)
        response = "Sorry, I encountered an error while processing your request."

    try:
        llm = ChatNVIDIA(model=model_name)
    except Exception as e:
        hint = (
            "Failed to initialize the NVIDIA chat client. Check NVIDIA env vars and model availability."
        )
        raise HTTPException(status_code=500, detail=f"NVIDIA client init error: {e}. {hint}")

    from typing import Generator

    def sse_encode(text: str) -> Generator[str, None, None]:
        # SSE requires lines starting with 'data:'. Ensure no bare newlines.
        for line in text.splitlines() or [text]:
            yield f"data: {line}\n\n"

    async def event_generator():
        # Try to use the model's streaming API if available
        try:
            sig = None
            try:
                sig = inspect.signature(llm.invoke)
            except Exception:
                sig = None

            # If llm.invoke accepts a 'stream' parameter, attempt real streaming
            if sig and 'stream' in sig.parameters:
                try:
                    stream_resp = llm.invoke(prompt, stream=True)
                    # If the response is iterable, yield its parts
                    if hasattr(stream_resp, '__iter__'):
                        for chunk in stream_resp:
                            try:
                                text = getattr(chunk, 'content', None) or str(chunk)
                            except Exception:
                                text = str(chunk)
                            for out in sse_encode(text):
                                yield out
                        return
                except Exception:
                    # If streaming failed, fall back to synchronous call below
                    pass

            # Fallback: call synchronously and chunk the final response
            resp = llm.invoke(prompt)
            resp_text = getattr(resp, 'content', None) or str(resp)

            # Chunk size in characters
            chunk_size = 200
            for i in range(0, len(resp_text), chunk_size):
                chunk = resp_text[i:i+chunk_size]
                for out in sse_encode(chunk):
                    yield out

        except Exception as e:
            # Send error via SSE and finish
            err_msg = f"error: {e}"
            yield f"event: error\ndata: {err_msg}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream')


@app.post("/logout/")
def logout(user_id: int | None = None, purge: bool = False, chroma_collection: Collection = Depends(get_chroma_collection)):
    """
    Logout endpoint.

    By default this endpoint does not remove user data. It simply acknowledges logout so the
    frontend can clear local session state. To explicitly delete a user's uploaded vectors,
    call this endpoint with the query parameter `purge=true` (and `user_id=<id>`).
    """
    if not purge:
        # Do not clear server-side data by default. Return a friendly message.
        return {"message": "Logged out. User data retained on server."}

    # If purge is requested, user_id is required
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id is required when purge=true")

    user_id_str = str(user_id)
    try:
        chroma_collection.delete(where={"user_id": user_id_str})
    except Exception as primary_err:
        try:
            # Fallback: page through results and delete by ids in batches
            while True:
                results = chroma_collection.query(n_results=1000, where={"user_id": user_id_str})
                ids_batch = []
                if results and 'ids' in results and len(results['ids']) > 0:
                    ids_batch = [i for i in results['ids'][0] if i]
                if not ids_batch:
                    break
                chroma_collection.delete(ids=ids_batch)
                if len(ids_batch) < 1000:
                    break
        except Exception as fallback_err:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to clear user data (primary error: {primary_err}; fallback error: {fallback_err})"
            )

    return {"message": "Logged out and user data cleared"}

@app.get("/")
def read_root():
    return {"Hello": "World"}