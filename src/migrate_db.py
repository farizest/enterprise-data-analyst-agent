import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🔌 Connecting to databases...")

# 1. Connect to SQLite using Python's built-in library to easily bypass bad characters
sqlite_conn = sqlite3.connect("data/AdventureWorks.db")
sqlite_conn.text_factory = lambda b: b.decode(errors='ignore')

# 2. Connect to the new PostgreSQL database using SQLAlchemy
postgres_url = os.getenv("DATABASE_URL")
postgres_engine = create_engine(postgres_url)

# 3. Define the core tables we need
tables_to_migrate = [
    "Customer",
    "Product",
    "SalesOrderHeader",
    "SalesOrderDetail"
]

print("🚀 Starting Data Migration (SQLite -> PostgreSQL)...")

# 4. Loop through and copy the data
for table in tables_to_migrate:
    print(f"   -> Extracting {table} from SQLite...")
    # Extract using a direct SQL query
    df = pd.read_sql_query(f"SELECT * FROM {table}", con=sqlite_conn)
    
    print(f"   -> Loading {table} into PostgreSQL... ({len(df)} rows)")
    # Load into Postgres
    df.to_sql(table, con=postgres_engine, if_exists='replace', index=False)

print("✅ Migration complete! Your PostgreSQL database is now populated.")