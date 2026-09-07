# src/schema_loader.py

ADVENTUREWORKS_SCHEMA_MAP = {
    "product": "production.product",
    "productcategory": "production.productcategory",
    "productsubcategory": "production.productsubcategory",
    "customer": "sales.customer",
    "salesorderheader": "sales.salesorderheader",
    "salesorderdetail": "sales.salesorderdetail",
    "address": "person.address",
    "person": "person.person",
}

def get_qualified_table_name(table_name: str) -> str:
    """Returns the fully qualified schema.table name for AdventureWorks."""
    clean_name = table_name.lower().replace(".", "").strip()
    return ADVENTUREWORKS_SCHEMA_MAP.get(clean_name, table_name)