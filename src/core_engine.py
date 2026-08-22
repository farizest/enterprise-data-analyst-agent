import os
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent

# 1. Load the secret API key from the .env file securely
load_dotenv()

# 2. Connect to the SQLite Database in your 'data' folder
# Note: If you haven't downloaded AdventureWorks.db yet, make sure it is in the 'data' folder!
db = SQLDatabase.from_uri("sqlite:///data/AdventureWorks.db")

# 3. Initialize the Free LLM (Gemini 1.5 Flash is extremely fast and capable)
# 3. Initialize the Free LLM (Updated to current model)
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
# 4. Create the LangChain SQL Agent 
agent_executor = create_sql_agent(llm, db=db, agent_type="tool-calling", verbose=True)
# 5. Ask the AI a question!
print("Starting the Enterprise Data Analyst AI...\n")
question = "How many tables are in this database, and what are their names?"
print(f"User: {question}\n")

# The agent will process the question, generate SQL, execute it, and return the answer
agent_executor.invoke({"input": question})