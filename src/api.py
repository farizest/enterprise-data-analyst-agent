import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Import your agent workflow
from src.agentic_workflow import app as ai_team

api = FastAPI(
    title="Enterprise AI Analyst API", 
    version="1.0",
    description="Backend API for Enterprise Data Analyst Agent"
)

# Explicit origins + regex for Vercel preview/production deployments
origins = [
    "https://enterprise-data-analyst-agent.vercel.app",
    "https://enterprise-data-analyst-agent-fz37duclg-farizests-projects.vercel.app",
    "http://localhost:3000",
    "http://localhost:8501",
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Matches all Vercel deployment URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserQuery(BaseModel):
    question: str

@api.get("/")
async def serve_frontend():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "Enterprise AI Analyst API is running live!"}

# Note: Changed to synchronous `def` so FastAPI handles `.invoke()` in a threadpool!
@api.post("/api/query")
@api.post("/api/ask")
def ask_ai(query: UserQuery):
    print(f"📥 Received question: {query.question}")
    
    try:
        initial_clipboard = {"question": query.question, "confidence_score": 1.0}
        
        # Run agentic workflow
        final_state = ai_team.invoke(initial_clipboard)

        df = final_state.get("data_frame")
        data_rows = df.to_dict(orient="records") if df is not None else []

        return {
            "status": "success",
            "answer": final_state.get("final_answer"),
            "data": data_rows,
            "sql": final_state.get("sql_query")
        }
        
    except Exception as e:
        print(f"❌ Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while processing the agent workflow: {str(e)}"
        )