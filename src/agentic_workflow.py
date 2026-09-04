import pandas as pd
from typing import TypedDict, Any
# ... (keep your other imports like SQLDatabase and ChatGoogleGenerativeAI) ...
from pandas._libs import properties
import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
import chromadb

# 1. Load secrets and connect to Database & AI
load_dotenv()

# Fetch the PostgreSQL URL from the environment securely
postgres_url = os.environ.get("DATABASE_URL")
db = SQLDatabase.from_uri(postgres_url)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path="data/chroma_db")
schema_collection = chroma_client.get_collection(name="adventureworks_schema")

# This is our 'clipboard' that gets passed between our AI agents
class AgentState(TypedDict):
    question: str
    chat_history: list          # NEW: Stores past conversation context
    schema_context: str
    business_rules: str
    sql_query: str
    sql_valid: bool
    data_result: str
    data_frame: Any             
    final_answer: str
    confidence_score: float
# --- WORKER 0: SCHEMA RETRIEVER ---
def retrieve_schema(state: AgentState):
    print("-> Worker 0: Retrieving relevant schema from memory...")
    question = state["question"]
    
    # Search ChromaDB for the 2 most relevant tables based on the question
    results = schema_collection.query(
        query_texts=[question],
        n_results=2
    )
    
    # Format the results into a readable string
    retrieved_tables = ""
    for i in range(len(results['documents'][0])):
        table_name = results['metadatas'][0][i]['table_name']
        description = results['documents'][0][i]
        retrieved_tables += f"Table '{table_name}': {description}\n"
        
    print(f"   [+] Retrieved Tables:\n{retrieved_tables.strip()}")
    
    # Return the context to the clipboard
    return {"schema_context": retrieved_tables.strip()}

# --- WORKER 0.5: SEMANTIC RESOLVER (ADR-003, Join Paths & Glossary) ---
def semantic_resolver(state: AgentState):
    print("-> Worker 0.5: Resolving business semantics...")
    question = state["question"].lower()
    rules = ""
    
    # Implementing ADR-003: Revenue = TotalDue
    if "revenue" in question:
        rules += "CRITICAL BUSINESS RULE: When calculating 'revenue', you MUST use the 'totaldue' column in the sales.salesorderheader table.\n"
        
    # Implementing Join-Path Resolution
    if "city" in question or "location" in question or "where" in question:
        rules += "CRITICAL JOIN RULE: When joining sales orders to addresses, always use 'shiptoaddressid' (not billtoaddressid) unless explicitly asked for billing.\n"
        
    # Implementing Synthetic Glossary Layer
    if "big spender" in question or "big spenders" in question:
        rules += "GLOSSARY RULE: 'Big Spenders' are defined as customers (customerid) whose total sum of 'totaldue' across all orders is strictly greater than 10000.\n"
        
    if "slow mover" in question or "slow movers" in question:
        rules += "GLOSSARY RULE: 'Slow Movers' are defined as products (productid) where the total sum of 'orderqty' across all orders is strictly less than 50.\n"
        
    if rules:
        print("   [+] Applied Business Rules for this query.")
        
    return {"business_rules": rules}
   # --- WORKER 1: SQL GENERATOR (Upgraded with Memory) ---
def generate_sql(state: AgentState):
    print("-> Worker 1: Generating SQL...")
    question = state["question"]
    rules = state.get("business_rules", "")
    history = state.get("chat_history", [])
    
    # Format the past conversation so the AI can read it
    history_text = ""
    if history:
        history_text = "PREVIOUS CONVERSATION CONTEXT:\n"
        for msg in history:
            history_text += f"{msg['role'].upper()}: {msg['content']}\n"
    
    schema = """
    Table: sales.salesorderheader
    Columns: salesorderid (int), customerid (int), totaldue (numeric)
    
    Table: person.address
    Columns: addressid (int), city (varchar)
    """
    
    prompt = f"""You are an expert Enterprise Data Analyst querying a PostgreSQL database. 
    You must write valid PostgreSQL syntax exclusively.
    
    CRITICAL: The database tables and columns are strictly LOWERCASE. 
    You must use the exact lowercase table and column names provided in the schema below. 
    
    {rules}
    
    {history_text}
    
    Write a SQL query to answer this new question: {question}
    If the question is a follow-up, use the PREVIOUS CONVERSATION CONTEXT to understand what the user is referring to.
    
    Use the following table schemas to help you write the query:
    {schema}
    
    Only return the SQL query, nothing else. No markdown formatting like ```sql.
    """
    
    response = llm.invoke(prompt)
    
    if isinstance(response.content, list):
        raw_text = response.content[0].get("text", "")
    else:
        raw_text = response.content
        
    sql = raw_text.replace('```sql', '').replace('```', '').strip()
    return {"sql_query": sql}


