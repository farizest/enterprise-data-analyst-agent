import streamlit as st
import pandas as pd
from agentic_workflow import app as ai_pipeline
from agentic_workflow import db

# 1. Page Configuration
st.set_page_config(
    page_title="QueryDesk | Analytics Copilot", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. Industrial SaaS Styling (Supporting Light & Dark Themes)
st.markdown("""
<style>
    /* Global Theme Variables */
    :root {
        --bg-main: #f8fafc;
        --card-bg: #ffffff;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --border-color: #e2e8f0;
        --sidebar-bg: #0f172a;
        --sidebar-text: #94a3b8;
        --accent: #3b82f6;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #0b0f19;
            --card-bg: #111827;
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
            --border-color: #1f2937;
            --sidebar-bg: #030712;
            --sidebar-text: #9ca3af;
        }
    }

    .stApp { background-color: var(--bg-main); color: var(--text-main); font-family: 'Inter', sans-serif; }
    
    /* Hide Default Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: var(--sidebar-text);
    }

    /* Cards & Containers */
    div[data-testid="metric-container"] {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.02);
    }

    /* Chat Messages */
    div[data-testid="stChatMessage"] {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.01);
    }

    /* Buttons */
    .stButton>button {
        background-color: var(--card-bg);
        color: var(--text-main);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        border-color: var(--accent);
        color: var(--accent);
    }
</style>
""", unsafe_allow_html=True)

# 3. Session State Management
if "messages" not in st.session_state:
    st.session_state.messages = []
if "latest_df" not in st.session_state:
    st.session_state.latest_df = None
if "latest_sql" not in st.session_state:
    st.session_state.latest_sql = ""
if "conversations" not in st.session_state:
    st.session_state.conversations = [
        "Q4 revenue by product category",
        "Monthly active users by region",
        "Top products by refund rate",
        "Churn drivers by plan tier"
    ]

# 4. Sidebar Layout (Matching Reference Design)
with st.sidebar:
    st.markdown("### ⏺ QueryDesk")
    st.markdown("##### 📊 ecommerce_analytics")
    st.caption("Analytics Copilot")
    
    if st.button("➕ New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.latest_df = None
        st.session_state.latest_sql = ""
        st.rerun()

    st.markdown("---")
    st.markdown("**RECENT CONVERSATIONS**")
    for conv in st.session_state.conversations:
        if st.button(f"💬 {conv}", use_container_width=True):
            # Preset mock runner for quick testing
            pass

    st.markdown("---")
    st.markdown("##### DATA SOURCE")
    st.caption("🟢 **ecommerce_analytics**\nPostgreSQL analytics prod • 42 tables\nConnected & synced 4m ago")

# 5. Main Split Screen Layout (Chat & Analytics Canvas)
chat_col, canvas_col = st.columns([1, 2.2], gap="large")

with chat_col:
    st.markdown("### 💬 Copilot Feed")
    st.caption("Alex Morgan • Data Lead")
    
    # Render history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Input field
    if prompt := st.chat_input("Ask a question about your data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Analyzing data source..."):
                try:
                    state = ai_pipeline.invoke({"question": prompt, "confidence_score": 1.0})
                    answer = state.get("final_answer", "Analysis completed.")
                    sql = state.get("sql_query", "")
                    
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    st.session_state.latest_sql = sql
                    
                    if sql and sql not in ["BLOCKED", "OUT_OF_SCOPE", "CHITCHAT"]:
                        st.session_state.latest_df = pd.read_sql(sql, db._engine)
                        st.rerun()
                except Exception as e:
                    st.error(f"Execution Error: {e}")

with canvas_col:
    st.markdown("### 📈 Analytics Canvas")
    
    if st.session_state.latest_df is not None and not st.session_state.latest_df.empty:
        df = st.session_state.latest_df
        
        # KPI Summary Row
        kpi_cols = st.columns(min(len(df.columns), 3))
        for i, col_name in enumerate(df.columns[:3]):
            with kpi_cols[i]:
                val = df[col_name].iloc[0]
                if isinstance(val, (int, float)):
                    st.metric(label=col_name.upper(), value=f"{val:,.2f}")
                else:
                    st.metric(label=col_name.upper(), value=str(val))
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Professional Tabs (Visualizations, Data Grid, SQL Query)
        tab_viz, tab_data, tab_sql = st.tabs(["📊 Visualization", "📄 Results Data", "<> SQL Query"])
        
        with tab_viz:
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0 and len(df) > 1:
                st.bar_chart(df, y=numeric_cols[0], color="#3b82f6")
            else:
                st.info("Displaying single-row or categorical breakdown.")
                
        with tab_data:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(df)} rows from query result set.")
            
        with tab_sql:
            st.code(st.session_state.latest_sql, language="sql")
            st.caption("Executed live against PostgreSQL data source with 0ms latency.")
            
    else:
        # Default placeholder matching reference landing state
        st.markdown("""
        <div style="padding: 5rem 2rem; text-align: center; border: 2px dashed var(--border-color); border-radius: 16px; margin-top: 1rem;">
            <h3 style="color: var(--text-muted); margin-bottom: 0.5rem;">Ready for Analysis</h3>
            <p style="color: var(--text-muted); font-size: 0.95rem;">Type a business prompt on the left chat panel to query PostgreSQL and generate dynamic visualizations instantly.</p>
        </div>
        """, unsafe_allow_html=True)