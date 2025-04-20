import os
from datetime import datetime, timedelta

from fastapi import FastAPI, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import List
import json

import motor.motor_asyncio
from passlib.context import CryptContext
from jose import jwt

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from topics import create_question_banks

# Initialize FastAPI app
app = FastAPI()

# MongoDB setup
MONGO_CONNECTION_STRING = os.environ.get("MONGO_CONNECTION_STRING", "mongodb://localhost:27017")
print(f"MongoDB connection string: {MONGO_CONNECTION_STRING}")
client = MongoClient(MONGO_CONNECTION_STRING)
db = client["QuestionsAI"]
users_collection = db["users"]

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

# Syllabus endpoints (unchanged)
class SyllabusEntry(BaseModel):
    topic: str
    subtopics: List[str]

@app.post("/syllabus")
async def collect_syllabus(syllabus: List[SyllabusEntry]):
    # Convert Pydantic models to dictionaries
    syllabus_data = [entry.dict() for entry in syllabus]

    # Call the main function to generate the question bank CSV file
    all_questions = create_question_banks(syllabus_data)
    print("All questions generated:")
    print(json.dumps(all_questions, indent=2))
    # Return a success message
    return {"message": "Question bank created successfully. All questions: {}".format(all_questions)}

@app.get("/question_bank")
async def get_question_bank():
    """
    Return the generated question bank CSV file.
    """
    return FileResponse("question_bank.csv", media_type="text/csv", filename="question_bank.csv")

# Signup model and endpoint
class SignupUser(BaseModel):
    name: str
    email: EmailStr
    password: str

@app.post("/signup")
def signup_user(user: SignupUser):
    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_data = user.dict()
    user_data["password"] = hash_password(user.password)

    result = users_collection.insert_one(user_data)
    user_id = str(result.inserted_id)

    access_token = create_access_token(data={"sub": user.email, "user_id": user_id})

    return {
        "message": "Account created successfully",
        "access_token": access_token,
        "token_type": "bearer"
    }