# --- WORKER 2: THE EXECUTOR (Upgraded for Charts) ---
def execute_sql(state: AgentState):
    print("-> Worker 2: Executing SQL and extracting structured data...")
    query = state["sql_query"]
    
    try:
        # Run the SQL query using Pandas and the SQLAlchemy engine
        df = pd.read_sql(query, db._engine)
        
        # We need the string version for the AI to read, 
        # and the raw DataFrame version for Streamlit to chart!
        result_string = df.to_string(index=False)
        
        return {"data_result": result_string, "data_frame": df}
        
    except Exception as e:
        error_msg = f"Error: {e}"
        print(f"   [!] Execution failed: {error_msg}")
        return {"data_result": error_msg, "data_frame": None}


# --- WORKER 3: THE VALIDATOR ---
def validate_sql(state: AgentState):
    print("-> Worker 3: Validating SQL for safety...")
    query = state.get("sql_query", "")
    
    # Simple security check: Only allow SELECT statements
    if query.strip().upper().startswith("SELECT"):
        print("   [+] Query is safe (SELECT only).")
        return {"sql_valid": True}
    else:
        print("   [!] SECURITY ALERT: Blocked dangerous or invalid query!")
        return {"sql_valid": False}


# --- WORKER 5: HUMAN CONFIRMATION (HITL) ---
def human_confirmation(state: AgentState):
    print("-> Worker 5: Human-in-the-Loop Intervention Required!")
    print(f"\n⚠️ The AI is unsure (Confidence: {state.get('confidence_score', 0)}).")
    print(f"Generated SQL: {state.get('sql_query')}")
    
    # Pause the terminal and wait for human input
    user_input = input("\nDo you approve this query to run? (y/n): ")
    
    if user_input.strip().lower() == 'y':
        print("   [+] Query APPROVED by human.")
        return {"sql_valid": True}
    else:
        print("   [!] Query REJECTED by human.")
        # We override the query to force a safe failure
        return {"sql_valid": False, "sql_query": "SELECT 'Query rejected by user'"}

# --- ROUTER: DECIDE NEXT STEP ---
def route_validation(state: AgentState):
    # If the SQL is valid, go to the executor. If not, stop the process.
    if state.get("sql_valid") == True:
        return "executor"
    else:
        return END


# --- WORKER 4: INSIGHT GENERATOR ---
def generate_insight(state: AgentState):
    print("-> Worker 4: Generating human-readable insight...")
    question = state["question"]
    sql = state.get("sql_query", "")
    data = state.get("data_result", "No data returned")
    
    prompt = f"""You are a helpful Enterprise Data Analyst. 
    The user asked: {question}
    The SQL query executed was: {sql}
    The raw database result is: {data}
    
    Based on this result, write a short, professional answer to the user's question. 
    Do not mention the SQL query in your response, just answer the question.
    """
    
    response = llm.invoke(prompt)
    
    if isinstance(response.content, list):
        insight = response.content[0].get("text", "")
    else:
        insight = response.content
        
    # Paste the final human-readable answer to the clipboard
    return {"final_answer": insight.strip()}
# --- ROUTER: CHECK CONFIDENCE ---
def route_confidence(state: AgentState):
    # ADR 9: Only pause for confirmation if confidence is < 0.7
    confidence = state.get("confidence_score", 1.0)
    if confidence < 0.7:
        return "human_confirmation"
    else:
        return "executor"
def check_confidence_node(state: AgentState):
    return {}

# --- BUILD THE FLOWCHART ---
workflow = StateGraph(AgentState)

workflow.add_node("schema_retriever", retrieve_schema)
workflow.add_node("semantic_resolver", semantic_resolver)
workflow.add_node("sql_generator", generate_sql)
workflow.add_node("validator", validate_sql)
workflow.add_node("check_confidence", check_confidence_node) 
workflow.add_node("human_confirmation", human_confirmation)  
workflow.add_node("executor", execute_sql)
workflow.add_node("insight_generator", generate_insight)

workflow.set_entry_point("schema_retriever")
workflow.add_edge("schema_retriever", "semantic_resolver")
workflow.add_edge("semantic_resolver", "sql_generator")
workflow.add_edge("sql_generator", "validator") 

workflow.add_conditional_edges(
    "validator", 
    route_validation,
    {
        "executor": "check_confidence", 
        END: END
    }
)

workflow.add_conditional_edges(
    "check_confidence",
    route_confidence,
    {
        "human_confirmation": "human_confirmation", 
        "executor": "executor"                      
    }
)

workflow.add_edge("human_confirmation", "executor")
workflow.add_edge("executor", "insight_generator") 
workflow.add_edge("insight_generator", END) 

app = workflow.compile()
# --- TEST IT! ---
if __name__ == "__main__":
    print("\n--- Starting the LangGraph AI Team ---")
    
    # Testing a query that returns multiple rows for charting
    initial_clipboard = {
        "question": "What is the total revenue for each customer ID? Give me the top 5.",
        "confidence_score": 1.0  # Skipping HITL for this quick test
    }    
    final_state = app.invoke(initial_clipboard)
    
    print("\n--- Final Clipboard Results ---")
    print(f"AI Analyst Response: {final_state.get('final_answer')}")
    
    # Let's verify the DataFrame was created!
    df = final_state.get('data_frame')
    if df is not None:
        print("\n📊 Extracted DataFrame:")
        print(df.head())