import chromadb

# 1. Connect to the ChromaDB folder you just created
client = chromadb.PersistentClient(path="data/chroma_db")

# 2. Create a 'collection' (like a specialized folder) for our schema
collection = client.get_or_create_collection(name="adventureworks_schema")

# 3. Define the tables we care about based on our isolated domains
tables = [
    "Customer",
    "Product",
    "SalesOrderHeader",
    "SalesOrderDetail"
]

# 4. Write simple English descriptions for each table
descriptions = [
    "Contains customer information like names, account numbers, and store IDs.",
    "Contains product details like names, standard costs, list prices, colors, and sizes.",
    "Contains the main header information for a sales order, like order date, customer ID, and total due.",
    "Contains the individual items purchased in a sales order, linking products to specific orders."
]

# 5. Load them into ChromaDB
print("Loading schema into ChromaDB...")
collection.add(
    documents=descriptions,
    metadatas=[{"table_name": t} for t in tables],
    ids=[f"table_{i}" for i in range(len(tables))]
)

print("Success! Your AI's memory bank is now populated.")