import sys
import os
import pandas as pd
import yaml
import time
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.agentic_workflow import app as ai_pipeline
from src.agentic_workflow import db  

def normalize_dataframe(df: pd.DataFrame) -> list:
    if df is None or df.empty:
        return []
    
    df = df[sorted(df.columns)]
    
    for col in df.select_dtypes(include=['float64', 'object']).columns:
        try:
            df[col] = pd.to_numeric(df[col]).round(2)
        except Exception:
            pass
            
    records = [tuple(x) for x in df.to_numpy()]
    return sorted(records)

def run_pipeline_for_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    question = entry["question"]
    expected_sql = entry["expected_sql"]
    state = {} # Initialize early to prevent UnboundLocalError
    
    try:
        state = ai_pipeline.invoke({"question": question, "confidence_score": 1.0})
        generated_sql = state.get("sql_query", "")
        
        if expected_sql in ["BLOCKED", "OUT_OF_SCOPE", "CHITCHAT"]:
            is_correct = (state.get("sql_valid") == False) or (expected_sql in state.get("final_answer", ""))
            return {"is_correct": is_correct, "generated_sql": generated_sql, "error": None}
        
        expected_df = pd.read_sql(expected_sql, db._engine)
        
        if not generated_sql or generated_sql.strip() == "":
            return {"is_correct": False, "generated_sql": "NO SQL GENERATED", "error": "Missing SQL"}
            
        generated_df = pd.read_sql(generated_sql, db._engine)
        
        norm_expected = normalize_dataframe(expected_df)
        norm_generated = normalize_dataframe(generated_df)
        
        is_correct = (norm_expected == norm_generated)
        
        return {"is_correct": is_correct, "generated_sql": generated_sql, "error": None}
        
    except Exception as e:
        return {"is_correct": False, "generated_sql": state.get("sql_query", "Failed before generation"), "error": str(e)}

if __name__ == "__main__":
    print("--- 📊 Starting Full Execution Accuracy Evaluation ---\n")
    
    with open("tests/golden_set/queries.yaml", "r") as f:
        eval_set = yaml.safe_load(f)
        
    total = len(eval_set)
    passed = 0
    
    for entry in eval_set:
        print(f"Testing [{entry['id']} - {entry['intent']}]: {entry['question']}")
        
        result = run_pipeline_for_entry(entry)
        
        if result['is_correct']:
            print("   ✅ PASS")
            passed += 1
        else:
            print("   ❌ FAIL")
            print(f"      Expected: {entry['expected_sql']}")
            print(f"      Generated: {result['generated_sql']}")
            if result['error']:
                print(f"      Error: {result['error']}")
        print("-" * 60)
        
        # Prevent Gemini Free Tier rate limits (5 requests per minute)
        print("⏳ Waiting 15 seconds to respect API rate limits...")
        time.sleep(15)
        
    accuracy = (passed / total) * 100
    print(f"\n🏆 Final Accuracy: {accuracy:.1f}% ({passed}/{total})") 