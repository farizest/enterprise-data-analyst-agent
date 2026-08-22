import streamlit as st
import pandas as pd
import ast
from agentic_workflow import app 

st.set_page_config(page_title="Enterprise AI Analyst", page_icon="📊")
st.title("📊 Enterprise Data Analyst AI")
st.markdown("Ask me anything about your business data (Sales, Customers, Products).")

user_question = st.text_input("What would you like to know?")

if st.button("Run Analysis"):
    if user_question:
        with st.spinner("Analyzing database..."):
            initial_clipboard = {"question": user_question}
            final_state = app.invoke(initial_clipboard)
            
            st.markdown("### 💡 AI Insight")
            st.info(final_state.get('final_answer'))
            
            # --- NEW: VISUALIZATION ENGINE ---
            raw_data = final_state.get('data_result', '')
            try:
                # Safely convert the raw text into a Python list
                parsed_data = ast.literal_eval(raw_data)
                if isinstance(parsed_data, list) and len(parsed_data) > 0 and isinstance(parsed_data[0], tuple):
                    df = pd.DataFrame(parsed_data)
                    st.markdown("### 📈 Data Visualization")
                    if len(df.columns) == 2:
                        df.set_index(0, inplace=True)
                        st.bar_chart(df)
                    else:
                        st.dataframe(df)
            except Exception:
                pass # Skip chart if data isn't chart-friendly
                
            with st.expander("🛠️ View Execution Details (SQL & Raw Data)"):
                st.markdown("**Generated SQL:**")
                st.code(final_state.get('sql_query'), language="sql")
                st.markdown("**Raw Database Output:**")
                st.write(final_state.get('data_result'))
    else:
        st.warning("Please enter a question first!")