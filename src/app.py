import streamlit as st
from agentic_workflow import app  # Imports your working AI team!

# 1. Set up the webpage title and header
st.set_page_config(page_title="Enterprise AI Analyst", page_icon="📊")
st.title("📊 Enterprise Data Analyst AI")
st.markdown("Ask me anything about your business data (Sales, Customers, Products).")

# 2. Create a text input box for the user
user_question = st.text_input("What would you like to know?")

# 3. Create an 'Ask' button
if st.button("Run Analysis"):
    if user_question:
        # Show a loading spinner while the AI team works
        with st.spinner("Analyzing database..."):
            
            # Put the question on the clipboard and run the workflow
            initial_clipboard = {"question": user_question}
            final_state = app.invoke(initial_clipboard)
            
            # 4. Display the Final Answer nicely
            st.markdown("### 💡 AI Insight")
            st.info(final_state.get('final_answer'))
            
            # 5. Create a drop-down menu for nerds/recruiters who want to see the code
            with st.expander("🛠️ View Execution Details (SQL & Raw Data)"):
                st.markdown("**Generated SQL:**")
                st.code(final_state.get('sql_query'), language="sql")
                
                st.markdown("**Raw Database Output:**")
                st.write(final_state.get('data_result'))
    else:
        st.warning("Please enter a question first!")