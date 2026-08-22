from agentic_workflow import app

# 1. Define our 'Golden Set' of business questions
golden_set = [
    "How many tables are in the database?",
    "What are the names and list prices of the top 5 most expensive products?",
    "How many customers do we have in total?"
]

print("🧪 Running Enterprise AI Evaluation Suite...")
passed = 0

# 2. Loop through each question and test the AI
for question in golden_set:
    print(f"\n👉 Testing: '{question}'")
    
    # Run the AI workflow
    result = app.invoke({"question": question})
    
    # Check if the AI generated valid SQL and successfully pulled data
    if result.get("sql_valid") and len(result.get("data_result", "")) > 2:
        print("✅ PASS: Valid SQL generated and data retrieved.")
        passed += 1
    else:
        print("❌ FAIL: AI struggled to answer this question.")

# 3. Print the final grade
print(f"\n🏆 Final Score: {passed}/{len(golden_set)} Tests Passed")