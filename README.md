FinchQL Copilot: Enterprise AI Data Analyst Agent
FinchQL Copilot is a production-grade, full-stack AI platform that bridges the gap between natural language and complex relational databases. Designed as a comprehensive portfolio piece for a fresh AI Data Science graduate, this project demonstrates real-world architectural design, agentic AI workflows, and end-to-end cloud deployment [cite: Imagine you are a project mentor helping a beginner Fresh AI Data Science BTECH graduate to do this project and a get job as soon as possible using this project .So you have mentor me simple way.].

Technological Architecture
The system is built on a decoupled, three-tier architecture ensuring scalability, modularity, and rapid query execution [cite: Imagine you are a project mentor helping a beginner Fresh AI Data Science BTECH graduate to do this project and a get job as soon as possible using this project .So you have mentor me simple way.].

Presentation Layer (Frontend): A React and Vite-powered interactive dashboard hosted on Vercel. It manages state for multi-turn conversations, renders dynamic data grids, and highlights generated SQL syntax.

Logic & AI Layer (Backend): A FastAPI server deployed on Render. It orchestrates a LangGraph state machine where Google's Gemini 2.5 acts as the core reasoning engine.

Vector Retrieval (RAG): ChromaDB stores database schema metadata as vector embeddings. When a user asks a question, the agent retrieves only the relevant table schemas to inject into the LLM context, ensuring accuracy and minimizing token usage.

Data Layer (Database): A PostgreSQL instance hosted on Render, populated with the enterprise-scale AdventureWorks dataset.

Containerization: The entire application is packaged using Docker and Docker Compose, ensuring exact environmental parity between local development and cloud production.

Core Features
Agentic Text-to-SQL: Translates plain English business questions directly into optimized PostgreSQL queries.

Dynamic Schema Injection: Automatically maps user intent to the correct database tables using semantic search, eliminating the need to hardcode database context.

Instant Execution & Visualization: Executes the generated SQL securely against the live database and visualizes the output in a clean, responsive UI grid.

Multi-Modal Output: Returns an executive text summary, the raw data rows, and the exact SQL executed for total transparency.

Live Links & Setup
Live Application: https://enterprise-data-analyst-agent.vercel.app

Repository: https://github.com/farizest/enterprise-data-analyst-agent.git

Local Installation

Clone the repository and navigate into the root directory.

Create a .env file containing your GEMINI_API_KEY and local DATABASE_URL.

Execute docker compose up --build -d to launch the API, local database container, and React UI simultaneously.
