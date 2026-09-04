import streamlit as st
import pandas as pd
import os

# Import our compiled LangGraph pipeline
from agentic_workflow import app as ai_pipeline

st.set_page_config(page_title="Enterprise AI Data Analyst", page_icon="📊", layout="wide")

st.title("📊 Enterprise AI Data Analyst")
st.markdown("Ask me anything about the AdventureWorks database!")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # If there's a dataframe stored in the message history, display it!
        if "df" in message and message["df"] is not None:
            st.dataframe(message["df"])
            if len(message["df"].columns) >= 2:
                st.bar_chart(message["df"].set_index(message["df"].columns[0]))

if prompt := st.chat_input("E.g., What is the total revenue for the top 5 customers?"):
    
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Agents are analyzing the database..."):
        try:
            # --- NEW MEMORY LOGIC ---
            # Grab the last 4 messages (excluding the one they just typed) to save token space
            recent_history = []
            if len(st.session_state.messages) > 1:
                # Get the last few messages, format them simply
                recent_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:-1]]
            
            # Pass the history to the AI via initial_state!
            initial_state = {
                "question": prompt, 
                "confidence_score": 1.0,
                "chat_history": recent_history
            } 
            final_state = ai_pipeline.invoke(initial_state)
            # ------------------------
            
            answer = final_state.get("final_answer", "Sorry, I couldn't find an answer.")
            sql = final_state.get("sql_query", "")
            df = final_state.get("data_frame") # Grab the Pandas DataFrame!
            
            ui_response = f"{answer}\n\n---\n**🤖 AI Generated SQL:**\n```sql\n{sql}\n```"

            with st.chat_message("assistant"):
                st.markdown(ui_response)
                
                # Draw the charts dynamically!
                if isinstance(df, pd.DataFrame) and not df.empty:
                    st.write("**📊 Data Visualization:**")
                    st.dataframe(df) # Display the raw table
                    
                    # If we have at least 2 columns, draw a bar chart using the first column as the X-axis
                    if len(df.columns) >= 2:
                        st.bar_chart(df.set_index(df.columns[0]))
            
            # Save the response and the dataframe to history
            st.session_state.messages.append({"role": "assistant", "content": ui_response, "df": df})
            
        except Exception as e:
            st.error(f"Pipeline Error: {e}")