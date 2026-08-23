from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agentic_workflow import app as ai_team
from fastapi.responses import FileResponse

# Initialize the API
api = FastAPI(title="Enterprise AI Analyst API", version="1.0")

# 🛡️ THE FIX: Add CORS Middleware to allow your HTML file to connect
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows any frontend to connect
    allow_credentials=True,
    allow_methods=["*"], # Allows POST, GET, etc.
    allow_headers=["*"],
)

# Define the expected incoming data
class UserQuery(BaseModel):
    question: str


# Serve the HTML frontend
@api.get("/")
async def serve_frontend():
    return FileResponse("index.html")

# Create the endpoint
@api.post("/api/ask")
async def ask_ai(query: UserQuery):
    print(f"📥 Received question: {query.question}")
    
    # Run the AI workflow
    initial_clipboard = {"question": query.question}
    final_state = ai_team.invoke(initial_clipboard)
    
    # Return the clean JSON payload
    return {
        "insight": final_state.get("final_answer"),
        "raw_data": final_state.get("data_result"),
        "sql_executed": final_state.get("sql_query")
    }