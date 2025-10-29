from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from qa_service import qa_service
from data_service import data_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    question: str
    answer: Optional[str] = None
    data_sources: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QuestionRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class DataSummaryResponse(BaseModel):
    crop_production: Optional[dict] = None
    rainfall: Optional[dict] = None
    social_groups: Optional[dict] = None

# Routes
@api_router.get("/")
async def root():
    return {"message": "Project Samarth - Intelligent Q&A System"}

@api_router.get("/data/summary", response_model=DataSummaryResponse)
async def get_data_summary():
    """Get summary of available datasets"""
    try:
        summary = data_service.get_data_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/qa/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question and get AI-powered answer"""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get answer from QA service
        result = await qa_service.analyze_question(request.question, session_id)
        
        # Save to database
        chat_message = ChatMessage(
            session_id=session_id,
            question=request.question,
            answer=result['answer'],
            data_sources=result['data_sources']
        )
        
        doc = chat_message.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        
        await db.chat_history.insert_one(doc)
        
        return {
            'session_id': session_id,
            'question': request.question,
            'answer': result['answer'],
            'data_sources': result['data_sources'],
            'data_used': result.get('data_used')
        }
        
    except Exception as e:
        logging.error(f"Error in ask_question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/qa/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session"""
    try:
        history = await db.chat_history.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("timestamp", 1).to_list(100)
        
        return {"session_id": session_id, "messages": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/qa/sessions")
async def get_all_sessions():
    """Get all chat sessions"""
    try:
        sessions = await db.chat_history.distinct("session_id")
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()