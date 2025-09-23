from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from chroma_connection import get_chroma_collection
from chromadb.api.models.Collection import Collection
import base64
import uuid
from pypdf import PdfReader
import io
import tiktoken
from langchain_nvidia_ai_endpoints import ChatNVIDIA

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
    for result in results['documents'][0]:
        context += result + "\n"

    if query.version == "Pro":
        model_name = "nvidia/llama3-chatqa-1.5-8b"
    else:
        model_name = "nvidia/llama3-chatqa-1.5-70b"

    llm = ChatNVIDIA(model=model_name)
    
    response = llm.invoke(f""" You are a helpful assistant. Use the following context to answer the user's question.
If the answer is not in the context, say you don't know.
                          Context: {context}\n\nQuestion: {query.query} 
""")

    #return {"response": response.content, "context": context}
    return {"response": response.content}

@app.get("/")
def read_root():
    return {"Hello": "World"}