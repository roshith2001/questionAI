import os
from datetime import datetime, timedelta
import json

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List

import motor.motor_asyncio
from passlib.context import CryptContext
from jose import jwt
from bson import ObjectId

from topics import create_question_banks

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with allowed origins if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup using Motor (async)
MONGO_CONNECTION_STRING = os.environ.get(
    "MONGO_CONNECTION_STRING",
    "mongodb+srv://roshithj:Kolathara1@question-generator.qaqioqn.mongodb.net/?retryWrites=true&w=majority&appName=Question-Generator"
)
print(f"MongoDB connection string: {MONGO_CONNECTION_STRING}")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_CONNECTION_STRING)
db = client["QuestionsAI"]
users_collection = db["users"]
history_collection = db["history"]

# Authentication settings
SECRET_KEY = os.environ.get("SECRET_KEY", "YOUR_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# OAuth2 schema for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# Syllabus endpoints
class SyllabusEntry(BaseModel):
    topic: str
    subtopics: List[str]

@app.post("/syllabus")
async def collect_syllabus(syllabus: List[SyllabusEntry], current_user: dict = Depends(get_current_user)):
    syllabus_data = [entry.dict() for entry in syllabus]
    all_questions = create_question_banks(syllabus_data)
    print("All questions generated:")
    print(json.dumps(all_questions, indent=2))
    
    history_doc = {
        "user_id": current_user["_id"],
        "syllabus": syllabus_data,
        "questions": all_questions,
        "created_at": datetime.utcnow()
    }
    result = await history_collection.insert_one(history_doc)
    
    # Create a copy of history_doc for response
    response_doc = history_doc.copy()
    response_doc["_id"] = str(result.inserted_id)
    response_doc["user_id"] = str(response_doc["user_id"])
    # Convert datetime to ISO format string
    response_doc["created_at"] = response_doc["created_at"].isoformat()
    
    return JSONResponse(content=response_doc)

@app.get("/question_bank")
async def get_question_bank():
    """
    Return the generated question bank CSV file.
    """
    return FileResponse("question_bank.csv", media_type="text/csv", filename="question_bank.csv")

@app.get("/history")
async def get_history(current_user: dict = Depends(get_current_user)):
    # Find all history items for the current user
    cursor = history_collection.find({"user_id": current_user["_id"]})
    history_list = await cursor.to_list(length=None)
    
    # Convert ObjectIds and datetimes to strings
    for item in history_list:
        item["_id"] = str(item["_id"])
        item["user_id"] = str(item["user_id"])
        if "created_at" in item:
            item["created_at"] = item["created_at"].isoformat()
    
    return JSONResponse(content=history_list)

# Signup model and endpoint
class SignupUser(BaseModel):
    name: str
    email: EmailStr
    password: str

@app.post("/signup")
async def signup_user(user: SignupUser):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_data = user.dict()
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)
    user_data["password"] = hash_password(user.password)

    result = await users_collection.insert_one(user_data)
    user_id = str(result.inserted_id)

    access_token = create_access_token(data={"sub": user.email, "user_id": user_id})

    return {
        "message": "Account created successfully",
        "access_token": access_token,
        "token_type": "bearer"
    }

# Login model and endpoint
class LoginUser(BaseModel):
    email: EmailStr
    password: str

@app.post("/login")
async def login_user(user: LoginUser):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email, "user_id": str(db_user["_id"])})
    return {
        "message": "Logged in successfully",
        "access_token": access_token,
        "token_type": "bearer"
    }