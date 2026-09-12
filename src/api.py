from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agentic_workflow import app as ai_team
from fastapi.responses import FileResponse

api = FastAPI(title="Enterprise AI Analyst API", version="1.0")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserQuery(BaseModel):
    question: str

@api.get("/")
async def serve_frontend():
    return FileResponse("index.html")

# Added: Supporting /api/query on this instance too
@api.post("/api/query")
@api.post("/api/ask")
async def ask_ai(query: UserQuery):
    print(f"📥 Received question: {query.question}")
    
    initial_clipboard = {"question": query.question, "confidence_score": 1.0}
    final_state = ai_team.invoke(initial_clipboard)
    
    df = final_state.get("data_frame")
    data_rows = df.to_dict(orient="records") if df is not None else []
    
    return {
        "answer": final_state.get("final_answer"),
        "data": data_rows,
        "sql": final_state.get("sql_query")
    }