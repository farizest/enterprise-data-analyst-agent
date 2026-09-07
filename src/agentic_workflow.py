import pandas as pd
from typing import TypedDict, Any
import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
import chromadb

# Import our schema mapper to guarantee correct table paths!
from .schema_loader import get_qualified_table_name
# 1. Load secrets and connect to Database & AI
load_dotenv()

postgres_url = os.environ.get("DATABASE_URL")
db = SQLDatabase.from_uri(postgres_url)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path="data/chroma_db")
# To this:
schema_collection = chroma_client.get_or_create_collection(name="adventureworks_schema")

# Ensure it contains the base schema metadata if empty:
if schema_collection.count() == 0:
    schema_collection.add(
        documents=[
            "Table: production.product - Columns: productid, name, listprice, standardcost, productnumber",
            "Table: sales.salesorderheader - Columns: salesorderid, customerid, totaldue, orderdate, shiptoaddressid",
            "Table: sales.salesorderdetail - Columns: salesorderid, productid, orderqty, unitprice, linetotal",
            "Table: sales.customer - Columns: customerid, personid, storeid, territoryid",
            "Table: person.address - Columns: addressid, city, stateprovinceid, postalcode"
        ],
        metadatas=[
            {"table_name": "production.product"},
            {"table_name": "sales.salesorderheader"},
            {"table_name": "sales.salesorderdetail"},
            {"table_name": "sales.customer"},
            {"table_name": "person.address"}
        ],
        ids=["doc_prod", "doc_soh", "doc_sod", "doc_cust", "doc_addr"]
    )

class AgentState(TypedDict):
    question: str
    chat_history: list
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
    
    results = schema_collection.query(
        query_texts=[question],
        n_results=2
    )
    
    retrieved_tables = ""
    for i in range(len(results['documents'][0])):
        table_name = results['metadatas'][0][i]['table_name']
        description = results['documents'][0][i]
        retrieved_tables += f"Table '{table_name}': {description}\n"
        
    print(f"   [+] Retrieved Tables:\n{retrieved_tables.strip()}")
    return {"schema_context": retrieved_tables.strip()}

# --- WORKER 0.5: SEMANTIC RESOLVER ---
def semantic_resolver(state: AgentState):
    print("-> Worker 0.5: Resolving business semantics...")
    question = state["question"].lower()
    rules = ""
    
    if "revenue" in question:
        rules += "CRITICAL BUSINESS RULE: When calculating 'revenue', you MUST use the 'totaldue' column in the sales.salesorderheader table.\n"
        
    if "city" in question or "location" in question or "where" in question:
        rules += "CRITICAL JOIN RULE: When joining sales orders to addresses, always use 'shiptoaddressid' (not billtoaddressid).\n"
        
    if "big spender" in question or "big spenders" in question:
        rules += "GLOSSARY RULE: 'Big Spenders' are customers whose total sum of 'totaldue' across all orders is > 10000.\n"
        
    if rules:
        print("   [+] Applied Business Rules for this query.")
        
    return {"business_rules": rules}

# --- WORKER 1: SQL GENERATOR (Upgraded with Mandatory Schema Prefixes) ---
def generate_sql(state: AgentState):
    print("-> Worker 1: Generating SQL...")
    question = state["question"]
    rules = state.get("business_rules", "")
    history = state.get("chat_history", [])
    
    history_text = ""
    if history:
        history_text = "PREVIOUS CONVERSATION CONTEXT:\n"
        for msg in history:
            history_text += f"{msg['role'].upper()}: {msg['content']}\n"
    
    # STRICT SCHEMA ENFORCEMENT FOR ADVENTUREWORKS
    schema = """
    CRITICAL DATABASE SCHEMA MAPPING:
    - Products: production.product (Columns: productid, name, listprice, etc.)
    - Categories: production.productcategory (Columns: productcategoryid, name)
    - Subcategories: production.productsubcategory (Columns: productsubcategoryid, productcategoryid, name)
    - Sales Orders: sales.salesorderheader (Columns: salesorderid, customerid, totaldue, shiptoaddressid)
    - Order Details: sales.salesorderdetail (Columns: salesorderid, productid, orderqty, linetotal)
    - Customers: sales.customer (Columns: customerid, personid)
    - Addresses: person.address (Columns: addressid, city)
    """
    
    prompt = f"""You are an expert Enterprise Data Analyst querying a PostgreSQL AdventureWorks database. 
    You must write valid PostgreSQL syntax exclusively.
    
    CRITICAL RULES:
    1. You MUST ALWAYS use fully qualified schema prefixes for tables (e.g., 'production.product', 'sales.salesorderheader'). 
    2. Never query a table with just its raw name (e.g., NEVER write 'FROM product', always write 'FROM production.product').
    
    {rules}
    
    {history_text}
    
    Write a SQL query to answer this question: {question}
    
    Use the schema mapping below:
    {schema}
    
    Only return the SQL query, nothing else. No markdown formatting like ```sql.
    """
    
    response = llm.invoke(prompt)
    
    if isinstance(response.content, list):
        raw_text = response.content[0].get("text", "")
    else:
        raw_text = response.content
        
    sql = raw_text.replace('```sql', '').replace('```', '').strip()
    
    print(f"   [+] Generated SQL: {sql}")
    return {"sql_query": sql}

# --- WORKER 2: THE EXECUTOR ---
def execute_sql(state: AgentState):
    print("-> Worker 2: Executing SQL and extracting structured data...")
    query = state["sql_query"]
    
    try:
        df = pd.read_sql(query, db._engine)
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
    
    if query.strip().upper().startswith("SELECT"):
        print("   [+] Query is safe (SELECT only).")
        return {"sql_valid": True}
    else:
        print("   [!] SECURITY ALERT: Blocked dangerous or invalid query!")
        return {"sql_valid": False}

# --- WORKER 5: HUMAN CONFIRMATION (HITL) ---
def human_confirmation(state: AgentState):
    print("-> Worker 5: Human-in-the-Loop Intervention Required!")
    user_input = input("\nDo you approve this query to run? (y/n): ")
    if user_input.strip().lower() == 'y':
        return {"sql_valid": True}
    else:
        return {"sql_valid": False, "sql_query": "SELECT 'Query rejected by user'"}

def route_validation(state: AgentState):
    if state.get("sql_valid") == True:
        return "executor"
    else:
        return END

# --- WORKER 4: INSIGHT GENERATOR ---
def generate_insight(state: AgentState):
    print("-> Worker 4: Generating structured human-readable insight...")
    question = state["question"]
    sql = state.get("sql_query", "")
    data = state.get("data_result", "No data returned")
    
    prompt = f"""You are a professional Enterprise Data Analyst presenting insights to a business stakeholder. 
    The user asked: {question}
    The SQL query executed was: {sql}
    The raw database result is: {data}
    
    CRITICAL FORMATTING RULES:
    1. Provide a brief, professional summary sentence first.
    2. Format all data points, rankings, or lists using clean, numbered bullet points (1., 2., 3., etc.).
    3. Make sure each item is on its own separate line with a line break (\\n). Bold the key names and nicely format the numbers (e.g., currency or counts).
    4. Do not mention the SQL query in your response.
    """
    
    response = llm.invoke(prompt)
    if isinstance(response.content, list):
        insight = response.content[0].get("text", "")
    else:
        insight = response.content
        
    return {"final_answer": insight.strip()}
def route_confidence(state: AgentState):
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