import React, { useState } from 'react';
import './Dashboard.css';

export default function Dashboard({ onBackToHome }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Welcome to FinchQL Copilot. Ask any question about your AdventureWorks database to begin.'
    }
  ]);
  const [inputVal, setInputVal] = useState('');
  const [activeTab, setActiveTab] = useState('viz');
  const [queryData, setQueryData] = useState([]);
  const [executedSql, setExecutedSql] = useState('SELECT * FROM production.product;');

  const recentChats = [
    "List all unique products",
    "What is our total revenue?",
    "Top products by revenue",
    "Monthly sales breakdown"
  ];

  const handleSend = async (e, customQuestion = null) => {
    if (e) e.preventDefault();
    const queryText = customQuestion || inputVal;
    if (!queryText.trim()) return;
    
    setMessages(prev => [...prev, { role: 'user', content: queryText }]);
    if (!customQuestion) setInputVal('');

    setMessages(prev => [...prev, { role: 'assistant', content: 'Analyzing schema and executing query...' }]);

    // Dynamic backend URL: falls back to localhost if environment variable is not defined
    const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

    try {
      const response = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: queryText })
      });
      const result = await response.json();

      setMessages(prev => {
        const filtered = prev.slice(0, -1);
        return [...filtered, { role: 'assistant', content: result.answer }];
      });

      if (result.sql) setExecutedSql(result.sql);
      if (result.data) setQueryData(result.data);

    } catch (err) {
      setMessages(prev => {
        const filtered = prev.slice(0, -1);
        return [...filtered, { role: 'assistant', content: 'Error connecting to backend server.' }];
      });
    }
  };

  return (
    <div className="query-desk-layout">
      {/* SIDEBAR */}
      <aside className="qd-sidebar">
        <div className="sidebar-header">
          <div className="logo-brand">
            <span className="dot-icon"></span> 
            <h2>FinchQL</h2>
          </div>
          <button className="new-chat-btn" onClick={() => setMessages([])}>
            <span>+</span> New conversation
          </button>
        </div>

        <div className="recent-section">
          <p className="section-label">Suggested Queries</p>
          <div className="recent-list custom-scroll">
            {recentChats.map((chat, idx) => (
              <div key={idx} className="recent-item" onClick={(e) => handleSend(null, chat)}>
                <span className="chat-text">{chat}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="datasource-box">
          <p className="section-label">Data Source</p>
          <div className="ds-info">
            <span className="status-dot"></span>
            <div>
              <strong>AdventureWorks</strong>
              <p>PostgreSQL • Local Instance</p>
              <small>Connected via Agent</small>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <main className="qd-main">
        <header className="qd-topnav">
          <div className="analyst-badge">
            <div className="avatar">AI</div>
            <div>
              <h4>FinchQL Copilot</h4>
              <p>LangGraph Agentic Workflow • Gemini 2.5</p>
            </div>
          </div>
          
          <div className="topnav-actions">
            <button className="back-home-btn" onClick={onBackToHome}>
              ← Back to Home
            </button>
          </div>
        </header>

        <div className="workspace-grid">
          {/* LEFT CHAT PANEL */}
          <section className="chat-panel">
            <div className="messages-wrapper custom-scroll">
              {messages.map((msg, idx) => (
                <div key={idx} className={`message-row ${msg.role}`}>
                  <div className="message-bubble">
                    {msg.content}
                  </div>
                </div>
              ))}
            </div>

            <div className="chat-input-container">
              <form onSubmit={(e) => handleSend(e)} className="chat-form">
                <input 
                  type="text" 
                  placeholder="Ask a question about your database..." 
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                />
                <button type="submit" className="send-icon-btn">↑</button>
              </form>
              <p className="disclaimer">Powered by LangGraph, ChromaDB, and PostgreSQL.</p>
            </div>
          </section>

          {/* RIGHT CANVAS PANEL */}
          <section className="canvas-panel custom-scroll">
            <div className="canvas-tabs-container">
              <div className="tab-headers">
                <button className={`tab-btn ${activeTab === 'viz' ? 'active' : ''}`} onClick={() => setActiveTab('viz')}>
                  Results Summary
                </button>
                <button className={`tab-btn ${activeTab === 'data' ? 'active' : ''}`} onClick={() => setActiveTab('data')}>
                  Raw Data Grid ({queryData.length} rows)
                </button>
                <button className={`tab-btn ${activeTab === 'sql' ? 'active' : ''}`} onClick={() => setActiveTab('sql')}>
                  SQL Query
                </button>
              </div>

              <div className="tab-content-box">
                {activeTab === 'viz' && (
                  <div className="viz-content">
                    <h4>Execution Results Output</h4>
                    {queryData.length > 0 ? (
                      <p style={{color: 'var(--text-secondary)'}}>Successfully queried database. Check the <b>Raw Data Grid</b> tab to view full table results or the <b>SQL Query</b> tab for code.</p>
                    ) : (
                      <p style={{color: 'var(--text-muted)'}}>Ask a question on the left panel to pull live data rows from PostgreSQL.</p>
                    )}
                  </div>
                )}

                {activeTab === 'data' && (
                  <div className="table-content">
                    {queryData.length > 0 ? (
                      <table className="data-grid">
                        <thead>
                          <tr>
                            {Object.keys(queryData[0]).map((key, i) => (
                              <th key={i}>{key.toUpperCase()}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {queryData.map((row, idx) => (
                            <tr key={idx}>
                              {Object.values(row).map((val, vIdx) => (
                                <td key={vIdx}>{String(val)}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <p style={{color: 'var(--text-muted)'}}>No table data loaded yet.</p>
                    )}
                  </div>
                )}

                {activeTab === 'sql' && (
                  <div 
                    className="sql-content"
                    style={{
                      backgroundColor: '#f8fafc',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      padding: '1.25rem'
                    }}
                  >
                    <pre 
                      style={{
                        backgroundColor: '#ffffff',
                        border: '1px solid #cbd5e1',
                        borderRadius: '6px',
                        padding: '1rem',
                        margin: '0',
                        overflowX: 'auto'
                      }}
                    >
                      <code 
                        style={{
                          color: '#0f172a',
                          backgroundColor: '#ffffff',
                          fontFamily: 'Consolas, Monaco, "Courier New", Courier, monospace',
                          fontSize: '0.9rem',
                          fontWeight: '600',
                          lineHeight: '1.5',
                          display: 'block'
                        }}
                      >
                        {executedSql}
                      </code>
                    </pre>
                    <span 
                      className="exec-time"
                      style={{
                        display: 'block',
                        fontSize: '0.75rem',
                        color: '#16a34a',
                        marginTop: '0.75rem',
                        fontWeight: '500'
                      }}
                    >
                      Generated dynamically via schema mapping & LangGraph.
                    </span>
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}