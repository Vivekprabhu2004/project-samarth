from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import nest_asyncio
from qa_service import qa_service
from data_service import data_service

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

app = FastAPI(title="Project Samarth API", description="Agricultural Q&A API")

class QuestionRequest(BaseModel):
    question: str
    session_id: str

class QuestionResponse(BaseModel):
    answer: str
    data_sources: list[str]

@app.get("/")
async def root():
    return {"message": "Project Samarth Agricultural Q&A API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/qa/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    try:
        result = await qa_service.analyze_question(request.question, request.session_id)
        return QuestionResponse(
            answer=result['answer'],
            data_sources=result['data_sources']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/api/data/summary")
async def get_data_summary():
    try:
        summary = data_service.get_data_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting data summary: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
