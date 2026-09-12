from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.agentic_workflow import app as ai_pipeline
app = FastAPI()

# Enable CORS so your React frontend (port 5173) can talk to Python (port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.post("/api/query")
@app.post("/query")
async def run_query(request: QueryRequest): # or whatever your function name/parameter is
    try:
        # Invoke your real LangGraph agent workflow!
        state = ai_pipeline.invoke({"question": req.question, "confidence_score": 1.0})
        
        answer = state.get("final_answer", "Analysis completed.")
        sql = state.get("sql_query", "")
        df = state.get("data_frame")
        
        # Convert DataFrame to a list of dictionaries for JSON compatibility
        data_rows = df.to_dict(orient="records") if df is not None else []
        
        return {
            "answer": answer,
            "sql": sql,
            "data": data_rows
        }
    except Exception as e:
        return {
            "answer": f"Error executing query: {str(e)}",
            "sql": "",
            "data": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)